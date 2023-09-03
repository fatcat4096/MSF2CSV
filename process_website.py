
from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from parse_contents import *
from extract_traits import *

import datetime
import getpass
import keyring
import os
import pickle
import time

alliance_name = "SIGMA Infamously Strange"

'''
Planned changes in workflow.

1. If no alliance passed in, we are defaulting to use whatever the login's alliance is.

* If no cached_data file exists, first run, clearly we need to login.
* If only one cached_data file exists, assume this is the login alliance. Use the modification time of this file to control whether we just return cached data or proceed to website.
* If multiple cached_data files exist, unknown which is default -- login and get alliance info. Once alliance_info['name'] is known, bail if alliance_name = '' and modification time of cached_data+alliance_info['name'] is too new.

? Any strategy to use if no alliance specified and multiple cached_data files exist? Should we be writing a default alliance hint somewhere so that we can tell which file is to be used and what to base the calculation upon? (I think so. Would obviate the need for third case above.)

2. If alliance name is passed in, this is the alliance we are basing our login on. 

* If no cached_data file for this alliance, first run, clearly we need to login. 
* If cached_data file exists for this alliance, use the modification time of this file to control whether we just return cached data or proceed to website.

3. If we proceed to website, download alliance_info.
4 If alliance_name = '' and modification time of cached_data+alliance_info['name'] is too new, bail.
5 If alliance_name == alliance_info['name'] this is the base case, we are updating the info for the login player's alliance. 
	* Use local definitions of strike_teams for output. Store the current values of strike_teams in alliance_info. 
	* Remove any members in processed_players who are no longer in the alliance.
	* Walk down the list of the members in the alliance_info['order'] list. 
		* If URL is known for player just get this page and parse data. Update if total power has changed since last update.
		* If URL is unknown for player, get URL for main alliance table, find appropriate button, scroll, and click. Update alliance_info['members'][member]['url'] with current URL.
	* Save the result in cached_data- + alliance_info['name']

6. If alliance_name != alliance_info['name'] then we are being told to update data for an alliance which is not the login. 
	* alliance_info = processed_chars['alliance_info']
	* Walk down the list of the members in the alliance_info['order'] list.
		* If URL is known for player, just get this page and parse data. Update if total power has changed since last update.
		* If URL is unknown for player, skip this player.
	* Save the result in cached_data- + alliance_info['name']


Addl: Need to change strike_teams to be dict with keys defined for 'gamma','incur','other'. Ultimately, users can define their own keys and specify which key they want to use in their out output, but these three should be standard.  
Addl: Make sure strike_teams are loaded prior to loading the rest of the data so they can be passed in and cached inside the processed_chars['alliance_info'] structure. This way we can still render output when working with another alliance.
Addl: At some point, do away with char_stats. Do stat analysis of each hero in the table prior to rendering. Just build info for the characters and keys included in each table. Less crap to lug around. (Hide extracted_traits in alliance_info instead.) 

'''

