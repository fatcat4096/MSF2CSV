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

import importlib
import inspect
import json
import char_info

from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

from parse_contents       import *
from generate_local_files import *
from file_io              import *
from login                import get_driver, login
from alliance_info        import *
from cached_info          import get_cached, set_cached
from msfgg_api            import *

# Returns a cached_data version of alliance_info, or one freshly updated from online.
@timed(level=3)
def get_alliance_info(alliance_name='', prompt=False, force='', headless=False, scopely_login=''):

	cached_alliance_info = find_cached_data(alliance_name)

	# If we loaded a cached_data file, need to check when updated last. 
	if cached_alliance_info:

		# If we expect cached data or if it's 'fresh enough' and we aren't forcing 'fresh'. 
		if force == 'stale' or (not force and not prompt and fresh_enough(cached_alliance_info)):
			print ("Using cached_data from file:", cached_alliance_info['file_path'])

			# If forced stale, make no changes.
			if force == 'stale':
				return cached_alliance_info

			# Update the strike team info if we have valid teams in strike_teams.py
			update_strike_teams(cached_alliance_info)
			return cached_alliance_info

		# If no alliance_name specified but we found one obvious candidate, report that we are using it.
		if not alliance_name:
			alliance_name = cached_alliance_info['name']
			print (f"Defaulting to alliance from cached_data: {alliance_name}")

	# Start by logging into the website.
	driver = login(prompt, headless, scopely_login=scopely_login)

	if not driver:
		print ('Failed to login to MSF website. Aborting.')
		return

	alliance_info = parse_alliance(driver)

	# If no alliance_name specified, use the login's alliance.
	if not alliance_name:
		print (f"Defaulting to alliance from website login: {alliance_info['name']}")

	# If the alliance requested is NOT the one from the login, fail gracefully. 
	elif alliance_name.lower() != alliance_info['name'].lower():
		print (f"Alliance requested ({alliance_name}) doesn't match login alliance ({alliance_info['name']}). Aborting.")
		return

	# Verify the fresh and old cached data are the same alliance 
	# Merge data if old info available
	find_cached_and_merge(alliance_info)

	# Make note of when we begin.
	start_time = datetime.datetime.now()

	# Initialize structures used during refresh.
	rosters_output  = []
	roster_csv_data = {}

	# Work the website or cached URLs to update alliance_info 
	for member in list(alliance_info['members']):
		rosters_output += process_rosters(alliance_info, driver, [member], roster_csv_data)

	# If anything was updated, do some additional work.
	status = ''.join([line[15:] for line in rosters_output])
	if 'UPD' in status or 'NEW' in status:
	
		# Keep a copy of critical stats from today's run for historical analysis.
		update_history(alliance_info)

	# Close the Selenium session.
	driver.close()

	# Print a summary of the results.
	roster_results(alliance_info, start_time, rosters_output)

	# Make sure we have a valid strike_team for Chaos Raids. 
	updated = get_valid_strike_teams(alliance_info) 

	# Generate strike_teams.py if we updated strike team definitions or if this file doesn't exist locally.
	if updated or 'strike_teams' not in globals():
		generate_strike_teams(alliance_info)

	# Write the collected roster info to disk.
	write_cached_data(alliance_info)

	return alliance_info



