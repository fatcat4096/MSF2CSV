#!/usr/bin/env python3
# Encoding: UTF-8
"""process_website.py
Returns cached_data information if still fresh 
Logs into website and updates data from Alliance Information if not
"""

import datetime
import getpass
import keyring
import os
import pickle
import string
import sys
import time

from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from parse_contents import *
from extract_traits import *
from generate_local_files import *

import traceback

# If not frozen, work in the same directory as this script.
path = os.path.dirname(__file__)

# If frozen, work in the same directory as the executable.
if getattr(sys, 'frozen', False):
	path = os.path.dirname(sys.executable)
	

# Returns a cached_data version of alliance_info, or one freshly updated from online.
def get_alliance_info(alliance_name='', cached_data='', prompt=False, force=False):

	global strike_teams

	cached_alliance_info = {}

	# Look for cached_data files. 
	cached_data_files = get_cached_data_files(cached_data)

	# If alliance specified and is in the list of cached_data files, need to check when updated last. 
	if 'cached_data-'+alliance_name+'.msf' in cached_data_files:

		# Load cached_alliance_info and ensure it's valid and fresh. 
		if valid_cached_data(cached_alliance_info, 'cached_data-'+alliance_name+'.msf', cached_data_files, force):
			print ("Using cached_data from file:", 'cached_data-'+alliance_name+'.msf')
			return cached_alliance_info

	# Or if only one cached_data file and alliance_name=='', assume this is the alliance to use. 
	elif (len(cached_data_files) == 1 and not alliance_name):

		# Load cached_alliance_info and ensure it's valid and fresh. 
		if valid_cached_data(cached_alliance_info, cached_data_files[0], cached_data_files, force):
			print ("Using cached_data from file:", cached_data_files[0])
			return cached_alliance_info

		alliance_name = cached_data_files[0].split('cached_data-')[1][:-4]

		## WE SHOULD NO LONGER BE LOOKING DIRECTLY AT SYS.ARGV. 
		## All arguments should have been properly parsed by parse_args
		## WE NEED TO CHANGE THIS TO PULL A FILENAME DIRECTLY FROM THERE.
		
		# If we double-clicked or passed this in as an argument, alliance_name won't be set automatically. 
		#if len(sys.argv)>1 and sys.argv[1] == cached_data_files[0]:
		#	alliance_name = sys.argv[1].split('cached_data-')[1][:-4]

	# Login to the website. 
	driver = login(prompt)
	
	# We are in, wait until loaded before starting
	WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.TAG_NAME, 'H4')))

	# Pull alliance information from this Alliance Info screen
	website_alliance_info  = parse_alliance(driver.page_source) 

	# If no alliance_name specified, we are defaulting to use whatever the login's alliance is.
	if not alliance_name:
		alliance_name = website_alliance_info['name']

	# If we don't have cached_data, we have to work from the website. Fall back to the login alliance_info. 
	if not [file for file in cached_data_files if file.find('cached_data-'+alliance_name+'.msf') != -1] and alliance_name != website_alliance_info['name']:
		print ("Cached_data not found for %s. Generating tables for %s instead." % (alliance_name, website_alliance_info['name']))
		alliance_name = website_alliance_info['name']

	# We're working from website if the specified alliance_name matches the website alliance_name
	working_from_website = (alliance_name == website_alliance_info['name'])
	cached_data_file     = 'cached_data-'+remove_tags(alliance_name)+'.msf'
	
	# If working_from_website, the website_alliance_info will be our baseline. 
	if working_from_website:
		alliance_info = website_alliance_info
	
		# * Does this cached_data file exist? If so, load it. 
		if cached_data_file in cached_data_files:
	
			# Load cached_alliance_info and ensure it's valid and fresh. On the website, only overt indication that something has changed is changes in membership.
			if valid_cached_data(cached_alliance_info, cached_data_file, cached_data_files, force) and alliance_info['members'].keys() == cached_alliance_info['members'].keys():
				print ("Using cached_data from file:", cached_data_file)
				driver.close()
				return cached_alliance_info	

			# So we have fresh alliance_info and the stale cached information.
			# Copy over extra information into freshly downloaded alliance_info.
			for key in cached_alliance_info:
				if key not in alliance_info:
					alliance_info[key] = cached_alliance_info[key]
					
			# Also copy over additional information inside the member definitions.
			for member in alliance_info['members']:
				for key in ['processed_chars','last_download','url']:
					if key in cached_alliance_info['members'].get(member,{}):
						alliance_info['members'][member][key] = cached_alliance_info['members'][member][key]

	# If not working_from_website, the cached_alliance_info will be our baseline. 
	else:
		alliance_info = cached_alliance_info

	# Work the website or cached URLs to update alliance_info 
	process_rosters(driver, alliance_info, working_from_website, force)

	# If working from website, use strike team definition . 
	if working_from_website:

		# Just in case file didn't exist, start by at least creating a structure to store teams in. 
		if 'strike_teams' not in globals():
			strike_teams = {}

		# Make sure we have a valid strike_team for Incursion. 
		updated = get_valid_strike_teams('incur', driver, strike_teams, alliance_info) 

		# Make sure we have a valid strike_team for Incursion. 
		updated = get_valid_strike_teams('other', driver, strike_teams, alliance_info) or updated 

		# Whatever the final result in strike_teams, stow that away in the alliance info structure for output.
		alliance_info['strike_teams'] = strike_teams
		
		# Generate strike_teams.py if we updated either definition or if this file doesn't exist locally.
		if updated or not os.path.exists(path+os.sep+'strike_teams.py'):
			generate_strike_teams(strike_teams)	

	# Close the Selenium session.
	driver.close()

	# Update extracted_traits if necessary.
	get_extracted_traits(alliance_info)

	# Keep a copy of critical stats from today's run for historical analysis.
	update_history(alliance_info)
	
	# Change working directory to the local directory and cache the updated roster info to disk.
	os.chdir(path)
	pickle.dump(alliance_info,open(cached_data_file,'wb'))

	return alliance_info


