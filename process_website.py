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
def get_alliance_info(alliance_name='', prompt=False, force='', headless=False):

	cached_alliance_info = find_cached_data(alliance_name)

	# If we loaded a cached_data file, need to check when updated last. 
	if cached_alliance_info:

		# If we didn't pass in an alliance_name but found a single MSF file, define alliance_name now
		if not alliance_name:
			alliance_name = cached_alliance_info['name']
			
		# If we expect cached data or if it's 'fresh enough' and we aren't forcing 'fresh'. 
		if force == 'stale' or (force != 'fresh' and fresh_enough(cached_alliance_info)):
			print ("Using cached_data from file:", cached_alliance_info['file_path'])

			# Update the strike team info if we have valid teams in strike_teams.py
			update_strike_teams(cached_alliance_info)
			return cached_alliance_info

	# Login to the website. 
	driver = login(prompt, headless)
	
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
			if force == 'stale' or (force != 'fresh' and fresh_enough(cached_alliance_info) and alliance_info['members'].keys() == cached_alliance_info['members'].keys()):
				print ("Using cached_data from file:", cached_alliance_info['file_path'])
				
				# Update the strike team info if we have valid teams in strike_teams.py
				update_strike_teams(cached_alliance_info)
				return cached_alliance_info	

			# So we have fresh alliance_info and the stale cached information.
			# Copy over extra information into freshly downloaded alliance_info.
			for key in cached_alliance_info:
				if key not in alliance_info:
					alliance_info[key] = cached_alliance_info[key]
					
			# Also copy over additional information inside the member definitions. 
			for member in alliance_info['members']:
				for key in ['processed_chars','url','other_data','max','arena','blitz','stars','red','tot_power','last_update']:
					if key in cached_alliance_info['members'].get(member,{}) and key not in alliance_info['members'][member]:
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

		# Make sure we have a valid strike_team for Incursion and Other. 
		updated = get_valid_strike_teams(alliance_info) 

	# Update extracted_traits if necessary.
	add_extracted_traits(alliance_info)

	# Keep a copy of critical stats from today's run for historical analysis.
	update_history(alliance_info)

	# Write the collected roster info to disk in a subdirectory.
	write_cached_data(alliance_info)

	return alliance_info


# Has is been less than 24 hours since last update of cached_data?
def fresh_enough(alliance_info):
	return time.time()-os.path.getmtime(alliance_info['file_path']) < 86400


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
	for member in list(members):

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
		if member == remove_tags(member_label.text.replace('[ME]','')):
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


# If locally defined strike_teams are valid for this cached_data, use them instead
# Only change we can make if relying on cached alliance info.
def update_strike_teams(alliance_info):

	strike_teams_defined = 'strike_teams' in globals()

	# Verify we have global definitions of strike_teams before starting. 
	if strike_teams_defined:

		# Iterate through each defined strike team.
		for raid_type in strike_teams:

			# If the strike_team is valid for this alliance, let's use it.
			if valid_strike_team(strike_teams.get(raid_type,[]), alliance_info):
			
				# Make some common sense fixes and then update the alliance_info dict.
				fix_strike_team(strike_teams[raid_type], alliance_info)
				alliance_info['strike_teams'][raid_type] = strike_teams[raid_type]

	# If no strike_teams.py exists, go ahead and use this info as the basis.
	if not strike_teams_defined:
		generate_strike_teams(alliance_info)


# Returns true if at least 2/3 people of the people in the Alliance are actually in the Strike Teams presented.
def valid_strike_team(strike_team, alliance_info):
	return len(set(sum(strike_team,[])).intersection(alliance_info['members'])) > len(alliance_info['members'])*.66	


# Before we take the strike_team.py definition as is, let's fix some common problems.
def fix_strike_team(strike_team, alliance_info):

	updated = False

	player_names  = list(alliance_info['members'])
	player_lower  = [name.lower() for name in player_names]

	# Make a copy to keep track of who we've found and who we haven't.
	still_to_find = player_names[:]
	not_yet_found = []

	# Start with looking for capitalization issues.
	for team in strike_team:

		# Fix any capitalization issues.
		for idx in range(len(team)):
			player_name = team[idx]

			# If can't find, maybe they just got the wrong case? Fix it silently, if so.
			if player_name not in player_names and player_name.lower() in player_lower:
				team[idx] = player_names[player_lower.index(player_name.lower())]
				updated = True

			# If we found it, remove it from the list to find.
			if team[idx] in still_to_find:
				still_to_find.remove(team[idx])
			# If not a divider, note that we didn't find this one.
			elif '--' not in team[idx]:
				not_yet_found.append(team[idx])
	
	# After everything, if we have the same number both missing and extra, 
	# assume we have replaced the missing people with the leftover ones.
	if len(still_to_find) == len(not_yet_found):

		updated = True

		# Put each of the new players into the old players spots.
		for idx in range(len(not_yet_found)):
			old_player_name = not_yet_found[idx]
			new_player_name = still_to_find[idx]

			# Find and replace them one by one.
			for team in strike_team:
				if old_player_name in team:
					team[team.index(old_player_name)] = new_player_name

	return updated


# Go through a multi-stage process to find a valid strike_team definition to use.
def get_valid_strike_teams(alliance_info):

	# Just in case file didn't exist, start by at least creating a structure to store teams in. 
	strike_teams_defined = 'strike_teams' in globals()

	updated = False

	for raid_type in ['incur','other']:

		# If a valid strike_team definition is in strike_teams.py --- USE THAT. 
		# If we update or fix the definition, write it to disk before we're done.
		if strike_teams_defined and valid_strike_team(strike_teams.get(raid_type,[]),alliance_info):
			print ("Using strike team definitions from strike_teams.py")

			# Keep track if there are any fixes to make
			updated = fix_strike_team(strike_teams[raid_type], alliance_info) or updated
			
			# Store the result in alliance_info.
			alliance_info.setdefault('strike_teams',{})[raid_type] = strike_teams[raid_type]

		# If strike_teams.py is missing or invalid, check for strike_teams cached in the alliance_info
		elif 'strike_teams' in alliance_info and valid_strike_team(alliance_info['strike_teams'].get(raid_type,[]), alliance_info):
			print ("Using cached strike_team definitions from alliance_info.")
	
			# Fix any issues. We will just update this info in cached_data.
			fix_strike_team(alliance_info['strike_teams'][raid_type], alliance_info)

		# No valid strike_team definitions found. Fall back to alphabetical list of members. 
		else:
			# If not there, just put the member list in generic groups of 8.
			print ("Valid strike_team defintion not found. Creating default strike_team from member list.")
			
			# Get member_list and sort them.
			members = sorted(alliance_info['members'],key=str.lower)

			# Break it up into chunks and add the appropriate dividers.
			alliance_info.setdefault('strike_teams',{})[raid_type] = add_strike_team_dividers(members, raid_type)

			# And if we didn't have a locally sourced strike_teams.py, go ahead and write this file to disk.
			if not strike_teams_defined:
				updated = True
	
	# Generate strike_teams.py if we updated either definition or if this file doesn't exist locally.
	if updated or not strike_teams_defined:
		generate_strike_teams(alliance_info)


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
