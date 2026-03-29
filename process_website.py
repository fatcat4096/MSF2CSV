#!/usr/bin/env python3
# Encoding: UTF-8
"""process_website.py
Returns cached_data information if still fresh 
Logs into website and updates data from Alliance Information if not
"""


import asyncio
import importlib
import json

from datetime import datetime

try:
	from .log_utils      import *
	from .parse_contents import *
	from .file_io        import *
	from .alliance_info  import *
	from .msf_api        import *
	from .cached_info    import get_cached, set_cached
except:
	from  log_utils      import *
	from  parse_contents import *
	from  file_io        import *
	from  alliance_info  import *
	from  msf_api        import *
	from  cached_info    import get_cached, set_cached


# Process rosters for every member in alliance_info.
@timed(level=3)
def process_rosters(alliance_info, to_process, AUTH, print=print, log_file=None):

	# If we're being called from Discord, provide the truncated output.
	rosters_output = []

	# Let's iterate through the member names in alliance_info.
	for member in to_process:

		start_time = datetime.now()

		# Let's get a little closer to our work
		member_info = alliance_info['members'].setdefault(member, {})

		# Take note of the original TCP size and whether anything has CHANGED
		tcp_start = member_info.get('tot_power',0)
		CHANGED   = member_info.get('tcp') != tcp_start

		# Only process available rosters that have been CHANGED
		if CHANGED and member_info.get('avail'):
			processed_chars = {}
			other_data      = {}

			# Query the Char info, if successful, parse and update all the info
			response = request_member_roster(AUTH['access_token'], memberid=member_info['url'], asOf=member_info.get('asOf'))
			
			# If response was successful, parse the member_roster dict
			if response and response.ok and response.status_code != 344:

				parse_roster_api(response, processed_chars, other_data)

				# Merge the processed roster information into our Alliance Info
				merge_roster(alliance_info, member, processed_chars, other_data)

				# Update the asof tag
				member_info['asOf'] = response.json()['meta']['asOf']

			# If response was UNSUCCESSFUL note the error
			elif not response or not response.ok:
				print (f"{ansi.ltcyan}API ROSTER REQUEST:{ansi.ltred} No valid response received{ansi.rst}")

		# Did we find an updated roster? 
		last_update = member_info.get('last_update')
		time_now    = datetime.now()
		
		updated     = last_update and last_update >= start_time and last_update <= time_now

		# Cache the IS_STALE info away for easier access later.
		member_stale = is_stale(alliance_info, member)
		member_info['is_stale'] = member_stale

		# Report changes to TCP.
		tcp_end  = member_info.get('tot_power',0)
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
		elif not member_info.get('avail'):
			result = 'NOT AVAIL'
			FORMAT = ansi.ltred
		# Never received Roster page to parse.
		elif CHANGED and not (response and response.ok): 
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

		print(f'{ansi.white}{LAST_LINE[:index]}{ansi.rst}{FORMAT}{LAST_LINE[index:]}{ansi.rst}')

	return rosters_output


	
# Find out who we are
def get_username_api(AUTH):

	response = request_player_info(AUTH)
	if not response or not response.ok:
		return 'Unable to get player information'
	
	# Return the username from response
	return remove_tags(response.json()['data']['name']).strip()



# Make multiple API requests to build up a base alliance_info (no roster info).
# Also, if char meta hashtag has changed, save responses and rebuild cached char files
@timed(level=3)
async def get_alliance_api(AUTH):

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
	
	# If char meta hashtag has changed, download fresh char info
	if response.json()['meta']['hashes']['chars'] != get_cached('char_meta'):
		await update_cached_char_info(AUTH)

	# Parse the provided responses into a base alliance_info
	alliance_info = parse_alliance_api(alliance_data, alliance_members)

	return response, alliance_info



# Rebuild fresh cached character info
@timed(level=3)
async def update_cached_char_info(AUTH):

	# Grab the list of PLAYABLE chars
	response = request_char_info(AUTH)
	PLAYABLE = response.json() if response and response.ok else None

	# Grab the list of UNPLAYABLE chars
	response = request_char_info(AUTH, PLAYABLE=False)
	UNPLAYABLE = response.json() if response and response.ok else None

	# Only process responses if both requests successful
	if not (PLAYABLE and UNPLAYABLE):
		return print (f"{ansi.ltcyan}API ROSTER REQUEST:{ansi.ltred} Failed to update character info.{ansi.rst}")

	# Extract the char meta hashtag from the last response
	char_meta = response.json()['meta']['hashes']['chars']

	# Combine the json response sent by the API into a single file and dump it to disk
	CHAR_INFO  = [f'# Defs to allow JSONs to process as dicts\ntrue  = True\nfalse = False\nnull  = None\n']
	CHAR_INFO.append(f'playable   = {json.dumps(PLAYABLE,   indent=2, sort_keys=True)}')
	CHAR_INFO.append(f'unplayable = {json.dumps(UNPLAYABLE, indent=2, sort_keys=True)}')

	# Write the updated module to disk
	write_file(f'{os.path.dirname(__file__)}{os.sep}char_info.py', '\n'.join(CHAR_INFO))

	# Let's build the cached char files
	char_list   = []
	char_lookup = {}
	portraits   = {}
	traits      = {}

	# Process the character dictionary
	await parse_char_data(PLAYABLE['data']+UNPLAYABLE['data'], char_list, char_lookup, portraits, traits)

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

	# After everything up to date, update char_meta to current hash
	set_cached('char_meta', char_meta)



