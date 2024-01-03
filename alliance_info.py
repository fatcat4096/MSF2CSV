#!/usr/bin/env python3
# Encoding: UTF-8
"""alliance_info.py
Routines used to work with alliance_info, to pull information out or maintain the structure.  
"""


import datetime


# Bring back a sorted list of characters from alliance_info
def get_char_list(alliance_info):

	# We only keep images for heroes that at least one person has recruited.
	char_list = sorted(alliance_info['portraits'])

	return char_list


# Bring back a sorted list of players from alliance_info
def get_player_list(alliance_info, sort_by='', stp_list={}):

	# Only include members that actually have processed_char information attached.
	player_list = [member for member in alliance_info['members'] if 'processed_chars' in alliance_info['members'][member]]

	# If Sort Order specified, sort player_list in the correct order. 
	if sort_by == 'stp':
		# If we weren't provided a list of STPs, fall back to using TCP.
		if not stp_list:
			sort_by = 'tcp'
		else:
			player_list = sorted(player_list, key=lambda x: -stp_list[x])

	if sort_by == 'tcp':
		player_list = sorted(player_list, key=lambda x: -alliance_info['members'][x]['tcp'])

	# Default sort: alphabetical, ignoring case
	if not sort_by:
		player_list.sort(key=str.lower)

	return player_list


# Pull out STP values from either Meta Chars or all Active Chars.
def get_stp_list(alliance_info, char_list, hist_tab='', team_pwr_dict={}):
	
	# Get the list of Alliance Members 
	player_list = get_player_list (alliance_info)

	for player_name in player_list:

		# Build a list of all character powers.
		all_char_pwr = [find_value_or_diff(alliance_info, player_name, char_name,'power', hist_tab)[0] for char_name in char_list]
		all_char_pwr.sort()

		# And sum up the Top 5 power entries for STP.
		team_pwr_dict[player_name] = sum(all_char_pwr[-5:])

	return team_pwr_dict


