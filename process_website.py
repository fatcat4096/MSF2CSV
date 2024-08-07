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
def get_alliance_info(alliance_name='', prompt=False, force='', headless=False, scopely_login=''):

	cached_alliance_info = find_cached_data(alliance_name)

	# If we loaded a cached_data file, need to check when updated last. 
	if cached_alliance_info:

		# If we expect cached data or if it's 'fresh enough' and we aren't forcing 'fresh'. 
		if force == 'stale' or (not force and not prompt and fresh_enough(cached_alliance_info)):
			print ("Using cached_data from file:", cached_alliance_info['file_path'])

			# Update the strike team info if we have valid teams in strike_teams.py
			update_strike_teams(cached_alliance_info)
			return cached_alliance_info

		# If no alliance_name specified but we found one obvious candidate, report that we are using it.
		if not alliance_name:
			alliance_name = cached_alliance_info['name']
			print (f"Defaulting to alliance from cached_data: {alliance_name}.")

	# Start by logging into the website.
	driver = login(prompt, headless, scopely_login=scopely_login)

	website_alliance_info = parse_alliance(driver)

	# If no alliance_name specified, use the login's alliance.
	if not alliance_name:
		alliance_name = website_alliance_info['name']
		print (f"Defaulting to alliance from website login: {alliance_name}.")

	# Now that we're guaranteed to have an alliance_name check one last time for a matching cached_data file. 
	if not cached_alliance_info:
		cached_alliance_info = find_cached_data(alliance_name)

	# We're working from website if the specified alliance_name matches the website alliance_name
	working_from_website = (alliance_name.lower() == website_alliance_info['name'].lower())

	# If we haven't found cached_data and the alliance requested is NOT the one from the login, fail gracefully. 
	if not working_from_website:
		print (f"Alliance requested doesn't match login alliance: {alliance_name}. Aborting.")
		return

	# If working_from_website, the website_alliance_info will be our baseline. 
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

	# Make note of when we begin.
	start_time = datetime.datetime.now()

	# Work the website or cached URLs to update alliance_info 
	process_rosters(driver, alliance_info, working_from_website)

	# Close the Selenium session.
	driver.close()

	# Print a summary of the results.
	roster_results(alliance_info, start_time)

	# Make sure we have a valid strike_team for Incursion and Other. 
	updated = get_valid_strike_teams(alliance_info) 

	# Generate strike_teams.py if we updated strike team definitions or if this file doesn't exist locally.
	if updated or 'strike_teams' not in globals():
		generate_strike_teams(alliance_info)

	# Write the collected roster info to disk in a subdirectory.
	write_cached_data(alliance_info)

	return alliance_info



