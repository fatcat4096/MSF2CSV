#!/usr/bin/env python3
# Encoding: UTF-8
"""alliance_info.py
Routines used to work with alliance_info, to pull information out or maintain the structure.  
"""

from log_utils import *

import datetime
import string
import copy
import re

from file_io     import find_cached_data
from parse_cache import update_parse_cache
from cached_info import get_cached

@timed(level=3)
def get_hist_date(alliance_info, table_format):
	hist_date = None

	# If this alliance_info qualifies for History and it's being requested, return the matching date.
	if 'hist' in alliance_info and len(alliance_info['hist'])>1 and table_format.get('inc_hist'):

		# Requested date is passed in the inc_hist tag.
		hist_date = table_format.get('inc_hist')

		# If requested date doesn't exist, jsut return the oldest date.
		if hist_date not in alliance_info['hist']:
			hist_date = min(alliance_info['hist'])

	return hist_date



# Bring back a sorted list of players from alliance_info
def get_player_list(alliance_info, sort_by: str='', stp_list: dict=None, section: dict=None, char_list: list=[], hist_date=None):

	player_list = alliance_info.get('members', [])

	# If Sort Order specified, sort player_list in the correct order. 
	if sort_by == 'stp' and stp_list:
		return sorted(player_list, key=lambda x: -stp_list[hist_date][x])

	# Sort by avail if requested, use stp as secondary criteria.
	elif sort_by == 'avail' and section:

		# Factor in STP when sorting by availability.
		local_stp = {}

		for player in player_list:
			inc_char = set([char for char in section.get('under_min',{}).get(player,{}) if not section.get('under_min',{}).get(player,{}).get(char)] + char_list)
			pow_list = sorted([find_value_or_diff(alliance_info, player, char_name, 'power') for char_name in inc_char])
			local_stp[player] = sum(pow_list[-5:])

		return sorted(player_list, key=lambda x: -len([char for char in section.get('under_min',{}).get(x,{}) if not section.get('under_min',{}).get(x,{}).get(char)])*10**10 - local_stp.get(x,0))

	# If we weren't provided a list of STPs, fall back to using TCP.
	elif sort_by in ('tcp','stp','avail'):
		return sorted(player_list, key=lambda x: -alliance_info['members'][x].get('tcp',0))
	
	# Otherwise, just do a default alpha sort.
	return sorted(player_list, key=str.lower)



# Pull out STP values from either Meta Chars or all Active Chars.
def get_stp_list(alliance_info, char_list, hist_date=None):
	
	stp_list = {}

	# Get the list of Alliance Members 
	player_list = get_player_list(alliance_info)

	# Do it twice if we're passed a valid hist_date
	for date_to_use in {None}.union({hist_date}):

		# Iterate through player_list building up STP for each player on the dates in question
		for player_name in player_list:

			# Build a list of all character powers.
			all_char_pwr = sorted([find_value_or_diff(alliance_info, player_name, char_name, 'power', date_to_use) for char_name in char_list])

			# And sum up the Top 5 power entries for STP.
			stp_list.setdefault(date_to_use,{})[player_name] = sum(all_char_pwr[-5:])

	return stp_list



