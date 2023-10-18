#!/usr/bin/env python3
# Encoding: UTF-8
"""process_website.py
Returns cached_data information if still fresh 
Logs into website and updates data from Alliance Information if not
"""

import datetime
import os
import sys
import time


from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from parse_contents       import *
from generate_local_files import *
from file_io              import *
from login                import login
from extract_traits       import add_extracted_traits
from parse_cache          import build_parse_cache
from alliance_info        import update_history


# Returns a cached_data version of alliance_info, or one freshly updated from online.
def get_alliance_info(alliance_name='', prompt=False, force=False):

	global strike_teams

	cached_alliance_info = find_cached_data(alliance_name)

	# If we loaded a cached_data file, need to check when updated last. 
	if cached_alliance_info:

		# If we didn't pass in an alliance_name but found a single MSF file, define alliance_name now
		if not alliance_name:
			alliance_name = cached_alliance_info['name']
			
		# Verify the cached_data is not too old. 
		if not force and fresh_cached_data(cached_alliance_info):
			print ("Using cached_data from file:", cached_alliance_info['file_path'])
			return cached_alliance_info

	# Login to the website. 
	driver = login(prompt)
	
	# We are in, wait until loaded before starting
	WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.TAG_NAME, 'H4')))

	# Pull alliance information from this Alliance Info screen
	website_alliance_info  = parse_alliance(driver.page_source) 

	# If no alliance_name specified, we are defaulting to use whatever the login's alliance is.
	if not alliance_name:
		alliance_name = website_alliance_info['name']

	# Now that we're guaranteed to have an alliance_name check one last time for a matching cached_data file. 
	if not cached_alliance_info:
		cached_alliance_info = find_cached_data(alliance_name)

	# If we don't have cached_data, we have to work from the website. Fall back to the login alliance_info. 
	if not cached_alliance_info and alliance_name != website_alliance_info['name']:
		print ("Cached_data not found for %s. Collecting info for %s instead." % (alliance_name, website_alliance_info['name']))
		alliance_name = website_alliance_info['name']

		# Final chance, check for an existing cached_data using the website_alliance_info's alliance_name
		cached_alliance_info = find_cached_data(alliance_name)

	# We're working from website if the specified alliance_name matches the website alliance_name
	working_from_website = (alliance_name == website_alliance_info['name'])

	# If working_from_website, the website_alliance_info will be our baseline. 
	if working_from_website:
		alliance_info = website_alliance_info
	
		# If we found cached_alliance_info, should we use it as-is or update the website info?
		if cached_alliance_info:
	
			# If fresh data and no membership changes, let's just use it as-is.
			if not force and fresh_cached_data(cached_alliance_info) and alliance_info['members'].keys() == cached_alliance_info['members'].keys():
				print ("Using cached_data from file:", cached_alliance_info['file_path'])
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

	# Close the Selenium session.
	driver.close()

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
		if updated or not os.path.exists(get_local_path()+'strike_teams.py'):
			generate_strike_teams(strike_teams)	

	# Update extracted_traits if necessary.
	add_extracted_traits(alliance_info)

	# Keep a copy of critical stats from today's run for historical analysis.
	update_history(alliance_info)

	# Write the collected roster info to disk in a subdirectory.
	write_cached_data(alliance_info)

	return alliance_info


# Load cached_alliance_info and ensure it's valid and fresh. 
def fresh_cached_data(cached_alliance_info):

	# If it's been less than 24 hours since last update, just return the cached data. 
	if time.time()-os.path.getmtime(cached_alliance_info['file_path']) < 86400:

		# If defined strike_teams are valid for this cached_data, use them.
		if 'strike_teams' in globals():

			if valid_strike_team(strike_teams['incur'], cached_alliance_info) and cached_alliance_info['strike_teams']['incur'] != strike_teams['incur']:
				print ("Updating Incursion strike_team definition from strike_teams.py.")
				cached_alliance_info['strike_teams']['incur'] = strike_teams['incur']

			if valid_strike_team(strike_teams['other'], cached_alliance_info) and cached_alliance_info['strike_teams']['other'] != strike_teams['other']:
				print ("Updating Other strike_team definition from strike_teams.py.")
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

			print ('Cached URL....',end='')
			
		# Cached URL is the ONLY option if not working_from_website
		elif not working_from_website:
			print ("Skipping",member,"-- no cached URL available.")
			continue

		# Otherwise, find an active roster button for this member
		else:
			print ('Roster Link...',end='')

			# Start off by getting back to the Alliance page if we're not already on it.
			if driver.current_url != alliance_url:
				driver.get(alliance_url)

			# If nothing returned, we didn't find it.
			if not find_members_roster(driver, member):
				continue

		process_roster(driver, alliance_info, parse_cache, member)


# Parse just the current Roster page.
def process_roster(driver, alliance_info, parse_cache, member=''):
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
	if len(driver.page_source)<1000000:
		print ("Failed to load a valid roster -- skipping...")
	else:
		member = parse_roster(driver.page_source, alliance_info, parse_cache, member)
	
		# Prevent second download within an hour.
		alliance_info['members'][member]['last_download'] = datetime.datetime.now()

		# Cache the URL just in case we can use this later
		alliance_info['members'][member]['url'] = driver.current_url.split('/')[-2]
		
		return member


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

	print ("%s team definitions in strike_teams.py were not valid." % ({'incur':'Incursion','other':'Gamma'}[raid_type]))

	# If not there, let's check for one cached in the alliance_info
	if 'strike_teams' in alliance_info and valid_strike_team(alliance_info['strike_teams'][raid_type], alliance_info):
		print ("Using cached strike_team definitions from alliance_info.")
		strike_teams[raid_type] = alliance_info['strike_teams'][raid_type]
		return True
		
	# If not there, just put the member list in generic groups of 8.
	print ("Valid strike_team defintion not found. Creating default strike_team from member list.")
	members = list(alliance_info['members'])
	members.sort(key=str.lower)

	# Break it up into chunks and add the appropriate dividers.
	strike_teams[raid_type] = add_strike_team_dividers(members, raid_type)
	return True


# Returns true if at least 2/3 people of the people in the Alliance are actually in the Strike Teams presented.
def valid_strike_team(strike_team, alliance_info):
	return len(set(sum(strike_team,[])).intersection(alliance_info['members'])) > len(alliance_info['members'])*.66	


# Add divider definitions in the right places, depending upon the raid_type
def add_strike_team_dividers(strike_team, raid_type):

	# Break it up into chunks for each team.
	strike_team = [strike_team[:8], strike_team[8:16], strike_team[16:]]

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
