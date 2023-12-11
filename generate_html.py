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
	
	output = table_format.get('output','query')
	
	# If we have a table, we're generating output for a raid.
	if table:

		lanes      = table.get('lanes',default_lanes)[:]
		table_name = table.get('name','')

		# Keep for later comparisons
		len_lanes = len(lanes)

		only_lane    = table_format.get('only_lane',0)
		only_section = table_format.get('only_section',0)
		only_image   = table_format.get('only_image',False)
		sections_per = table_format.get('sections_per',0)

		# Alter format to only process a specific lane if requested.
		if only_lane and only_lane in range(1,len(lanes)+1):
			lanes = [lanes[only_lane-1]]

		# Special handling if we want each section individually in a single lane format -- process each section individually.
		for lane_idx in range(len(lanes)):

			lane = lanes[lane_idx]

			if only_section in range(1,len(lane)+1):
				lane = [lane[only_section-1]]

			# If sections_per is 0 or undefined, include the whole lane.
			sections_per = table_format.get('sections_per')
			if not sections_per:
				sections_per = len(lane)

			# If there's only one lane because of only_lanes, specify the correct lane number.
			lane_num = [only_lane, lane_idx+1][not only_lane]
			file_num = ['-%s' % lane_num, ''][len_lanes == 1]

			# If there are multiple lanes, specify which lane. If not, just call it Roster Info
			tab_name = [f'LANE {lane_num}', 'ROSTER INFO'][len(lanes) == 1 and not only_lane]

			# Include the table name if it exists.
			if table_name:
				tab_name = f'{table_name.upper()} {tab_name}'

			# Generate a label for the History Tab if we have History and can include it.
			hist_tab = get_hist_tab(alliance_info, table_format)

			for section_idx in range(0,len(lane),sections_per):

				# Include the label for the lane plus the requested sections.
				html_file  = add_css_header(table_name)			
				html_file += add_tab_header(tab_name)	

				sections = lane[section_idx:section_idx+sections_per]
				for section in sections:
					html_file += generate_lanes(alliance_info, table, [[section]], table_format, using_tabs=False)

				# Include the history information if we have it and can include it.
				if hist_tab:
					html_file += add_tab_header(hist_tab)	
					html_file += generate_lanes(alliance_info, table, [[section]], table_format, hist_tab, using_tabs=False)

				# Wrap it up and add it to the collection.
				section_num = ''
				if only_section or sections_per != len(lane):
					section_num += [f'-s{only_section}', f'-s{section_idx+1}'][not only_section]
					if len(sections) != 1:
						section_num += f'-{section_idx+len(sections)}'

				html_file += '</body>\n</html>\n'
				html_files[output+'%s%s.html' % (file_num, section_num)] = html_file
		
	# If not, it's one of the supporting tabs.
	else:
		
		# Start with the CSS Header.
		html_file = add_css_header({'roster_analysis':'Roster Analysis','alliance_info':'Alliance Info'}[output])

		# Generate the appropriate midsection, either Roster Analysis...
		if output == 'roster_analysis':
			html_file += add_tab_header('ROSTER ANALYSIS (ACTUALS)')	
			html_file += generate_roster_analysis(alliance_info, stat_type='actual', using_tabs=False)
			html_file += add_tab_header('ROSTER ANALYSIS (PROGRESSIVE)')	
			html_file += generate_roster_analysis(alliance_info, stat_type='progressive', using_tabs=False)

			# Generate a label for the History Tab if we have History.
			hist_tab = get_hist_tab(alliance_info, table_format)
			if hist_tab:
				html_file += add_tab_header(hist_tab)	
				html_file += generate_roster_analysis(alliance_info, stat_type='progressive', using_tabs=False, hist_tab=hist_tab)
		
		# ...or Alliance Info. Don't use the tab labels for Alliance Info
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

	only_lane    = table_format.get('only_lane',0)
	only_section = table_format.get('only_section',0)

	# Alter format to only process a specific lane if requested.
	if only_lane and only_lane in range(1,len(lanes)+1):
		lanes = [lanes[only_lane-1]]

	# Alter lanes to only process a specific section if requested.
	for lane_idx in range(len(lanes)):
		if only_section and only_section in range(1,len(lanes[lane_idx])+1):
			lanes[lane_idx] = [lanes[lane_idx][only_section-1]]

	# Generate a label for the History Tab if we have History.
	hist_tab = get_hist_tab(alliance_info, table_format, lanes, tabbed=True)

	# Start with the CSS Header.
	html_file = add_css_header(table_name, len(lanes), hist_tab)

	# Add a tab for each lane. 
	html_file += generate_lanes(alliance_info, table, lanes, table_format)

	# Add a historical info tab.
	if hist_tab:
		html_file += generate_lanes(alliance_info, table, lanes, table_format, hist_tab)

	# Same tabs for all documents, so only need to generate them once.
	if not cached_tabs:
		cached_tabs['roster_analysis'] = generate_roster_analysis(alliance_info)
		cached_tabs['alliance_tab']    = generate_alliance_tab(alliance_info)

	# After all Lanes are added, add the Roster Analysis and Alliance Info tabs.
	html_file += cached_tabs['roster_analysis']
	html_file += cached_tabs['alliance_tab']

	# Finally, add the Javascript to control tabbed display.
	html_file += add_tabbed_footer()
		
	# All done with All Lanes. Close the file.
	html_file += '</body>\n</html>\n'

	return html_file


