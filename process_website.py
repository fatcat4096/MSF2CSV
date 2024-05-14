#!/usr/bin/env python3
# Encoding: UTF-8
"""process_website.py
Returns cached_data information if still fresh 
Logs into website and updates data from Alliance Information if not
"""

from log_utils import *

import datetime
import time
import sys
import traceback

from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

from parse_contents       import *
from generate_local_files import *
from file_io              import *
from login                import get_driver, login
from extract_traits       import add_extracted_traits
from parse_cache          import build_parse_cache
from alliance_info        import *

# Returns a cached_data version of alliance_info, or one freshly updated from online.
@timed(level=3)
def get_alliance_info(alliance_name='', prompt=False, force='', headless=False, scopely_login='', external_driver=None):

	cached_alliance_info = find_cached_data(alliance_name)

	# If we loaded a cached_data file, need to check when updated last. 
	if cached_alliance_info:

		# If we expect cached data or if it's 'fresh enough' and we aren't forcing 'fresh'. 
		if force == 'stale' or (not force and not prompt and fresh_enough(cached_alliance_info)):
			print ("Using cached_data from file:", cached_alliance_info['file_path'])

			# Update the strike team info if we have valid teams in strike_teams.py
			update_strike_teams(cached_alliance_info)
			return cached_alliance_info

	# Start by logging into the website.
	driver = login(prompt, headless, external_driver=external_driver, scopely_login=scopely_login)

	website_alliance_info = process_alliance_info(driver)

	# If no alliance_name specified, we are defaulting to use whatever the login's alliance is.
	if not alliance_name:
		alliance_name = website_alliance_info['name']

	# Now that we're guaranteed to have an alliance_name check one last time for a matching cached_data file. 
	if not cached_alliance_info:
		cached_alliance_info = find_cached_data(alliance_name)

	#
	# CHANGE THIS TO JUST **FAIL** GRACEFULLY -- IF REQUESTED INFO DOESN'T EXIST, SAY SO
	#

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
			if force == 'stale' or (not force and fresh_enough(cached_alliance_info) and alliance_info['members'].keys() == cached_alliance_info['members'].keys()):
				print ("Using cached_data from file:", cached_alliance_info['file_path'])
				
				# Update the strike team info if we have valid teams in strike_teams.py
				update_strike_teams(cached_alliance_info)
				return cached_alliance_info	

			# Update the fresh alliance_info from website with extra info from cached_data.
			update_alliance_info_from_cached(alliance_info, cached_alliance_info)

	# If not working_from_website, the cached_alliance_info will be our baseline. 
	else:
		alliance_info = cached_alliance_info

	# Make note of when we begin.
	start_time = datetime.datetime.now()

	# Work the website or cached URLs to update alliance_info 
	rosters_output = process_rosters(driver, alliance_info, working_from_website, force)

	# Close the Selenium session.
	if not external_driver:
		driver.close()

	rosters_output = roster_results(alliance_info, start_time, rosters_output)

	# Make sure we have a valid strike_team for Incursion and Other. 
	updated = get_valid_strike_teams(alliance_info) 

	# Generate strike_teams.py if we updated strike team definitions or if this file doesn't exist locally.
	if working_from_website and (updated or 'strike_teams' not in globals()):
		generate_strike_teams(alliance_info)

	# Write the collected roster info to disk in a subdirectory.
	write_cached_data(alliance_info)

	return [alliance_info,'\n'.join(rosters_output)][force == 'rosters_only']



# Wait til alliance_info is ready, then parse the contents..
@timed(level=3)
def process_alliance_info(driver, discord_user={}, scopely_login=''):

	# We are in, wait until loaded before starting
	WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.TAG_NAME, 'H4')))

	# Pull alliance information from this Alliance Info screen
	return parse_alliance(driver.page_source, discord_user, scopely_login)