# Split meta chars from other chars. Filter others based on provided traits.
@timed(level=3)
def get_meta_other_chars(alliance_info, table, section, table_format):

	# Get the list of usable characters
	char_list = get_cached('char_list')

	# Meta Chars not subject to min requirements. Filter out only uncollected heroes
	meta_chars   = section.get('meta',[])
	sort_char_by = None if '---' in meta_chars else 'alpha'
	
	meta_chars = [char for char in meta_chars if char in char_list]

	# Other is everything left over. 
	other_chars = [char for char in char_list if not char in meta_chars]

	# Get the list of Alliance Members we will iterate through as rows.	
	player_list = get_player_list(alliance_info)

	# Options are 'any' and 'all'. Not currently being used.
	traits_req = get_table_value(table_format, table, section, key='traits_req', default='any')

	# Apply filters to other_char list.
	other_chars = filter_on_traits(section, traits_req, other_chars)

	# Filter out any characters which no one has summoned
	other_chars = [char for char in other_chars if sum([find_value_or_diff(alliance_info, player, char, 'power') for player in player_list])]

	# Set aside a list of the other_chars prior to filtering for minimums
	before_filter = other_chars[:]

	# Filter out anyone less than the min_iso / min_tier
	other_chars = remove_min_iso_tier(alliance_info, table_format, table, section, player_list, other_chars)

	# Calculate info for an under_min section, hide it in table for later use. 
	section['under_min'] = {}

	# Before filtering further, while we have visibility for the entire section...
	for player_name in player_list:
		for char_name in meta_chars+other_chars:
			is_under_min(alliance_info, player_name, char_name, table_format, table, section) 

	# Start by pulling value from table_format or table
	max_others  = get_table_value(table_format, table, section, key='max_others', default=len(other_chars))
	min_others  = get_table_value(table_format, table, section, key='min_others', default=0)
	
	# Set min_others to max_others if both are defined
	min_others  = max_others if min_others and max_others else min_others

	# If span format requested, override max_others if necessary.
	if table_format.get('span') or table.get('span'):
		if meta_chars:
			max_others = 0
		elif max_others > 5:
			max_others = 5

	# No means no.
	if meta_chars and max_others == 0:
		other_chars = []

	# Default sort is still 'alpha'.
	if sort_char_by:
		sort_char_by = get_table_value(table_format, table, section, key='sort_char_by', default=sort_char_by)

	# This section sorts other_chars by power or availability, not by name.
	# If max_others, this order is also used to select which we keep. 
	if sort_char_by in ['power','avail'] or max_others or min_others:

		hist_date = get_hist_date(alliance_info, table_format)

		# Number of people who have summoned a character.
		dict_count = {char:sum([find_value_or_diff(alliance_info, player, char, 'power', hist_date) != 0 for player in player_list]) for char in other_chars}

		# Average power of this char across all rosters who have summoned.
		dict_power = {char:int(sum([find_value_or_diff(alliance_info, player, char, 'power', hist_date) for player in player_list])/max(dict_count[char],1)) for char in other_chars}

		# Sort by character availability -- how many have been leveled, tie breaker is power across alliance.
		# If we have min_iso/min_tier criteria, also use this to sort/filter the character list.
		dict_ready = {}
		if sort_char_by == 'avail':
			dict_ready = {char:sum([not section['under_min'].get(player,{}).get(char,True) for player in player_list]) for char in other_chars}
				
		# Determine which players are actually being included and which chars they have at level.
		players_in_report = sum(get_strike_teams(alliance_info, table, table_format),[])
		chars_in_report = {char:sum([not section['under_min'].get(player,{}).get(char,True) for player in players_in_report]) for char in other_chars}

		# When evaluating character popularity, only consider chars that will actually be included.
		dict_score = {f'{dict_ready.get(char,0):03}{dict_power[char]:010}':char for char in other_chars if chars_in_report[char]}
		other_chars = [dict_score[score] for score in sorted(dict_score, reverse=True)]

		# If max_others is defined, reduce the number of heroes included in Others.
		if max_others:
			other_chars = other_chars[:max_others]

		# If we're forcing a min number of entries to be displayed, ensure we have at least that many
		if min_others and min_others > len(other_chars):

			# Omit any we're already including, need to sort the rest by power
			before_filter = [char for char in before_filter if char not in other_chars]
			
			# Number of people who have summoned a character
			dict_count = {char:sum([find_value_or_diff(alliance_info, player, char, 'power', hist_date) != 0 for player in player_list]) for char in before_filter}

			# Calc average power for these toons
			dict_power = {char:int(sum([find_value_or_diff(alliance_info, player, char, 'power', hist_date) for player in player_list])/max(dict_count[char],1)) for char in before_filter}

			# Calculate a score for these toons
			dict_score = {f'{dict_power[char]:010}':char for char in before_filter}

			# Sort these by the same criteria and add them to the other_chars list
			other_chars += [dict_score[score] for score in sorted(dict_score, reverse=True)]

			# Truncate the composite list to min_others length
			other_chars = other_chars[:min_others]

	elif sort_char_by == 'alpha':
		other_chars.sort()

	# If only meta specified, just move it to others so we don't have to do anything special.
	if meta_chars and not other_chars:
		other_chars, meta_chars = meta_chars, other_chars

	return meta_chars, other_chars