# Handle the file list cleanly.
def get_cached_data_files(cached_data):

	# Fix any files that are missing the .msf extension
	for file in [file for file in os.listdir(path) if file.find('cached_data') != -1 and file[-4:] != '.msf']:
		os.rename(path+os.sep+file, path+os.sep+file+'.msf')

	# Check to see whether we were passed a cached_data file as an argument.
	if cached_data and cached_data.find('cached_data') != -1:
		return [cached_data]

	# Otherwise, return full paths to the cached_data files in the local directory.
	return [file for file in os.listdir(path) if file.find('cached_data') != -1]


# Load cached_alliance_info and ensure it's valid and fresh. 
def valid_cached_data(cached_alliance_info, cached_data_file, cached_data_files, force):

	# Check whether file needs full-pathname to be valid.
	filename = cached_data_file
	if not os.path.exists(filename) and os.path.exists(path+os.sep+filename):
		filename = path+os.sep+filename

	# Allow us to return an updated copy.
	temp_alliance_info = pickle.load(open(filename,'rb'))
	cached_alliance_info.update(temp_alliance_info)

	# Previous version of cached_data found. Pretending the file doesn't even exist. 
	if len(cached_alliance_info) == 2:
		print ("Old format cached_data found. Will be ignored and new data downloaded.")
		cached_data_files.remove(cached_data_file)

		return False

	# If it's been less than 24 hours since last update, just return the cached data. 
	elif not force and (time.time()-os.path.getmtime(filename) < 86400):

		# If defined strike_teams are valid for this cached_data, use them.
		if 'strike_teams' in globals():

			if valid_strike_team(strike_teams['incur'], cached_alliance_info):
				print ("Using Incursion strike_team definition from strike_teams.py.")
				cached_alliance_info['strike_teams']['incur'] = strike_teams['incur']

			if valid_strike_team(strike_teams['other'], cached_alliance_info):
				print ("Using Other strike_team definition from strike_teams.py.")
				cached_alliance_info['strike_teams']['other'] = strike_teams['other']

		return True