# If we're doing a single lane format and we have history, let's generate a historical data tab. 
def get_hist_tab(alliance_info, table_format, lanes=[], tabbed=False):

	# Default it to empty.
	hist_tab = ''

	# If this format qualifies for History (and it's no explicitly disabled) generate the tab label.
	if len(alliance_info['hist'])>1 and not table_format.get('no_hist'):
		if (tabbed and len(lanes) == 1) or (not tabbed and table_format.get('only_section') or table_format.get('sections_per') == 1):
			hist_tab = "CHANGES SINCE %s" % min(alliance_info['hist'])

	return hist_tab


# Just hide the messiness.
def add_tab_header(content):
	return '<table>\n<tr><td class="tablink" style="width:100%;">'+content+'</td></tr>\n</table>'


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
			traits = section.get('traits',[])
			if type(traits) == str:
				traits = [traits]
			
			table_lbl = '<br>'.join([translate_name(trait).upper() for trait in traits])

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

			span_data = table_format.get('span')
			if span_data is None:
				span_data = table.get('span',False)

			# Special code for Spanning format here. It's a very narrow window of applicability.
			if other_chars and not meta_chars and len(other_chars) <= 5 and span_data:

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
		name_cell_dim = 'name_blue_dim'
		name_alt      = 'name_alt'
		name_alt_dim  = 'name_alt_dim'
		team_pwr_lbl  = 'Team<br>Power'
	else:
		title_cell    = 'title_gray'
		table_header  = 'header_gray'
		char_cell     = 'char_gray'
		name_cell     = 'name_gray'
		name_cell_dim = 'name_gray_dim'
		name_alt      = 'name_galt'
		name_alt_dim  = 'name_galt_dim'
		team_pwr_lbl  = 'STP<br>(Top 5)'

	# Get the list of Alliance Members we will iterate through as rows.	
	sort_by  = table.get('sort_by', '')
	player_list = get_player_list (alliance_info, sort_by, stp_list)
	
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

			# See whether this person has 5 heroes in either meta or other that meet the minimum requirements for this raid section/game mode.
			not_ready = len([char for char in table['under_min'].get(player_name,{}) if not table['under_min'].get(player_name,{}).get(char)]) < min(len(char_list),5)

			# Player Name, then relevant stats for each character.
			html_file += '    <tr%s>\n' % [' class="hist"',''][not hist_tab]
			html_file += '     <th class="%s">%s</th>\n' % ([name_cell, name_alt, name_cell_dim, name_alt_dim][alt_color+2*not_ready], player_name.replace('Commander','Cmdr.'))

			# If Member's roster has grown more than 1% from last sync or hasn't synced in more than a week, indicate it is STALE DATA via Grayscale output.
			stale_data = (alliance_info['members'][player_name].get('tot_power',0)/alliance_info['members'][player_name]['tcp'])<0.985 or (datetime.datetime.now() - alliance_info['members'][player_name]['last_update']).total_seconds() > 60*60*24*7

			# Write the stat values for each character.
			for char_name in char_list:

				# Load up arguments from table, with defaults if necessary.
				under_min = table['under_min'][player_name][char_name]

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
def generate_roster_analysis(alliance_info, using_tabs=True, stat_type='actual', hist_tab=''):

	html_file=''

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
	
	html_file += ' <td width="200" colspan="5">Average</td>\n'	# All Avg Stats
	html_file += ' <td width="2" rowspan="2"></td>\n' 				# Vertical Divider

	html_file += ' <td width="160" colspan="4">Stars</td>\n'		# Yel 4-7
	html_file += ' <td width="2" rowspan="2"></td>\n' 				# Vertical Divider

	html_file += ' <td width="120" colspan="4">Red Stars</td>\n'	# Red 4-7
	html_file += ' <td width="2" rowspan="2"></td>\n' 				# Vertical Divider

	html_file += ' <td width="160" colspan="3">Diamonds</td>\n'	# Red 4-7
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
	html_file += ' <td class="blue" width="40">%s</td>\n' % ['1+','4*'][stat_type == 'actual']
	html_file += ' <td class="blue" width="40">%s</td>\n' % ['5+','5*'][stat_type == 'actual']
	html_file += ' <td class="blue" width="40">%s</td>\n' % ['6+','6*'][stat_type == 'actual']
	html_file += ' <td class="blue" width="40">%s</td>\n' % ['7*','7*'][stat_type == 'actual']
	
	# Red Stars
	html_file += ' <td class="blue" width="40">%s</td>\n' % ['1+','4*'][stat_type == 'actual']
	html_file += ' <td class="blue" width="40">%s</td>\n' % ['5+','5*'][stat_type == 'actual']
	html_file += ' <td class="blue" width="40">%s</td>\n' % ['6+','6*'][stat_type == 'actual']
	html_file += ' <td class="blue" width="40">%s</td>\n' % ['7+','7*'][stat_type == 'actual']

	# Diamonds
	html_file += ' <td class="blue" width="40">1💎</td>\n'
	html_file += ' <td class="blue" width="40">2💎</td>\n'
	html_file += ' <td class="blue" width="40">3💎</td>\n'

	# ISO Levels
	html_file += ' <td class="blue" width="40">%s</td>\n' % ['4','0-4'][stat_type == 'actual']
	html_file += ' <td class="blue" width="40">5+</td>\n'
	html_file += ' <td class="blue" width="40">%s</td>\n' % ['6+','6-8'][stat_type == 'actual']
	html_file += ' <td class="blue" width="40">9+</td>\n'
	html_file += ' <td class="blue" width="40">10</td>\n'

	# Gear Tiers
	html_file += ' <td class="blue" width="40">%s</td>\n' % ['13+','13'][stat_type == 'actual']
	html_file += ' <td class="blue" width="40">%s</td>\n' % ['14+','14'][stat_type == 'actual']
	html_file += ' <td class="blue" width="40">%s</td>\n' % ['15+','15'][stat_type == 'actual']
	html_file += ' <td class="blue" width="40">%s</td>\n' % ['16+','16'][stat_type == 'actual']
	html_file += ' <td class="blue" width="40">%s</td>\n' % ['17+','17'][stat_type == 'actual']
	html_file += ' <td class="blue" width="40">%s</td>\n' % ['18' ,'18'][stat_type == 'actual']

	# T4 Abilities
	html_file += ' <td class="blue" width="40">Bas</td>\n'
	html_file += ' <td class="blue" width="40">Spc</td>\n'
	html_file += ' <td class="blue" width="40">Ult</td>\n'
	html_file += ' <td class="blue" width="40">Pas</td>\n'

	# Level Ranges
	html_file += ' <td class="blue" width="50">%s</td>\n' % ['0-95', '0-65' ][stat_type == 'actual']
	html_file += ' <td class="blue" width="50">%s</td>\n' % ['66-95','66-70'][stat_type == 'actual']
	html_file += ' <td class="blue" width="50">%s</td>\n' % ['71-95','71-75'][stat_type == 'actual']
	html_file += ' <td class="blue" width="50">%s</td>\n' % ['76-95','76-80'][stat_type == 'actual']
	html_file += ' <td class="blue" width="50">%s</td>\n' % ['81-95','81-85'][stat_type == 'actual']
	html_file += ' <td class="blue" width="50">%s</td>\n' % ['86-95','86-90'][stat_type == 'actual']
	html_file += ' <td class="blue" width="50">%s</td>\n' % ['91-95','91-95'][stat_type == 'actual']

	html_file += '</tr>\n'
	
	# Start by doing stat analysis.	
	stats = get_roster_stats(alliance_info, stat_type, hist_tab)
	
	# Get the list of Alliance Members 
	member_list = list(alliance_info['hist'][max(alliance_info['hist'])])
	
	# Get a sorted list of members to use for this table output.
	alliance_order = sorted(alliance_info['members'].keys(), key = lambda x: alliance_info['members'][x]['tcp'], reverse=True)
	alliance_order = [member for member in alliance_order if member in member_list]

	# Iterate through each row for members in the table.
	for member in alliance_order:
			member_info = alliance_info['members'][member]
			member_stats = stats[member]
			stats_range  = stats['range']

			# If Member's roster has grown more than 1% from last sync or hasn't synced in more than a week, indicate it is STALE DATA via Grayscale output.
			stale_data = (member_info.get('tot_power',0)/member_info['tcp'])<0.985 or (datetime.datetime.now() - member_info['last_update']).total_seconds() > 60*60*24*7

			html_file += '<tr>\n'

			member_url = ' href="https://marvelstrikeforce.com/en/player/%s/characters"' % (alliance_info['members'][member].get('url',''))
			html_file += ' <td class="%s"><a style="text-decoration: none; color: black;"%s>%s</a></td>\n' % (['name_blue','name_gray'][stale_data], member_url, member)
			
			for key in ['tcp','stp','tcc']:
				html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(stats_range[key]), max(stats_range[key]), member_stats[key], stale_data=stale_data), f'{member_stats[key]:,}')
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Averages
			for key in ['yel', 'red', 'tier', 'lvl', 'iso']:
				html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(stats_range['tot_'+key]), max(stats_range['tot_'+key]), member_stats['tot_'+key], stale_data=stale_data), f'{member_stats["tot_"+key ] / member_stats["tcc"]:.2f}')
			html_file += ' <td></td>\n' 										# Vertical Divider
			
			# Yellow Stars
			for key in range(4,8):
				html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(stats_range['yel'][key]), max(stats_range['yel'][key]), member_stats['yel'].get(key,0), stale_data=stale_data), member_stats['yel'].get(key,0))
			html_file += ' <td></td>\n' 										# Vertical Divider                                                            
																																							  
			# Red Stars                                                                                                                                       
			for key in range(4,8):
				html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(stats_range['red'][key]), max(stats_range['red'][key]), member_stats['red'].get(key,0), stale_data=stale_data), member_stats['red'].get(key,0))
			html_file += ' <td></td>\n' 										# Vertical Divider                                                            

			# Diamonds
			for key in range(1,4):
				html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(stats_range['dmd'][key]), max(stats_range['dmd'][key]), member_stats['dmd'].get(key,0), stale_data=stale_data), member_stats['dmd'].get(key,0))
			html_file += ' <td></td>\n' 										# Vertical Divider                                                            
																																							  
			# ISO Levels                                                                                                                                      
			for key in [4,5,8,9,10]:
				html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(stats_range['iso'][key]), max(stats_range['iso'][key]), member_stats['iso'].get(key,0), stale_data=stale_data), member_stats['iso'].get(key,0))
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Gear Tiers
			for key in range(13,19):
				html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(stats_range['tier'][key]), max(stats_range['tier'][key]), member_stats['tier'].get(key,0), stale_data=stale_data), member_stats['tier'].get(key,0))
			html_file += ' <td></td>\n' 										# Vertical Divider

			# T4 Abilities
			for key in ['bas','spc','ult','pas']:
				html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(stats_range[key]), max(stats_range[key]), member_stats[key].get(7,0), stale_data=stale_data), member_stats[key].get(7,0))
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Level Ranges
			for key in range(65,100,5):
				html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(min(stats_range['lvl'][key]), max(stats_range['lvl'][key]), member_stats['lvl'].get(key,0), stale_data=stale_data), member_stats['lvl'].get(key,0))

			html_file += '</tr>\n'

	html_file += '</table>\n'

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file += '</div>\n'

	return html_file