def filter_on_traits(section, traits_req='any', char_list=None):

	# Only use trait filters for other_chars.
	traits = section.get('traits',[])
	if type(traits) is str:
		traits = [traits]

	# If no traits specified, no chars will be included.
	if not traits:
		return []

	if char_list is None:
		char_list = get_cached('char_list')[:]

	# Get extracted_traits from alliance_info
	extracted_traits = get_cached('traits')

	excluded_traits = [trait[4:] for trait in traits if trait[:4] == 'Non-']
	included_traits = [trait     for trait in traits if trait[:4] != 'Non-']

	for char in char_list[:]:

		# All is All
		if 'All' in included_traits:
			continue

		# Skip explicitly named characters.
		if char in included_traits:
			continue

		# Does this char have any of the listed traits?
		trait = ''
		for trait in included_traits:

			# any == additive (include if any trait is valid)
			if traits_req == 'any' and char in extracted_traits.get(trait,[]):
				break

			# all == reductive (must have all traits for inclusion)
			if traits_req == 'all' and char not in extracted_traits.get(trait,[]):
				break

		# If char isn't in the final trait examined, remove it.
		if trait and char not in extracted_traits.get(trait,[]):
			char_list.remove(char)			

		# Final check, does this character have any EXCLUDED traits?
		for trait in excluded_traits:

			# Character is from an EXCLUDED group. Remove it.
			if char in extracted_traits.get(trait,[]) and char in char_list:
				char_list.remove(char)

	return char_list



# Filter char list for only characters built to min specs
def remove_min_iso_tier(alliance_info, table_format, table, section, player_list, char_list):

	final_list = []

	for char in char_list:
		for player in player_list:
			# If at least one player has this char built to min specs, include in list and move on
			if not is_under_min(alliance_info, player, char, table_format, table, section):
				final_list.append(char)
				break

	return final_list



def is_under_min(alliance_info, player_name, char_name, table_format, table, section):

	# Short-circuit if possible
	under_min = section.get('under_min',{}).get(player_name,{}).get(char_name)
	if under_min is not None:
		return under_min

	# Not summoned is under_min
	if find_value_or_diff(alliance_info, player_name, char_name, 'power') == 0:
		section.setdefault('under_min',{}).setdefault(player_name,{})[char_name] = True
		return True

	# Profile only non-historical data
	PROFILE = table_format.setdefault('profile', {}).setdefault('min', {})

	# Calculate whether entry is under the min requirements for use in this raid/mode.
	for key in ('lvl','tier','iso','yel','red'):
		min_val = PROFILE[key] = get_table_value(table_format, table, section, key=f'min_{key}', default=0)

		if min_val and find_value_or_diff(alliance_info, player_name, char_name, key) < min_val:
			section.setdefault('under_min',{}).setdefault(player_name,{})[char_name] = True
			return True

	section.setdefault('under_min',{}).setdefault(player_name,{})[char_name] = False