# Process rosters for every member in alliance_info.
def process_rosters(driver, alliance_info, working_from_website, force):
	# Grab the Alliance Info url for future reference.
	alliance_url   = driver.current_url

	# Let's get a little closer to our work.
	members = alliance_info['members']

	# Use this cache to optimize our cached_data output.
	parse_cache = {}

	# Populate the parse_cache if we have existing history.  
	if 'hist' in alliance_info:
		build_parse_cache(alliance_info, parse_cache)

	# Let's iterate through the member names in alliance_info.
	for member in members:
		# Start off by checking if it's too soon. 
		if 'last_download' in members[member]:
			time_since_last = datetime.datetime.now() - members[member]['last_download']
			
			# Less than an hour since last refresh, let's skip it.
			if not force and (time_since_last.total_seconds() < 3600):
				print ("Found",member,"but too soon, skipping...")
				continue

		# Use a cached URL if available.
		if 'url' in members[member]:

			# Fix existing, cached entries.
			if 'https' in members[member]['url']:
				members[member]['url'] = members[member]['url'].split('/')[-2]
				
			#print ("Using cached URL to download",member)
			driver.get('https://marvelstrikeforce.com/en/player/%s/characters' % members[member]['url'])
			
		# Cached URL is the ONLY option if not working_from_website
		elif not working_from_website:
			print ("Skipping",member,"-- no cached URL available.")
			continue

		# Otherwise, find an active roster button for this member
		else:
			# Start off by getting back to the Alliance page if we're not already on it.
			if driver.current_url != alliance_url:
				driver.get(alliance_url)

			# If nothing returned, we didn't find it.
			if not find_members_roster(driver, member):
				continue

		process_roster(driver, alliance_info, parse_cache)


# Parse just the current Roster page.
def process_roster(driver, alliance_info, parse_cache):
	# At this point, we're on the right page. Just need to wait for it to load before we parse it.
	timer = 0
	
	# Page loads in sections, will be > 1MB after roster information loads.
	while len(driver.page_source)<1000000:
		# Still loading
		time.sleep(1)
		timer += 1
		
		# Call refresh if load failed to complete after 5 seconds.
		if timer == 5:
			driver.refresh()
		# Just give up after 10 seconds.
		elif timer == 10:
			break

	# If page loaded, pass contents to scraping routines for stat extraction.
	if len(driver.page_source)>1000000:
		member = parse_roster(driver.page_source, alliance_info, parse_cache)
	
		# Prevent second download within an hour.
		alliance_info['members'][member]['last_download'] = datetime.datetime.now()

		# Cache the URL just in case we can use this later
		alliance_info['members'][member]['url'] = driver.current_url.split('/')[-2]
		
		return member


# Use as many printable characters as possible. None of these cause problems in Discord or DOS.
ENCODING = string.digits + string.ascii_lowercase + string.ascii_uppercase + '!#$%+-./:;=?@[]{}~'


# Encode key info from alliance_info into something that fits in a DM.
def encode_alliance_info(alliance_info):
	block = []

	# Include basic info about the alliance.
	block.append(alliance_info['name'].replace(' ','_').replace('>','gt;').replace('<','lt;'))
	block.append(alliance_info['image'])
	block.append(alliance_info['stark_lvl'])
	block.append(alliance_info['trophies'])

	# Only members with a defined URL can be sent this way.
	encodable_members = [member for member in alliance_info['members'] if 'url' in alliance_info['members'][member]]

	encodable_leader   = [member for member in [alliance_info['leader']] if member in encodable_members]
	encodable_captains = [member for member in alliance_info['captains'] if member in encodable_members]

	captain_list  = encodable_leader + encodable_captains

	# Include the count of leader + captains.
	block.append(str(len(captain_list)))

	# Encode each member's URL.
	member_list = captain_list + [member for member in encodable_members if member not in captain_list]
	member_urls = [encode_url(alliance_info['members'][member]['url']) for member in member_list]
	block += member_urls

	# Encode the strike teams
	for team in ['incur','other']:
		encoded_team = ''
		for member in sum(alliance_info['strike_teams'][team],[]):
			if member in member_list:
				encoded_team += ENCODING[member_list.index(member)]
		block.append(encoded_team)
	
	# Smash it all together and hand it off.
	return ','.join(block)

	
