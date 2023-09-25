#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_html.py
Takes the processed alliance / roster data and generate readable output to spec.  
"""

import datetime

# Routines to create color gradient for heat map
from gradients import *	


# Build the entire file -- headers, footers, and tab content for each lane and the Alliance Information.
def generate_html(alliance_info, nohist, table, cached_tabs={}):

	default_lanes = [[{'traits': ['Mutant']},
					  {'traits': ['Bio']},
					  {'traits': ['Skill']},
					  {'traits': ['Mystic']},
					  {'traits': ['Tech']}]]

	lanes      = table.get('lanes',default_lanes)
	table_name = table.get('name','')
	
	# If we're doing a single lane format and we have history, let's generate a historical data tab. 
	hist_tab = ''
	if len(lanes) == 1 and len(alliance_info['hist'])>1 and {'power','tier','iso','lvl'}.issuperset(table.get('keys',[])) and not nohist:
		hist_tab = "CHANGES SINCE %s" % min(alliance_info['hist'])

	# Gotta start somewhere.
	html_file = '<!doctype html>\n<html lang="en">\n'

	# Add a header to give us a tabbed interface.
	html_file += add_tabbed_header(len(lanes), hist_tab, table_name)
	
	# Add a tab for each lane. 
	html_file += generate_lanes(alliance_info, table, lanes)

	# Add a historical info tab.
	if hist_tab:
		html_file += generate_lanes(alliance_info, table, lanes, hist_tab)

	# Same tabs for all documents, so only need to generate them once.
	cached_ranges= {}
	if not cached_tabs:
		cached_tabs['roster_analysis'] = generate_roster_analysis(alliance_info)
		cached_tabs['alliance_tab']    = generate_alliance_tab(alliance_info)

	# After all Lanes are added, add the Roster Analysis tab.
	html_file += cached_tabs['roster_analysis']

	# Finally, add the Alliance Info tab.
	html_file += cached_tabs['alliance_tab']

	# Finally, add the Javascript to control tabbed display.
	html_file += add_tabbed_footer()
	
	# All done with All Lanes. Close the file.
	html_file += '</html>\n'

	return html_file


# Generate the contents for each lane.
def generate_lanes(alliance_info, table, lanes, hist_tab = '', html_file = ''):

	# Iterate through all the lanes. Showing tables for each section. 
	for lane in lanes:
		
		# Display each lane in a separate tab.
		lane_num = lanes.index(lane)+1
		html_file += '<div id="%s%i" class="tabcontent">\n' % (['Hist','Lane'][not hist_tab], lane_num)

		# Process each section individually, filtering only the specified traits into the Active Chars list.
		for section in lane:
		
			meta_chars, other_chars = get_meta_other_chars(alliance_info, table, section, hist_tab)
			keys = table.get('keys',['power','tier','iso'])

			# Use the full Player List if explicit Strike Teams haven't been defined.
			strike_teams = alliance_info['strike_teams'].get(table.get('strike_teams'), [get_player_list(alliance_info)])

			# Start with the Basic Table Label and Colors.
			table_lbl = '<br>'.join([translate_name(trait) for trait in section['traits']]).upper()

			# Only calling it twice if we have meta_chars defined.
			if meta_chars:
				meta_lbl = table_lbl+'<br><span class="subtitle">META</span>'

				html_file += '<table>\n <tr>\n  <td>\n'
				html_file += generate_table(alliance_info, keys, meta_chars, strike_teams, meta_lbl, get_stp_list(alliance_info, meta_chars, hist_tab), hist_tab)
				html_file += '  </td>\n  <td><br></td>\n  <td>\n'

				# Differentiate Others Section from Meta Section
				table_lbl += '<br><span class="subtitle">OTHERS</span>'

			# Always generate the Others table.
			# Only label it as such if Meta section exists.
			html_file += generate_table(alliance_info, keys, other_chars, strike_teams, table_lbl, get_stp_list(alliance_info, meta_chars+other_chars, hist_tab), hist_tab)

			# If in a nested table, close the nested table.
			if meta_chars:
				html_file += '  </td>\n </tr>\n</table>\n'

			# If not the final section, add a divider row. 
			if lane.index(section) != len(lane)-1:
				html_file += '    <p></p>\n'

		# After Lane content is done, close the div for the Tab implementation.
		html_file += '</div>\n'

	return html_file


# Split meta chars from other chars. Filter others based on provided traits.
def get_meta_other_chars(alliance_info, table, section, hist_tab):

	# Get the list of usable characters
	char_list = get_char_list (alliance_info)

	# Meta Chars not subject to min requirements. Filter out only uncollected heroes.
	meta_chars = section.get('meta',[])
	meta_chars.sort()
	meta_chars = [char for char in char_list if char in meta_chars]

	# Other is everything left over. 
	other_chars = [char for char in char_list if not char in meta_chars]

	# Load up arguments from table, with defaults if necessary.
	min_iso  = table.get('min_iso', 0)
	min_tier = table.get('min_tier',0)

	# Get the list of Alliance Members we will iterate through as rows.	
	player_list = get_player_list (alliance_info)

	# If there are minimums or trait filters for this section, evaluate each character before using the active_chars list.
	if min_iso:
		other_chars = [char for char in other_chars if max([int(alliance_info['members'][player]['processed_chars'][char]['iso']) for player in player_list]) >= min_iso]

	if min_tier:
		other_chars = [char for char in other_chars if max([int(alliance_info['members'][player]['processed_chars'][char]['tier']) for player in player_list]) >= min_tier]
	
	# Get extracted_traits from alliance_info
	extracted_traits = alliance_info['extracted_traits']
	
	# Trait filters are additive. Only filter other_chars.
	traits = section['traits']
	if traits:
		for char in other_chars[:]:
			for trait in traits:
				if trait in extracted_traits and char in extracted_traits[trait]:
					# Character has at least one of these traits. Leave it in.
					break
			# Did we find this char in any of the traits?
			if trait not in extracted_traits or char not in extracted_traits[trait]:
				other_chars.remove(char)

	# Filter out any characters which no one has summoned.
	meta_chars  = [char for char in meta_chars  if sum([int(alliance_info['members'][player]['processed_chars'][char]['power']) for player in player_list])]
	other_chars = [char for char in other_chars if sum([int(alliance_info['members'][player]['processed_chars'][char]['power']) for player in player_list])]

	# If historical, filter out any character which no one has improved. 
	if hist_tab:
		meta_chars  = [char for char in meta_chars  if sum([find_oldest_diff(alliance_info, player, char, 'power')[0] for player in player_list])]
		other_chars = [char for char in other_chars if sum([find_oldest_diff(alliance_info, player, char, 'power')[0] for player in player_list])]

	# If only meta specified, just move it to others so we don't have to do anything special.
	if meta_chars and not other_chars:
		other_chars, meta_chars = meta_chars, other_chars
		
	return meta_chars, other_chars


# Generate individual tables for Meta/Other chars for each raid section.
def generate_table(alliance_info, keys=['power','tier','iso'], char_list=[], strike_teams = [], table_lbl='', all_team_pwr={}, hist_tab = '', html_file = ''):

	# Get the list of Alliance Members we will iterate through as rows.	
	player_list = get_player_list (alliance_info)

	if table_lbl.find('OTHERS') == -1:
		title_cell    = 'title_blue'
		table_header  = 'header_blue'
		char_cell     = 'char_blue'
		name_cell     = 'name_blue'
		name_cell_alt = 'name_blue_alt'
		team_pwr_lbl  = 'Team<br>Power'
	else:
		title_cell    = 'title_gray'
		table_header  = 'header_gray'
		char_cell     = 'char_gray'
		name_cell     = 'name_gray'
		name_cell_alt = 'name_gray_alt'
		team_pwr_lbl  = 'STP<br>(Top 5)'

	# Let's get this party started!
	html_file += '   <table>\n'

	# WRITE THE IMAGES ROW. #############################################
	html_file += '    <tr class="%s">\n' % (title_cell) 
	html_file += '     <td>%s</td>\n' % (table_lbl)

	# Include Images for each of the Characters.
	for char in char_list:
		html_file += '     <th class="image" colspan="%i"><img src="https://assets.marvelstrikeforce.com/imgs/Portrait_%s" alt="" width="100"></th>\n' % (len(keys), alliance_info['portraits'][char])

	# Include a Team Power column.
	html_file += '     <td></td>\n'
	html_file += '    </tr>\n'
	# DONE WITH THE IMAGES ROW. #########################################

	# WRITE THE CHARACTER NAMES ROW. ####################################
	html_file += '    <tr class="%s">\n' % (char_cell)
	
	if len(keys)>1 and len(strike_teams)>1:
		html_file += '     <th>Alliance<br>Member</th>\n'
	else:
		html_file += '     <td></td>\n'

	# Include information for the Meta Characters.
	for char in char_list:
		html_file += '     <th colspan="%i" width="100">%s</th>\n' % (len(keys), translate_name(char))

	# Include the Team Power column.
	html_file += '     <th></th>\n' 
	html_file += '    </tr>\n'
	# DONE WITH THE CHARACTER NAMES ROW. ################################

	# Iterate through each Strike Team.
	for team in strike_teams:

		# Find min/max for meta/strongest team power in this Strike Team
		# This will be used for color calculation for the Team Power column.
		tot_team_pwr = [all_team_pwr[player_name] for player_name in player_list if player_name in team]
		min_team_pwr = min(tot_team_pwr)
		max_team_pwr = max(tot_team_pwr)

		# WRITE THE HEADING ROW WITH VALUE DESCRIPTORS ##################
		# (only if more than one item requested)
		if len(keys)>1 or len(strike_teams)>1:
			html_file += '    <tr class="%s">\n' % table_header
			
			if len(strike_teams)>1:
				html_file += '     <td>STRIKE TEAM %i</td>\n' % (strike_teams.index(team)+1)
			else:
				html_file += '     <td>Alliance<br>Member</td>\n'

			# Insert stat headings for each included Character.
			for char in char_list:
				for key in keys:
					html_file += '     <td>%s</td>\n' % {'lvl':'Level'}.get(key,key.title())

			# Insert the Team Power column.
			html_file += '     <td class="power">%s</td>\n' % (team_pwr_lbl)
			html_file += '    </tr>\n'
		# DONE WITH THE HEADING ROW FOR THIS STRIKE TEAM ################

		# FINALLY, WRITE THE DATA FOR EACH ROW. #########################
		# Player Name, then relevant stats for each character.
		alt_color = False
		for player_name in team:
		
			# If can't find the specified player name, let's check to see if it's a simple issue of capitalization.
			if player_name not in player_list:

				# Maybe they just got the wrong case? Fix it silently, if so.
				player_lower = [player.lower() for player in player_list]
				if player_name.lower() in player_lower:
					player_name = player_list[player_lower.index(player_name.lower())]

				# Maybe we just haven't gotten a roster yet?
				elif player_name in alliance_info['members']:
					pass

				# Toggle a flag for each divider to change the color of Player Name slightly
				else:
					alt_color = not alt_color

			# Time to build the row.
			if player_name in player_list:
				html_file += '    <tr%s>\n' % [' class="hist"',''][not hist_tab]
				html_file += '     <th class="%s">%s</th>\n' % ([name_cell, name_cell_alt][alt_color], player_name)

				# Write the stat values for each character.
				for char_name in char_list:

					for key in keys:

						# Standard lookup. Get the range of values for this character for all rosters.
						if not hist_tab:
							key_vals = [int(alliance_info['members'][player]['processed_chars'][char_name][key]) for player in player_list]

						# If historical, we want the diff between the current values and the values in the oldest record
						else:
							key_vals = [find_oldest_diff(alliance_info, player, char_name, key)[0] for player in player_list]

						min_val = min(key_vals)
						max_val = max(key_vals)

						# Only look up the value if we have a roster.
						value = 0
						other_diffs = ''
						if player_name in player_list:
						
							# Standard lookup. Get the value for this character stat from this player's roster.
							if not hist_tab:
								value = alliance_info['members'][player_name]['processed_chars'][char_name][key]
							# If historical, we look for the first time this member appears in the History, and then display the difference between the stat in that record and this one.
							else:
								value,other_diffs = find_oldest_diff(alliance_info, player_name, char_name, key)
						style = ''
						if value not in (0,'0'):
							style = ' style="background:%s;%s"' % (get_value_color(min_val, max_val, value, key, hist_tab), ['color:black;',''][not hist_tab])
						html_file += '     <td%s%s>%s</td>\n' % (style, other_diffs, [value,'-'][value in (0,'0')])

				# Include the Team Power column.
				team_pwr = all_team_pwr.get(player_name,0)
				html_file += '     <td class="bold" style="background:%s;">%s</td>\n' % (get_value_color(min_team_pwr, max_team_pwr, team_pwr), [team_pwr,'-'][team_pwr in (0,'0')])
				html_file += '    </tr>\n'
		# DONE WITH THE DATA ROWS FOR THIS STRIKE TEAM ##################

	# Close the Table, we are done with this chunk.
	html_file += '   </table>\n'

	return html_file


# Find this member's oldest entry in our historical entries.
def find_oldest_diff(alliance_info, player_name, char_name, key):
	dates = list(alliance_info['hist'])

	# Start with the oldest entry in 'hist', looking for this member's stats.
	while dates:
		min_date = min(dates)
		if player_name in alliance_info['hist'][min_date]:

			# Get the current value of this key.
			value = int(alliance_info['members'][player_name]['processed_chars'][char_name][key]) - int(alliance_info['hist'][min_date][player_name].get(char_name,{}).get(key,0))

			if not value:
				return 0,''
		
			# If there was a difference, let's make note of what created that difference.
			diffs = []
			for entry in [item for item in ['power','lvl','tier','iso'] if item != key]:
				diff = int(alliance_info['members'][player_name]['processed_chars'][char_name][entry]) - int(alliance_info['hist'][min_date][player_name].get(char_name,{}).get(entry,0))

				if diff:
					diffs.append(f'{entry.title()}: {diff:+}')

			other_diffs = [' title="%s"' % (', '.join(diffs)),''][not diffs]
			return value, other_diffs

		# Oldest entry didn't have it, go one newer.
		dates.remove(min_date)

	# Should not happen. Should always at least find this member in the most recent run.
	return 0,''


# Find this member's oldest entry in our historical entries.
def find_oldest_val(alliance_info, player_name, char_name, key):
	dates = list(alliance_info['hist'])

	# Start with the oldest entry in 'hist', looking for this member's stats.
	while dates:
		min_date = min(dates)
		if player_name in alliance_info['hist'][min_date]:
			# Found a valid record, return the value in 'key'
			if char_name in alliance_info['hist'][min_date][player_name]:
				return alliance_info['hist'][min_date][player_name][char_name][key]
			# This character has been added since oldest history record.
			return '0'

		# Oldest entry didn't have it, go one newer.
		dates.remove(min_date)

	# Should not happen. Should always at least find this member in the most recent run.
	return '0'




# Generate just the Alliance Tab contents.
def generate_roster_analysis(alliance_info, html_file=''):

	html_file += '<div id="RosterAnalysis" class="tabcontent">\n'
	html_file += '<table>\n'

	# Create the headings for the Alliance Info table.
	html_file += '<tr class="header_blue" style="font-size:14pt;">\n'
	html_file += ' <td width="200" rowspan="2">Name</td>\n'            
	html_file += ' <td width="80" rowspan="2">Total<br>Power</td>\n'
	html_file += ' <td width="80" rowspan="2">Strongest<br>Team</td>\n'
	html_file += ' <td width="80" rowspan="2">Total<br>Chars</td>\n'
	html_file += ' <td width="2" rowspan="2"></td>\n' 				# Vertical Divider
	
	html_file += ' <td width="200" colspan="5">Average #</td>\n'	# All Avg Stats
	html_file += ' <td width="2" rowspan="2"></td>\n' 				# Vertical Divider

	html_file += ' <td width="160" colspan="4">Stars</td>\n'		# Yel 4-7
	html_file += ' <td width="2" rowspan="2"></td>\n' 				# Vertical Divider

	html_file += ' <td width="160" colspan="4">Red Stars</td>\n'	# Red 4-7
	html_file += ' <td width="2" rowspan="2"></td>\n' 				# Vertical Divider

	html_file += ' <td width="200" colspan="5">ISO</td>\n'			# ISO 1-4,5,6-8,9,10
	html_file += ' <td width="2" rowspan="2"></td>\n' 				# Vertical Divider

	html_file += ' <td width="240" colspan="6">Gear Tier</td>\n'	# Tier 13-18
	html_file += ' <td width="2" rowspan="2"></td>\n' 				# Vertical Divider

	html_file += ' <td width="160" colspan="4">T4 Abilities</td>\n'	# Bas/Spc/Ult/Pas
	html_file += ' <td width="2" rowspan="2"></td>\n' 				# Vertical Divider

	html_file += ' <td width="350" colspan="7">Levels</td>\n'		# <65,66-70,71-75,76-80,81-85,86-90,91-95
	html_file += '</tr\n'
	

	# Second Row with subheadings.
	html_file += '<tr>\n'

	# Averages
	html_file += ' <td class="name_blue" width="40">Yel</td>\n'
	html_file += ' <td class="name_blue" width="40">Red</td>\n'
	html_file += ' <td class="name_blue" width="40">Tier</td>\n'
	html_file += ' <td class="name_blue" width="40">Lvl</td>\n'
	html_file += ' <td class="name_blue" width="40">ISO</td>\n'
	
	# Yellow Stars
	html_file += ' <td class="name_blue" width="40">4*</td>\n'
	html_file += ' <td class="name_blue" width="40">5*</td>\n'
	html_file += ' <td class="name_blue" width="40">6*</td>\n'
	html_file += ' <td class="name_blue" width="40">7*</td>\n'
	
	# Red Stars
	html_file += ' <td class="name_blue" width="40">4*</td>\n'
	html_file += ' <td class="name_blue" width="40">5*</td>\n'
	html_file += ' <td class="name_blue" width="40">6*</td>\n'
	html_file += ' <td class="name_blue" width="40">7*</td>\n'

	# ISO Levels
	html_file += ' <td class="name_blue" width="40">1-4</td>\n'
	html_file += ' <td class="name_blue" width="40">5</td>\n'
	html_file += ' <td class="name_blue" width="40">6-8</td>\n'
	html_file += ' <td class="name_blue" width="40">9</td>\n'
	html_file += ' <td class="name_blue" width="40">10</td>\n'

	# Gear Tiers
	html_file += ' <td class="name_blue" width="40">13</td>\n'
	html_file += ' <td class="name_blue" width="40">14</td>\n'
	html_file += ' <td class="name_blue" width="40">15</td>\n'
	html_file += ' <td class="name_blue" width="40">16</td>\n'
	html_file += ' <td class="name_blue" width="40">17</td>\n'
	html_file += ' <td class="name_blue" width="40">18</td>\n'

	# T4 Abilities
	html_file += ' <td class="name_blue" width="40">Bas</td>\n'
	html_file += ' <td class="name_blue" width="40">Spc</td>\n'
	html_file += ' <td class="name_blue" width="40">Ult</td>\n'
	html_file += ' <td class="name_blue" width="40">Pas</td>\n'

	# Level Ranges
	html_file += ' <td class="name_blue" width="50">&lt;65</td>\n'
	html_file += ' <td class="name_blue" width="50">66-70</td>\n'
	html_file += ' <td class="name_blue" width="50">71-75</td>\n'
	html_file += ' <td class="name_blue" width="50">76-80</td>\n'
	html_file += ' <td class="name_blue" width="50">81-85</td>\n'
	html_file += ' <td class="name_blue" width="50">86-90</td>\n'
	html_file += ' <td class="name_blue" width="50">91-95</td>\n'

	html_file += '</tr>\n'
	
	stats = {}
	
	# Get the list of Alliance Members 
	member_list = get_player_list(alliance_info)

	# Get the list of usable characters for analysis.
	char_list = get_char_list(alliance_info)
	
	# Start by doing stat analysis.	
	for member in member_list:
	
		# Get a little closer to our work.
		member_stats = stats.setdefault(member,{})
		
		# Don't include stats from heroes that haven't been recruited yet.
		recruited_chars = [char for char in char_list if alliance_info['members'][member]['processed_chars'][char]['power']!='0']

		# Loop through every char
		for char in recruited_chars:
		
			# Get a little closer to our work.
			char_stats = alliance_info['members'][member]['processed_chars'][char]
			
			# Just tally the values in each key. Increment the count of each value found.
			for key in ['yel', 'red', 'lvl', 'tier', 'iso', 'bas', 'spc', 'ult', 'pas']:
				member_stats.setdefault(key,{})[int(char_stats[key])] = member_stats.get(key,{}).setdefault(int(char_stats[key]),0)+1

	# Build ranges for each statistic. We will use min() and max() to 
	tcp_range    = [alliance_info['members'][member]['tcp'] for member in member_list]
	stp_range    = [alliance_info['members'][member]['stp'] for member in member_list]
	tcc_range    = [alliance_info['members'][member]['tcc'] for member in member_list]

	# Averages
	stars_range  = [alliance_info['members'][member]['stars'] for member in member_list]
	red_range    = [alliance_info['members'][member]['red']   for member in member_list]
	tier_range   = [sum([lvl*stats[member]['tier'][lvl] for lvl in stats[member]['tier']]) for member in member_list]
	lvl_range    = [sum([lvl*stats[member]['lvl'][lvl]  for lvl in stats[member]['lvl']])  for member in member_list]
	iso_range    = [sum([lvl*stats[member]['iso'][lvl]  for lvl in stats[member]['iso']])  for member in member_list]
	
	# Yellow Stars
	yel4_range   = [stats[member]['yel'].get(4,0) for member in member_list]
	yel5_range   = [stats[member]['yel'].get(5,0) for member in member_list]
	yel6_range   = [stats[member]['yel'].get(6,0) for member in member_list]
	yel7_range   = [stats[member]['yel'].get(7,0) for member in member_list]

	# Red Stars
	red4_range   = [stats[member]['red'].get(4,0) for member in member_list]
	red5_range   = [stats[member]['red'].get(5,0) for member in member_list]
	red6_range   = [stats[member]['red'].get(6,0) for member in member_list]
	red7_range   = [stats[member]['red'].get(7,0) for member in member_list]

	# ISO Levels
	iso4_range   = [sum([stats[member]['iso'].get(iso,0) for iso in range(0,5)]) for member in member_list]
	iso5_range   = [stats[member]['iso'].get(5,0) for member in member_list]
	iso8_range   = [sum([stats[member]['iso'].get(iso,0) for iso in range(6,9)]) for member in member_list]
	iso9_range   = [stats[member]['iso'].get(9,0) for member in member_list]
	iso10_range  = [stats[member]['iso'].get(10,0) for member in member_list]

	# Gear Tiers
	tier13_range = [stats[member]['tier'].get(13,0) for member in member_list]
	tier14_range = [stats[member]['tier'].get(14,0) for member in member_list]
	tier15_range = [stats[member]['tier'].get(15,0) for member in member_list]
	tier16_range = [stats[member]['tier'].get(16,0) for member in member_list]
	tier17_range = [stats[member]['tier'].get(17,0) for member in member_list]
	tier18_range = [stats[member]['tier'].get(18,0) for member in member_list]

	# T4 Abilities
	bas_range   = [stats[member]['bas'].get(7,0)+stats[member]['bas'].get(8,0) for member in member_list]
	spc_range   = [stats[member]['spc'].get(7,0)+stats[member]['spc'].get(8,0) for member in member_list]
	ult_range   = [stats[member]['ult'].get(7,0)+stats[member]['ult'].get(8,0) for member in member_list]
	pas_range   = [stats[member]['pas'].get(5,0)+stats[member]['pas'].get(6,0) for member in member_list]

	# Level Ranges
	lvl65_range   = [sum([stats[member]['lvl'].get(lvl,0) for lvl in range( 1,66)]) for member in member_list]
	lvl70_range   = [sum([stats[member]['lvl'].get(lvl,0) for lvl in range(66,71)]) for member in member_list]
	lvl75_range   = [sum([stats[member]['lvl'].get(lvl,0) for lvl in range(71,76)]) for member in member_list]
	lvl80_range   = [sum([stats[member]['lvl'].get(lvl,0) for lvl in range(76,81)]) for member in member_list]
	lvl85_range   = [sum([stats[member]['lvl'].get(lvl,0) for lvl in range(81,86)]) for member in member_list]
	lvl90_range   = [sum([stats[member]['lvl'].get(lvl,0) for lvl in range(86,91)]) for member in member_list]
	lvl95_range   = [sum([stats[member]['lvl'].get(lvl,0) for lvl in range(91,96)]) for member in member_list]

	# Iterate through each row for members in the table.
	for member in member_list:
			member_info = alliance_info['members'][member]
			member_stats = stats[member]
			
			html_file += '<tr>\n'
			html_file += ' <td class="name_blue">%s</td>\n' % (member)
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(tcp_range), max(tcp_range), member_info['tcp']), f'{member_info["tcp"]:,}')
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(stp_range), max(stp_range), member_info['stp']), f'{member_info["stp"]:,}')
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(tcc_range), max(tcc_range), member_info['tcc']), f'{member_info["tcc"]:,}')
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Averages
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(stars_range), max(stars_range), member_info['stars']), round(member_info['stars'] / member_info['tcc'], 2))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(red_range),   max(red_range),   member_info['red']),   round(member_info['red']   / member_info['tcc'], 2))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(tier_range),  max(tier_range),  sum([lvl*member_stats['tier'][lvl] for lvl in member_stats['tier']])), round(sum([lvl*member_stats['tier'][lvl] for lvl in member_stats['tier']]) / member_info['tcc'], 2))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(lvl_range),   max(lvl_range),   sum([lvl*member_stats['lvl' ][lvl] for lvl in member_stats['lvl' ]])), round(sum([lvl*member_stats['lvl' ][lvl] for lvl in member_stats['lvl' ]]) / member_info['tcc'], 2))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(iso_range),   max(iso_range),   sum([lvl*member_stats['iso' ][lvl] for lvl in member_stats['iso' ]])), round(sum([lvl*member_stats['iso' ][lvl] for lvl in member_stats['iso' ]]) / member_info['tcc'], 2))
			html_file += ' <td></td>\n' 										# Vertical Divider
			
			# Yellow Stars
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(yel4_range),  max(yel4_range),  member_stats['yel'].get(4,0)),  member_stats['yel'].get(4,0))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(yel5_range),  max(yel5_range),  member_stats['yel'].get(5,0)),  member_stats['yel'].get(5,0))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(yel6_range),  max(yel6_range),  member_stats['yel'].get(6,0)),  member_stats['yel'].get(6,0))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(yel7_range),  max(yel7_range),  member_stats['yel'].get(7,0)),  member_stats['yel'].get(7,0))
			html_file += ' <td></td>\n' 										# Vertical Divider                                                            
																																							  
			# Red Stars                                                                                                                                       
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(red4_range),  max(red4_range),  member_stats['red'].get(4,0)),  member_stats['red'].get(4,0))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(red5_range),  max(red5_range),  member_stats['red'].get(5,0)),  member_stats['red'].get(5,0))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(red6_range),  max(red6_range),  member_stats['red'].get(6,0)),  member_stats['red'].get(6,0))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(red7_range),  max(red7_range),  member_stats['red'].get(7,0)),  member_stats['red'].get(7,0))
			html_file += ' <td></td>\n' 										# Vertical Divider                                                            
																																							  
			# ISO Levels                                                                                                                                      
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(iso4_range),  max(iso4_range),  sum([member_stats['iso'].get(iso,0) for iso in range(0,5)])), sum([member_stats['iso'].get(iso,0) for iso in range(0,5)]))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(iso5_range),  max(iso5_range),  member_stats['iso'].get(5,0)),  member_stats['iso'].get(5,0))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(iso8_range),  max(iso8_range),  sum([member_stats['iso'].get(iso,0) for iso in range(6,9)])), sum([member_stats['iso'].get(iso,0) for iso in range(6,9)]))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(iso9_range),  max(iso9_range),  member_stats['iso'].get(9,0)),  member_stats['iso'].get(9,0))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(iso10_range), max(iso10_range), member_stats['iso'].get(10,0)), member_stats['iso'].get(10,0))
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Gear Tiers
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(tier13_range),  max(tier13_range), member_stats['tier'].get(13,0)), member_stats['tier'].get(13,0))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(tier14_range),  max(tier14_range), member_stats['tier'].get(14,0)), member_stats['tier'].get(14,0))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(tier15_range),  max(tier15_range), member_stats['tier'].get(15,0)), member_stats['tier'].get(15,0))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(tier16_range),  max(tier16_range), member_stats['tier'].get(16,0)), member_stats['tier'].get(16,0))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(tier17_range),  max(tier17_range), member_stats['tier'].get(17,0)), member_stats['tier'].get(17,0))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(tier18_range),  max(tier18_range), member_stats['tier'].get(18,0)), member_stats['tier'].get(18,0))
			html_file += ' <td></td>\n' 										# Vertical Divider

			# T4 Abilities
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(bas_range), max(bas_range), member_stats['bas'].get(7,0)+member_stats['bas'].get(8,0)), member_stats['bas'].get(7,0)+member_stats['bas'].get(8,0))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(spc_range), max(spc_range), member_stats['spc'].get(7,0)+member_stats['spc'].get(8,0)), member_stats['spc'].get(7,0)+member_stats['spc'].get(8,0))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(ult_range), max(ult_range), member_stats['ult'].get(7,0)+member_stats['ult'].get(8,0)), member_stats['ult'].get(7,0)+member_stats['ult'].get(8,0))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(pas_range), max(pas_range), member_stats['pas'].get(5,0)+member_stats['pas'].get(6,0)), member_stats['pas'].get(5,0)+member_stats['pas'].get(6,0))
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Level Ranges
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(lvl65_range), max(lvl65_range), sum([member_stats['lvl'].get(lvl,0) for lvl in range( 1,66)])), sum([member_stats['lvl'].get(lvl,0) for lvl in range( 1,66)]))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(lvl70_range), max(lvl70_range), sum([member_stats['lvl'].get(lvl,0) for lvl in range(66,71)])), sum([member_stats['lvl'].get(lvl,0) for lvl in range(66,71)]))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(lvl75_range), max(lvl75_range), sum([member_stats['lvl'].get(lvl,0) for lvl in range(71,76)])), sum([member_stats['lvl'].get(lvl,0) for lvl in range(71,76)]))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(lvl80_range), max(lvl80_range), sum([member_stats['lvl'].get(lvl,0) for lvl in range(76,81)])), sum([member_stats['lvl'].get(lvl,0) for lvl in range(76,81)]))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(lvl85_range), max(lvl85_range), sum([member_stats['lvl'].get(lvl,0) for lvl in range(81,86)])), sum([member_stats['lvl'].get(lvl,0) for lvl in range(81,86)]))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(lvl90_range), max(lvl90_range), sum([member_stats['lvl'].get(lvl,0) for lvl in range(86,91)])), sum([member_stats['lvl'].get(lvl,0) for lvl in range(86,91)]))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(lvl95_range), max(lvl95_range), sum([member_stats['lvl'].get(lvl,0) for lvl in range(91,96)])), sum([member_stats['lvl'].get(lvl,0) for lvl in range(91,96)]))

			html_file += '</tr>\n'

	html_file += '</table>\n'
	html_file += '</div>\n'

	return html_file


# Generate just the Alliance Tab contents.
def generate_alliance_tab(alliance_info, html_file=''):

	tot_power = sum([alliance_info['members'][member]['tcp'] for member in alliance_info['members']])
	avg_power = int(tot_power/len(alliance_info['members']))

	# Use this flag to determine which header information is displayed.
	extras_avail = alliance_info.get('trophies')
	
	html_file += '<div id="AllianceInfo" class="tabcontent">\n'
	html_file += '<table style="background:SteelBlue;">\n'

	html_file += '<tr>\n</tr>\n'

	html_file += '<tr style="font-size:18px;">\n'
	html_file += ' <td colspan="2"  rowspan="2"><img src="https://assets.marvelstrikeforce.com/imgs/ALLIANCEICON_%s"/></td>\n' % (alliance_info['image'])
	html_file += ' <td colspan="10" rowspan="%s" class="alliance_name">%s</td>' % (['1','2'][not extras_avail], alliance_info['name'].upper())
	
	if extras_avail:	html_file += ' <td colspan="2" rowspan="2"><span class="bold" style="font-size:24px">Alliance Message:</span><br>%s</td>' % (alliance_info['desc'])
	else:				html_file += ' <td colspan="2">Total Power<br><span style="font-size:24px;"><b>%s</b></span></td>\n' % (f'{tot_power:,}')

	html_file += '</tr>\n'

	html_file += '<tr style="font-size:18px;">\n'
	if extras_avail:	html_file += ' <td colspan="2">Members<br><span style="font-size:24px;"><b>%i/24</b></span></td>\n' % (len(alliance_info['members']))
	if extras_avail:	html_file += ' <td colspan="2">Total Power<br><span style="font-size:24px;"><b>%s</b></span></td>\n' % (f'{tot_power:,}')
	html_file += ' <td colspan="2">Average Collection Power<br><span style="font-size:24px;"><b>%s</b></span></td>\n' % (f'{avg_power:,}')
	if extras_avail:	html_file += ' <td colspan="2">Level<br><span style="font-size:24px;"><b>%s</b></span></td>\n' % (alliance_info['stark_lvl'])
	if extras_avail:	html_file += ' <td colspan="2">Trophies<br><span style="font-size:24px;"><b>%s</b></span></td>\n' % (alliance_info['trophies'])
	html_file += '</tr>\n'
	
	# Create the headings for the Alliance Info table.
	html_file += '<tr class="header_blue" style="font-size:14pt;">\n'
	html_file += ' <td width="60" ></td>\n'
	html_file += ' <td width="215">Name</td>\n'            
	html_file += ' <td width="110">Level</td>\n'
	html_file += ' <td width="110">Role</td>\n'
	html_file += ' <td width="110">Collection<br>Power</td>\n'
	html_file += ' <td width="110">Strongest<br>Team</td>\n'
	html_file += ' <td width="110">War<br>MVP</td>\n'
	html_file += ' <td width="110">Total<br>Collected</td>\n'
	html_file += ' <td width="110">Max<br>Stars</td>\n'
	html_file += ' <td width="110">Arena<br>Rank</td>\n'
	html_file += ' <td width="110">Blitz<br>Wins</td>\n'
	html_file += ' <td width="110">Total<br>Stars</td>\n'
	html_file += ' <td width="110">Total<br>Red</td>\n'
	html_file += ' <td width="215">Last Updated:</td>\n'
	html_file += '</tr>\n'
	
	alliance_order = sorted(alliance_info['members'].keys(), key = lambda x: alliance_info['members'][x]['tcp'], reverse=True)
	
	# Build up the list of Alliance Members
	member_list =  [alliance_info['leader']] + alliance_info['captains']
	member_list += [member for member in alliance_order if member not in member_list]

	tcp_range   = [alliance_info['members'][member]['tcp']   for member in member_list]
	stp_range   = [alliance_info['members'][member]['stp']   for member in member_list]
	mvp_range   = [alliance_info['members'][member]['mvp']   for member in member_list]
	tcc_range   = [alliance_info['members'][member]['tcc']   for member in member_list]
	max_range   = [alliance_info['members'][member].get('max',0)   for member in member_list]
	arena_range = [alliance_info['members'][member].get('arena',0) for member in member_list]
	blitz_range = [alliance_info['members'][member].get('blitz',0) for member in member_list]
	stars_range = [alliance_info['members'][member].get('stars',0) for member in member_list]
	red_range   = [alliance_info['members'][member].get('red',0)   for member in member_list]

	for member in member_list:
		# Get a little closer to what we're working with.
		member_stats = alliance_info['members'][member]
		
		if member in alliance_info['leader']:
			member_role = 'Leader'
		elif member in alliance_info['captains']:
			member_role = 'Captain'
		else:
			member_role = 'Member'

		member_color = {'Leader':  'PowderBlue',
						'Captain': 'DeepSkyBlue',
						'Member':  'PowderBlue' }[member_role]

		html_file += ' <tr style="background:%s;">\n' % (member_color)
		html_file += '  <td style="padding:0px;"><img height="45" src="https://assets.marvelstrikeforce.com/imgs/Portrait_%s"/></td>\n' % (member_stats['image'])
		html_file += '  <td class="bold">%s</td>\n' % (member)
		html_file += '  <td>%i</td>\n' % (member_stats['level'])
		html_file += '  <td>%s</td>\n' % (member_role)
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(min(tcp_range),   max(tcp_range),   member_stats['tcp']),   f'{member_stats["tcp"]:,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(min(stp_range),   max(stp_range),   member_stats['stp']),   f'{member_stats["stp"]:,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(min(mvp_range),   max(mvp_range),   member_stats['mvp']),   f'{member_stats["mvp"]:,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(max(tcc_range)-5, max(tcc_range),   member_stats['tcc']),   f'{member_stats["tcc"]:,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(min(max_range),   max(max_range),   member_stats.get('max',0)),   f'{member_stats.get("max",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(max(arena_range), min(arena_range), member_stats.get('arena',0)), f'{member_stats.get("arena",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(min(blitz_range), max(blitz_range), member_stats.get('blitz',0)), f'{member_stats.get("blitz",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(min(stars_range), max(stars_range), member_stats.get('stars',0)), f'{member_stats.get("stars",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(min(red_range),   max(red_range),   member_stats.get('red',0)),   f'{member_stats.get("red",0):,}')

		time_since_last = 4*86400
		time_value      = 'Never<br>Ask member to sync roster.'
		if member in alliance_info['members'] and 'processed_chars' in member_stats:
			time_since_last = datetime.datetime.now() - member_stats['processed_chars']['last_update']
			time_value = '%s,<br>%s ago' % (member_stats['processed_chars']['last_update'].strftime('%A, %B %d'), str(time_since_last).split('.')[0])
			time_since_last = time_since_last.total_seconds()
		
		time_color = get_value_color(0, 4*86400, (4*86400)-time_since_last)
		html_file += '  <td style="background:%s;">%s</td>\n' % (time_color, time_value)
		html_file += ' </tr>\n'

	html_file += '</table>\n'
	html_file += '</div>\n'

	return html_file


# Including this here for expedience.
def generate_csv(alliance_info):
	# Write the basic output to a CSV in the local directory.
	keys = ['fav','lvl','power','yel','red','tier','bas','spc','ult','pas','class','iso','iso','iso','iso','iso','iso']
	
	csv_file = ['Name,AllianceName,CharacterId,Favorite,Level,Power,Stars,RedStar,GearLevel,Basic,Special,Ultimate,Passive,ISO Class,ISO Level,ISO Armor,ISO Damage,ISO Focus,ISO Health,ISO Resist']
	
	player_list = get_player_list(alliance_info)
	char_list   = get_char_list (alliance_info)
		
	alliance_name = alliance_info['name']
			
	for player_name in player_list:
		processed_chars = alliance_info['members'][player_name]['processed_chars']

		# Only include entries for recruited characters.
		for char_name in char_list:
			if processed_chars[char_name]['lvl'] != '0':
				csv_file.append(','.join([player_name, alliance_name, char_name] + [processed_chars[char_name][key] for key in keys]))

	return '\n'.join(csv_file)


# Pull out STP values from either Meta Chars or all Active Chars.
def get_stp_list(alliance_info, char_list, hist_tab='', team_pwr_dict={}):
	
	# Get the list of Alliance Members 
	player_list = get_player_list (alliance_info)

	for player_name in player_list:

		# Build a list of all character powers.
		all_char_pwr = [int(alliance_info['members'][player_name]['processed_chars'][char_name]['power']) for char_name in char_list]
		all_char_pwr.sort()

		# And sum up the Top 5 power entries for STP.
		team_pwr_dict[player_name] = sum(all_char_pwr[-5:])

		# Get power of all heroes in the char_list from earliest entry in history. We will sum these and subtract from entry below. 
		if hist_tab:
			old_char_pwr = [int(find_oldest_val(alliance_info, player_name, char_name, 'power')) for char_name in char_list]
			old_char_pwr.sort()
			
			# Use the difference between the new STP and the old value.
			team_pwr_dict[player_name] -= sum(old_char_pwr[-5:])
			
	return team_pwr_dict


# Bring back a sorted list of characters from alliance_info
def get_char_list(alliance_info):

	# We only keep images for heroes that at least one person has recruited.
	char_list = list(alliance_info['portraits'])
	char_list.sort()

	return char_list


# Bring back a sorted list of players from alliance_info
def get_player_list(alliance_info):

	# Only include members that actually have processed_char information attached.
	player_list = [member for member in alliance_info['members'] if 'processed_chars' in alliance_info['members'][member]]
	player_list.sort(key=str.lower)
	
	return player_list


# Quick and dirty translation to shorter or better names.
def translate_name(value):

	tlist = {	"Avenger": "Avengers",
				"AForce": "A-Force",
				"BionicAvenger": "Bionic<br>Avengers",
				"BlackOrder": "Black<br>Order",
				"Brawler": "Brawlers",
				"Brotherhood": "B'Hood",
				"DarkHunter": "Dark<br>Hunters",
				"Defender": "Defenders",
				"Eternal": "Eternals",
				"HeroesForHire": "H4H",
				"Hydra Armored Guard": "Hydra Arm Guard",
				"InfinityWatch": "Infinity<br>Watch",
				"Invader": "Invaders",
				"MastersOfEvil": "Masters<br>Of Evil",
				"Mercenary": "Mercs",
				"NewAvenger": "New<br>Avengers",
				"NewWarrior": "New<br>Warriors",
				"PymTech": "Pym Tech",
				"Ravager": "Ravagers",
				"SecretAvenger": "Secret<br>Avengers",
				"SecretDefender": "Secret<br>Defenders",
				"SinisterSix": "Sinister<br>Six",
				"SpiderVerse": "Spiders",
				"Symbiote": "Symbiotes",
				"TangledWeb": "Tangled<br>Web",
				"WarDog": "War Dogs",
				"WeaponX": "Weapon X",
				"WebWarrior": "Web<br>Warriors",
				"XFactor": "X-Factor",
				"Xforce": "X-Force",
				"Xmen": "X-Men",
				"YoungAvenger": "Young<br>Avengers",
				"Captain America (WWII)": "Capt. America (WWII)",
				"Captain America (Sam)": "Capt. America (Sam)"}

	# Return the translation if available.
	return tlist.get(value, value)


# Quick and dirty CSS to allow Tabbed implementation for raids with lanes.
def add_tabbed_header(num_lanes, hist_tab, table_name = ''):

		html_file = '''
<head>
<title>'''+table_name+''' Info</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fira+Sans+Condensed:wght@400;700;900&display=swap" rel="stylesheet">
<style>

/* Style tab links */
.tablink {
  background  : #888;
  color       : white;
  float       : left;
  border      : none;
  outline     : none;
  cursor      : pointer;
  padding     : 14px 16px;
  font-size   : 24px;
  font-family : 'Fira Sans Condensed';
  font-weight : 900;
  width       : '''+str(int(100/(num_lanes+[3,2][not hist_tab]))) +'''%;	# Adding 1 for Roster Analysis and Alliance Info tabs, 3 if there's also history.
}
.tablink:hover {
  background  : #555;
}
.tabcontent {
  background  : #343734;
  display     : none;
  padding     : 70px 20px;
  height      : 100%;
}

/* Styles for table cells */

.bold {
  font-weight : bold;
  color       : black;
}
.alliance_name {
  font-weight : 700;
  font-size   : 36pt;
}
.title_blue {
  font-weight : 700;
  font-size   : 14pt;
  background  : PowderBlue;
}
.title_gray {
  font-weight : 700;
  font-size   : 14pt;
  background  : Gainsboro;
}
.header_blue {
  font-weight : 700;
  background  : MidnightBlue;
  color       : white;
  white-space : nowrap;
}
.header_gray {
  font-weight : 700;
  background  : Black;
  color       : white;
  white-space : nowrap;
}
.char_blue {
  font-weight : 700;
  background  : SkyBlue;
}
.char_gray {
  font-weight : 700;
  background  : Silver;
}
.name_blue {
  font-weight : 700;
  background  : PowderBlue;
  white-space : nowrap;
  color       : black;
}
.name_blue_alt {
  font-weight : 700;
  background  : DeepSkyBlue;
  white-space : nowrap;
  color       : black;
}
.name_gray {
  font-weight : 700;
  background  : Gainsboro;
  white-space : nowrap;
  color       : black;
}
.name_gray_alt {
  font-weight : 700;
  background  : DarkGray;
  white-space : nowrap;
  color       : black;
}
.subtitle {
  font-size   : 12pt;
  font-weight : normal;
}
.image {
  background  : Black;
}
.power {
  font-weight : 700;
  background  : Maroon;
  color       : white;
}
.hist {
  background  : #282828;
  color       : #919191;
}
'''

		for num in range(num_lanes):
			html_file += '#Lane%i {background: #343734;}\n' % (num+1)

		if hist_tab:
			html_file += '#Hist {background: #343734;}\n'

		html_file += '#AllianceInfo {background: #343734;}\n'	

		html_file += '</style>\n'
		html_file += '</head>\n'
		html_file += '<body style="background: #343734; font-family: \'Fira Sans Condensed\', sans-serif; text-align:center;">\n'

		for num in range(num_lanes):
			tab_name = ['ROSTER INFO', 'LANE %i' % (num+1)][num_lanes>1]

			if table_name:
				tab_name = '%s %s' % (table_name.upper(), tab_name)

			html_file += '''<button class="tablink" onclick="openPage('Lane%i', this)" %s>%s</button>''' % (num+1,['','id="defaultOpen"'][not num],tab_name) + '\n'

		if hist_tab:
			html_file += '''<button class="tablink" onclick="openPage('Hist1', this)">%s</button>''' % (hist_tab) + '\n'

		html_file += '''<button class="tablink" onclick="openPage('RosterAnalysis', this)">ROSTER ANALYSIS</button>''' + '\n'

		# And a tab for Alliance Info
		html_file += '''<button class="tablink" onclick="openPage('AllianceInfo', this)">ALLIANCE INFO</button>''' + '\n'

		return html_file


# Quick and dirty Javascript to allow Tabbed implementation for raids with lanes.
def add_tabbed_footer():
		return '''
<script>
function openPage(pageName,elmnt) {
  var i, tabcontent, tablinks;
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
	tabcontent[i].style.display = "none";
  }
  tablinks = document.getElementsByClassName("tablink");
  for (i = 0; i < tablinks.length; i++) {
	tablinks[i].style.backgroundColor = "";
  }
  document.getElementById(pageName).style.display = "block";
  elmnt.style.backgroundColor = "#343734";
}

// Get the element with id="defaultOpen" and click on it
document.getElementById("defaultOpen").click();
</script>
</body>
'''