# Process rosters for every member in alliance_info.
@timed(level=3)
def process_rosters(driver, alliance_info, working_from_website=False, force='', only_process=[], log_file=None):

	# Really only used for Working From Website processing.
	alliance_url   = 'https://marvelstrikeforce.com/en/alliance/members'

	# Let's get a little closer to our work.
	members = alliance_info['members']

	# If we're being called from Discord, provide the truncated output.
	rosters_only   = force == "rosters_only"
	rosters_output = []

	# Use this cache to optimize our cached_data output.
	parse_cache = {}

	# Populate the parse_cache if we have existing history.  
	if 'hist' in alliance_info:
		build_parse_cache(alliance_info, parse_cache)

	# Let's iterate through the member names in alliance_info.
	for member in list(members):

		# If only_process and this member isn't in the list, skip.
		if only_process and member not in only_process:
			continue

		# Cached URL is the ONLY option if not working_from_website
		if members[member].get('url','') in ('','auth') and not working_from_website: 
	
			# One message for bot, one for the screen.
			rosters_output.append(f'{member:17}NEED URL')
			print (f'No cached URL available -- skipping {member}')

			continue

		# Start by defining the number of retries available for each attempt. 
		retries = 3
		page_source = ''
		current_url = ''

		while retries:
			try:
				# Use a cached URL if available.
				if members[member].get('url','') not in ('','auth'):
					driver.get(f"https://marvelstrikeforce.com/en/v1/players/{members[member]['url']}/characters")

				# Or need to find an active roster button for this member
				else:

					# Start off by getting back to the Alliance page if we're not already on it.
					current_url=alliance_url
					if driver.current_url != alliance_url:
						driver.get(alliance_url)

					# If successful, the active roster button was found and clicked.
					# If nothing returned, we didn't find an active roster button.
					if not find_members_roster(driver, member, rosters_output):
						break

				# Note when we began processing
				start_time = datetime.datetime.now()
				time_limit = 6
				refreshed  = False
				
				# Page loads in sections, will be > 1MB after roster information loads.
				while (datetime.datetime.now()-start_time).seconds < time_limit:

					# Give it a moment
					time.sleep(0.25)

					page_source = driver.page_source
					current_url = driver.current_url

					# If page_source is over 700K, page has completely loaded.
					if len(page_source)>700000:
						break

				# If page loaded, pass contents to scraping routines for stat extraction.
				if len(page_source)>700000:
					member = parse_roster(page_source, alliance_info, parse_cache, member)
				# Retry if we have retries remaining. Page never fully loaded.
				elif working_from_website and (current_url == alliance_url or (datetime.datetime.now()-start_time).seconds > time_limit):
					retries -= 1
					continue
				
				# Made it out successfully. End the loop.
				break

			except (NoSuchElementException, TimeoutException, WebDriverException) as e:
				# Still have retries available?
				if retries:
					retries -= 1
					print (f"Retries left {retries}, continuing on {traceback.format_exc()}")
				# Too many retries, time to give up and bail.
				else:
					raise e
			except Exception:
				print (traceback.format_exc())
				raise Exception

		# Skip this member if invalid data provided OR if we never found a roster page.
		if not member or ('url' not in members[member] and current_url == alliance_url):
			continue

		# Only cache URL if we processed a valid roster page.
		if len(page_source)>700000:
			members[member]['url'] = current_url.split('/')[-2]

		# Did we find an updated roster? 
		last_update = members[member].get('last_update')
		time_now    = datetime.datetime.now()
		not_updated = last_update and (last_update < start_time or last_update > time_now)	# Deal with dates from .msf files imported from outside the current time zone.

		found = (f'Parsing {len(page_source):7} bytes   Found: ','')[rosters_only]+f'{member:17}'

		member_stale = is_stale(alliance_info, member)
		alliance_info['members'][member]['is_stale'] = member_stale
		stale = ''
		if alliance_info['members'][member]['is_stale']:
			stale = '/Stale'

		if not_updated:
			time_since = time_now - last_update
			result =  [f'Last upd: {time_since.days}d{int(time_since.seconds/3600): 2}h ago',f'{max(0,time_since.days):>2}d'][rosters_only]
		else:
			result = ['Updated','NEW'][rosters_only]

		# Never received Roster page to parse.
		if len(page_source) < 700000: 
			result = 'SITE DOWN'
			stale  = ''
		# Empty Roster page. Member has never synced.
		elif not alliance_info['members'][member].get('tot_power'):
			result = 'NEED SYNC'
			stale = ''

		rosters_output.append(f'{found}{result}{stale}')
		print(rosters_output[-1])

	# Keep a copy of critical stats from today's run for historical analysis.
	update_history(alliance_info)

	# Update traits info if necessary.
	add_extracted_traits(alliance_info)

	return rosters_output