# Process rosters for every member in alliance_info.
@timed(level=3)
def process_rosters(driver, alliance_info, working_from_website=False, only_process=[], roster_csv_data={}, log_file=None):

	# Really only used for Working From Website processing.
	alliance_url   = 'https://marvelstrikeforce.com/en/alliance/members'

	# Let's get a little closer to our work.
	members = alliance_info['members']

	# If we're being called from Discord, provide the truncated output.
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
			rosters_output.append(f'{member:17}NO URL')
			print (f'No cached URL available -- skipping {member}')

			continue

		# Start by defining the number of retries available for each attempt. 
		retries = 3
		page_source = ''
		current_url = ''
		MEMBER_URL = members[member].get('url','')
		HAVE_URL = MEMBER_URL not in ('','auth') and (members[member].get('avail') or member == driver.username)		# Own roster will always be available.

		while retries:
			try:

				# Note when we began processing
				start_time = datetime.datetime.now()
				time_limit = 6

				# Navigate to the roster page.
				if HAVE_URL:
					# Start by getting to Profile page.
					driver.get(f"https://marvelstrikeforce.com/en/member/{MEMBER_URL}/info")

					try:
						# Parse the Player Stats on the Profile page.
						player_stats = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "player-stats-table")))
						parse_player_stats(player_stats.get_attribute('innerHTML'), alliance_info['members'][member])

					# If we timeout on the Player Profile page, handle it in stride.
					except TimeoutException as exc:
						# Report the error and move on to the Roster Page.
						print ("\nTIMEOUT on Player Profile tab. Moving on to Roster tab instead.")
					
					# Look for the Roster Button.
					buttons = []
					while not buttons:
						time.sleep(0.25)
						buttons = driver.find_elements(By.XPATH,f'//a[@href="/member/{MEMBER_URL}/characters"]')
					
					# Navigate from Profile tab to Roster tab.
					buttons[0].click()
						
				# Or need to find an active roster button for this member
				else:
					
					# Nothing to do. Roster hasn't been made available.
					break
				
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
					member = parse_roster(page_source, alliance_info, parse_cache, member, driver.roster_csv, roster_csv_data)
					break

				# If we got here, we exceeded the time limit and our page still hasn't fully loaded.
				retries -= 1

				print ("TIMED OUT! Retries remaining...",retries, )

			except (NoSuchElementException, TimeoutException, WebDriverException) as exc:
				# Still have retries available?
				if retries:
					retries -= 1
					print (f"Retries left {retries}, continuing on {traceback.format_exc()}")
				# Too many retries, time to give up and bail.
				else:
					raise
			except Exception as exc:
				print (traceback.format_exc())
				raise

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

		# Cache the IS_STALE info away for easier access later.
		member_stale = is_stale(alliance_info, member)
		members[member]['is_stale'] = member_stale

		# Report our findings

		# Never received Roster page to parse.
		if not members[member].get('avail'):
			result = 'UNAVAIL'
		elif len(page_source) < 700000: 
			result = 'TIMEOUT'
		# Empty Roster page. Member has never synced.
		elif not alliance_info['members'][member].get('tot_power'):
			result = 'NO DATA'
		# No update. Report how long it's been.
		elif not_updated:
			time_since = time_now - last_update
			result =  f'{max(0,time_since.days):>2}d {int(time_since.seconds/3600)}h'
		# Got an update, and it's brand new
		elif not HAVE_URL:
			result = 'NEW'
		# Got an update, but we've seen it before.
		else:
			result = 'UPD' if member_stale else 'UPDATED'
			
		# If Stale / Needs to Update, add this to our report.
		if member_stale:
			result += '/OLD' if not_updated else '/STL'

		# The status the bot will actually use.
		rosters_output.append(f'{member:17}{result}')
		
		# Printed result on terminal screen.
		print(f'Parsing {len(page_source):7} bytes   Found: {rosters_output[-1]}')

	# If anything was updated, do some additional work.
	status = ''.join([line[17:] for line in rosters_output])
	if 'UPD' in status or 'NEW' in status:

		# Keep a copy of critical stats from today's run for historical analysis.
		update_history(alliance_info)

		# Update traits info if necessary.
		add_extracted_traits(alliance_info)

	return rosters_output



@timed(level=3)
def roster_results(alliance_info, start_time, rosters_output=[]):
	
	summary = []

	# And make note of when we end.
	time_now = datetime.datetime.now()
	summary.append('\n**Total time:** %s seconds' % ((time_now - start_time).seconds))
	print (summary[-1].replace('**',''))

	# Get a little closer to our work. 
	members = alliance_info['members']

	# Quick report of our findings.
	updated = len([member for member in alliance_info['members'] if alliance_info['members'][member].get('last_update',start_time) > start_time])
	stale   = len([member for member in members if members[member].get('is_stale', True)])
	
	# Summarize the results of processing
	summary.append(f'Found **{updated}** new, **{len(members)-updated}** old, **{stale}** stale')
	print (summary[-1].replace('**',''))

	# If roster_output included, generate Key for footer as well.
	status = ''.join([line[17:] for line in rosters_output])

	status_key = [] 

	if 'UNAVAIL' in status:
		status_key.append("* **UNAVAIL** - Change Sharing to **ALLIANCE ONLY**")

	"""if 'NEW/STL' in status:
		status_key.append("* **NEW/STL** - Newly added but stale. Needs sync")

	if 'UPD/STL' in status:
		status_key.append("* **UPD/STL** - Updated but stale. Needs sync")

	if '/OLD' in status:
		status_key.append('* **OLD** - Roster is old/stale. Needs sync')
		
	if 'NO DATA' in status:
		status_key.append('* **NO DATA** - Roster is empty. Needs sync')

	if 'NO URL' in status:
		status_key.append("* **NO URL** - No 'View Roster' link. Sync, then **/alliance refresh**")"""

	if 'TIMEOUT' in status:
		status_key.append('* **TIMEOUT** - Website slow/down. Try later')

	if status_key:
		summary += [''] + status_key

	return summary



