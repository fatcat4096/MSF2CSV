#!/usr/bin/env python3
# Encoding: UTF-8
"""alliance_info.py
Routines used to work with alliance_info, to pull information out or maintain the structure.  
"""

from log_utils import *

import datetime
import string


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


# Bring back a sorted list of characters from alliance_info
@timed(level=3)
def get_char_list(alliance_info):

	# We only keep images for heroes that at least one person has recruited.
	char_list = sorted(alliance_info.get('portraits',{}))

	return char_list


# Bring back a sorted list of players from alliance_info
def get_player_list(alliance_info, sort_by='', stp_list={}, table={}):

	player_list = alliance_info['members']

	# If Sort Order specified, sort player_list in the correct order. 
	if sort_by == 'stp' and stp_list:
		return sorted(player_list, key=lambda x: -stp_list[None][x])
	# Sort by avail if requested.
	elif sort_by == 'avail' and table:
		return sorted(player_list, key=lambda x: -len([char for char in table.get('under_min',{}).get(x,{}) if not table.get('under_min',{}).get(x,{}).get(char)]))
	# If we weren't provided a list of STPs, fall back to using TCP.
	elif sort_by in ('tcp','stp','avail'):
		return sorted(player_list, key=lambda x: -alliance_info['members'][x].get('tcp',0))
	
	# Otherwise, just do a default sort.
	return sorted(player_list, key=str.lower)


# Pull out STP values from either Meta Chars or all Active Chars.
def get_stp_list(alliance_info, char_list, hist_date=None, team_pwr_dict={}):
	
	# Get the list of Alliance Members 
	player_list = get_player_list(alliance_info)

	for player_name in player_list:

		# Build a list of all character powers.
		all_char_pwr = sorted([find_value_or_diff(alliance_info, player_name, char_name, 'power', hist_date)[0] for char_name in char_list], reverse=True)

		# And sum up the Top 5 power entries for STP.
		team_pwr_dict.setdefault(hist_date,{})[player_name] = sum(all_char_pwr[:5])

	return team_pwr_dict