# Decode the encoded block and populate alliance_info with stats and rosters from MSF.gg. 
def decode_alliance_info(block):
	
	alliance_info = {'members':{}}
	
	parts = block.split(',')

	alliance_info['name']  = parts[0].replace('_',' ').replace('gt;','>').replace('lt;','<')
	alliance_info['image'] = parts[1]
	
	alliance_info['stark_lvl'] = parts[2]
	alliance_info['trophies']  = parts[3]

	leader_count = int(parts[4])
	
	# These are the encoded URL fragments
	member_urls = [decode_url(part) for part in parts[5:-2]]
	
	# These are the encoded Strike Teams
	encoded_strike_teams = {}
	encoded_strike_teams['incur'] = parts[-2]
	encoded_strike_teams['other'] = parts[-1]
	
	# Start by logging in. 
	driver = login()

	# Download and parse each roster
	member_list = []
	parse_cache = {}
	for member_url in member_urls:
		driver.get('https://marvelstrikeforce.com/en/player/%s/characters' % member_url)
		member_name = process_roster(driver, alliance_info, parse_cache)
		member_list.append(member_name)

	# Close the Selenium session.
	driver.close()

	alliance_info['leader']   = member_list[0]
	alliance_info['captains'] = member_list[1:leader_count]

	# Translate the Strike Teams from the encoded format.
	strike_teams = alliance_info.setdefault('strike_teams',{})
	
	for raid_type in ['incur','other']:
		strike_team = []
		for encoded_member in encoded_strike_teams[raid_type]:
			strike_team.append(member_list[ENCODING.index(encoded_member)])

		# Break it up into chunks for each team.
		strike_teams[raid_type] = add_strike_team_dividers([strike_team[:8], strike_team[8:16], strike_team[16:]], raid_type)

	# Populate extracted_traits.
	get_extracted_traits(alliance_info)

	# Keep a copy of critical stats from today's run for historical analysis.
	update_history(alliance_info)
	
	# Change working directory to the local directory and cache the updated roster info to disk.
	os.chdir(path)
	pickle.dump(alliance_info,open('cached_data-'+remove_tags(alliance_info['name'])+'-block.msf','wb'))

	return alliance_info


# Convert to Base 92 for shorter encoding.
def encode_url(decoded):

	# Start by removing any dashes and converting to base 10 int
	pid = int(decoded.replace('-',''),16)

	# Convert from base 10 to base 92.
	encoded = []
	while pid != 0:
		pid, mod = divmod(pid, len(ENCODING))
		encoded.append(ENCODING[mod])

	return ''.join(reversed(encoded))


# Decode from base 92 and insert hyphens as needed.
def decode_url(encoded):
	pid = 0
	
	for idx in range(len(encoded)-1,-1,-1):
		pid += ENCODING.index(encoded[idx]) * len(ENCODING)**(len(encoded)-1-idx)
	decoded = hex(pid)[2:].zfill(13)
	
	# If short format, we're done.
	if len(decoded)==13:
		return decoded

	# Long format includes dashes.
	decoded = decoded.zfill(32)
	return decoded[:8]+'-'+decoded[8:12]+'-'+decoded[12:16]+'-'+decoded[16:20]+'-'+decoded[20:]
	

# Login to the website. Return the Selenium Driver object.
def login(prompt=False, url = 'https://marvelstrikeforce.com/en/alliance/members'):

	options = webdriver.ChromeOptions()
	options.add_argument('--log-level=3')
	options.add_argument('--accept-lang=en-US')	

	facebook_cred, scopely_cred = get_creds(prompt)

	# If login/password are provided, run this as a headless server.
	# If no passwords are provided, the user will need to Interactively log on to allow the rest of the process to run.
	#if scopely_cred or facebook_cred:
	#	options.add_argument('--headless=new')

	driver = webdriver.Chrome(options=options)
	driver.get(url)

	# Default to Scopely Login, does not require 2FA.
	if scopely_cred:
		scopely_login(driver, scopely_cred.username, scopely_cred.password)

	# If Scopely login not defined, use Facebook login instead.
	elif facebook_cred:
		facebook_login(driver, facebook_cred.username, facebook_cred.password)
		
	# Waiting while you login manually, automatically, or approve login via 2FA.
	try:
		WebDriverWait(driver, 300).until(EC.presence_of_element_located((By.CLASS_NAME, 'alliance-roster')))
	except TimeoutException:
		print("Timed out. Unable to complete login.")

	return driver


# Check for saved credentials. If none and never asked, ask if would like to cache them.
def get_creds(prompt):
	facebook_cred = keyring.get_credential('facebook','')
	scopely_cred  = keyring.get_credential('scopely','')

	# Check for prompt flag or presence of 'noprompt' file. 
	if prompt or not os.path.exists(path+os.sep+'noprompt'):

		# If 'noprompt' doesn't exist, prompt if person would like to cache their credentials
		if input("Would you like to cache your credentials? (Y/N): ").upper() == 'Y':

			# Ask which login they would like to use.
			if input("Would you like to cache 'F'acebook or 'S'copely credentials? (F/S): ").upper() == "F":

				# Prompt for each login and pass and store in keyring.
				login = input("Facebook Login: ")
				keyring.set_password('facebook', login, getpass.getpass(prompt="Facebook Password:"))
			else:
				login = input("Scopely Login: ")
				keyring.set_password('scopely', login, getpass.getpass(prompt="Scopely Password:"))

			# Reload both credentials before proceeding.
			facebook_cred = keyring.get_credential('facebook','')
			scopely_cred  = keyring.get_credential('scopely','')

		# Create the file so we aren't asked again. User can delete if credentials have changed.
		open(path+os.sep+'noprompt','a').close()

	return facebook_cred, scopely_cred