@timed(level=3)
def roster_results(alliance_info, start_time, rosters_output=[]):

	# And make note of when we end.
	time_now = datetime.datetime.now()
	rosters_output.append('\nTotal time: %s seconds' % ((time_now - start_time).seconds))
	print (rosters_output[-1])

	# Get a little closer to our work. 
	members = alliance_info['members']

	# Quick report of our findings.
	updated = len([member for member in alliance_info['members'] if alliance_info['members'][member].get('last_update',start_time) > start_time])
	stale   = len([member for member in members if members[member].get('is_stale', True)])
	
	# Summarize the results of processing
	rosters_output.append(f'{updated} new, {len(members)-updated} old, {stale} stale')
	print (rosters_output[-1])

	return rosters_output



# Get back to the Alliance page, then search to find the member's name and the related Roster button.
@timed(level=3)
def find_members_roster(driver, member, rosters_output=[]):

	# Once member labels have populated, we're ready.
	while len(driver.find_elements(By.TAG_NAME, "H4"))<10:
		time.sleep(0.25)

	# Start by looking for the H4 label for this member. 
	member_labels = driver.find_elements(By.TAG_NAME, "H4")

	for member_label in member_labels:
		if member == remove_tags(member_label.text.replace('[ME]','')):
			break

		# This isn't it.
		member_label = None
	
	# This shouldn't happen. Should always be able to find Member on screen.
	if not member_label:
	
		# One message for bot, one for the screen.
		rosters_output.append(f'{member:17}NO LABEL')
		print (f'Could not find label - skipping {member}')

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

		# One message for bot, one for the screen.
		rosters_output.append(f'{member:17}NEED SYNC')
		print (f'Button not found - skipping {member}')

		return False

	# Scroll so this button is visible. Subtracting 200 because it's scrolling TOO FAR DOWN.
	driver.execute_script("window.scrollTo(0, %i)" % (button.location['y']-200))

	# Use a Try / Except structure because in my testing, offscreen buttons always throw an exception, even
	# when I tell Selenium to scroll to them first. With Try/Except, first click focuses them, second succeeds.
	try:
		time.sleep(0.50)
		button.click()
	except:
		# If the URL / page title hasn't changed, try one more time
		try:
			#if 'Alliance' in driver.title:
			time.sleep(0.50)
			button.click()
		# If second exception, exit with False and move on.
		except:

			# One message for bot, one for the screen.
			rosters_output.append(f'{member:17}EXCEPTION')
			print (f'Exception raised 2x - skipping {member}')

			return False

	time.sleep(0.50)
	return True


# If locally defined strike_teams are valid for this cached_data, use them instead
@timed(level=3)
def update_strike_teams(alliance_info):

	strike_teams_defined = 'strike_teams' in globals()

	# Temporary update strike team definitions to remove dividers and 'incur2'.
	updated = migrate_strike_teams(alliance_info)

	# Transition 'extracted_traits' to 'traits' and update missing traits.
	updated = add_extracted_traits(alliance_info) or updated

	# Fix errant Display Names.
	for member in alliance_info['members']:
		if is_valid_user_id(alliance_info['members'][member].get('display_name','')):
			del alliance_info['members'][member]['display_name']

	# Iterate through each defined strike team.
	for raid_type in ('incur','gamma'):

		# If the global definition of strike_team is valid for this alliance, let's use it. 
		if strike_teams_defined and valid_strike_team(strike_teams.get(raid_type,[]), alliance_info):

			# Make some common sense fixes and then update the alliance_info dict.
			updated = fix_strike_team(strike_teams[raid_type], alliance_info) or updated

			# Only 'updated' if we changed the cached value.
			if alliance_info.get('strike_teams',{}).get(raid_type) != strike_teams[raid_type]:
				alliance_info.setdefault('strike_teams',{})[raid_type] = strike_teams[raid_type]
				updated = True

		# If strike_teams.py is not valid, check for strike_teams cached in the alliance_info
		elif 'strike_teams' in alliance_info and valid_strike_team(alliance_info['strike_teams'].get(raid_type,[]), alliance_info):
	
			# Fix any issues. We will just update this info in cached_data.
			updated = fix_strike_team(alliance_info['strike_teams'][raid_type], alliance_info) or updated

	# Refresh the is_stale data in the file.
	update_is_stale(alliance_info)

	# If a change was made, update the cached_data file, but do not change the modification date.
	if updated:
		write_cached_data(alliance_info, timestamp='keep')

	# If no valid strike_teams.py exists, use this info as the basis.
	if not strike_teams_defined:
		generate_strike_teams(alliance_info)