# Split meta chars from other chars. Filter others based on provided traits.
@timed(level=3)
def get_meta_other_chars(alliance_info, table, section, table_format):

	# Get the list of usable characters
	char_list = get_char_list (alliance_info)

	# Meta Chars not subject to min requirements. Filter out only uncollected heroes.
	meta_chars = sorted(section.get('meta',[]))
	meta_chars = [char for char in char_list if char in meta_chars]

	# Other is everything left over. 
	other_chars = [char for char in char_list if not char in meta_chars]

	# Get the list of Alliance Members we will iterate through as rows.	
	player_list = get_player_list (alliance_info)

	# Get extracted_traits from alliance_info
	extracted_traits = alliance_info.get('traits',{})

	# Only use trait filters for other_chars.
	traits = section.get('traits',[])
	if type(traits) is str:
		traits = [traits]

	# If no traits specified, no other chars will be included.
	if not traits:
		other_chars = []

	# Options are 'any' and 'all'. Not currently being used.
	traits_req = get_table_value(table_format, table, section, key='traits_req', default='any')

	excluded_traits = [trait[4:] for trait in traits if trait[:4] == 'Non-']
	traits          = [trait     for trait in traits if trait[:4] != 'Non-']

	for char in other_chars[:]:

		# All is All
		if 'All' in traits:
			continue

		# Skip explicitly named characters.
		if char in traits:
			continue

		# Does this char have any of the listed traits?
		trait = ''
		for trait in traits:

			# any == additive (include if any trait is valid)
			if traits_req == 'any' and char in extracted_traits.get(trait,[]):
				break

			# all == reductive (must have all traits for inclusion)
			if traits_req == 'all' and char not in extracted_traits.get(trait,[]):
				break

		# If char isn't in the final trait examined, remove it.
		if trait and char not in extracted_traits.get(trait,[]):
			other_chars.remove(char)			

		# Final check, does this character have any EXCLUDED traits?
		for trait in excluded_traits:

			# Character is from an EXCLUDED group. Remove it.
			if char in extracted_traits.get(trait,[]) and char in other_chars:
				other_chars.remove(char)

	# Filter out anyone less than the min_iso / min_tier
	other_chars = remove_min_iso_tier(alliance_info, table_format, table, section, player_list, other_chars)

	# Filter out any characters which no one has summoned.
	other_chars = [char for char in other_chars if sum([find_value_or_diff(alliance_info, player, char, 'power')[0] for player in player_list])]

	# Calculate info for an under_min section, hide it in table for later use. 
	table['under_min'] = {}

	# Load up arguments from table, with defaults if necessary.
	min_lvl  = get_table_value(table_format, table, section, key='min_lvl',  default=0)
	min_tier = get_table_value(table_format, table, section, key='min_tier', default=0)
	min_iso  = get_table_value(table_format, table, section, key='min_iso',  default=0)

	# Before filtering further, while we have visibility for the entire section...
	for player_name in player_list:
		for char_name in meta_chars+other_chars:

			# ...calculate whether entry is under the min requirements for use in this raid/mode .
			under_min = 0
			if min_lvl:
				under_min = under_min or find_value_or_diff(alliance_info, player_name, char_name, 'lvl' )[0] < min_lvl
			if min_tier:
				under_min = under_min or find_value_or_diff(alliance_info, player_name, char_name, 'tier')[0] < min_tier
			if min_iso:
				under_min = under_min or find_value_or_diff(alliance_info, player_name, char_name, 'iso' )[0] < min_iso
			table['under_min'].setdefault(player_name,{})[char_name] = under_min 

	# Start by pulling value from table_format or table.
	max_others  = get_table_value(table_format, table, section, key='max_others', default=len(other_chars))

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
	sort_char_by = get_table_value(table_format, table, section, key='sort_char_by', default='alpha')

	# This section sorts other_chars by power or availability, not by name.
	# If max_others, this order is also used to select which we keep. 
	if sort_char_by in ['power','avail'] or max_others:

		hist_date = get_hist_date(alliance_info, table_format)

		# Number of people who have summoned a character.
		dict_count = {char:sum([find_value_or_diff(alliance_info, player, char, 'power', hist_date)[0] != 0 for player in player_list]) for char in other_chars}

		# Average power of this char across all rosters who have summoned.
		dict_power = {char:int(sum([find_value_or_diff(alliance_info, player, char, 'power', hist_date)[0] for player in player_list])/max(dict_count[char],1)) for char in other_chars}

		# Sort by character availability -- how many have been leveled, tie breaker is power across alliance.
		# If we have min_iso/min_tier criteria, also use this to sort/filter the character list.
		dict_ready = {}
		if sort_char_by == 'avail' or min_lvl or min_tier or min_iso:
			dict_ready = {char:sum([not table['under_min'].get(player,{}).get(char,True) for player in player_list]) for char in other_chars}
		
		# If sort_by 'power', dict_ready is ignored.
		dict_score = {f'{dict_ready.get(char,0):03}{dict_power[char]:010}':char for char in other_chars}

		# If max_others is defined, reduce the number of heroes included in Others.
		other_chars = [dict_score[score] for score in sorted(dict_score, reverse=True)]
		if max_others:
			other_chars = other_chars[:max_others]

	if sort_char_by == 'alpha':
		other_chars.sort()

	# If only meta specified, just move it to others so we don't have to do anything special.
	if meta_chars and not other_chars:
		other_chars, meta_chars = meta_chars, other_chars

	return meta_chars, other_chars


