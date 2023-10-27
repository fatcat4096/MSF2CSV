#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_html.py
Takes the processed alliance / roster data and generate readable output to spec.  
"""


import datetime
import string

# Routines to create color gradient for heat map
from alliance_info import *
from generate_css  import *
from gradients     import color_scale, darken, grayscale


# Build specific tab output for use in generating PNG graphics.
def generate_html_files(alliance_info, table, table_format, output=''):

	default_lanes = [[{'traits': ['Mutant']},
					  {'traits': ['Bio']},
					  {'traits': ['Skill']},
					  {'traits': ['Mystic']},
					  {'traits': ['Tech']}]]

	html_files = {}
	
	# If we have a table, we're generating output for a raid.
	if table:

		lanes      = table.get('lanes',default_lanes)
		table_name = table.get('name')
		
		# Alter format to only process a specific lane if requested.
		only_lane = table_format.get('only_lane',0)
		if only_lane and only_lane in range(1,len(lanes)+1):
			lanes = [lanes[only_lane-1]]

		# Alter lanes to only process a specific section if requested.
		only_section = table_format.get('only_section',0)
		for lane_idx in range(len(lanes)):
			if only_section and only_section in range(1,len(lanes[lane_idx])+1):
				lanes[lane_idx] = [lanes[lane_idx][only_section-1]]

		# Special handling if it's a single lane format -- process each section individually.
		if len(lanes) == 1:

			# Use the standard Tab Label to title the graphic.
			tab_name = ['LANE %s' % only_lane, 'ROSTER INFO'][not only_lane]
			if table_name:
				tab_name = '%s %s' % (table_name.upper(), tab_name)
			
			# Generate a label for the History Tab if we have History.
			hist_tab = ''
			if len(alliance_info['hist'])>1 and not table_format.get('no_hist'):
				hist_tab = "CHANGES SINCE %s" % min(alliance_info['hist'])
			
			# Loop through each section, building a file for each section.
			for section in lanes[0]:
				html_file = add_css_header()			
				
				# Include the label for the main section plus the table.
				html_file += '<p class="tablink">'+tab_name+'</p><br>\n'	
				html_file += generate_lanes(alliance_info, table, [[section]], table_format, using_tabs=False)

				# Include the history information if we have it.
				if hist_tab:
					html_file += '<p class="tablink">'+hist_tab+'</p><br>\n'	
					html_file += generate_lanes(alliance_info, table, [[section]], table_format, hist_tab, using_tabs=False)

				# Wrap it up and add it to the collection.
				html_file += '</body>\n</html>\n'
				html_files[output+'-%s.html' % (len(html_files)+1)] = html_file
				
		# If multiple lanes, generate a file for each lane. 
		else:
			for lane in lanes:

				# Use the standard Tab Label to title the graphic.
				lane_num = lanes.index(lane)+1
				tab_name = 'LANE %s' % (lane_num)
				if table_name:
					tab_name = '%s %s' % (table_name.upper(), tab_name)

				# Include the label for the lane plus all the tables.
				html_file = add_css_header()			
				html_file += '<p class="tablink">'+tab_name+'</p><br>\n'	
				html_file += generate_lanes(alliance_info, table, [lane], table_format, using_tabs=False)

				# Wrap it up and add it to the collection.
				html_file += '</body>\n</html>\n'
				html_files[output+'-%s.html' % (lane_num)] = html_file
		
	# If not, it's one of the supporting tabs.
	else:
		
		# Start with the CSS Header.
		html_file = add_css_header()

		# Generate the appropriate midsection
		if output == 'roster_analysis':
			html_file += '<p class="tablink">ROSTER ANALYSIS</p><br>\n'	
			html_file += generate_roster_analysis(alliance_info, using_tabs=False)
		# Don't use the tab labels for Alliance Info
		elif output == 'alliance_info':
			html_file += generate_alliance_tab(alliance_info, using_tabs=False)

		# Wrap it up and add it to the collection.
		html_file += '</body>\n</html>\n'
		html_files[output+'.html'] = html_file	

	return html_files


# Build the entire file -- headers, footers, and tab content for each lane and the Alliance Information.
def generate_tabbed_html(alliance_info, table, table_format, cached_tabs={}):

	default_lanes = [[{'traits': ['Mutant']},
					  {'traits': ['Bio']},
					  {'traits': ['Skill']},
					  {'traits': ['Mystic']},
					  {'traits': ['Tech']}]]

	lanes      = table.get('lanes',default_lanes)
	table_name = table.get('name','')

	# Alter format to only process a specific lane if requested.
	only_lane = table_format.get('only_lane',0)
	if only_lane and only_lane in range(1,len(lanes)+1):
		lanes = [lanes[only_lane-1]]

	# Alter lanes to only process a specific section if requested.
	only_section = table_format.get('only_section',0)
	for lane_idx in range(len(lanes)):
		if only_section and only_section in range(1,len(lanes[lane_idx])+1):
			lanes[lane_idx] = [lanes[lane_idx][only_section-1]]

	# If we're doing a single lane format and we have history, let's generate a historical data tab. 
	hist_tab = ''
	if len(lanes) == 1 and len(alliance_info['hist'])>1 and not table_format.get('no_hist'):
		hist_tab = "CHANGES SINCE %s" % min(alliance_info['hist'])

	# Start with the CSS Header.
	html_file = add_css_header(table_name, len(lanes), hist_tab)

	# Add a tab for each lane. 
	html_file += generate_lanes(alliance_info, table, lanes, table_format)

	# Add a historical info tab.
	if hist_tab:
		html_file += generate_lanes(alliance_info, table, lanes, table_format, hist_tab)

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
	html_file += '</body>\n</html>\n'

	return html_file


# Generate the contents for each lane.
def generate_lanes(alliance_info, table, lanes, table_format, hist_tab = '', using_tabs=True):

	html_file = ''

	# Use the full Player List if explicit Strike Teams haven't been defined.
	sort_by = table.get('sort_by','')
	strike_teams = alliance_info['strike_teams'].get(table.get('strike_teams'), [get_player_list(alliance_info, sort_by)])

	# Iterate through all the lanes. Showing tables for each section. 
	for lane in lanes:

		# Display each lane in a separate tab.
		divider_id = ['Hist','Lane'][not hist_tab] + str(lanes.index(lane)+1)
		
		# Only include Dividers if using as part of a multi-tab document
		if using_tabs:
			html_file += '<div id="%s" class="tabcontent">\n' % (divider_id)

		# Process each section individually, filtering only the specified traits into the Active Chars list.
		for section in lane:
		
			meta_chars, other_chars = get_meta_other_chars(alliance_info, table, section, table_format, hist_tab)

			# Start with the Basic Table Label and Colors.
			table_lbl = '<br>'.join([translate_name(trait) for trait in section['traits']]).upper()

			# Let's make it easy on ourselves. Start every section the same way.
			html_file += '<table>\n <tr>\n  <td>\n'

			# Only building meta table if we have meta_chars defined.
			if meta_chars:
				meta_lbl = table_lbl+'<br><span class="subtitle">META</span>'

				stp_list = get_stp_list(alliance_info, meta_chars, hist_tab)

				html_file += generate_table(alliance_info, table, meta_chars, strike_teams, meta_lbl, stp_list, hist_tab)
				html_file += '  </td>\n  <td><br></td>\n  <td>\n'

				# Differentiate Others Section from Meta Section
				table_lbl += '<br><span class="subtitle">OTHERS</span>'

			# Generate stp_list dict for the Other Table calls.
			stp_list = get_stp_list(alliance_info, meta_chars+other_chars, hist_tab)
			
			# Special code for Spanning format here. It's a very narrow window of applicability.
			if other_chars and not meta_chars and len(other_chars) <= 5 and table.get('format') == 'span':

				# If strike_team is just the entire player list, break it up into 3 groups.
				if len(strike_teams) == 1:
					
					# Need to do a new sort for strike_teams if sort_by is STP.
					if sort_by == 'stp':
						strike_temp = [get_player_list(alliance_info, sort_by, stp_list)]
					else:
						strike_temp = strike_teams[:]
						
					# Split the sorted player list into 3 groups of 8 players.
					strike_temp = [[strike_temp[0][:8]], [strike_temp[0][8:16]], [strike_temp[0][16:]]]

				# If we have defined Strike Teams, create a fake set of Strike Teams so that a label is generated.
				else:
					strike_temp = [[strike_teams[0],[],[]],
								   [[],strike_teams[1],[]],
								   [[],[],strike_teams[2]]]

				# Generate 3 tables, spanning the page.
				for strike_team in strike_temp:
					# Pass in only a single chunk of 8 players three separate times.
					html_file += generate_table(alliance_info, table, other_chars, strike_team, table_lbl, stp_list, hist_tab)
					html_file += '  </td>\n  <td><br></td>\n  <td>\n'

			# We are NOT spanning. Standard table generation.
			else:
				html_file += generate_table(alliance_info, table, other_chars, strike_teams, table_lbl, stp_list, hist_tab)

			# End every section the same way.
			html_file += '  </td>\n </tr>\n</table>\n'

			# If not the final section, add a divider row. 
			if lane.index(section) != len(lane)-1:
				html_file += '    <p></p>\n'

		# After Lane content is done, close the div for the Tab implementation.
		if using_tabs:
			html_file += '</div>\n'

	return html_file


# Generate individual tables for Meta/Other chars for each raid section.
def generate_table(alliance_info, table, char_list, strike_teams, table_lbl, stp_list, hist_tab):

	# Pick a color scheme.
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

	# Get the list of Alliance Members we will iterate through as rows.	
	sort_by  = table.get('sort_by', '')
	player_list = get_player_list (alliance_info, sort_by, stp_list)

	# Clean up the strike_team defs before we begin.
	player_upper = list(alliance_info['members'])
	player_lower = [player.lower() for player in player_upper]
	for strike_team in strike_teams:

		# Fix any capitalization issues.
		for idx in range(len(strike_team)):
			player_name = strike_team[idx]

			# If can't find, maybe they just got the wrong case? Fix it silently, if so.
			if player_name not in player_upper and player_name.lower() in player_lower:
				strike_team[idx] = player_upper[player_lower.index(player_name.lower())]

		# After fixing case, if no roster available, just remove them from the strike team.
		for player_name in strike_team[:]:
			if player_name in player_upper and player_name not in player_list:
				strike_team.remove(player_name)

	# Let's get this party started!
	html_file = '   <table>\n'

	# WRITE THE IMAGES ROW. #############################################
	html_file += '    <tr class="%s">\n' % (title_cell) 
	html_file += '     <td>%s</td>\n' % (table_lbl)

	keys = table.get('keys', ['power','tier','iso'])

	# Include Images for each of the Characters.
	for char in char_list:
		html_file += '     <td class="image" colspan="%i"><img src="https://assets.marvelstrikeforce.com/imgs/Portrait_%s.png" alt="" width="100"></td>\n' % (len(keys), alliance_info['portraits'][char])

	# Include a Team Power column.
	html_file += '     <td></td>\n'
	html_file += '    </tr>\n'
	# DONE WITH THE IMAGES ROW. #########################################

	# WRITE THE CHARACTER NAMES ROW. ####################################
	html_file += '    <tr class="%s">\n' % (char_cell)
	
	if len(keys)>1 and len(strike_teams)>1:
		html_file += '     <th>Alliance<br>Member</th>\n'
	else:
		## TO DO: DECIDE WHETHER TO INCLUDE THE LOGO (BELOW) OR NOT.
		html_file += '     <td></td>\n'  #<img src="https://assets.marvelstrikeforce.com/www/img/logos/logo-en.png" alt="" width="125">

	# Include Names of the included characters.
	for char in char_list:
		html_file += '     <th colspan="%i" width="100">%s</th>\n' % (len(keys), translate_name(char))

	# Include the Team Power column.
	html_file += '     <th></th>\n' 
	html_file += '    </tr>\n'
	# DONE WITH THE CHARACTER NAMES ROW. ################################

	# Iterate through each Strike Team.
	for strike_team in strike_teams:

		# Add this to allow us to pass in fake Strike_Team definitions so that the correct "Strike Team #" label gets generated. 
		# This is primarily for Spanning output, where one strike team is generated per table.
		if not strike_team:
			continue

		# Find min/max for meta/strongest team power in the Alliance
		# This will be used for color calculation for the Team Power column.
		all_stps = [stp_list[player_name] for player_name in player_list]
		min_all_stps = min(all_stps)
		max_all_stps = max(all_stps)

		# WRITE THE HEADING ROW WITH VALUE DESCRIPTORS ##################
		# (only if more than one item requested)
		if len(keys)>1 or len(strike_teams)>1:
			html_file += '    <tr class="%s">\n' % table_header
			
			if len(strike_teams)>1:
				html_file += '     <td>STRIKE TEAM %i</td>\n' % (strike_teams.index(strike_team)+1)
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

		# Last minute sort if proscribed by the table format.
		if sort_by:
			strike_team = [member for member in player_list if member in strike_team]

		# FINALLY, WRITE THE DATA FOR EACH ROW. #########################
		alt_color = False
		for player_name in strike_team:
		
			# If strike_team name not in the player_list, it's a divider.
			# Toggle a flag for each divider to change the color of Player Name slightly
			if player_name not in player_list:
				alt_color = not alt_color
				continue

			# Player Name, then relevant stats for each character.
			html_file += '    <tr%s>\n' % [' class="hist"',''][not hist_tab]
			html_file += '     <th class="%s">%s</th>\n' % ([name_cell, name_cell_alt][alt_color], player_name.replace('Commander','Cmdr.'))

			# If Member hasn't synced data in more than a week, indicate this fact via Grayscale output.
			stale_data = (datetime.datetime.now() - alliance_info['members'][player_name]['processed_chars']['last_update']).total_seconds() > 60*60*24*7

			# Write the stat values for each character.
			for char_name in char_list:

				# Load up arguments from table, with defaults if necessary.
				under_min = find_value_or_diff(alliance_info, player_name, char_name, 'iso' )[0] < table.get('min_iso', 0)
				under_min = find_value_or_diff(alliance_info, player_name, char_name, 'tier')[0] < table.get('min_tier',0) or under_min

				for key in keys:

					# Get the range of values for this character for all rosters.
					# If historical, we want the diff between the current values and the values in the oldest record
					key_vals = [find_value_or_diff(alliance_info, player, char_name, key, hist_tab)[0] for player in player_list]

					min_val = min(key_vals)
					max_val = max(key_vals)

					# Only look up the value if we have a roster.
					value = 0
					other_diffs = ''
					if player_name in player_list:
					
						# Standard lookup. Get the value for this character stat from this player's roster.
						# If historical, we look for the first time this member appears in the History, and then display the difference between the stat in that record and this one.
						value,other_diffs = find_value_or_diff(alliance_info, player_name, char_name, key, hist_tab)

					if value == 0 and hist_tab:
						style = ''
					else:
						style = ' style="background:%s;%s"' % (get_value_color(min_val, max_val, value, key, under_min, stale_data, hist_tab), ['color:black;',''][not hist_tab])
					html_file += '     <td%s%s>%s</td>\n' % (style, ['',other_diffs][key=='power'], [value,'-'][not value])

			# Include the Team Power column.
			player_stp = stp_list.get(player_name,0)
			html_file += '     <td class="bold" style="background:%s;">%s</td>\n' % (get_value_color(min_all_stps, max_all_stps, player_stp, stale_data=stale_data), [player_stp,'-'][not player_stp])
			html_file += '    </tr>\n'
		# DONE WITH THE DATA ROWS FOR THIS STRIKE TEAM ##################

	# Close the Table, we are done with this chunk.
	html_file += '   </table>\n'

	return html_file


# Generate just the Alliance Tab contents.
def generate_roster_analysis(alliance_info, using_tabs=True, html_file=''):

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
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
	html_file += ' <td class="blue" width="40">Yel</td>\n'
	html_file += ' <td class="blue" width="40">Red</td>\n'
	html_file += ' <td class="blue" width="40">Tier</td>\n'
	html_file += ' <td class="blue" width="40">Lvl</td>\n'
	html_file += ' <td class="blue" width="40">ISO</td>\n'
	
	# Yellow Stars
	html_file += ' <td class="blue" width="40">4*</td>\n'
	html_file += ' <td class="blue" width="40">5*</td>\n'
	html_file += ' <td class="blue" width="40">6*</td>\n'
	html_file += ' <td class="blue" width="40">7*</td>\n'
	
	# Red Stars
	html_file += ' <td class="blue" width="40">4*</td>\n'
	html_file += ' <td class="blue" width="40">5*</td>\n'
	html_file += ' <td class="blue" width="40">6*</td>\n'
	html_file += ' <td class="blue" width="40">7*</td>\n'

	# ISO Levels
	html_file += ' <td class="blue" width="40">0-4</td>\n'
	html_file += ' <td class="blue" width="40">5</td>\n'
	html_file += ' <td class="blue" width="40">6-8</td>\n'
	html_file += ' <td class="blue" width="40">9</td>\n'
	html_file += ' <td class="blue" width="40">10</td>\n'

	# Gear Tiers
	html_file += ' <td class="blue" width="40">13</td>\n'
	html_file += ' <td class="blue" width="40">14</td>\n'
	html_file += ' <td class="blue" width="40">15</td>\n'
	html_file += ' <td class="blue" width="40">16</td>\n'
	html_file += ' <td class="blue" width="40">17</td>\n'
	html_file += ' <td class="blue" width="40">18</td>\n'

	# T4 Abilities
	html_file += ' <td class="blue" width="40">Bas</td>\n'
	html_file += ' <td class="blue" width="40">Spc</td>\n'
	html_file += ' <td class="blue" width="40">Ult</td>\n'
	html_file += ' <td class="blue" width="40">Pas</td>\n'

	# Level Ranges
	html_file += ' <td class="blue" width="50">&lt;65</td>\n'
	html_file += ' <td class="blue" width="50">66-70</td>\n'
	html_file += ' <td class="blue" width="50">71-75</td>\n'
	html_file += ' <td class="blue" width="50">76-80</td>\n'
	html_file += ' <td class="blue" width="50">81-85</td>\n'
	html_file += ' <td class="blue" width="50">86-90</td>\n'
	html_file += ' <td class="blue" width="50">91-95</td>\n'

	html_file += '</tr>\n'
	
	stats = {}
	
	# Get the list of Alliance Members 
	member_list = [member for member in get_player_list(alliance_info) if 'processed_chars' in alliance_info['members'][member]]

	# Get the list of usable characters for analysis.
	char_list = get_char_list(alliance_info)
	
	alliance_order = sorted(alliance_info['members'].keys(), key = lambda x: alliance_info['members'][x]['tcp'], reverse=True)
	alliance_order = [member for member in alliance_order if member in member_list]

	# Start by doing stat analysis.	
	for member in member_list:
	
		# Get a little closer to our work.
		member_stats = stats.setdefault(member,{})
		
		# Don't include stats from heroes that haven't been recruited yet.
		recruited_chars = [char for char in char_list if alliance_info['members'][member]['processed_chars'][char]['power']!=0]

		# Loop through every char
		for char in recruited_chars:
		
			# Get a little closer to our work.
			char_stats = alliance_info['members'][member]['processed_chars'][char]
			
			# Just tally the values in each key. Increment the count of each value found.
			for key in ['yel', 'red', 'lvl', 'tier', 'iso']:
				member_stats.setdefault(key,{})[char_stats[key]] = member_stats.get(key,{}).setdefault(char_stats[key],0)+1

			# Abilities have to be treated a little differently. 
			bas,abil = divmod(char_stats['abil'],1000)
			spc,abil = divmod(abil,100)
			ult,pas  = divmod(abil,10)
			abil_stats = {'bas':bas, 'spc':spc, 'ult':ult, 'pas':pas}

			for key in abil_stats:
				member_stats.setdefault(key,{})[abil_stats[key]] = member_stats.get(key,{}).setdefault(abil_stats[key],0)+1

	# Build ranges for each statistic. We will use min() and max() to 
	tcp_range    = [alliance_info['members'][member]['tcp'] for member in member_list]
	stp_range    = [alliance_info['members'][member]['stp'] for member in member_list]
	tcc_range    = [alliance_info['members'][member]['tcc'] for member in member_list]

	# Averages
	stars_range  = [alliance_info['members'][member].get('stars',0) for member in member_list]
	red_range    = [alliance_info['members'][member].get('red',0)   for member in member_list]
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
	for member in alliance_order:
			member_info = alliance_info['members'][member]
			member_stats = stats[member]
			
			html_file += '<tr>\n'
			html_file += ' <td class="name_blue">%s</td>\n' % (member)
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(tcp_range), max(tcp_range), member_info['tcp']), f'{member_info["tcp"]:,}')
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(stp_range), max(stp_range), member_info['stp']), f'{member_info["stp"]:,}')
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(tcc_range), max(tcc_range), member_info['tcc']), f'{member_info["tcc"]:,}')
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Averages
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(stars_range), max(stars_range), member_info.get('stars',0)), round(member_info.get('stars',0) / member_info['tcc'], 2))
			html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(red_range),   max(red_range),   member_info.get('red',0)),   round(member_info.get('red',0)   / member_info['tcc'], 2))
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

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file += '</div>\n'

	return html_file


# Generate just the Alliance Tab contents.
def generate_alliance_tab(alliance_info, using_tabs=True, html_file=''):

	alt_color = extract_color(alliance_info['name'])
	
	tot_power = sum([alliance_info['members'][member]['tcp'] for member in alliance_info['members']])
	avg_power = int(tot_power/len(alliance_info['members']))

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file += '<div id="AllianceInfo" class="tabcontent">\n'

	html_file += '<table style="background:#222;">\n'

	html_file += '<tr>\n</tr>\n'

	html_file += '<tr style="font-size:18px;color:white;">\n'
	html_file += ' <td colspan="2" rowspan="2"><img src="https://assets.marvelstrikeforce.com/www/img/logos/logo-en.png" alt=""></td>'
	html_file += ' <td colspan="10" class="alliance_name"%s>%s</td>' % (alt_color, alliance_info['name'].upper())
	html_file += ' <td colspan="2"  rowspan="2"><img src="https://assets.marvelstrikeforce.com/imgs/ALLIANCEICON_%s.png" alt=""/></td>\n' % (alliance_info['image'])
	html_file += '</tr>\n'

	html_file += '<tr style="font-size:18px;color:white;">\n'
	html_file += ' <td colspan="2">Members<br><span style="font-size:24px;"><b>%i/24</b></span></td>\n' % (len(alliance_info['members']))
	html_file += ' <td colspan="2">Total Power<br><span style="font-size:24px;"><b>%s</b></span></td>\n' % (f'{tot_power:,}')
	html_file += ' <td colspan="2">Average Power<br><span style="font-size:24px;"><b>%s</b></span></td>\n' % (f'{avg_power:,}')
	html_file += ' <td colspan="2">Level<br><span style="font-size:24px;"><b>%s</b></span></td>\n' % (alliance_info.get('stark_lvl','80'))
	html_file += ' <td colspan="2">Trophies<br><span style="font-size:24px;"><b>%s</b></span></td>\n' % (alliance_info.get('trophies','XXX'))
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
		html_file += '  <td style="padding:0px;"><img height="45" src="https://assets.marvelstrikeforce.com/imgs/Portrait_%s.png"/></td>\n' % (member_stats['image'])
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
		time_value      = 'Never<br>Ask member to sync.'
		if member in alliance_info['members'] and 'processed_chars' in member_stats:
			time_since_last = datetime.datetime.now() - member_stats['processed_chars']['last_update']
			time_value = '%s,<br>%s ago' % (member_stats['processed_chars']['last_update'].strftime('%A, %B %d'), str(time_since_last).split('.')[0])
			time_since_last = time_since_last.total_seconds()
		
		time_color = get_value_color(0, 4*86400, (4*86400)-time_since_last)
		html_file += '  <td style="background:%s;">%s</td>\n' % (time_color, time_value)
		html_file += ' </tr>\n'

	html_file += '</table>\n'
	
	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file += '</div>\n'

	return html_file


def extract_color(alliance_name):
	alt_color = ''

	check_for_color = ''.join(alliance_name.split()).lower()

	# If we have a color, clean it up and extract it.
	if '<color=' in check_for_color:
			color_name = check_for_color.split('<color=')[1].split('>')[0].replace('#','')

			# Is this a hex number or a named color?
			hex_or_named = ['','#'][all(char in string.hexdigits for char in color_name)]

			alt_color=' style="color:%s%s";' % (hex_or_named, color_name)

	return alt_color


# Translate value to a color from the Heat Map gradient.
def get_value_color(min, max, value, stat='power', under_min=False, stale_data=False, hist_tab=''):
	
	# Just in case passed a string.
	value = int(value)

	max_colors  = len(color_scale)-1
	
	# Special treatment for the '0' fields. 
	if not value:
		return '#282828;color:#919191'

	#Tweak gradients for Tier, ISO, Level, and Red/Yellow stars.
	if stat=='iso':
		if not hist_tab:
			scaled_value = int(((value**3)/10**3) * max_colors)
		else:
			scaled_value = [int((0.6 + 0.4 * ((value**3)/10**3)) * max_colors),0][value<0]
	elif stat=='tier':
		if not hist_tab and value <= 15:
			scaled_value = int(((value**2)/15**2)*0.50 * max_colors)
		elif not hist_tab:
			scaled_value = int((0.65 + 0.35 * ((value-16)/3)) * max_colors)
		else:
			scaled_value = int((0.60 + 0.40 * ((value**2)/17**2)) * max_colors)
	elif stat=='lvl':
		if not hist_tab and value <= 75:
			scaled_value = int(((value**2)/75**2)*0.50 * max_colors)
		elif not hist_tab:
			scaled_value = int((0.65 + 0.35 * ((value-75)/20)) * max_colors)
		else:
			scaled_value = int((0.60 + 0.40 * ((value**2)/95**2)) * max_colors)
	elif stat in ('red','yel'):
		min = 2
		max = 7
		scaled_value = int((value-min)/(max-min) * max_colors)
	# Everything else.
	else:
		if min == max:
			scaled_value = max_colors
		else:
			scaled_value = int((value-min)/(max-min) * max_colors)
	
	if scaled_value < 0:
		scaled_value = 0
	elif scaled_value > max_colors:
		scaled_value = max_colors

	color = color_scale[scaled_value]
	
	# Dim values slightly if under the minimum specified for the report.
	if under_min and not hist_tab:
		color = darken(color)

	# If data is more than a week old, make grayscale to indicate stale data.
	if stale_data:
		color = grayscale(color)

	return color
	

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