# Process rosters for every member in alliance_info.
@timed(level=3)
def process_rosters(alliance_info={}, driver=None, only_process=[], roster_csv_data={}, AUTH=None, log_file=None):

	# Let's get a little closer to our work.
	members = alliance_info['members']

	# If we're being called from Discord, provide the truncated output.
	rosters_output = []

	# TEMP: Pull expected member order out of info.csv.
	member_order = [member for member in alliance_info['members'] if alliance_info['members'][member].get('avail')]

	# If calling from the command line.
	if not AUTH:

		# If we're missing char_lookup, or it's a day old
		# build the temp files with current API responses
		if not fresh_enough('char_lookup'):
			update_cached_char_info()

		# Processes roster_csv data on first pass only 
		if not roster_csv_data and member_order:
			parse_roster_csv(driver.roster_csv, roster_csv_data, member_order)

	# Let's iterate through the member names in alliance_info.
	for member in list(members):

		start_time = datetime.datetime.now()

		# If only_process and this member isn't in the list, skip.
		if only_process and member not in only_process:
			continue

		# Take note of the original TCP size.
		tcp_start = members[member].get('tot_power',0)

		# If we have AUTH, use that.
		if AUTH and members[member].get('avail'):
			processed_chars = {}
			other_data      = {}

			# Query the Char info, if successful, parse and update all the info. 
			response = request_member_roster(AUTH['access_token'], memberid=members[member]['url'], asOf=members[member].get('asOf'))
			
			# If response was successful, parse the member_roster dict
			if response and response.ok:
				parse_roster_api(response, processed_chars, other_data)
				
				# Merge the processed roster information into our Alliance Info
				merge_roster(alliance_info, member, processed_chars, other_data)

			# What happens if response is not ok? Interpreted as no change?
			else:
				print ("API ROSTER REQUEST: No valid response received")

		# If member's info is in the roster_csv_data, use that.
		elif member in roster_csv_data:

			processed_chars = roster_csv_data[member]['processed_chars']
			other_data      = roster_csv_data[member]['other_data']
			
			# Merge the processed roster information into our Alliance Info
			merge_roster(alliance_info, member, processed_chars, other_data)

		# If we have a Recruit URL, process from website.
		elif members[member].get('url') and members[member].get('avail'):

			# SHOULD NOT BE USED FOR /ROSTER REFRESH
			if roster_csv_data:
				print ('SHOULD NOT HAPPEN: Could not find member',member,'in roster_csv_data:',roster_csv_data.keys())

			page_source = get_roster_html(driver, members[member]['url'], member, alliance_info)
			if page_source:
				parse_roster_html(page_source, alliance_info, member)

		# Did we find an updated roster? 
		last_update = members[member].get('last_update')
		time_now    = datetime.datetime.now()
		
		updated     = last_update and last_update >= start_time and last_update <= time_now

		# Cache the IS_STALE info away for easier access later.
		member_stale = is_stale(alliance_info, member)
		members[member]['is_stale'] = member_stale

		# Report changes to TCP.
		tcp_end  = members[member].get('tot_power',0)
		tcp_diff = tcp_end - tcp_start

		if   tcp_end > 10**6:	tcp_end  = f'{tcp_end/10**6:>6.1f}M'
		elif tcp_end > 1000:	tcp_end  = f'{tcp_end/1000:>6.1f}K'
		else:					tcp_end  = f'{tcp_end:>6.1f} '

		if   abs(tcp_diff) > 10**6:	tcp_diff = f'{tcp_diff/10**6:>+6.1f}M'
		elif abs(tcp_diff) > 1000:	tcp_diff = f'{tcp_diff/1000:>+6.0f}K'
		else:					tcp_diff = f'{tcp_diff:>+6.0f} '

		# Used CSV for Roster update
		if updated:
			# If roster is NEW say so
			if not tcp_start:
				result = f'NEW:{tcp_end}'
			else:
				result = f'UPD:{tcp_diff}'
		# Roster not available on website.
		elif member not in roster_csv_data and not members[member].get('avail'):
			result = 'NOT AVAIL'
		# Never received Roster page to parse.
		elif member not in roster_csv_data and driver and len(driver.page_source) < 700000: 
			result = 'TIMEOUT'
		# Not sure what happened here. Side stepping an odd error condition.
		elif not last_update:
			result = 'UNKNOWN'
		# No update. Just report how long it's been.
		else:
			time_since = time_now - last_update 

			days  = f'{time_since.days}d' if time_since.days else ''
			hours = f'{int(time_since.seconds/3600)}h'
			mins  = f'{int(time_since.seconds%3600/60):0>2}m'

			# After 10 hours, just report days.
			if days or time_since.seconds > 36000:
				time_since = f'{days} {hours}'
			else:
				time_since = f'{hours} {mins}'

			result =  f'OLD:{time_since:>7}'

		# Format line depending on whether entry available.
		if ':' in result:
			rosters_output.append(f'{member[:14]:14} {result}')
		else:
			rosters_output.append(f'{member:16} {result:>9}')

		print(f'Found: {rosters_output[-1]}')

	return rosters_output


	