# Auto Login via Scopely authentication using cached credentials.
def scopely_login(driver, scopely_user, scopely_pass):
	try:
		wait = WebDriverWait(driver, 10)
	
		# Click on the Scopely Login button.
		login = wait.until(EC.element_to_be_clickable((By.ID, 'scopely-login')))
		login.click()

		# Find and enter Scopely ID for login.
		login_field = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'ant-input')))
		login_field.send_keys(scopely_user)
				
		login_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'submitButton')))
		login_button.click()

		# Enter password instead of using e-mailed link.
		use_password = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'link')))
		use_password.click()
				
		# Find login field and enter password to complete login process.
		pass_field = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'password-with-toggle')))
		pass_field.send_keys(scopely_pass)

		login_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'button')))
		login_button.click()

	except TimeoutException:
		print("Timed out. Unable to complete login.")


# Auto Login via Facebook authentication using cached credentials.
def facebook_login(driver, facebook_user, facebook_pass):
	try:
		wait = WebDriverWait(driver, 10)
	
		# Click on the Facebook Login button.
		login = wait.until(EC.element_to_be_clickable((By.ID, 'facebook-login')))
		login.click()

		# Fill in username and password.
		login_field = wait.until(EC.presence_of_element_located((By.ID,'email')))
		login_field.send_keys(facebook_user)

		pass_field = wait.until(EC.presence_of_element_located((By.ID,'pass')))
		pass_field.send_keys(facebook_pass)

		# Click the login button to generate 2FA challenge.
		login_button = wait.until(EC.element_to_be_clickable((By.ID, 'loginbutton')))
		login_button.click()

	except TimeoutException:
		print("Timed out. Unable to complete login.")


# Get back to the Alliance page, then search to find the member's name and the related Roster button.
def find_members_roster(driver, member):

	# Once member labels have populated, we're ready.
	while len(driver.find_elements(By.TAG_NAME, "H4"))<4:
		time.sleep(0.5)

	# Start by looking for the H4 label for this member. 
	member_labels = driver.find_elements(By.TAG_NAME, "H4")

	for member_label in member_labels:
		if member == member_label.text.replace('[ME]',''):
			break

		# This isn't it.
		member_label = None
	
	# This shouldn't happen. Should always be able to find Member on screen.
	if not member_label:
		print ("Couldn't find label for member",member,"-- skipping...")
		return False

	# Find the roster button in same row as the Member name and click on it. 
	buttons = driver.find_elements(By.CLASS_NAME, 'button')
	
	for button in buttons:
		if abs(member_label.location['y']-button.location['y'])<12 and button.size['width'] in (53,54):
			break
			
		# This isn't it.
		button = None

	# Abort if we couldn't find the button, or found it and it's not active.
	if not button or not button.is_enabled():
		print ("Active roster button not found for member",member,"-- skipping...")
		return False

	# Scroll so this button is visible. Subtracting 200 because it's scrolling TOO FAR DOWN.
	driver.execute_script("window.scrollTo(0, %i)" % (button.location['y']-200))

	# Use a Try / Except structure because in my testing, offscreen buttons always throw an exception, even
	# when I tell Selenium to scroll to them first. With Try/Except, first click focuses them, second succeeds.
	try:
		button.click()
	except:
		time.sleep(0.5)

		# If the URL / page title hasn't changed, try one more time
		try:
			#if 'Alliance' in driver.title:
			button.click()
		# If second exception, exit with False and move on.
		except:
			print ("Click raised exception twice for ",member,"-- skipping...")
			return False
	
	return True