# Return the correct strike_team definitions, depending on formatting flags.
@timed(level=3)
def get_strike_teams(alliance_info, table, table_format):
	# If only_members specified, use this list instead of previously defined Strike Teams.
	only_members = get_table_value(table_format, table, key='only_members')
	if only_members:

		# If a single name was provided, wrap it in a list.
		if type(only_members) is str:
			only_members = [only_members]

		# Wrap up the only_members list in a Strike Team entry.
		strike_teams = [only_members]
	else:
		# Which strike_teams should we use? (Strike Teams CANNOT vary section by section.)
		strike_teams = get_table_value(table_format, table, key='strike_teams')

		# Grab specified strike teams if available. 
		strike_teams = alliance_info.get('strike_teams',{}).get(strike_teams)

		# Insert dividers as necessary
		inc_dividers = get_table_value(table_format, table, key='inc_dividers', default='other')
		if inc_dividers and strike_teams:
			strike_teams = insert_dividers(strike_teams, inc_dividers)

	# If no strike team definitions are specified / found or 
	# If only_team == 0 (ignore strike_teams) **AND**
	# no sort_by has been specified, force sort_by to 'stp'
	only_team = get_table_value(table_format, table, key='only_team')
	if (not strike_teams or only_team == 0) and not get_table_value(table_format, table, key='sort_by'):
		table_format['sort_by'] = 'stp'

	# Sort player list if requested.
	sort_by = get_table_value(table_format, table, key='sort_by')

	# Use the full Player List sorted by stp if explicit Strike Teams haven't been defined.
	if not strike_teams or only_team == 0:
		strike_teams = [get_player_list(alliance_info, sort_by)]

	return strike_teams



# Insert dividers based on the type of team. 
@timed
def insert_dividers(strike_teams, raid_type):

	# Start with a copy, just to be safe.
	strike_teams = copy.deepcopy(strike_teams)

	for team in strike_teams:

		# Use 2-3-3 lanes if Incursion 1.x -- OBSOLETE, UNUSED
		if raid_type in ('incur'):
			if len(team) > 2:
				team.insert(2,'----')
			if len(team) > 6:
				team.insert(6,'----')

		# Use 3-2-3 lanes if Thunder
		elif raid_type in ('323'):
			if len(team) > 3:
				team.insert(3,'----')
			if len(team) > 6:
				team.insert(6,'----')

		# Use 2-2-2-2 lanes if Spotlight -- OBSOLETE, UNUSED
		elif raid_type in ('spotlight'):
			if len(team) > 2:
				team.insert(2,'----')
			if len(team) > 5:
				team.insert(5,'----')
			if len(team) > 8:
				team.insert(8,'----')

		# Use 5/3 split for Sort by STP within Strike Teams.
		elif raid_type == '53':
			if len(team) > 5:
				team.insert(5,'----')

		# Put a divider in the middle to reflect left/right symmetry of raids.
		else:
			if len(team) > 4:
				team.insert(4,'----')

	return strike_teams
	
	

