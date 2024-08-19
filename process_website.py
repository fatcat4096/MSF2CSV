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

	# If we haven't found cached_data and the alliance requested is NOT the one from the login, fail gracefully. 
	if alliance_name.lower() != website_alliance_info['name'].lower():
		print (f"Alliance requested doesn't match login alliance: {alliance_name}. Aborting.")
		return

	# If working_from_website, the website_alliance_info will be our baseline. 
	alliance_info = website_alliance_info

	# If we found cached_alliance_info, should we use it as-is or update the website info?
	if cached_alliance_info:

		# Update the fresh alliance_info from website with extra info from cached_data.
		update_alliance_info_from_cached(alliance_info, cached_alliance_info)

	# Make note of when we begin.
	start_time = datetime.datetime.now()

	# Initialize structures used during refresh.
	status          = []
	roster_csv_data = {}

	# Work the website or cached URLs to update alliance_info 
	for member in list(alliance_info['members']):
		status += process_rosters(driver, alliance_info, [member], roster_csv_data)

	# If anything was updated, do some additional work.
	status = ''.join([line[17:] for line in status])
	if 'UPD' in status:
	
		# Keep a copy of critical stats from today's run for historical analysis.
		update_history(alliance_info)

		# Update traits info if necessary.
		add_extracted_traits(alliance_info)

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
def process_rosters(driver, alliance_info, only_process=[], roster_csv_data={}, log_file=None):

	# Let's get a little closer to our work.
	members = alliance_info['members']

	# If we're being called from Discord, provide the truncated output.
	rosters_output = []

	# TEMP: Pull expected member order out of info.csv.
	member_order = [member for member in alliance_info['members'] if alliance_info['members'][member].get('avail')]

	# Need to make note of which entry had [ME] in it. Store that in Driver. 
	# When parsing info.csv, URL for [ME] should be stored in Driver.

	# Make routine that fills portraits from disk, or if cached_file is more than 24 hours old
	# builds a NEW one from the URL for [ME] and saves it to disk.
	
	if not roster_csv_data and alliance_info.get('portraits'):
		parse_roster_csv_data(driver.roster_csv, alliance_info.get('portraits'), roster_csv_data, member_order)

	# Let's iterate through the member names in alliance_info.
	for member in list(members):

		start_time = datetime.datetime.now()

		# If only_process and this member isn't in the list, skip.
		if only_process and member not in only_process:
			continue

		# If member's info is in the roster_csv_data, use that.
		if member in roster_csv_data:

			processed_chars = roster_csv_data[member]['processed_chars']
			other_data      = roster_csv_data[member]['other_data']
			
			# Merge the processed roster information into our Alliance Info
			merge_roster(alliance_info, member, processed_chars, other_data)

		# If we have a Recruit URL, process from website.
		elif members[member].get('url') and members[member].get('avail'):

			# SHOULD NOT BE USED FOR /ROSTER REFRESH
			if roster_csv_data:
				print ('could not find member',member,'in roster_csv_data:',roster_csv_data.keys())

			process_roster_html(driver, alliance_info, member)
			
		# Did we find an updated roster? 
		last_update = members[member].get('last_update')
		time_now    = datetime.datetime.now()
		
		updated     = last_update and last_update >= start_time and last_update <= time_now

		# Cache the IS_STALE info away for easier access later.
		member_stale = is_stale(alliance_info, member)
		members[member]['is_stale'] = member_stale

		# Report our findings

		# Used CSV for Roster update
		if updated:
			result = 'UPDATED'
		# Roster not available on website.
		elif member not in roster_csv_data and not members[member].get('avail'):
			result = 'UNAVAIL'
		# Never received Roster page to parse.
		elif member not in roster_csv_data and len(driver.page_source) < 700000: 
			result = 'TIMEOUT'
		# No update. Just report how long it's been.
		else:
			time_since = time_now - last_update
			result =  f'{max(0,time_since.days):>2}d {int(time_since.seconds/3600)}h'

		# One for the bot, one for the screen.
		rosters_output.append(f'{member:17}{result}')
		print(f'Found: {rosters_output[-1]}')

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

	if 'TIMEOUT' in status:
		status_key.append('* **TIMEOUT** - Website slow/down. Try later')

	if status_key:
		summary += [''] + status_key

	return summary



def process_roster_html(driver, alliance_info, member):

	# Start by defining the number of retries and time limit for each attempt. 
	retries    = 3
	time_limit = 6

	page_source = ''
	MEMBER_URL = alliance_info['members'][member]['url']
	
	while retries:
		try:
			# Note when we began processing
			start_time = datetime.datetime.now()

			# Start by getting to Profile page.
			driver.get(f"https://marvelstrikeforce.com/en/member/{MEMBER_URL}/info")

			try:
				# Parse the Player Stats on the Profile page.
				player_stats = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CLASS_NAME, "player-stats-table")))
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
			
			#print ('Calling process_roster_htmls(), loading roster tab...')
			
			# Page loads in sections, will be > 700K after roster information loads.
			while (datetime.datetime.now()-start_time).seconds < time_limit and len(page_source)<700000:

				# Give it a moment, then see what's loaded.
				time.sleep(0.25)
				page_source = driver.page_source

			# If page loaded, extract stats and exit.
			if len(page_source)>700000:
				#print (f'Parsing page for member: {member} - {len(page_source)} bytes')
				return parse_roster_html(page_source, alliance_info, member)

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
			
			

# If locally defined strike_teams are valid for this cached_data, use them instead
@timed(level=3)
def update_strike_teams(alliance_info):

	strike_teams_defined = 'strike_teams' in globals()

	# Temporary update strike team definitions to remove dividers and 'incur2'.
	updated = migrate_strike_teams(alliance_info)

	# Transition 'extracted_traits' to 'traits' and update missing traits.
	updated = add_extracted_traits(alliance_info) or updated

	# Iterate through each defined strike team.
	for raid_type in ('incur','orchis','spotlight'):

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

	for raid_type in ('incur','orchis','spotlight'):

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

		# Incur defined, but no Orchis yet?
		if 'incur' in strike_teams and 'orchis' not in strike_teams:
			strike_teams['orchis'] = strike_teams['incur']
			updated = True

	# Update the alliance_info structure as well, just in case it's all we've got.
	if 'strike_teams' in alliance_info:

		temp_list = []

		# Incur defined, but no Orchis yet?
		if 'incur' in alliance_info['strike_teams'] and 'orchis' not in alliance_info['strike_teams']:
			alliance_info['strike_teams']['orchis'] = alliance_info['strike_teams']['incur']
			updated = True

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

