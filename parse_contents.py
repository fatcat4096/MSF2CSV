#!/usr/bin/env python3
# Encoding: UTF-8
"""parse_contents.py
Scrapes the alliance.html (Alliance display page) and characters.html file (Roster display page) from MSF.gg.  

Returns in easy to use dicts for inclusion in tables.
"""

from log_utils import *

import re

from file_io     import *
from datetime    import datetime
from cached_info import get_cached


def parse_alliance_api(alliance_data, alliance_members):

	alliance = {}

	# Used for file naming
	alliance['name'] = alliance_data['name']

	# Used for display in reports -- this is the clean version for reports.
	alliance['display_name'] = remove_tags(alliance_data['name'])

	# Used to discriminate if multiple alliances have same base filename					# Need a complete rewrite, possibly along with the above.
	#alliance['color'] = ''.join([x[6:] for x in driver.alliance_html.split('"') if x.startswith('color:')])

	# Parse the Alliance image and frame
	alliance['image']      = alliance_data['icon'].split('ALLIANCEICON_')[-1][:-4]
	alliance['frame']      = alliance_data['frame'].split('ALLIANCEICON_')[-1][:-4]
	
	# Parse the Alliance stats
	alliance['trophies']   = alliance_data.get('warTrophies','')
	alliance['tot_power']  = alliance_data.get('tcp','')
	alliance['avg_power']  = alliance_data.get('avgTcp','')
	alliance['war_zone']   = alliance_data.get('warZone','')
	alliance['war_league'] = alliance_data.get('warLeague','')
	alliance['war_rank']   = alliance_data.get('warRank','')
	alliance['raid_rank']  = alliance_data.get('raidRank','')

	members  = {}
	captains = []

	# Pull base Member Info from the info.csv file.
	parse_info_api(alliance_members, alliance, captains, members)

	alliance['members']  = members
	alliance['captains'] = captains

	# Return the parsed alliance info.
	return alliance



# Parse the Member data directly from the API call
def parse_info_api(alliance_members, alliance, captains, members):

	# Iterate through each entry, building up a member dict with stats for each.
	for alliance_member in alliance_members:
		member = {}

		# Get a little bit closer to our work
		member_card = alliance_member['card']

		# Remove HTML tags if present
		member_name = remove_tags(member_card['name']).strip()

		# Ensure name isn't duplicated
		if member_name in members:
			member_name += str(alliance_members.index(alliance_member))

		# Process role information
		member_role     = alliance_member['rank']
		if member_role == 'leader':
			alliance['leader'] = member_name
		elif member_role == 'captain':
			captains.append(member_name)

		member['url']   = alliance_member['id']
		
		# Process other info from the Member Card
		member['image'] = member_card['icon'].split('Portrait_')[-1][:-4]
		member['frame'] = member_card['frame'].split('ICON_FRAME_')[-1][:-4]
		member['level'] = member_card.get('level',{}).get('completedTier',0)
		member['tcp']   = member_card.get('tcp')
		member['stp']   = member_card.get('stp')
		member['mvp']   = member_card.get('warMvp',0)
		member['tcc']   = member_card.get('charactersCollected')
		member['avail'] = member_card.get('rosterShare')

		# Store the finished member info.
		members[member_name] = member
		


# Break this out as a separate routine so can be used to merge roster.csv data.
@timed(level=3)
def merge_roster(alliance_info, member, processed_chars, other_data):

	# Get a little closer to our work. 
	member_info = alliance_info['members'].setdefault(member,{})
	
	# Update 'last_update' if the calculated tot_power has changed.
	calc_pwr = sum([processed_chars[char]['power'] for char in processed_chars])
	if  member_info.get('tot_power') != calc_pwr:
		member_info['tot_power']      = calc_pwr
		member_info['last_update']    = datetime.now()

	# Add the 'clean' parsed data to our list of processed players.
	member_info['processed_chars'] = processed_chars
	member_info['other_data']      = other_data
	
	# Do I really USE the display_name?
	member_info['display_name']    = member

	# Temporary fix. Calculate values if possible.
	calc_lvl             = max([processed_chars[char_name].get('lvl',0) for char_name in processed_chars]) if processed_chars else 0
	calc_stp             = sum(sorted([processed_chars[member]['power'] for member in processed_chars], reverse=True)[:5])
	calc_tcc             = len([char for char in processed_chars if processed_chars[char]['power']])
	member_info['max']   = len([char for char in processed_chars if processed_chars[char]['yel']==7])
	member_info['stars'] = sum([processed_chars[char]['yel'] for char in processed_chars])
	member_info['red']   = sum([processed_chars[char]['red'] for char in processed_chars])

	# Only use calculated TCP, STP, and TCC if higher than the recorded values in Alliance Info.
	member_info['level'] = max(calc_lvl, member_info.get('level',0))
	member_info['tcp']   = max(calc_pwr, member_info.get('tcp',0))
	member_info['stp']   = max(calc_stp, member_info.get('stp',0))
	member_info['tcc']   = max(calc_tcc, member_info.get('tcc',0))


	