@timed(level=3)
def roster_results(alliance_info, start_time, rosters_output=[]):
	
	NEW = len([x for x in rosters_output if 'NEW' in x[15:]])
	UPD = len([x for x in rosters_output if 'UPD' in x[15:]])
	OLD = len([x for x in rosters_output if 'OLD' in x[15:]])

	NEW = f'**{NEW}** new'     if NEW else ''
	UPD = f'**{UPD}** updated' if UPD else ''
	OLD = f'**{OLD}** old'     if OLD else ''

	SUMMARY = [NEW, UPD, OLD]
	while '' in SUMMARY:
		SUMMARY.remove('')

	REQ = (datetime.datetime.now()-start_time).seconds

	# Summarize the results of processing
	summary = [f'Found {", ".join(SUMMARY)} in {REQ}s']
	print (summary[-1].replace('**',''))

	# If roster_output included, generate Key for footer as well.
	status_key = [] 

	NOT_AVAIL = [f'* `{x[:16].strip()}`' for x in rosters_output if 'NOT AVAIL' in x]
	TIMEOUT   = [f'* `{x[:16].strip()}`' for x in rosters_output if 'TIMEOUT'   in x]

	if NOT_AVAIL:
		status_key.append(f"**{len(NOT_AVAIL)}** need roster shared w/ **ALLIANCE ONLY**:")
		status_key += NOT_AVAIL

	if TIMEOUT:
		status_key.append('* **TIMEOUT** - MSF.gg slow/down. Could not refresh:')
		status_key += TIMEOUT

	if status_key:
		summary += [''] + status_key

	return summary



@timed(level=3)
def get_roster_html(driver, member_url, member='', alliance_info={}):

	# Start by defining the number of retries and time limit for each attempt. 
	retries    = 3
	time_limit = 6

	page_source = ''
	
	while retries:
		try:
			# Note when we began processing
			start_time = datetime.datetime.now()

			# Start by getting to Profile page.
			driver.get(f"https://marvelstrikeforce.com/en/member/{member_url}/info")

			# Click on the Roster button when available.
			button = WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.XPATH,f'//a[@href="/member/{member_url}/characters"]')))
			button.click()
			
			# Page loads in sections, will be > 700K after roster information loads.
			while (datetime.datetime.now()-start_time).seconds < time_limit:

				# Give it a moment, then see what's loaded.
				time.sleep(0.25)
				page_source = driver.page_source

				# If page fully loaded, return this
				if len(page_source)>700000:
					return page_source

			# Timed out and page hasn't fully loaded.
			raise TimeoutException

		except Exception as exc:
			retries -= 1

			# Just a timeout?
			if isinstance(exc, TimeoutException):
				print (f'TIMED OUT!', end=' ')

			# If not, display the exception.
			else:
				print (f'EXCEPTION! {type(exc).__name__}: {exc}', end=' ')

			print (f'{retries} retries remaining...')

			# Too many retries, report exception and bail.
			if not retries:
				if isinstance(exc, TimeoutException):
					return
				print (traceback.format_exc())
				raise



# Find out who we are
@timed(level=3)
def get_username_api(AUTH):

	response = request_player_info(AUTH)
	if not response or not response.ok:
		return 'Unable to get player information'
	
	# Return the username from response
	return remove_tags(response.json()['data']['name']).strip()



# Make multiple API requests to build up a base alliance_info (no roster info).
# Also, if char meta hashtag has changed, save responses and rebuild cached char files
@timed(level=3)
def get_alliance_api(AUTH):

	# Get the general ALLIANCE information
	response = request_alliance_info(AUTH)
	if not response or not response.ok:
		return response, 'alliance'

	# Extract the alliance_data from response.
	alliance_data = response.json()['data']
	
	# Get the list of alliance MEMBERS
	response = request_alliance_members(AUTH)
	if not response or not response.ok:
		return response, 'member'

	# Extract the alliance_members from response.
	alliance_members = response.json()['data']
	
	# Extract the current char meta hashtag from response
	char_meta = response.json()['meta']['hashes']['chars']

	# If char meta hashtag has changed, download fresh char info
	if char_meta != get_cached('char_meta'):

		# Grab the list of PLAYABLE chars
		response = request_char_info(AUTH)
		if not response or not response.ok:
			return response, 'playable char'

		PLAYABLE = response.json()
	
		# Grab the list of UNPLAYABLE chars
		response = request_char_info(AUTH, PLAYABLE=False)
		if not response or not response.ok:
			return response, 'unplayable char'

		UNPLAYABLE = response.json()
	
		# Write these json structures out and update all cached char info
		update_cached_char_info(PLAYABLE, UNPLAYABLE)

		# Update the cached char meta to current hashtag value
		set_cached('char_meta', char_meta)
	
	# Parse the provided responses into a base alliance_info
	alliance_info = parse_alliance_api(alliance_data, alliance_members)

	return response, alliance_info