def remove_min_iso_tier(alliance_info, table_format, table, section, player_list, char_list):

	# Load up arguments from table, with defaults if necessary.
	min_lvl  = get_table_value(table_format, table, section, key='min_lvl',  default=0)
	min_tier = get_table_value(table_format, table, section, key='min_tier', default=0)
	min_iso  = get_table_value(table_format, table, section, key='min_iso',  default=0)
 
	# If there are minimums or trait filters for this section, evaluate each character before using the active_chars list.
	if min_lvl:
		char_list = [char for char in char_list if max([find_value_or_diff(alliance_info, player, char, 'lvl' )[0] for player in player_list]) >= min_lvl]
	if min_tier:
		char_list = [char for char in char_list if max([find_value_or_diff(alliance_info, player, char, 'tier')[0] for player in player_list]) >= min_tier]
	if min_iso:
		char_list = [char for char in char_list if max([find_value_or_diff(alliance_info, player, char, 'iso' )[0] for player in player_list]) >= min_iso]

	return char_list


# Find this member's oldest entry in our historical entries.
def find_value_or_diff(alliance_info, player_name, char_name, key, hist_date=None):

	other_data = ''

	# Find the current value. 
	char_info = alliance_info['members'][player_name].get('processed_chars',{}).get(char_name,{})

	# Abilities have to be treated a little differently. 
	if key in ('bas','spc','ult','pas'):
		bas,abil = divmod(char_info.get('abil',0),1000)
		spc,abil = divmod(abil,100)
		ult,pas  = divmod(abil,10)
		char_info = char_info.copy()
		char_info.update({'bas':bas, 'spc':spc, 'ult':ult, 'pas':pas})

	current_val = int(char_info.get(key,0))
	
	# If we're not on a history tab, we're almost done.
	if not hist_date:
	
		# If we're on a 'power' entry, summarize the other stats for display in a tooltip
		if key == 'power' and current_val:
			
			lvl  = char_info.get('lvl',0)
			tier = char_info.get('tier',0)
			iso  = char_info.get('iso',0)
			yel  = char_info.get('yel',0)
			red  = char_info.get('red',0)
			dmd  = char_info.get('dmd',0)
			abil = char_info.get('abil','n/a')

			data = [f'<b>Lvl:</b> {lvl}t{tier}']
			if iso:
				data.append('<b>ISO:</b> %s-%s' % (int((iso-1)/5)+1,(iso-1)%5+1))
			data.append(f'<b>Stars:</b> {yel}Y' + [f'{red}R',''][not red] + [f'{dmd}D',''][not dmd])
			data.append(f'<b>Abil:</b> {abil}')

			# Create a tooltip with the noted differences.
			other_data = '<span class="ttt">%s</span>' % ('<br>'.join(data))
	
		return current_val,other_data

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

		# If there's a difference and the key is power, we need details for tooltip. 
		if delta_val and key == 'power':

			# Iterate through all the stats we're currently tracking.
			diffs = []
			for entry in char_info:
			
				diff = char_info[entry] - hist_info.get(entry,0)

				if diff:
					# Straightforward diff for most entries.
					if entry != 'abil':
						diff_lbl = {'power':'Pwr'}.get(entry,entry.title())
						diffs.append(f'<b>{diff_lbl}:</b> {diff:+}')

					# More work to decode the Ability entry.
					else:
						bas,abil = divmod(diff,1000)
						spc,abil = divmod(abil,100)
						ult,pas  = divmod(abil,10)
						abil_diffs = {'bas':bas, 'spc':spc, 'ult':ult, 'pas':pas}
						
						# And then add only the specific abilities which changed.
						for abil in abil_diffs:
							if abil_diffs[abil]:
								diffs.append(f'<b>{abil.title()}:</b> {abil_diffs[abil]:+}')

			# Create a tooltip with the noted differences.
			other_data = ['<span class="ttt">%s</span>' % ('<br>'.join(diffs)),''][not diffs]
		
		return delta_val, other_data

	# Should not happen. Missing alliance members should be copied into all historical entries.
	return 0,other_data