# Go through a multi-stage process to find a valid strike_team definition to use.
def get_valid_strike_teams(raid_type, driver, strike_teams, alliance_info):

	# If a valid strike_team definition is in strike_teams.py --- USE THAT. 
	if valid_strike_team(strike_teams.get(raid_type,[]),alliance_info):
		# Return FALSE, nothing to update.
		return False

	# If not there, let's check on the website for a valid definition.
	print ("%s team definitions in strike_teams.py were not valid. Checking definitions on MSF.gg" % ({'incur':'Incursion','other':'Gamma'}[raid_type]))
	strike_team = get_strike_teams(driver,raid_type)

	# If valid, update strike_teams with this info
	if valid_strike_team(strike_team, alliance_info):
		print ("Using strike_team definition from website.")
		strike_teams[raid_type] = strike_team
		return True

	# If not there, let's check for one cached in the alliance_info
	if 'strike_teams' in alliance_info and valid_strike_team(alliance_info['strike_teams'][raid_type], alliance_info):
		print ("Using cached strike_team definitions from alliance_info.")
		strike_teams[raid_type] = alliance_info['strike_teams'][raid_type]
		return True
		
	# If not there, just put the member list in generic groups of 8.
	print ("Valid strike_team defintion not found. Creating default strike_team from member list.")
	members = list(alliance_info['members'])
	members.sort()

	# Break it up into chunks for each team.
	strike_teams[raid_type] = add_strike_team_dividers([members[:8], members[8:16], members[16:]], raid_type)
	return True


# Returns true if at least 75% people of the people in the Alliance are actually in the Strike Teams presented.
def valid_strike_team(strike_team, alliance_info):
	return len(set(sum(strike_team,[])).intersection(alliance_info['members'])) > len(alliance_info['members'])*.75	


# Pull Strike Team definitions from MSF.gg Lanes 
def get_strike_teams(driver,raid_type='incur'):

	strike_team = []

	# Download and parse each page for the specified Raid
	for team_num in range(3):
		driver.get('https://marvelstrikeforce.com/en/alliance/maps/raid_%s/0?strikeTeam=%i' % ({'incur':'incursion','other':'gamma_d'}[raid_type], team_num+1))

		print ("Parsing %s raid Team #%i..." % ({'incur':'Incursion','other':'Gamma'}[raid_type], team_num+1))
		# Wait until the list of Players is displayed.
		WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'alliance-user')))

		# Parse the current page.
		team_def = parse_teams(driver.page_source)

		# Add each team to the Strike Team definition
		strike_team.append(team_def)

	return add_strike_team_dividers(strike_team, raid_type)


# Add divider definitions in the right places, depending upon the raid_type
def add_strike_team_dividers(strike_team, raid_type):

	for team in strike_team:

		# Automatically use 2-3-3 lanes if Incursion.
		if raid_type == "incur":
			if len(team) > 2:
				team.insert(2,'----')
			if len(team) > 6:
				team.insert(6,'----')

		# Put a divider in the middle to reflect left/right symmetry for Greek raids.
		elif raid_type == "other":
			if len(team) > 4:
				team.insert(4,'----')

	return strike_team


# Archive the current run into the 'hist' tag for future analysis.
def update_history(alliance_info):	

	# Create the 'hist' key if it doesn't already exist.
	hist = alliance_info.setdefault('hist',{})

	# Overwrite any existing info for today.
	today = datetime.date.today()
	if today in hist:
		del hist[today]

	# Building Compare today's data vs. the most recent History entry. 
	# If anything identical to previous entry, point today's entry at the previous entry.
	
	# Create an entry for today.
	today_info = hist.setdefault(today,{})

	# Iterate through each of the members.
	for member in alliance_info['members']:
	
		# Can only examine those with processed roster information.
		if 'processed_chars' in alliance_info['members'][member]:

			# Get a little closer to our work.
			member_info = alliance_info['members'][member]
			hist_info   = hist[max(hist)].get(member)

			# Compare today's information vs the previous run.
			if member_info['processed_chars'] == hist_info:
			
				# If equal, no changes have been made or roster hasn't been resynced.
				# Point the info in processed_chars to the previous entry
				member_info['processed_chars'] = hist_info

			# Finally set today's entry to the final value.
			today_info[member] = member_info['processed_chars']

	# Keep the oldest entry, plus one per ISO calendar week. Also, purge any entries > 60 days. 
	for key in list(hist):
		if (key != today and key.isocalendar().week == today.isocalendar().week and key is not min(hist)) or today-key > datetime.timedelta(60):
			del alliance_info['hist'][key]

