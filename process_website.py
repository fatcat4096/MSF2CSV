#!/usr/bin/env python3
# Encoding: UTF-8
"""process_website.py
Returns cached_data information if still fresh 
Logs into website and updates data from Alliance Information if not
"""

from log_utils import *

import datetime

import importlib
import inspect
import json
import char_info

from parse_contents       import *
from generate_local_files import *
from file_io              import *
from alliance_info        import *
from cached_info          import get_cached, set_cached
from msf_api              import *


# Process rosters for every member in alliance_info.
@timed(level=3)
def process_rosters(alliance_info, only_process, AUTH, log_file, logger=print):

	# Let's get a little closer to our work.
	members = alliance_info['members']

	# If we're being called from Discord, provide the truncated output.
	rosters_output = []

	# TEMP: Pull expected member order out of info.csv.
	member_order = [member for member in alliance_info['members'] if alliance_info['members'][member].get('avail')]

	# Let's iterate through the member names in alliance_info.
	for member in list(members):

		start_time = datetime.datetime.now()

		# If only_process and this member isn't in the list, skip.
		if only_process and member not in only_process:
			continue

		# Take note of the original TCP size.
		tcp_start = members[member].get('tot_power',0)

		# Only process members who have available rosters
		if members[member].get('avail'):
			processed_chars = {}
			other_data      = {}

			# Query the Char info, if successful, parse and update all the info
			response = request_member_roster(AUTH['access_token'], memberid=members[member]['url'], asOf=members[member].get('asOf'))
			
			# If response was successful, parse the member_roster dict
			if response and response.ok and response.status_code != 344:

				parse_roster_api(response, processed_chars, other_data)
				
				# Merge the processed roster information into our Alliance Info
				merge_roster(alliance_info, member, processed_chars, other_data)

				# Update the asof tag
				alliance_info['members'][member]['asOf'] = response.json()['meta']['asOf']

			# If response was UNSUCCESSFUL note the error
			elif not response or not response.ok:
				print (f"{ansi.ltcyan}API ROSTER REQUEST:{ansi.ltred} No valid response received{ansi.reset}")

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

		# If we found updated info
		if updated:
			# If roster is NEW say so
			if not tcp_start:
				result = f'NEW:{tcp_end}'
				FORMAT = ansi.ltgrn
			else:
				result = f'UPD:{tcp_diff}'
				FORMAT = ansi.ltyel
		# Roster not available on website.
		elif not members[member].get('avail'):
			result = 'NOT AVAIL'
			FORMAT = ansi.ltred
		# Never received Roster page to parse.
		elif not (response and response.ok): 
			result = 'TIMEOUT'
			FORMAT = ansi.ltred
		# Not sure what happened here. Side stepping an odd error condition.
		elif not last_update:
			result = 'UNKNOWN'
			FORMAT = ansi.ltred
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
			FORMAT = ansi.yellow

		# Format line depending on whether entry available.
		if ':' in result:
			rosters_output.append(f'{member[:14]:14} {result}')
		else:
			rosters_output.append(f'{member:16} {result:>9}')

		# Grab the last line. Add formatting
		LAST_LINE =  rosters_output[-1]
		index = 15 + (':' not in LAST_LINE)

		logger(f'Found: {ansi.bold}{LAST_LINE[:index]}{ansi.reset}{FORMAT}{LAST_LINE[index:]}{ansi.reset}')

	return rosters_output


	