# Get back to the Alliance page, then search to find the member's name and the related Roster button.
@timed(level=3)
def find_members_roster(driver, member, rosters_output=[]):

	# Once member entries have populated, we're ready.
	while len(driver.find_elements(By.TAG_NAME, "tr"))<10:
		time.sleep(0.25)

	# Start by looking for the row with this member.
	table_rows = driver.find_elements(By.TAG_NAME, "tr")
	
	for table_row in table_rows:

		member_labels = table_row.find_elements(By.TAG_NAME, "H4")
		if member_labels and member.lower() == remove_tags(member_labels[0].text.replace('[ME]','')).lower():
			break

		# Wrong row. Keep searching.
		table_row = None
	
	# This shouldn't happen. Should always find Member on screen.
	if not table_row:
	
		# One message for bot, one for the screen.
		rosters_output.append(f'{member:17}NO LABEL')
		print (f'Could not find label - skipping {member}')

		return False

	# Find the buttons in the same row as the Member name. 
	buttons = table_row.find_elements(By.CLASS_NAME, 'button')

	# Did we find it and is it active? .
	button = buttons[0] if buttons and buttons[0].is_enabled() else None

	# If we couldn't find an active View Roster button
	if not button:

		# One message for bot, one for the screen.
		rosters_output.append(f'{member:17}NO URL')
		print (f'Link not found - skipping {member}')

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

	# Iterate through each defined strike team.
	for raid_type in ('incur','spotlight'):

		# If the global definition of strike_team is valid for this alliance, let's use it. 
		if strike_teams_defined and valid_strike_team(strike_teams.get(raid_type,[]), alliance_info):

			# Make some common sense fixes and then update the alliance_info dict.
			updated = fix_strike_teams(strike_teams[raid_type], alliance_info) or updated

			# Only 'updated' if we changed the cached value.
			if alliance_info.get('strike_teams',{}).get(raid_type) != strike_teams[raid_type]:
				alliance_info.setdefault('strike_teams',{})[raid_type] = strike_teams[raid_type]
				updated = True

		# If strike_teams.py is not valid, check for strike_teams cached in the alliance_info
		elif 'strike_teams' in alliance_info and valid_strike_team(alliance_info['strike_teams'].get(raid_type,[]), alliance_info):
	
			# Fix any issues. We will just update this info in cached_data.
			updated = fix_strike_teams(alliance_info['strike_teams'][raid_type], alliance_info) or updated

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

	for raid_type in ('incur','spotlight'):

		# If a valid strike_team definition is in strike_teams.py --- USE THAT. 
		if strike_teams_defined and valid_strike_team(strike_teams.get(raid_type,[]),alliance_info):

			# If we update or fix the definition, write it to disk before we're done.
			updated = fix_strike_teams(strike_teams[raid_type], alliance_info) or updated
			
			# Store the result in alliance_info.
			alliance_info.setdefault('strike_teams',{})[raid_type] = strike_teams[raid_type]

		# If strike_teams.py is missing or invalid, check for strike_teams cached in the alliance_info
		elif 'strike_teams' in alliance_info and valid_strike_team(alliance_info['strike_teams'].get(raid_type,[]), alliance_info):
	
			# Fix any issues. We will just update this info in cached_data.
			fix_strike_teams(alliance_info['strike_teams'][raid_type], alliance_info)

	update_is_stale(alliance_info)

	return updated