# Rebuild fresh cached character info
@timed(level=3)
def update_cached_char_info(PLAYABLE=None, UNPLAYABLE=None):

	# If we got API response passed in, start by writing
	if PLAYABLE:

		# Combine the json response sent by the API into a single file and dump it to disk
		PLAYABLE   = json.dumps(PLAYABLE,   indent=2, sort_keys=True)
		UNPLAYABLE = json.dumps(UNPLAYABLE, indent=2, sort_keys=True)
		
		CHAR_INFO  = f'# Defs to allow JSONs to process as dicts\ntrue  = True\nfalse = False\nnull  = None\n\n'
		CHAR_INFO += f'playable   = {PLAYABLE}\nunplayable = {UNPLAYABLE}' 

		# Write the new module to disk
		write_file(inspect.getfile(char_info), CHAR_INFO)

		# Refresh the sourced definition
		importlib.reload(char_info)

	# Combine the data sections from the sourced API responses.
	CHAR_DATA = char_info.playable['data'] + char_info.unplayable['data']
	
	# Let's build the cached char files
	char_list   = []
	char_lookup = {}
	portraits   = {}
	traits      = {}

	# Process the character dictionary
	parse_char_data(CHAR_DATA, char_list, char_lookup, portraits, traits)

	# Write the portraits
	set_cached('portraits', portraits)

	# Write char_list for MSF RosterBot use
	set_cached('char_list', sorted(char_list))

	# Write trait_list for MSF RosterBot use
	set_cached('traits', traits)

	# Write trait_list for MSF RosterBot use
	set_cached('trait_list', sorted(traits))

	# Finally, cache the value of char_lookup
	set_cached('char_lookup', char_lookup)



# If locally defined strike_teams are valid for this cached_data, use them instead
@timed(level=3)
def update_strike_teams(alliance_info):

	strike_teams_defined = 'strike_teams' in globals()

	# Temporary update strike team definitions if necessary
	updated = migrate_strike_teams(alliance_info)

	# Iterate through each defined strike team.
	for raid_type in ('chaos','spotlight'):

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

	# Update strike team definitions if necessary
	updated = migrate_strike_teams(alliance_info)

	for raid_type in ('chaos','spotlight'):

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



# Update strike teams if necessary
@timed(level=3)
def migrate_strike_teams(alliance_info):

	updated = False

	# Update old format strike team definitions.
	if 'strike_teams' in globals():
		
		# Orchis defined, but no Chaos yet?
		if 'orchis' in strike_teams and 'chaos' not in strike_teams:
			strike_teams['chaos'] = strike_teams['orchis']
			updated = True

		# Look for outdated strike_team definitions
		for raid_type in ('orchis','incur','gamma'):
			if raid_type in strike_teams:
				del strike_teams[raid_type]
				updated = True

	# Update the alliance_info structure as well, just in case it's all we've got.
	if 'strike_teams' in alliance_info:

		# Orchis defined, but no Chaos yet?
		if 'orchis' in alliance_info['strike_teams'] and 'chaos' not in alliance_info['strike_teams']:
			alliance_info['strike_teams']['chaos'] = alliance_info['strike_teams']['orchis']
			updated = True
	
		# Look for outdated strike_team definitions
		for raid_type in ('orchis','incur','gamma'):
			if raid_type in alliance_info['strike_teams']:
				del alliance_info['strike_teams'][raid_type]
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



@timed(level=3)
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



@timed(level=3)
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