# STILL NEED TO WORK ON HISTORICAL PRESENTATION. SHOULD USE PROGRESSIVE STAT CALCULATIONS FOR BOTH TO SUCCESSFULLY COMMUNICATE PROGRESS.

def get_roster_stats(alliance_info, stat_type, hist_tab=''):
	
	stats = {}
	
	current_rosters = alliance_info['hist'][max(alliance_info['hist'])].copy()
	oldest_rosters  = alliance_info['hist'][min(alliance_info['hist'])].copy()
	
	# Get the list of Alliance Members 
	member_list = list(current_rosters)

	# Get the list of usable characters for analysis.
	char_list = get_char_list(alliance_info)
	
	# Start by doing stat analysis.	
	for member in member_list:
	
		# Get a little closer to our work.
		member_stats = stats.setdefault(member,{})
		
		# Don't include stats from heroes that haven't been recruited yet.
		recruited_chars = [char for char in char_list if current_rosters[member][char]['power']]

		# Use this as a comparator to just return current values.
		null_stats = {'yel':0, 'red':0, 'dmd':0, 'lvl':0, 'tier':0, 'iso':0, 'abil':0, 'power':0}
		diff_stats = null_stats.copy()
		
		# Loop through every char
		for char in recruited_chars:
		
			# Get a little closer to our work.
			char_stats = current_rosters[member][char]

			# If hist_tab, we want the difference between current_rosters and the oldest_rosters.
			if hist_tab:
				char_stats = oldest_rosters[member].get(char, null_stats)
				#diff_stats = oldest_rosters[member].get(char, null_stats)

			# Use for Total / Average # columns -- do this BEFORE normalizing data.
			for key in ['yel','red','dmd','tier','lvl','iso']:
				member_stats['tot_'+key] = member_stats.get('tot_'+key,0) + char_stats[key] # - diff_stats[key]

			# Normalize the data.
			# If stat_type = 'actual', combine ISO and LVL columns before tallying
			# If 'progressive', make each entry count in those below it.

			# If progressive, only report the highest USABLE red star and diamonds only valid if 7R.
			if stat_type == 'progressive':
				if char_stats['red'] > char_stats['yel']:
					char_stats['red'] = char_stats['yel']
				if char_stats['red'] != 7:
					char_stats['dmd'] = 0
				if diff_stats['red'] > diff_stats['yel']:
					diff_stats['red'] = diff_stats['yel']
				if diff_stats['red'] != 7:
					diff_stats['dmd'] = 0
				
			# For either stat_type, combine certain columns for ISO and Level data.
			if char_stats['lvl']<65:
				char_stats['lvl'] = 65
			else:
				char_stats['lvl'] += 4-(char_stats['lvl']+4)%5			# Round up to nearest multiple of 5.

			if diff_stats['lvl']<65:
				diff_stats['lvl'] = 65
			else:
				diff_stats['lvl'] += 4-(diff_stats['lvl']+4)%5			# Round up to nearest multiple of 5.

			if char_stats['iso']<4:
				char_stats['iso'] = 4
			elif char_stats['iso'] in range(6,9):
				char_stats['iso'] = 8
				
			if diff_stats['iso']<4:
				diff_stats['iso'] = 4
			elif diff_stats['iso'] in range(6,9):
				diff_stats['iso'] = 8
			
			# Just tally the values in each key. Increment the count of each value found.
			for key in ['yel', 'lvl', 'red', 'dmd', 'tier', 'iso']:
				if stat_type == 'progressive':
					for x in range(0,char_stats[key]+1):
						member_stats.setdefault(key,{})[x] = member_stats.get(key,{}).setdefault(x,0)+1
					#for x in range(4,diff_stats[key]+1):
					#	member_stats.setdefault(key,{})[x] = member_stats.get(key,{}).setdefault(x,0)-1
				else:
					member_stats.setdefault(key,{})[char_stats[key]] = member_stats.get(key,{}).setdefault(char_stats[key],0)+1
					
				#member_stats.setdefault(key,{})[diff_stats[key]] = member_stats.get(key,{}).setdefault(diff_stats[key],0) - (diff_stats[key]!=0)

			# Abilities have to be treated a little differently. 
			bas,abil = divmod(char_stats['abil'],1000)
			spc,abil = divmod(abil,100)
			ult,pas  = divmod(abil,10)
			abil_stats = {'bas':bas, 'spc':spc, 'ult':ult, 'pas':pas}
			
			# Normalize skill data: anything T4 and above is included in level 7. 
			for key in ['bas','spc','ult']:
				if abil_stats[key] == 8: 
					abil_stats[key] = 7
			if abil_stats['pas'] in (5,6):
				abil_stats['pas'] = 7

			for key in abil_stats:
				member_stats.setdefault(key,{})[abil_stats[key]] = member_stats.get(key,{}).setdefault(abil_stats[key],0)+1

			# Use for TCP, STP, TCC columns
			member_stats.setdefault('power',[]).append(char_stats['power'])
			#member_stats.setdefault('power',[]).append(char_stats['power']-diff_stats['power'])

		# Calculate roster-wide statistics
		member_stats['tcp'] = sum(member_stats['power'])
		member_stats['stp'] = sum(sorted(member_stats['power'])[-5:])
		member_stats['tcc'] = len(member_stats['power'])

	# Calculate alliance-wide ranges for each statistic. Use min() and max() to determine colors
	stats['range'] = {}
	stats['range']['tcp'] = [stats[member]['tcp'] for member in member_list]
	stats['range']['stp'] = [stats[member]['stp'] for member in member_list]
	stats['range']['tcc'] = [stats[member]['tcc'] for member in member_list]

	# Totals (and create dicts for the rest of the ranges)
	for key in ['yel','red','dmd','tier','lvl','iso']:
		stats['range'][key]  = {}
		stats['range']['tot_'+key]  = [stats[member]['tot_'+key] for member in member_list]
	
	# Yellow and Red Stars
	for key in range(4,8):
		stats['range']['yel'][key] = [stats[member]['yel'].get(key,0) for member in member_list]
		stats['range']['red'][key] = [stats[member]['red'].get(key,0) for member in member_list]

	# Diamonds
	for key in range(1,4):
		stats['range']['dmd'][key] = [stats[member]['dmd'].get(key,0) for member in member_list]

	# ISO Levels
	for key in range(4,11):
		stats['range']['iso'][key] = [stats[member]['iso'].get(key,0) for member in member_list]

	# Gear Tiers
	for key in range(13,19):
		stats['range']['tier'][key] = [stats[member]['tier'].get(key,0) for member in member_list]

	# Level Ranges
	for key in range(65,100,5):
		stats['range']['lvl'][key] = [stats[member]['lvl'].get(key,0) for member in member_list]

	# T4 Abilities
	for key in ['bas','spc','ult','pas']:
		stats['range'][key] = [stats[member][key].get(7,0) for member in member_list]

	return stats


