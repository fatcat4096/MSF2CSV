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

from concurrent.futures import as_completed
from requests_futures.sessions import FuturesSession

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
async def update_cached_cost_info(self, AUTH):

	self.bot.logger.info(f'{ansi.white}COMMAND CALLED:{ansi.rst} {ansi.ltcyan}update_cached_cost_info(){ansi.rst}')

	# Get cached data
	char_list   = get_cached('char_lookup')
	gold_costs  = get_cached('gold_costs')
	iso_classes = get_cached('iso_classes')

	self.bot.logger.info(f'Parsing level upgrade costs')

	# Get info about the cost to update to each level
	await asyncio.get_event_loop().run_in_executor(None, get_level_cost_info, AUTH, gold_costs)

	self.bot.logger.info(f'Parsing ISO upgrade costs for {len(char_list)} characters')

	# Update AUTH['session'] with post-processing hooks
	AUTH['session'].hooks['response'] = parse_gear_and_iso_info

	# Create a Futures Session to handle all requests at once
	AUTH['session'] = FuturesSession(session=AUTH['session'])

	FUTURES = []

	# Get the cached list of characters
	for char_name in char_list:

		# Make the API call
		future = request_char_details(AUTH, char_name)

		# Make a note of member name and add this to our futures list
		future.char = char_name
		FUTURES.append(future)

	# Then process each of the responses as they return complete
	for future in as_completed(FUTURES):
		get_gear_and_iso_info(future.result(), future.char, gold_costs, iso_classes)

	# Finally, cache the value of char_lookup
	set_cached('gold_costs',  gold_costs)
	set_cached('iso_classes', iso_classes)

	self.bot.logger.info(f"{ansi.dkgray}COMMAND CLOSED:{ansi.rst} {ansi.ltblu}update_cached_cost_info(){ansi.rst}")



def get_level_cost_info(AUTH, gold_costs):
	
	# Make the API call
	response = request_upgrade_info(AUTH, 'characterLevelTotalXp')

	# Go straight to the data if present
	xp_req = response.json().get('data',{}) if response and response.ok else {}

	for lvl, xp_tot in enumerate(xp_req):
		xp_diff = xp_tot - xp_req[lvl-1] if lvl and xp_tot else 0
		gold_costs.setdefault(None, {})[lvl-1] = int(xp_diff * 6.25)



def parse_gear_and_iso_info(response, *args, **kwargs):
	response.data = response.json().get('data',{}) if response and response.ok else {}



def get_gear_and_iso_info(response, char_name, gold_costs, iso_classes):

	# Translate to common name
	char_name = get_cached('char_lookup').get(char_name)

	# Look deeper into the response
	gear_info = response.data.get('gearTiers', {})
	iso_info  = response.data.get('iso8ClassAdoption',{})

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