def process_website(alliance_name=alliance_name, force=False):

	char_stats        = {}
	processed_players = {}

	# Load cached roster info from pickled data, this is possibly stale, but we will attempt to refresh.
	if os.path.exists('cached_data-'+alliance_name):
		[char_stats,processed_players] = pickle.load(open('cached_data-'+alliance_name,'rb'))

		# If it's been less than 24 hours since last update, just return the cached data. 
		if not force and (time.time()-os.path.getmtime('cached_data-'+alliance_name) < 86400):
			return char_stats,processed_players

	# Let's get fresh data from the website.

	# Login to the website. 
	driver = login()

	# We are in, wait a second before starting.
	time.sleep(1)

	# Grab the Alliance Info title/url for future reference.
	alliance_title = driver.title
	alliance_url   = driver.current_url
	
	# Pull alliance information from this Alliance Info screen
	alliance_info  = parse_alliance(driver.page_source) 

	# DOES THE ALLIANCE I LOGGED INTO MATCH THE NAME OF THE ALLIANCE I AM EXPECTING?
	#if alliance_info['name'] == alliance_name:
	
		# IF SO, I CAN UPDATE STRIKE TEAMS AND ROSTERS AND ALLIANCE INFO WITH THIS DATA
		
		# IF NOT, I SHOULD USE THE ALLIANCE_INFO FROM THE CACHED DATA TO UPDATE ROSTERS.

	# Remove any members in processed_players who are no longer in the alliance.
	for member in list(processed_players):
		if member != 'alliance_info' and member not in alliance_info['members']:
			print ('%s is no longer in this alliance. Removing from the output.' % member)
			del processed_players[member]

	# Let's use the h4 headers to drive Roster extraction.
	members = driver.find_elements(By.TAG_NAME, "H4")
	
	for index in range(len(members)):
		member = driver.find_elements(By.TAG_NAME, "H4")[index]

		if member.text:
			#print ("Looking for roster button for",member.text,"...")
			
			# Find the relevant button.
			buttons = driver.find_elements(By.CLASS_NAME, 'button')
			
			for button in buttons:

				if abs(member.location['y']-button.location['y'])<12 and button.size['width'] in (53,54):
					break
					
				# This isn't it.
				button = None

			# If button on screen, but not enabled, member needs to login and resync before we can use.
			if not button.is_enabled():
				#print ("Roster button is not clickable. On to next H4 entry!")
				continue

			# Scroll so this button is visible.
			driver.execute_script("window.scrollTo(0, %i)" % button.location['y'])
			
			# We found a Roster Button. Should we click it?
			# If we already have an entry for this person, see if it's up-to-date/recent
			member = member.text.replace('[ME]','')
			
			if member in processed_players and 'last_download' in processed_players[member]:
				time_since_last = datetime.datetime.now()-processed_players[member]['last_download']
				
				# Less than an hour since last refresh, or power hasn't changed, let's skip it.
				if not force and ((time_since_last.total_seconds() < 3600) or (processed_players[member]['tot_power'] == alliance_info['members'][member]['tcp'])):
					print ("Found",member,"but",["too soon,","unchanged,"][time_since_last.total_seconds() > 3600],"skipping...")
					continue

			try:
				button.click()
			except:
				time.sleep(0.5)
				button.click()

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
				parse_roster(driver.page_source, char_stats, processed_players)
				processed_players[member]['last_download'] = datetime.datetime.now()
			
			# Cache the URL just in case we can use this later
			alliance_info['members'][member]['url'] = driver.current_url
			
			# Back up and move on to the next roster on the page.
			driver.back()
			time.sleep(1)
			while driver.title != alliance_title:
				time.sleep(1)

	# While we are in, let's double check the Strike Teams defined for Incursion and Gamma 4.5
	
	# Same strike teams are defined for all difficulties.  
	#incur_strike_teams = get_strike_teams(driver,'incursion')
	#other_strike_teams = get_strike_teams(driver,'gamma_d')
	
	# Close the Selenium session.
	driver.close()

	# After everything, update processed_players with the current alliance_info.
	processed_players['alliance_info'] = alliance_info
	
	# If the old trait file isn't being used, extracted_traits needs to be updated.
	if 'trait_file' not in char_stats or char_stats['trait_file'] not in alliance_info['scripts']:
		print ("Extracted traits location has changed...updating.")
		for script in alliance_info['scripts']:
			extracted_traits = extract_traits(script)

			# If this file was correctly parsed, store this new trait file.
			if extracted_traits:
				print ("Found extracted traits in",script)

				# Remember which script was the valid trait file
				char_stats['trait_file'] = script
				char_stats['extracted_traits'] = extracted_traits
				break
		
	# cache the updated roster info to disk.
	pickle.dump([char_stats,processed_players],open('cached_data-'+alliance_name,'wb'))

	return char_stats,processed_players


def get_strike_teams(driver,raid='alpha_d',diff=0):
	#
	strike_teams = []
	#
	for team_num in range(3):
		wait = WebDriverWait(driver, 10)
		#
		driver.get('https://marvelstrikeforce.com/en/alliance/maps/raid_%s/%i?strikeTeam=%i' % (raid, diff, team_num+1))
		wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'alliance-user')))
		#
		strike_teams.append(parse_teams(driver.page_source))
	#
	return strike_teams


def login():

	alliance_path = 'https://marvelstrikeforce.com/en/alliance/members'

	options = webdriver.ChromeOptions()
	options.add_argument('--log-level=3')

	facebook_cred, scopely_cred = get_creds()

	# If login/password are provided, run this as a headless server.
	# If no passwords are provided, the user will need to Interactively log on to allow the rest of the process to run.
	#if scopely_cred or facebook_cred:
	#	options.add_argument('--headless=new')
	
	driver = webdriver.Chrome(options=options)
	driver.get(alliance_path)

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

	# Check for page language. Change to English if necessary.
	try:
		if driver.find_element(By.TAG_NAME, 'html').get_attribute('lang') != 'en_US':
			wait = WebDriverWait(driver, 10)
			
			# Click on language selection
			language = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'language-selector')))
			language.click()
			
			# Select English language 
			english = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.language-selector a[title="English"]')))
			english.click()
	except TimeoutException:
		print("Timed out. Unable to switch to english.")

	return driver


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


def get_creds():
	facebook_cred = keyring.get_credential('facebook','')
	scopely_cred  = keyring.get_credential('scopely','')

	# If no credentials are entered, check for presence of 'noprompt' file. 
	if not os.path.exists('noprompt'):

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
		open('noprompt','a').close()

	return facebook_cred, scopely_cred