# Generate just the Alliance Tab contents.
def generate_alliance_tab(alliance_info, using_tabs=True, html_file=''):

	# Start by sorting members by TCP.
	alliance_order = sorted(alliance_info['members'].keys(), key = lambda x: alliance_info['members'][x]['tcp'], reverse=True)
	
	# Build up the list of Alliance Members in the order we will present them.
	member_list =  [alliance_info['leader']] + alliance_info['captains']
	member_list += [member for member in alliance_order if member not in member_list]

	tot_power = sum([alliance_info['members'][member]['tcp'] for member in alliance_info['members']])
	avg_power = int(tot_power/len(alliance_info['members']))

	# See if name includes a color tag.
	alt_color = extract_color(alliance_info['name'])

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
	html_file += ' <td width="110">Total<br>Collected</td>\n'
	html_file += ' <td width="110">Max<br>Stars</td>\n'
	html_file += ' <td width="110">Arena<br>Rank</td>\n'
	html_file += ' <td width="110">Blitz<br>Wins</td>\n'
	html_file += ' <td width="110">War<br>MVP</td>\n'
	html_file += ' <td width="110">Total<br>Stars</td>\n'
	html_file += ' <td width="110">Total<br>Red</td>\n'
	html_file += ' <td width="215">Last Updated:</td>\n'
	html_file += '</tr>\n'
	
	tcp_range   = [alliance_info['members'][member].get('tcp',0)   for member in member_list]
	stp_range   = [alliance_info['members'][member].get('stp',0)   for member in member_list]
	tcc_range   = [alliance_info['members'][member].get('tcc',0)   for member in member_list]
	mvp_range   = [alliance_info['members'][member].get('mvp',0)   for member in member_list]
	max_range   = [alliance_info['members'][member].get('max',0)   for member in member_list]
	arena_range = [alliance_info['members'][member].get('arena',0) for member in member_list]
	blitz_range = [alliance_info['members'][member].get('blitz',0) for member in member_list]
	stars_range = [alliance_info['members'][member].get('stars',0) for member in member_list]
	red_range   = [alliance_info['members'][member].get('red',0)   for member in member_list]

	for member in member_list:
		# Get a little closer to what we're working with.
		member_stats = alliance_info['members'][member]

		# If Member's roster has grown more than 1% from last sync or hasn't synced in more than a week, indicate it is STALE DATA via Grayscale output.
		stale_data = (member_stats.get('tot_power',0)/member_stats['tcp'])<0.985 or (datetime.datetime.now() - member_stats['last_update']).total_seconds() > 60*60*24*7
		
		member_color = ['#B0E0E6','#DCDCDC'][stale_data]

		if member in alliance_info['leader']:
			member_role = 'Leader'
		elif member in alliance_info['captains']:
			member_role = 'Captain'
			member_color = ['#00BFFF','#A9A9A9'][stale_data]		
		else:
			member_role = 'Member'

		html_file += ' <tr style="background:%s;">\n' % (member_color)
		html_file += '  <td style="padding:0px;"><img height="45" src="https://assets.marvelstrikeforce.com/imgs/Portrait_%s.png"/></td>\n' % (member_stats['image'])

		member_url = alliance_info['members'][member].get('url','')
		if member_url:
			member_url = ' href="https://marvelstrikeforce.com/en/player/%s/characters"' % (member_url)

		html_file += '  <td class="bold"><a style="text-decoration: none; color: black;""%s>%s</a></td>\n' % (member_url, member)
		html_file += '  <td>%i</td>\n' % (member_stats['level'])
		html_file += '  <td>%s</td>\n' % (member_role)
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(min(tcp_range),   max(tcp_range),   member_stats.get('tcp',0),   stale_data=stale_data), f'{member_stats.get("tcp",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(min(stp_range),   max(stp_range),   member_stats.get('stp',0),   stale_data=stale_data), f'{member_stats.get("stp",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(max(tcc_range)-5, max(tcc_range),   member_stats.get('tcc',0),   stale_data=stale_data), f'{member_stats.get("tcc",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(min(max_range),   max(max_range),   member_stats.get('max',0),   stale_data=stale_data), f'{member_stats.get("max",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(max(arena_range), min(arena_range), member_stats.get('arena',0), stale_data=stale_data), f'{member_stats.get("arena",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(min(blitz_range), max(blitz_range), member_stats.get('blitz',0), stale_data=stale_data), f'{member_stats.get("blitz",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(min(mvp_range),   max(mvp_range),   member_stats.get('mvp',0),   stale_data=stale_data), f'{member_stats.get("mvp",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(min(stars_range), max(stars_range), member_stats.get('stars',0), stale_data=stale_data), f'{member_stats.get("stars",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(min(red_range),   max(red_range),   member_stats.get('red',0),   stale_data=stale_data), f'{member_stats.get("red",0):,}')

		if 'last_update' in member_stats:
			last_update = datetime.datetime.now() - member_stats['last_update']
			time_color  = get_value_color(4*86400, 0, last_update.total_seconds(), stale_data=stale_data)
			
			if stale_data:
				time_value = '%s, %s days ago<br><b><i>Stale. Please re-sync.</i></b>' % (member_stats['last_update'].strftime('%a, %b %d'), last_update.days)
			else:
				time_value = '%s,<br>%s ago' % (member_stats['last_update'].strftime('%A, %B %d'), str(last_update).split('.')[0]) 
		else:
			time_color = get_value_color(0, 1, 0)
			time_value = 'NEVER<br><b><i>Ask member to sync.</i></b>'
		
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