@timed(level=3)
def roster_results(alliance_info, start_time, rosters_output, only_summary=False, logger=print):
	
	NEW = len([x for x in rosters_output if 'NEW' in x[15:]])
	UPD = len([x for x in rosters_output if 'UPD' in x[15:]])
	OLD = len([x for x in rosters_output if 'OLD' in x[15:]])

	NEW = f'**{NEW}** new'     if NEW else ''
	UPD = f'**{UPD}** updated' if UPD else ''
	OLD = f'**{OLD}** old'     if OLD else ''

	# Change OLD output if nothing was updated.
	if not (NEW or UPD):
		OLD = f'**NO UPDATED INFO**'

	SUMMARY = ", ".join([x for x in (NEW, UPD, OLD) if x])
	REQ = (datetime.datetime.now()-start_time).seconds

	# Summarize the results of processing
	summary = [f'Found {SUMMARY} in {REQ}s']

	# Make the log output pretty
	logger (f'{ansi.ltcyan}Refresh complete!{ansi.reset} Found {ansi.ltyel}{SUMMARY.replace("**","")}{ansi.reset} in {ansi.ltyel}{REQ}s{ansi.reset}')

	# If roster_output included, generate Key for footer as well.
	status_key = [] 

	NOT_AVAIL = [f'* *{x[:16].strip()}*' for x in rosters_output if 'NOT AVAIL' in x]
	TIMEOUT   = [f'* {x[:16].strip()}' for x in rosters_output if 'TIMEOUT'   in x]

	if only_summary:
		if NOT_AVAIL:
			status_key.append(f"**{len(NOT_AVAIL)}** not sharing")

		if TIMEOUT:
			status_key.append(f"**{len(TIMEOUT)}** timeouts")

		if status_key:
			summary += [f'Issues: ' + ', '.join(status_key)]
	else:
		if NOT_AVAIL:
			status_key.append(f"**{len(NOT_AVAIL)}** need roster shared w/ **ALLIANCE ONLY**:")
			status_key += NOT_AVAIL

		if TIMEOUT:
			status_key.append('**TIMEOUT** API failed. Not updated:')
			status_key += TIMEOUT

		if status_key:
			summary += [''] + status_key

	return summary



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
		PLAYABLE = response.json() if response and response.ok else None
	
		# Grab the list of UNPLAYABLE chars
		response = request_char_info(AUTH, PLAYABLE=False)
		UNPLAYABLE = response.json() if response and response.ok else None
	
		# Only process responses if both requests successful
		if PLAYABLE and UNPLAYABLE:

			# Write these json structures out and update all cached char info
			update_cached_char_info(PLAYABLE, UNPLAYABLE)

			# Update the cached char meta to current hashtag value
			set_cached('char_meta', char_meta)

		# Note that we did have an issue with the API calls
		else:
			print (f"{ansi.ltcyan}API ROSTER REQUEST:{ansi.ltred} Failed requesting updated character info.{ansi.reset}")

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

	updated = False

	# Fix missing people in each defined strike team.
	for raid_type in ('spotlight','annihilation','thunderstrike'):

		# If strike_teams.py is not valid, check for strike_teams cached in the alliance_info
		if 'strike_teams' in alliance_info and raid_type in alliance_info['strike_teams'] and valid_strike_team(alliance_info['strike_teams'][raid_type], alliance_info):
	
			# Fix any issues. We will just update this info in cached_data
			updated = fix_strike_teams(alliance_info['strike_teams'][raid_type], alliance_info) or updated

	# Update strike team definitions if necessary
	updated = migrate_strike_teams(alliance_info) or updated

	# If a change was made, update the cached_data file, but do not change the modification date.
	if updated:
		write_cached_data(alliance_info, timestamp='keep')

	return updated



# Update strike teams if necessary
@timed(level=3)
def migrate_strike_teams(alliance_info):

	updated = False

	# Update old format strike team definitions.
	if 'strike_teams' in globals():
		
		# Chaos defined, but no Annihilation yet?
		if 'chaos' in strike_teams and 'annihilation' not in strike_teams:
			strike_teams['annihilation'] = strike_teams['chaos']
			updated = True

		# Annihilation defined, but no Thunderstrike yet?
		if 'annihilation' in strike_teams and 'thunderstrike' not in strike_teams:
			strike_teams['thunderstrike'] = strike_teams['annihilation']
			updated = True

		# Look for outdated strike_team definitions
		for raid_type in ('chaos','orchis','incur','gamma'):
			if raid_type in strike_teams:
				del strike_teams[raid_type]
				updated = True

	# Update the alliance_info structure as well, just in case it's all we've got.
	if 'strike_teams' in alliance_info:

		# Chaos defined, but no Annihilation yet?
		if 'chaos' in alliance_info['strike_teams'] and 'annihilation' not in alliance_info['strike_teams']:
			alliance_info['strike_teams']['annihilation'] = alliance_info['strike_teams']['chaos']
			updated = True

		# Annihilation defined, but no Thunderstrike yet?
		if 'annihilation' in alliance_info['strike_teams'] and 'thunderstrike' not in alliance_info['strike_teams']:
			alliance_info['strike_teams']['thunderstrike'] = alliance_info['strike_teams']['annihilation']
			updated = True
	
		# Look for outdated strike_team definitions
		for raid_type in ('chaos','orchis','incur','gamma'):
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
	return similar_members(sum(strike_team,[]), alliance_info['members'])



# Returns true if at least 2/3 people of the people in the Alliance are actually in the Strike Teams presented.
@timed(level=3)
def similar_members(member_list_1, member_list_2):
	return len(set(member_list_1).intersection(member_list_2)) > len(member_list_2)*.5	



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
@timed(level=3)
def update_is_stale(alliance_info):
	for member in alliance_info['members']:
		alliance_info['members'][member]['is_stale'] = is_stale(alliance_info, member)