# Rebuild fresh cached character info
@timed(level=3)
async def update_cached_cost_info(AUTH):

	# Get cached data
	char_list   = get_cached('char_lookup')
	gold_costs  = get_cached('gold_costs')
	iso_classes = get_cached('iso_classes')

	# Initialize variables
	loop = asyncio.get_event_loop()

	# Get info about the cost to update to each level
	await loop.run_in_executor(None, get_level_cost_info, AUTH, gold_costs)
	
	# Get the cached list of characters
	for char_name in char_list:
		await loop.run_in_executor(None, get_gear_and_iso_info, AUTH, char_name, gold_costs, iso_classes)

	# Finally, cache the value of char_lookup
	set_cached('gold_costs',  gold_costs)
	set_cached('iso_classes', iso_classes)



def get_level_cost_info(AUTH, gold_costs):
	
	# Make the API call
	response = request_upgrade_info(AUTH, 'characterLevelTotalXp')

	# Go straight to the data if present
	xp_req = response.json().get('data',{}) if response and response.ok else {}

	# Temp, for visibility
	if response:	print (f'Parsing level upgrade costs')

	for lvl, xp_tot in enumerate(xp_req):
		xp_diff = xp_tot - xp_req[lvl-1] if lvl and xp_tot else 0
		gold_costs.setdefault(None, {})[lvl-1] = int(xp_diff * 6.25)



def get_gear_and_iso_info(AUTH, char_name, gold_costs, iso_classes):
	
	# Make the API call
	response = request_char_details(AUTH, char_name)

	# Go straight to the data if present
	response = response.json().get('data',{}) if response and response.ok else {}

	# Translate to common name
	char_name = get_cached('char_lookup').get(char_name)

	# Temp, for visibility
	if response:	print (f'Parsing:  {char_name}')
	else:			print (f'Skipping: {char_name}')

	# Look deeper into the response
	gear_info = response.get('gearTiers', {})
	iso_info  = response.get('iso8ClassAdoption',{})

	# Get a little closer to our work
	gear_cost =  gold_costs.setdefault(char_name,{})
	iso_class = iso_classes.setdefault(char_name,{})

	# Process gear tier cost info if provided
	for tier in gear_info:

		# Initialize tier cost
		gear_cost[int(tier)] = 0

		# Iterate through each slot
		for slot in gear_info[tier].get('slots',[]):

			# Search the subpieces for gold pricing info
			for subpiece in slot.get('piece').get('directCost',[]):
				if subpiece.get('item').get('id') == 'SC':
					gear_cost[int(tier)] += subpiece.get('quantity')

	# Process iso class adoption rates if available
	iso_class.update(iso_info)

	

# If locally defined strike_teams are valid for this cached_data, use them instead
def update_strike_teams(alliance_info):

	updated = False

	# Fix missing people in each defined strike team.
	for raid_type in ('spotlight','annihilation','thunderstrike'):

		# If strike_teams.py is not valid, check for strike_teams cached in the alliance_info
		if raid_type in alliance_info.get('strike_teams', []) and valid_strike_team(alliance_info['strike_teams'][raid_type], alliance_info):
	
			# Fix any issues. We will just update this info in cached_data
			updated = fix_strike_teams(alliance_info['strike_teams'][raid_type], alliance_info) or updated

	# Update strike team definitions if necessary
	updated = migrate_strike_teams(alliance_info) or updated

	# If a change was made, update the cached_data file, but do not change the modification date.
	if updated:
		write_cached_data(alliance_info, timestamp='keep')

	return updated



# Update strike teams if necessary
def migrate_strike_teams(alliance_info):

	updated = False

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
		


# Returns true if at least half of the people in the Alliance are actually in the Strike Teams presented
def valid_strike_team(strike_team, alliance_info):
	return similar_members(sum(strike_team,[]), alliance_info['members'])



# Returns true if at least half of the people in first list are present in the second list presented
def similar_members(member_list_1, member_list_2):
	return len(set(member_list_1).intersection(member_list_2)) > len(member_list_2)*.5	



# Before we take the strike_team.py definition as is, let's fix some common problems
def fix_strike_teams(strike_teams, alliance_info):

	# Track whether anything has been changed
	updated = False

	# Track which members have been used
	members_used = set()

	# Get a working list of valid member names
	MEMBER_LIST = sorted(alliance_info.get('members',[]), key=str.lower)
	
	# Start by removing invalid entries or duplicates
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