# Archive the current run into the 'hist' tag for future analysis.
@timed(level=3)
def update_history(alliance_info):	

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

	# Clean up any old / unnecessary entries in 'hist':
	for entry in sorted(hist,reverse=True):
	
		# Remove anyone who isn't still in the alliance.
		for member in list(hist[entry]):
			if member not in alliance_members:
				del hist[entry][member]

			## Temp code to clean up junk data in hist entries for old cached_data files.
			## DELETE IN 2024
			else:
				if 'tot_power'   in hist[entry][member]:	del hist[entry][member]['tot_power']
				if 'last_update' in hist[entry][member]:	del hist[entry][member]['last_update']

		# If someone in the alliance isn't in the older hist entry, copy the earliest entry in to normalize hist data.
		for member in prev_entry:
			if member not in hist[entry]:
				hist[entry][member] = prev_entry[member]

		# Change frame of reference to this historical entry as we move backward
		prev_entry = hist[entry]
		
	# Compare today's data vs. the most recent History entry. 
	# If anything identical to previous entry, point today's entry at the previous entry.
	hist_list = list(hist)
	hist_list.remove(today)
	
	for member in alliance_members:
	
		# Can only examine those with processed roster information.
		if 'processed_chars' in alliance_members[member] and hist_list and member in hist[max(hist_list)]:

			# Get a little closer to our work.
			member_info = alliance_members[member]
			
			# Compare today's information vs the previous run.
			if member_info['processed_chars'] == hist[max(hist_list)][member]:

				# If equal, no changes have been made or roster hasn't been resynced.
				# Point processed_chars and today's entry to the previous entry
				member_info['processed_chars'] = hist[max(hist_list)][member]
				today_info[member] = hist[max(hist_list)][member]

	# Keep the oldest entry, plus one per ISO calendar week. Also, purge any entries > 60 days. 
	for key in hist_list:
		if (key.isocalendar().week == today.isocalendar().week and key is not min(hist)) or today-key > datetime.timedelta(90):
			del alliance_info['hist'][key]


# If Member's roster has grown more than 1% from last sync or hasn't synced in more than a week, consider it stale.
@timed(level=3)
def is_stale(alliance_info, member_name):

	# TEMPORARY PATH, ALWAYS RETURN FALSE FOR IS_STALE.
	return False
	
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
def get_table_value(table_format, table, section={}, key='', default=None):

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


# parse a string containing roster_urls, return only the first valid User ID.
@timed(level=3)
def find_valid_roster_url(field_value):
	
	found_url = ''
	
	# Parse the whole string and only extract the first if any found.
	found_urls = find_valid_roster_urls(field_value)
	if found_urls:
		found_url = found_urls[0]
		
	return found_url


# parse a string containing roster_urls, looking for valid user IDs.
@timed(level=3)
def find_valid_roster_urls(field_value):

	found_urls = []

	# Short-circuit if we received None
	if not field_value:
		return found_urls	
			
	# If multiple values entered in a single field, process them all.
	for value in field_value.split():

		# If it looks like a URL or Roster ID, check it out. 
		for piece in value.split('/'):
			if is_valid_user_id(piece):
				found_urls.append(piece)
	
	return found_urls


# Validate user_id formatting.
@timed(level=3)
def is_valid_user_id(s):
	if not s:
		return False
	if len(s) == 13 and set(s).issubset(string.hexdigits):
		return True
	elif len(s) == 36 and s[8]+s[13]+s[18]+s[23] == '----' and s.count('-') == 4 and set(s).issubset(string.hexdigits+'-'):
		return True
	return False



# Update the fresh alliance_info from website with extra info from cached_data.
@timed(level=3)
def update_alliance_info_from_cached(alliance_info, cached_alliance_info):

	# Copy over extra information into freshly downloaded alliance_info.
	for key in cached_alliance_info:
		if key not in alliance_info:
			alliance_info[key] = cached_alliance_info[key]
			
	# Also copy over additional information inside the member definitions. 
	for member in alliance_info['members']:
		for key in ['processed_chars','url','other_data','max','arena','blitz','stars','red','tot_power','last_update','discord','scopely']:
			if key in cached_alliance_info['members'].get(member,{}) and key not in alliance_info['members'][member]:
				alliance_info['members'][member][key] = cached_alliance_info['members'][member][key]