# Go through a multi-stage process to find a valid strike_team definition to use.
@timed(level=3)
def get_valid_strike_teams(alliance_info):

	strike_teams_defined = 'strike_teams' in globals()

	# Update strike team definitions to remove dividers and 'incur2'.
	updated = migrate_strike_teams(alliance_info)

	for raid_type in ('incur','gamma'):

		# If a valid strike_team definition is in strike_teams.py --- USE THAT. 
		if strike_teams_defined and valid_strike_team(strike_teams.get(raid_type,[]),alliance_info):

			# If we update or fix the definition, write it to disk before we're done.
			updated = fix_strike_team(strike_teams[raid_type], alliance_info) or updated
			
			# Store the result in alliance_info.
			alliance_info.setdefault('strike_teams',{})[raid_type] = strike_teams[raid_type]

		# If strike_teams.py is missing or invalid, check for strike_teams cached in the alliance_info
		elif 'strike_teams' in alliance_info and valid_strike_team(alliance_info['strike_teams'].get(raid_type,[]), alliance_info):
	
			# Fix any issues. We will just update this info in cached_data.
			fix_strike_team(alliance_info['strike_teams'][raid_type], alliance_info)

	update_is_stale(alliance_info)

	return updated


# Update strike teams to remove dividers and 'incur2' 
@timed(level=3)
def migrate_strike_teams(alliance_info):

	updated = False

	# Update old format strike team definitions. Key off of the presence of 'incur2'.
	if 'strike_teams' in globals() and 'incur2' in strike_teams:

		# Move 'incur2' into 'incur' to start.
		strike_teams['incur'] = strike_teams.pop('incur2')

		# Remove dividers from both strike teams. We will add dividers at run time.
		for raid_type in strike_teams:
			for idx in range(len(strike_teams[raid_type])):
				strike_teams[raid_type][idx] = [member for member in strike_teams[raid_type][idx] if '--' not in member]

		# Since we changed strike_teams.py, return updated = True so calling routine will write the updated file to disk.
		updated = True
	
	# Update the alliance_info structure as well, just in case it's all we've got.
	if 'strike_teams' in alliance_info and 'incur2' in alliance_info['strike_teams']:

		# Move 'incur2' into 'incur' to start.
		alliance_info['strike_teams']['incur'] = alliance_info['strike_teams'].pop('incur2')
		
		# Remove dividers from both strike teams. We will add dividers at run time.
		for raid_type in alliance_info['strike_teams']:
			for idx in range(len(alliance_info['strike_teams'][raid_type])):
				alliance_info['strike_teams'][raid_type][idx] = [member for member in alliance_info['strike_teams'][raid_type][idx] if '--' not in member]

		if 'trophies' in alliance_info:
			del alliance_info['trophies']
			del alliance_info['stark_lvl']

	if 'admin' not in alliance_info:
		alliance_info['admin'] = {'name':'fatcat4096', 'id':564592015975645184}
		updated = True

	return updated
		

# Returns true if at least 2/3 people of the people in the Alliance are actually in the Strike Teams presented.
@timed(level=3)
def valid_strike_team(strike_team, alliance_info):
	return len(set(sum(strike_team,[])).intersection(alliance_info['members'])) > len(alliance_info['members'])*.5	


# Before we take the strike_team.py definition as is, let's fix some common problems.
@timed(level=3)
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
	if still_to_find and len(still_to_find) <= len(not_yet_found):

		updated = True

		# Put each of the new players into the old players spots.
		for idx in range(len(still_to_find)):
			old_player_name = not_yet_found[idx]
			new_player_name = still_to_find[idx]

			# Find and replace them one by one.
			for team in strike_team:
				if old_player_name in team:
					team[team.index(old_player_name)] = new_player_name

	return updated


# Calculate is_stale for each member and cache in alliance_info.
def update_is_stale(alliance_info):
	for member in alliance_info['members']:
		alliance_info['members'][member]['is_stale'] = is_stale(alliance_info, member)