# Update strike teams to remove dividers and 'incur2' 
@timed(level=3)
def migrate_strike_teams(alliance_info):

	updated = False

	# Update old format strike team definitions. Key off of the presence of 'incur2'.
	if 'strike_teams' in globals():
		
		temp_list = []

		# Still has old Gamma strike teams?
		if 'gamma' in strike_teams:
			temp_list = sum(strike_teams.pop('gamma'), [])

		# Need to merge the 4 teams back into 3?
		elif 'spotlight' in strike_teams and len(strike_teams['spotlight']) == 4:
			temp_list = sum(strike_teams.pop('spotlight'), [])

		# Work to do?
		if temp_list:

			# Remove any entries which aren't valid player names.
			temp_list = [member for member in temp_list if member in alliance_info['members']]

			# Break the list of players into 3 new groups of 8.
			spotlight = []
			for idx in [0,8,16]:
				spotlight.append(temp_list[idx:idx+8])

			# And add the definition of the new Spotlight teams to strike_teams.
			strike_teams['spotlight'] = spotlight

			# Since we changed strike_teams.py, return updated = True so calling routine will write the updated file to disk.
			updated = True

	# Update the alliance_info structure as well, just in case it's all we've got.
	if 'strike_teams' in alliance_info:

		temp_list = []

		# Still has old Gamma strike teams?
		if 'gamma' in alliance_info['strike_teams']:
			temp_list = sum(alliance_info['strike_teams'].pop('gamma'), [])

		# Need to merge the 4 teams back into 3?
		elif 'spotlight' in alliance_info['strike_teams'] and len(alliance_info['strike_teams']['spotlight']) == 4:
			temp_list = sum(alliance_info['strike_teams'].pop('spotlight'), [])

		# Work to do?
		if temp_list:

			# Remove any entries which aren't valid player names.
			temp_list = [member for member in temp_list if member in alliance_info['members']]

			# Break the list of players into 4 new groups of 6.
			spotlight = []
			for idx in [0,8,16]:
				spotlight.append(temp_list[idx:idx+8])

			# And add the definition of the new Spotlight teams to strike_teams.
			alliance_info['strike_teams']['spotlight'] = spotlight

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
def fix_strike_teams(strike_teams, alliance_info):

	# Track whether anything has been changed.
	updated = False

	# Track which members have been used.
	members_used = set()

	# Get a working list of valid member names.
	MEMBER_LIST = sorted(alliance_info.get('members',[]), key=str.lower)
	
	# Start by removing invalid entries or duplicates. 
	for strike_team in strike_teams:
		updated = clean_strike_team(strike_team, MEMBER_LIST, members_used) or updated
	
	# Finally, fill any empty entries with the remaining members 
	for strike_team in strike_teams:
		updated = fill_strike_team(strike_team, MEMBER_LIST, members_used) or updated

	return updated


def clean_strike_team(strike_team, MEMBER_LIST, members_used):

	# Track whether anything has been changed.
	updated = False

	MEMBER_LOWER = [member.lower for member in MEMBER_LIST]

	for idx,member in enumerate(strike_team):

		# Start by fixing case if necessary.
		if member not in MEMBER_LIST and member.lower() in MEMBER_LOWER:
			member = MEMBER_LIST[MEMBER_LOWER.index(member.lower())]
			strike_team[idx] = member
			updated = True
	
		# Clear duplicate or invalid entries.
		if member not in MEMBER_LIST or member in members_used:
			strike_team[idx] = ''
			updated = True

		# Make note that a name has been used.
		elif member in MEMBER_LIST:
			members_used.add(member)
	
	return updated


def fill_strike_team(strike_team, MEMBER_LIST, members_used):
	
	# Track whether anything has been changed.
	updated = False

	members_to_add = [member for member in MEMBER_LIST if member not in members_used]

	# Ensure we have 8 entries to fill.
	while len(strike_team) < 8:
		strike_team.append('')
	
	for idx,member in enumerate(strike_team):
		if not member and members_to_add:
			strike_team[idx] = members_to_add.pop(0)
			members_used.add(strike_team[idx])
			updated = True

	return updated
	

# Calculate is_stale for each member and cache in alliance_info.
def update_is_stale(alliance_info):
	for member in alliance_info['members']:
		alliance_info['members'][member]['is_stale'] = is_stale(alliance_info, member)