# Split meta chars from other chars. Filter others based on provided traits.
def get_meta_other_chars(alliance_info, table, section, table_format, hist_tab=''):

	# Get the list of usable characters
	char_list = get_char_list (alliance_info)

	# Meta Chars not subject to min requirements. Filter out only uncollected heroes.
	meta_chars = sorted(section.get('meta',[]))
	meta_chars = [char for char in char_list if char in meta_chars]

	# Other is everything left over. 
	other_chars = [char for char in char_list if not char in meta_chars]

	# Load up arguments from table, with defaults if necessary.
	min_iso  = table_format.get('min_iso')
	if min_iso is None:
		min_iso = table.get('min_iso',0)
	min_tier  = table_format.get('min_tier')
	if min_tier is None:
		min_tier = table.get('min_tier',0)
 
	# Get the list of Alliance Members we will iterate through as rows.	
	player_list = get_player_list (alliance_info)

	# If there are minimums or trait filters for this section, evaluate each character before using the active_chars list.
	if min_iso:
		other_chars = [char for char in other_chars if max([find_value_or_diff(alliance_info, player, char, 'iso')[0] for player in player_list]) >= min_iso]

	if min_tier:
		other_chars = [char for char in other_chars if max([find_value_or_diff(alliance_info, player, char, 'tier')[0] for player in player_list]) >= min_tier]

	# Get extracted_traits from alliance_info
	extracted_traits = alliance_info['extracted_traits']

	# Only filter other_chars.
	traits = section.get('traits',[])
	if type(traits) is str:
		traits = [traits]
		
	traits_req = table.get('traits_req','any')		# Default is 'any'

	excluded_traits = [trait[4:] for trait in traits if trait[:4] == 'Non-']
	traits          = [trait     for trait in traits if trait[:4] != 'Non-']

	for char in other_chars[:]:

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
		if char not in extracted_traits.get(trait,[]):
			other_chars.remove(char)			

		# Final check, does this character have any EXCLUDED traits?
		for trait in excluded_traits:

			# Character is from an EXCLUDED group. Remove it.
			if char in extracted_traits.get(trait,[]) and char in other_chars:
				other_chars.remove(char)

	# Filter out any characters which no one has summoned.
	meta_chars  = [char for char in meta_chars  if sum([find_value_or_diff(alliance_info, player, char, 'power')[0] for player in player_list])]
	other_chars = [char for char in other_chars if sum([find_value_or_diff(alliance_info, player, char, 'power')[0] for player in player_list])]

	# Calculate info for an under_min section, hide it in table for later use. 
	table['under_min'] = {}

	# Before filtering further, while we have visibility for the entire section...
	for player_name in player_list:
		for char_name in meta_chars+other_chars:

			# ...calculate whether entry is under the min requirements for use in this raid/mode .
			under_min =              find_value_or_diff(alliance_info, player_name, char_name, 'iso' )[0] < min_iso
			under_min = under_min or find_value_or_diff(alliance_info, player_name, char_name, 'tier')[0] < min_tier
			table['under_min'].setdefault(player_name,{})[char_name] = under_min 

	# If not overridden, pull value from table if it exists.
	max_others  = table_format.get('max_others')
	if max_others is None:
		max_others = table.get('max_others', len(other_chars))

	# No means no.
	if meta_chars and max_others == 0:
		other_chars = []

	# Default sort is still 'alpha'.
	sort_char_by = table_format.get('sort_char_by')
	if sort_char_by is None:
		sort_char_by = table.get('sort_char_by','alpha')

	# This section sorts other_chars by power or availability, not by name.
	# If max_others, this order is also used to select which we keep. 
	if sort_char_by in ['power','avail'] or max_others:

		# Number of people who have summoned a character.
		dict_count = {char:sum([find_value_or_diff(alliance_info, player, char, 'power', hist_tab)[0] != 0 for player in player_list]) for char in other_chars}

		# Average power of this char across all rosters who have summoned.
		dict_power = {char:int(sum([find_value_or_diff(alliance_info, player, char, 'power', hist_tab)[0] for player in player_list])/max(dict_count[char],1)) for char in other_chars}

		# Sort by character availability -- how many have been leveled, tie breaker is power across alliance.
		# If we have min_iso/min_tier criteria, also use this to sort/filter the character list.
		dict_ready = {}
		if sort_char_by == 'avail' or min_iso or min_tier:
			dict_ready = {char:sum([not table['under_min'].get(player,{}).get(char,True) for player in player_list]) for char in other_chars}
		
		# If sort_by 'power', dict_ready is ignored.
		dict_score = {f'{dict_ready.get(char,0):03}{dict_power[char]:010}':char for char in other_chars}

		# If max_others is defined, reduce the number of heroes included in Others. 
		other_chars = [dict_score[score] for score in sorted(dict_score, reverse=True)][:max_others]

	if sort_char_by == 'alpha':
		other_chars.sort()

	# If only meta specified, just move it to others so we don't have to do anything special.
	if meta_chars and not other_chars:
		other_chars, meta_chars = meta_chars, other_chars
	
	return meta_chars, other_chars


# Find this member's oldest entry in our historical entries.
def find_value_or_diff(alliance_info, player_name, char_name, key, hist_tab=''):

	other_data = ''

	# Find the current value. 
	char_info = alliance_info['members'][player_name]['processed_chars'][char_name]
	current_val = int(char_info[key])
	
	# If we're not on a history tab, we're almost done.
	if not hist_tab:
	
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

	# Start with the oldest entry in 'hist'.
	min_date = min(alliance_info['hist'])
	if player_name in alliance_info['hist'][min_date]:

		hist_info   = alliance_info['hist'][min_date][player_name].get(char_name,{})

		# get the difference between the oldest value and the current one.
		delta_val = current_val - int(hist_info.get(key,0))

		# If there's a difference and the key is power, we need details for tooltip. 
		if delta_val and key == 'power':

			# Iterate through all the stats we're currently tracking.
			diffs = []
			for entry in char_info:
				diff = int(char_info[entry]) - int(hist_info.get(entry,0))

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