# Find this member's oldest entry in our historical entries.
def find_value_or_diff(alliance_info, player_name, char_name, key, hist_date=None, null=0, other_info=''):

	# Find the current value. 
	char_info = alliance_info['members'][player_name].get('processed_chars',{}).get(char_name,{})

	# Abilities have to be treated a little differently. 
	if key in ('bas','spc','ult','pas'):
		bas,abil = divmod(char_info.get('abil',0),1000)
		spc,abil = divmod(abil,100)
		ult,pas  = divmod(abil,10)
		char_info = char_info.copy()
		char_info.update({'bas':bas, 'spc':spc, 'ult':ult, 'pas':pas})

	current_val = char_info.get(key,null)

	if key == 'red':
		current_val += int(char_info.get('dmd',0))

	# If we're not on a history tab, we're almost done.
	if not hist_date:
	
		# If we're on a 'power' entry, summarize the other stats for display in a tooltip
		if other_info and key == 'power' and current_val:
			
			lvl_info = f"Lvl: {char_info.get('lvl',0)}t{char_info.get('tier',0)}<br>"

			iso  = char_info.get('iso',0)
			iso_info = f'ISO: {int((iso-1)/5)+1}-{(iso-1)%5+1}<br>' if iso else ''

			red  = char_info.get('red',0)
			dmd  = char_info.get('dmd',0)
			red_or_dmd = f'{dmd}D' if dmd else f'{red}R' if red else ''

			star_info = f"Rank: {char_info.get('yel',0)}Y{red_or_dmd}<br>"
			abil_info = f"Abil: {char_info.get('abil','n/a')}"

			# Create a tooltip with the noted differences.
			other_info = f'<span class="TT">{lvl_info}{iso_info}{star_info}{abil_info}</span>'
	
		return (current_val, other_info) if other_info else current_val

	# If requested date doesn't exist or no date specified, use the oldest date available.
	if hist_date not in alliance_info['hist']:
		hist_list = sorted([date for date in alliance_info['hist'] if date<hist_date])
		hist_date = hist_list[-1] if hist_list else min(alliance_info['hist'])

	if player_name in alliance_info['hist'][hist_date]:

		hist_info = alliance_info['hist'][hist_date][player_name].get(char_name,{})

		# Abilities have to be treated a little differently. 
		if key in ('bas','spc','ult','pas'):
			bas,abil = divmod(hist_info.get('abil',0),1000)
			spc,abil = divmod(abil,100)
			ult,pas  = divmod(abil,10)
			hist_info = char_info.copy()
			hist_info.update({'bas':bas, 'spc':spc, 'ult':ult, 'pas':pas})

		# get the difference between the oldest value and the current one.
		delta_val = current_val - hist_info.get(key,0)
		if key == 'red':
			delta_val -= hist_info.get('dmd',0)

		# If there's a difference and the key is power, we need details for tooltip. 
		if other_info and delta_val and key == 'power':

			# Iterate through all the stats we're currently tracking.
			diffs = []
			for entry in char_info:
			
				diff = char_info[entry] - hist_info.get(entry,0)

				if diff:
					# Straightforward diff for most entries.
					if entry != 'abil':
						diff_lbl = {'power':'Pwr'}.get(entry,entry.title())
						diffs.append(f'{diff_lbl}: {diff:+}')

					# More work to decode the Ability entry.
					else:
						bas,abil = divmod(diff,1000)
						spc,abil = divmod(abil,100)
						ult,pas  = divmod(abil,10)
						abil_diffs = {'bas':bas, 'spc':spc, 'ult':ult, 'pas':pas}
						
						# And then add only the specific abilities which changed.
						for abil in abil_diffs:
							if abil_diffs[abil]:
								diffs.append(f'{abil.title()}: {abil_diffs[abil]:+}')

			# Create a tooltip with the noted differences.
			other_info = f'<span class="TT">{"<br>".join(diffs)}</span>' if diffs else ''
		
		return (delta_val, other_info) if other_info else delta_val

	# Should not happen. Missing alliance members should be copied into all historical entries.
	return (null, other_info) if other_info else null



# Archive the current run into the 'hist' tag for future analysis.
@timed(level=3)
def update_history(alliance_info):	

	# Get a little closer to our work.
	alliance_members = alliance_info['members']

	# Create the 'hist' key if it doesn't already exist.
	hist = alliance_info.setdefault('hist',{})

	# Overwrite any existing info for today.
	today      = datetime.date.today()
	today_info = hist.setdefault(today,{})

	for member in alliance_members:
		if 'processed_chars' in alliance_members[member]:
			today_info[member] = alliance_members[member]['processed_chars']
	
	# Start with today as a reference. 
	prev_entry = today_info

	# Let's clean things up.
	parse_cache = {}
	char_list = get_cached('portraits')
	
	# Clean up any old / unnecessary entries in 'hist':
	for entry in sorted(hist,reverse=True):
	
		# Remove anyone who isn't still in the alliance.
		for member in list(hist[entry]):
			if member not in alliance_members:
				del hist[entry][member]

		# If someone in the alliance isn't in the older hist entry, copy the earliest entry in to normalize hist data.
		for member in prev_entry:
			if member not in hist[entry]:
				hist[entry][member] = prev_entry[member]

		# Change frame of reference to this historical entry as we move backward
		prev_entry = hist[entry]

	# One more loop through to clean up toon entries.
	for entry in sorted(hist):
		for member in list(hist[entry]):
			# Start by cleaning up toon entries.
			for char_name in list(hist[entry][member]):

				# Delete errant information added when name translations not available.
				if char_name not in char_list:
					del hist[entry][member][char_name]
					continue

				# Look for a duplicate entry in our cache and point both to the same entry if possible.
				update_parse_cache(hist[entry][member],char_name,parse_cache)
		
	# Compare today's data vs. the most recent History entry. 
	# If anything identical to previous entry, point today's entry at the previous entry.
	hist_list = sorted(hist)
	hist_list.remove(today)
	
	for member in alliance_members:
	
		# Can only examine those with processed roster information.
		if 'processed_chars' in alliance_members[member] and hist_list and member in hist[max(hist_list)]:

			# Get a little closer to our work.
			member_info = alliance_members[member]

			# Optimize the leaves.
			for char_name in list(alliance_members[member]['processed_chars']):

				# Delete errant information added when name translations not available.
				if char_name not in char_list:
					del alliance_members[member]['processed_chars'][char_name]
					continue

				# Look for a duplicate entry in our cache and point both to the same entry if possible.
				update_parse_cache(alliance_members[member]['processed_chars'],char_name,parse_cache)
		
			# Compare today's information vs the previous run.
			if member_info['processed_chars'] == hist[max(hist_list)][member]:

				# If equal, no changes have been made or roster hasn't been resynced.
				# Point processed_chars and today's entry to the previous entry
				member_info['processed_chars'] = hist[max(hist_list)][member]
				today_info[member] = hist[max(hist_list)][member]

	# Keep every day for a week, keep every other day after a week, keep one per week after two weeks, anything over 365 days is deleted
	prev_week  = None
	prev_day   = None

	for key in hist_list:
		date_diff = (today-key).days

		key_week  = key.isocalendar().week
		key_day   = int(key.timetuple().tm_yday/2)
		
		if date_diff > 365 or (date_diff > 14 and key_week == prev_week) or (date_diff > 7 and key_day == prev_day):
			del alliance_info['hist'][key]

		prev_week  = key_week
		prev_day   = key_day
		


