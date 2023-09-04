
from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from parse_contents import *
from extract_traits import *
from generate_strike_teams import *

import datetime
import getpass
import keyring
import os
import pickle
import sys
import time

'''
Addl: Need to change strike_teams to be dict with keys defined for 'gamma','incur','other'. Ultimately, users can define their own keys and specify which key they want to use in their out output, but these three should be standard.  
Addl: Make sure strike_teams are loaded prior to loading the rest of the data so they can be passed in and cached inside the alliance_info structure. This way we can still render output when working with another alliance.
'''
def get_alliance_info(alliance_name='', force=False):

	# Value for checking freshness of cached_data files, 86400 seconds = one day.
	stale_period = 86400

	# If updated recently, use this to determine whether cached_data is stale.
	if os.path.exists('strike_teams.py'):
		stale_period = min(86400,os.path.getmtime('strike_teams.py'))

	# Look for cached_data files. 
	cached_data_files = [file for file in os.listdir() if file.find('cached_data') != -1]
	
	# If alliance specified and is in the list of cached_data files, need to check when updated last. 
	# Or if only one cached_data file and alliance_name=='', assume this is the alliance to use. 
	if 'cached_data-'+alliance_name in cached_data_files or (len(cached_data_files) == 1 and not alliance_name):

		# Base case, checking if cached_data stale
		cached_data_file = ['cached_data-'+alliance_name,cached_data_files[0]][not alliance_name]
		cached_alliance_info =  pickle.load(open(cached_data_file,'rb'))

		# If it's been less than 24 hours since last update, just return the cached data. 
		if not force and (time.time()-os.path.getmtime(cached_data_file) < stale_period):
			return cached_alliance_info
	
	# Login to the website. 
	driver = login()
	
	# We are in, wait until loaded before starting.
	WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.TAG_NAME, 'H4')))

	# Pull alliance information from this Alliance Info screen
	website_alliance_info  = parse_alliance(driver.page_source) 

	# If no alliance_name specified, we are defaulting to use whatever the login's alliance is.
	if not alliance_name:
		alliance_name = website_alliance_info['name']

	# If we don't have cached_data, we have to work from the website. Fall back to the login alliance_info. 
	if 'cached_data-'+alliance_name not in cached_data_files and alliance_name != website_alliance_info['name']:
		print ("Cached_data not found for %s. Generating tables for %s instead." % (alliance_name, website_alliance_info['name']))
		alliance_name = website_alliance_info['name']

	# We're working from website if the specified alliance_name matches the website alliance_name
	working_from_website = (alliance_name == website_alliance_info['name'])
	cached_data_file     = 'cached_data-'+alliance_name
	
	# If working_from_website, the website_alliance_info will be our baseline. 
	if working_from_website:
		alliance_info = website_alliance_info
	
		# * Does this cached_data file exist? If so, load it. 
		if cached_data_file in cached_data_files:
			cached_alliance_info = pickle.load(open(cached_data_file,'rb'))

			# If member lists are identical and it's been less than 24 hours since last update, just return the cached data. 
			if not force and alliance_info.keys() == cached_alliance_info.keys() and (time.time()-os.path.getmtime(cached_data_file) < stale_period):
				driver.close()
				return cached_alliance_info

			# So we have fresh alliance_info and the stale cached information.
			# Copy over extra information into freshly downloaded alliance_info.
			alliance_info['trait_file']       = cached_alliance_info['trait_file']
			alliance_info['extracted_traits'] = cached_alliance_info['extracted_traits']
			alliance_info['portraits']        = cached_alliance_info['portraits']
			alliance_info['strike_teams']     = cached_alliance_info['strike_teams']
			
			for member in alliance_info['members']:
				for key in ['processed_chars','last_download','url']:
					if key in cached_alliance_info['members'][member]:
						alliance_info['members'][member][key] = cached_alliance_info['members'][member][key]

	# If not working_from_website, the cached_alliance_info will be our baseline. 
	else:
		alliance_info = cached_alliance_info

	# Work the website or cached URLs to update alliance_info 
	process_rosters(driver, alliance_info, working_from_website, force)

	# Close the Selenium session.
	driver.close()

	# Update extracted_traits if necessary.
	get_extracted_traits(alliance_info)

	# Generate strike_teams.py if one doesn't exist locally already.
	if 'strike_teams' not in sys.modules:
		global strike_teams
		strike_teams = generate_strike_teams(list(alliance_info['members']))	

	# Update the strike_teams definition in alliance_info if majority of the members listed in them are actually in the alliance. 
	if len(set(sum(sum(strike_teams.values(),[]),[])).intersection(alliance_info['members'])) > len(alliance_info['members']) / 2:
		alliance_info['strike_teams'] = strike_teams

	# cache the updated roster info to disk.
	pickle.dump(alliance_info,open(cached_data_file,'wb'))

	return alliance_info


def process_rosters(driver, alliance_info, working_from_website, force):
	# Grab the Alliance Info title/url for future reference.
	alliance_title = driver.title
	alliance_url   = driver.current_url

	# Let's get a little closer to our work.
	members = alliance_info['members']

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
			#print ("Using cached URL to download",member)
			driver.get(members[member]['url'])
		# Cached URL is the ONLY option if not working_from_website
		elif not working_from_website:
			print ("Skipping",member,"-- no cached URL available.")
			continue
		# Otherwise, if working from website, we can look for a button.
		else:
			#print("Looking for roster button for",member)
			# Start off by getting back to the Alliance page if we're not already on it.
			if driver.current_url != alliance_url:

				# Request the alliance page and then wait until we get back to it.
				driver.get(alliance_url)
				time.sleep(1)

				# Once the title indicates we're back, continue.
				while driver.title != alliance_title:
					time.sleep(1)

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
				continue

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
				continue

			# Scroll so this button is visible.
			driver.execute_script("window.scrollTo(0, %i)" % button.location['y'])
		
			# Use a Try / Except structure because in my testing, offscreen buttons always throw an exception, even
			# when I tell Selenium to scroll to them first. With Try/Except, first click focuses them, second succeeds.
			try:
				button.click()
			except:
				time.sleep(0.5)
				button.click()
		
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
			parse_roster(driver.page_source, alliance_info)
		
			# Prevent second download within an hour.
			members[member]['last_download'] = datetime.datetime.now()

			# Cache the URL just in case we can use this later
			members[member]['url'] = driver.current_url


# Login to the website. Return the Selenium Driver object.
def login(url = 'https://marvelstrikeforce.com/en/alliance/members'):

	options = webdriver.ChromeOptions()
	options.add_argument('--log-level=3')

	facebook_cred, scopely_cred = get_creds()

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


# Check for saved credentials. If none and never asked, ask if would like to cache them.
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


# Update the Character Trait information using the latest info from website.
def get_extracted_traits(alliance_info):
	# If the old trait file isn't being used, extracted_traits needs to be updated.
	if 'trait_file' not in alliance_info or alliance_info['trait_file'] not in alliance_info['scripts']:
		print ("Extracted traits location has changed...updating.")
		for script in alliance_info['scripts']:
			extracted_traits = extract_traits(script)

			# If this file was correctly parsed, store this new trait file.
			if extracted_traits:
				print ("Found extracted traits in",script)

				# Remember which script was the valid trait file
				alliance_info['trait_file'] = script
				alliance_info['extracted_traits'] = extracted_traits
				break