@timed(level=3)
def parse_roster_api(response, processed_chars, other_data):

	# Load cached char_lookup
	char_lookup = get_cached('char_lookup')

	# Iterate through each in roster, building up a member dict with stats for each.
	for entry in response.json()['data']:

		char_name = char_lookup.get(entry['id'])
		
		# SHOULD NOT HAPPEN. If lookup failed, we're missing the translation. Can't insert this data.
		if not char_name:
			print ("missing translation for",entry)
			continue

		char_info = processed_chars.setdefault(char_name,{})

		char_info['lvl']   = entry.get('level',0)
		char_info['power'] = entry.get('power',0)
		char_info['yel']   = entry.get('activeYellow',0)
		
		active_red = entry.get('activeRed',0)
		char_info['red']   = active_red   if active_red < 7 else 7 
		char_info['dmd']   = active_red-7 if active_red > 7 else 0
		
		char_info['tier']  = entry.get('gearTier',0)
		char_info['op']    = entry.get('overpower',0)

		bas = entry.get('basic',0)
		spc = entry.get('special',0)
		ult = entry.get('ultimate',0)
		pas = entry.get('passive',0)

		char_info['abil'] = int(f'{bas}{spc}{ult}{pas}')

		iso_entry = entry.get('iso8').split(',')
		iso_class = iso_entry[6] if len(iso_entry) > 6 else None

		iso_classes = {	'fortifier':1,
						'healer':2,
						'skirmisher':3,
						'raider':4,
						'striker':5}

		other_data[char_name] = iso_classes.get(iso_class,0)

		iso_index = {	'striker':7,
						'fortifier':8,
						'healer':9,
						'skirmisher':10,
						'raider':11}.get(iso_class)

		char_info['iso'] = int(iso_entry[iso_index]) if iso_class and iso_index+1 <= len(iso_entry) else 0



# Parse character names, traits, portraits all out of API character call
@timed(level=3)
def parse_char_data(CHAR_DATA, char_list, char_lookup, portraits, traits):

	for char in CHAR_DATA:

		# Short circuit if this isn't a valid entry
		if not char.get('portrait') or not char.get('name'):
			continue

		char_id   = char['id']    # Internal naming
		char_name = char['name']  # Human readable

		PLAYABLE = char['status'] == 'playable'
		
		# Build char_lookup (for name translation)
		char_lookup[char_id] = char_name
		
		# Build portrait lookup -- only accept first definition to avoid being overwritten by Unplayable chars
		portraits.setdefault(char_name, char['portrait'].split('Portrait_')[-1][:-4])
		
		# Only include playable toons in char_list and traits
		if PLAYABLE:
			char_list.append(char_name)
		
			for trait in char.get('traits',[]):
				traits.setdefault(trait,{})[char_name] = 1
			
			for trait in char.get('eventTraits',[]):
				traits.setdefault(trait,{})[char_name] = 1
			
			for trait in char.get('invisibleTraits',[]):
				traits.setdefault(trait,{})[char_name] = 1

	# Delete all Useless traits
	for useless in ['Chargeable', 'Couples', 'Exposed', 'KnowhereHeist', 'KnullChallengers', 'Ultron', 'Wave1', 'Wave1Avenger', 'WebSlinger']:
		if not traits.pop(useless, None):
			print (f'{ansi.bold}No longer need to delete: {ansi.ltyel}{useless}{ansi.reset}')