# If Member's roster has grown more than 1% from last sync or hasn't synced in more than a week, consider it stale.
@timed(level=3)
def is_stale(alliance_info, member_name):

	# Load thresholds, if they're explicitly defined.
	max_growth = alliance_info.get('settings',{}).get('percent_growth', 1.5)
	max_age    = alliance_info.get('settings',{}).get('older_than', 7)

	# Get a little closer to our work. 
	member_info = alliance_info['members'][member_name]
	
	# Using the inverse to avoid a divide by zero if roster unavailable.
	percent_growth = member_info.get('tot_power',0)/member_info.get('tcp',1)

	# Time since last roster sync 
	last_update = 'last_update' in member_info and (datetime.datetime.now() - member_info['last_update']).total_seconds()
	
	# If either is true, flag it as stale.
	return percent_growth < (1-(max_growth/100)) or last_update > 60*60*24*max_age



# All settings, we build up the same way
def get_table_value(table_format, table, section: dict={}, key: str='', default=None):

	# Check for a custom value in table_format
	value = table_format.get(key)

	# If nothing in table_format, look for a value in section
	if value is None:
		value = section.get(key)
	
	# If still nothing, look in table definition
	# If nothing there fall back to the default value.
	if value is None:
		value = table.get(key,default)
	
	return value



# Verify the fresh and old cached data are the same alliance 
# Merge data if old info available
@timed(level=3)
def find_cached_and_merge(alliance_info, old_alliance_name=None):

	# Look for an existing cached_data file with the old name (if provided) or the current one 
	cached_info = find_cached_data(old_alliance_name or alliance_info['name'])
	
	# Nothing to merge.
	if not cached_info:
		return

	# Copy over extra information into freshly downloaded alliance_info.
	for key in cached_info:
		if key not in alliance_info:
			alliance_info[key] = cached_info[key]
	
	# Also copy over additional information inside the member definitions. 
	for member in alliance_info['members']:
		for key in cached_info.get('members',{}).get(member,{}):
			if key not in alliance_info['members'][member]:
				alliance_info['members'][member][key] = cached_info['members'][member][key]

	# Explicitly bring over missing 'hist' entries as well. 
	for key in cached_info.get('hist',{}):
		if key not in alliance_info.setdefault('hist',{}):
			alliance_info['hist'][key] = cached_info['hist'][key]
	
	# If we merged with the old alliance name first, repeat the process with the current name
	if old_alliance_name:
		find_cached_and_merge(alliance_info)
