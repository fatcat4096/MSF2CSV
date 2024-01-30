#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_html.py
Takes the processed alliance / roster data and generate readable output to spec.  
"""


import datetime
import string
import copy

# Routines to create color gradient for heat map
from alliance_info import *
from generate_css  import *
from gradients     import color_scale, darken, grayscale


# Build specific tab output for use in generating PNG graphics.
def generate_html(alliance_info, table, table_format, output=''):

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
			file_num = [f'-{lane_num:02}', ''][len_lanes == 1]

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
					section_num += [f'-s{only_section:02}', f'-s{section_idx+1:02}'][not only_section]
					if len(sections) != 1:
						section_num += f'-{section_idx+len(sections):02}'

				# Include scripts to support sorting.
				html_file += add_sort_scripts()

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

		# Include scripts to support sorting.
		html_file += add_sort_scripts()

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

	# Include scripts to support sorting.
	html_file += add_sort_scripts()

	# Finally, add the Javascript to control tabbed display.
	html_file += add_tabbed_footer()
		
	# All done with All Lanes. Close the file.
	html_file += '</body>\n</html>\n'

	return html_file


# If we're doing a single lane format and we have history, let's generate a historical data tab. 
def get_hist_tab(alliance_info, table_format, lanes=[], tabbed=False):

	# Default it to empty.
	hist_tab = ''

	# If this format qualifies for History and it's being requested, generate the tab label.
	if 'hist' in alliance_info and len(alliance_info['hist'])>1 and table_format.get('inc_hist'):
		if (tabbed and len(lanes) == 1) or (not tabbed and table_format.get('only_section') or table_format.get('sections_per') == 1):
			hist_tab = "CHANGES SINCE %s" % min(alliance_info['hist'])

	return hist_tab


# Just hide the messiness.
def add_tab_header(content):
	return '<table>\n<tr><td class="tablink" style="width:100%;">'+content+'</td></tr>\n</table>'


# Generate the contents for each lane.
def generate_lanes(alliance_info, table, lanes, table_format, hist_tab = '', using_tabs=True):

	html_file = ''

	# Grab specified strike teams if available. 
	strike_teams = alliance_info.get('strike_teams',{}).get(table.get('strike_teams'))
	
	# If no strike team definitions are specified / found or 
	# If only_team == 0 (ignore strike_teams) **AND**
	# no sort_by has been specified, force sort_by to 'stp'
	only_team = table_format.get('only_team')
	if (not strike_teams or only_team == 0) and not table_format.get('sort_by'):
		table_format['sort_by'] = 'stp'

	# Sort player list if requested.
	sort_by  = table_format.get('sort_by')
	if not sort_by:
		sort_by  = table.get('sort_by')

	# Use the full Player List sorted by stp if explicit Strike Teams haven't been defined.
	if not strike_teams or only_team == 0:
		strike_teams = [get_player_list(alliance_info, sort_by)]

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

			# If no explicit label defined for the section...
			table_lbl = section.get('label','').upper()
			if not table_lbl:

				# Make a table label based on the included traits.
				traits = section.get('traits',[])
				if type(traits) == str:
					traits = [traits]
			
				# Truncate Table Label after 4 entries, if more than 4, use first 3 plus "AND MORE"
				traits = [translate_name(trait).upper() for trait in traits] 
				if len(traits) > 4:
					traits = traits[:3] + ['AND MORE']
				table_lbl = '<br>'.join(traits)

			# Let's make it easy on ourselves. Start every section the same way.
			html_file += '<table>\n <tr>\n  <td>\n'

			# Only building meta table if we have meta_chars defined.
			if meta_chars:
				meta_lbl = table_lbl+'<br><span class="subtitle">META</span>'

				stp_list = get_stp_list(alliance_info, meta_chars, hist_tab)

				html_file += generate_table(alliance_info, table, table_format, meta_chars, strike_teams, meta_lbl, stp_list, hist_tab)
				html_file += '  </td>\n  <td><br></td>\n  <td>\n'

				# Differentiate Others Section from Meta Section
				table_lbl += '<br><span class="subtitle">OTHERS</span>'

			# Generate stp_list dict for the Other Table calls.
			stp_list = get_stp_list(alliance_info, meta_chars+other_chars, hist_tab)

			span_data = table_format.get('span')
			if span_data is None:
				span_data = table.get('span',False)

			# Special code for Spanning format here. It's a very narrow window of applicability.
			if other_chars and not meta_chars and len(other_chars) <= 5 and span_data and not only_team:

				# If strike_team is just the entire player list, break it up into 3 groups.
				if len(strike_teams) == 1 or only_team == 0:
					
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
					html_file += generate_table(alliance_info, table, table_format, other_chars, strike_team, table_lbl, stp_list, hist_tab)
					html_file += '  </td>\n  <td><br></td>\n  <td>\n'

			# We are NOT spanning. Standard table generation.
			else:
				html_file += generate_table(alliance_info, table, table_format, other_chars, strike_teams, table_lbl, stp_list, hist_tab)

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
def generate_table(alliance_info, table, table_format, char_list, strike_teams, table_lbl, stp_list, hist_tab):

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
		button_hover  = 'blu_btn'
		
	else:
		title_cell    = 'title_gray'
		table_header  = 'header_gray'
		char_cell     = 'char_gray'
		name_cell     = 'name_gray'
		name_cell_dim = 'name_gray_dim'
		name_alt      = 'name_galt'
		name_alt_dim  = 'name_galt_dim'
		team_pwr_lbl  = 'STP<br>(Top 5)'
		button_hover  = 'blk_btn'

	# Sort player list if requested.
	sort_by  = table_format.get('sort_by')
	if not sort_by:
		sort_by  = table.get('sort_by', '')

	# Get the list of Alliance Members we will iterate through as rows.	
	player_list = get_player_list (alliance_info, sort_by, stp_list)

	# Generate a table ID to allow sorting. 
	table_id = datetime.datetime.now().strftime('%S%f')
			
	# Let's get this party started!
	html_file = '   <table id="%s">\n' % (table_id)

	# Get keys from table_format/table, with defaults if necessary.
	keys = table_format.get('inc_keys')
	if keys is None:
		keys = table.get('keys', ['power','tier','iso'])

	# Include Available and Include ISO Class flags
	# Get value from table_format/table, with defaults if necessary.

	inc_avail  = table_format.get('inc_avail') and 'OTHERS' not in table_lbl
	if inc_avail is None:
		inc_avail = table.get('inc_avail', False) and 'OTHERS' not in table_lbl

	inc_class  = table_format.get('inc_class')
	if inc_class is None:
		inc_class = table.get('inc_class',False)

	# WRITE THE IMAGES ROW. #############################################
	html_file += '    <tr class="%s">\n' % (title_cell) 
	html_file += '     <td>%s</td>\n' % (table_lbl)

	# Include a column for "# Avail" info if requested.
	if inc_avail:
		html_file += '     <td></td>\n'

	# Number of columns under each Character entry.
	num_cols = len(keys) + inc_class

	# Include Images for each of the Characters.
	for char in char_list:
		html_file += '     <td class="image" colspan="%i"><img src="https://assets.marvelstrikeforce.com/imgs/Portrait_%s.png" alt="" width="100"></td>\n' % (num_cols, alliance_info['portraits'][char])

	# Include a Team Power column.
	html_file += '     <td></td>\n'
	html_file += '    </tr>\n'
	# DONE WITH THE IMAGES ROW. #########################################

	# WRITE THE CHARACTER NAMES ROW. ####################################
	html_file += '    <tr class="%s">\n' % (char_cell)
	
	if num_cols>1 and len(strike_teams)>1:
		html_file += '     <th>Alliance<br>Member</th>\n'
		
		# Include a column for "# Avail" info if requested.
		if inc_avail:
			html_file += '     <td></td>\n'
	else:
		html_file += '     <td></td>\n'

		# Include a header if "# Avail" info requested.
		if inc_avail:
			html_file += '     <td></td>\n'

	# Include Names of the included characters.
	for char in char_list:
		html_file += '     <th colspan="%i" width="100">%s</th>\n' % (num_cols, translate_name(char))

	# Include the Team Power column.
	html_file += '     <th></th>\n' 
	html_file += '    </tr>\n'
	# DONE WITH THE CHARACTER NAMES ROW. ################################

	# Initialize this count. Will add to it with each strike_team section.
	row_idx = 3

	# Find min/max for meta/strongest team power in the Alliance
	# This will be used for color calculation for the Team Power column.
	stp_range = [stp_list[player_name] for player_name in player_list]

	# Find max available heroes. Anything under 5 is forced to red.
	if inc_avail:
		max_avail = max([len([char for char in table['under_min'].get(player,{}) if not table['under_min'].get(player,{}).get(char)]) for player in player_list])

	# Iterate through each Strike Team.
	for strike_team in strike_teams:

		team_num = strike_teams.index(strike_team)+1

		# Determine if we are requesting a subset of the strike_team,
		# or for strike_teams to be ignored (only_team == 0) 
		only_team = table_format.get('only_team')

		# Add this to allow us to pass in fake Strike_Team definitions so that the correct "Strike Team #" label gets generated. 
		# This is primarily for Spanning output, where one strike team is generated per table.
		if not strike_team or (only_team and only_team != team_num):
			continue

		# Start by composing the data rows for the Strike Team. 
		# We need the length of this block to sort the right 
		# number of lines when clicking on table headers. 
		
		st_rows = 0
		st_html = ''

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
			num_avail = len([char for char in table['under_min'].get(player_name,{}) if not table['under_min'].get(player_name,{}).get(char)])
			not_ready = num_avail < min(len(char_list),5)

			# Player Name, then relevant stats for each character.
			st_html += '    <tr%s>\n' % [' class="hist"',''][not hist_tab]
			st_html += '     <td class="%s">%s</td>\n' % ([name_cell, name_alt, name_cell_dim, name_alt_dim][alt_color+2*not_ready], player_name.replace('Commander','Cmdr.'))

			# If Member's roster has grown more than 1% from last sync or hasn't synced in more than a week, indicate it is STALE DATA via Grayscale output.
			stale_data = is_stale(alliance_info, player_name)

			# Include "# Avail" info if requested.
			if inc_avail:
				st_html += '     <td class="bold" style="background:%s;">%s</td>\n' % (get_value_color_ext(0, max_avail, [num_avail,-1][not_ready], stale_data), num_avail)

			# Write the stat values for each character.
			for char_name in char_list:

				# Load up arguments from table, with defaults if necessary.
				under_min = table['under_min'][player_name][char_name]

				for key in keys:

					# Get the range of values for this character for all rosters.
					# If historical, we want the diff between the current values and the values in the oldest record
					key_range = [find_value_or_diff(alliance_info, player, char_name, key, hist_tab)[0] for player in player_list]

					# Only look up the key_val if we have a roster.
					key_val = 0
					other_diffs = ''
					if player_name in player_list:
					
						# Standard lookup. Get the key_val for this character stat from this player's roster.
						# If historical, we look for the first time this member appears in the History, and then display the difference between the stat in that record and this one.
						key_val,other_diffs = find_value_or_diff(alliance_info, player_name, char_name, key, hist_tab)

					if key_val == 0 and hist_tab:
						style = ''
					else:
						style = ' style="background:%s;%s"' % (get_value_color(key_range, key_val, stale_data, key, under_min, hist_tab), ['color:black;',''][not hist_tab])
					st_html += '     <td%s%s>%s%s</td>\n' % (style, ['',' class="tt"'][key=='power'], [key_val,'-'][not key_val], ['',other_diffs][key=='power'])

				# Include ISO class information if requested
				if inc_class:
					# Get the ISO Class in use for this member's toon.
					iso_code  = alliance_info['members'][player_name].get('other_data',{}).get(char_name,0)%6
					
					# Translate it to a code to specify the correct CSS URI.
					iso_class = ['','fortifier','healer','skirmisher','raider','striker'][iso_code]
					
					# Do a quick tally of all the ISO Classes in use. Remove the '0' entries from consideration.
					all_iso_codes = [alliance_info['members'][player].get('other_data',{}).get(char_name,0)%6 for player in player_list]
					all_iso_codes = [code for code in all_iso_codes if code]
					
					# Calculate a confidence for this code based on the tally of all codes in use.
					iso_conf = 0
					if all_iso_codes:
						iso_conf  = int((all_iso_codes.count(iso_code)/len(all_iso_codes))*100)

					# Include the graphic via CSS and use the confidence for background color.
					if iso_class:
						st_html += '     <td class="%s tt" style="background-color:%s;"><span class="ttt"><b>%s:</b><br>%s</span></td>\n' % (iso_class, get_value_color_ext(0, 100, iso_conf, stale_data, under_min=under_min), iso_class.title(), f'{iso_conf}%')
					else:
						st_html += '     <td style="background:#282828;color:#919191;">-</td>\n'
			# Include the Team Power column.
			player_stp = stp_list.get(player_name,0)
			st_html += '     <td class="bold" style="background:%s;">%s</td>\n' % (get_value_color(stp_range, player_stp, stale_data), [player_stp,'-'][not player_stp])
			st_html += '    </tr>\n'
			
			# Increment the count of data rows by one.
			st_rows += 1
		# DONE WITH THE DATA ROWS FOR THIS STRIKE TEAM ##################
		
		# WRITE THE HEADING ROW WITH VALUE DESCRIPTORS ##################
		# (only if more than one item requested)
		if num_cols>1 or len(strike_teams)>1:
			html_file += '    <tr class="%s">\n' % table_header

			# Simplify inclusion of the sort function code
			sort_func = 'onclick="sortx(%s,\'%s\',%s,%s)"' % ('%s', table_id, row_idx, st_rows)

			if len(strike_teams)>1:
				html_file += f'     <td class="{button_hover}" {sort_func % 0}>STRIKE TEAM {team_num}</td>\n'
			else:
				html_file += f'     <td class="{button_hover}" {sort_func % 0}>Alliance<br>Member</td>\n'

			# Include header if "# Avail" info requested.
			if inc_avail:
				html_file += f'     <td class="{button_hover}" {sort_func % 1}>Avail<br>Char</td>\n'

			col_idx = 1 + inc_avail

			# Insert stat headings for each included Character.
			for char in char_list:
				for key in keys:
					html_file += f'     <td class="{button_hover}" {sort_func % col_idx}>{key.title()}</td>\n'
					col_idx += 1

				# Include a header for ISO Class info if requested.
				if inc_class:
					html_file += '     <td>Cls</td>\n'
					col_idx += 1
			
			# Insert the Team Power column.
			html_file += f'     <td class="red_btn" {sort_func % col_idx}>{team_pwr_lbl}</td>\n'
			html_file += '    </tr>\n'
			
			row_idx += 1
		# DONE WITH THE HEADING ROW FOR THIS STRIKE TEAM ################

		# Add in the block of Strike Team Data Rows.
		html_file += st_html
		row_idx   += st_rows

	# Close the Table, we are done with this chunk.
	html_file += '   </table>\n'

	return html_file


# Generate just the Alliance Tab contents.
def generate_roster_analysis(alliance_info, using_tabs=True, stat_type='actual', hist_tab=''):

	html_file=''

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file += '<div id="RosterAnalysis" class="tabcontent">\n'

	# Generate a table ID to allow sorting. 
	table_id = datetime.datetime.now().strftime('%S%f')
	html_file += '<table id="%s">\n' % (table_id)

	# Simplify inclusion of the sort function code
	sort_func = 'class="%s" onclick="sort(%s,\'%s\',2)"' % ("blu_btn nam", '%s', table_id)

	# Create the headings for the Alliance Info table.
	html_file += '<tr class="header_blue" style="font-size:14pt;">\n'
	html_file += f' <td width="200" rowspan="2" {sort_func % 0}>Name</td>\n'          

	# Simplify inclusion of the sort function code
	sort_func = 'class="%s" onclick="sort(%s,\'%s\',2)"' % ("blu_btn tot", '%s', table_id)

	html_file += f' <td width="80" rowspan="2" {sort_func % 1}>Total<br>Power</td>\n'
	html_file += f' <td width="80" rowspan="2" {sort_func % 2}>Strongest<br>Team</td>\n'
	html_file += f' <td width="80" rowspan="2" {sort_func % 3}>Total<br>Chars</td>\n'
	html_file += ' <td width="2" rowspan="2"></td>\n' 				# Vertical Divider
	
	html_file += ' <td width="200" colspan="5">Average</td>\n'	# All Avg Stats
	html_file += ' <td width="2" rowspan="2"></td>\n' 				# Vertical Divider

	html_file += ' <td width="160" colspan="4">Stars</td>\n'		# Yel 4-7
	html_file += ' <td width="2" rowspan="2"></td>\n' 				# Vertical Divider

	html_file += ' <td width="120" colspan="4">Red Stars</td>\n'	# Red 4-7
	html_file += ' <td width="2" rowspan="2"></td>\n' 				# Vertical Divider

	#html_file += ' <td width="160" colspan="3">Diamonds</td>\n'	# Red 4-7
	#html_file += ' <td width="2" rowspan="2"></td>\n' 				# Vertical Divider

	html_file += ' <td width="200" colspan="5">ISO</td>\n'			# ISO 1-4,5,6-8,9,10
	html_file += ' <td width="2" rowspan="2"></td>\n' 				# Vertical Divider

	html_file += ' <td width="240" colspan="6">Gear Tier</td>\n'	# Tier 13-18
	html_file += ' <td width="2" rowspan="2"></td>\n' 				# Vertical Divider

	html_file += ' <td width="160" colspan="4">T4 Abilities</td>\n'	# Bas/Spc/Ult/Pas
	html_file += ' <td width="2" rowspan="2"></td>\n' 				# Vertical Divider

	html_file += ' <td width="350" colspan="7">Levels</td>\n'		# <65,66-70,71-75,76-80,81-85,86-90,91-95
	html_file += '</tr>\n'

	# Second Row with subheadings.
	html_file += '<tr>\n'

	# Simplify inclusion of the sort function code
	sort_func = 'class="%s" onclick="sort(%s,\'%s\',2)"' % ("ltb_btn col", '%s', table_id)

	# Averages
	html_file += f' <td {sort_func % 5}>Yel</td>\n'
	html_file += f' <td {sort_func % 6}>Red</td>\n'
	html_file += f' <td {sort_func % 7}>Tier</td>\n'
	html_file += f' <td {sort_func % 8}>Lvl</td>\n'
	html_file += f' <td {sort_func % 9}>ISO</td>\n'
	
	# Yellow Stars
	html_file += f' <td {sort_func % 11}>%s</td>\n' % (['4+','4*'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 12}>%s</td>\n' % (['5+','5*'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 13}>%s</td>\n' % (['6+','6*'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 14}>%s</td>\n' % (['7*','7*'][stat_type == 'actual'])
	
	# Red Stars
	html_file += f' <td {sort_func % 16}>%s</td>\n' % (['4+','4*'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 17}>%s</td>\n' % (['5+','5*'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 18}>%s</td>\n' % (['6+','6*'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 19}>%s</td>\n' % (['7+','7*'][stat_type == 'actual'])

	# Diamonds
	#html_file += f' <td {sort_func % 21}>1&#x1F48E;</td>\n'
	#html_file += f' <td {sort_func % 22}>2&#x1F48E;</td>\n'
	#html_file += f' <td {sort_func % 23}>3&#x1F48E;</td>\n'

	# ISO Levels
	html_file += f' <td {sort_func % 25}>%s</td>\n' % (['4+','0-4'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 26}>%s</td>\n' % (['5+','5'  ][stat_type == 'actual'])
	html_file += f' <td {sort_func % 27}>%s</td>\n' % (['8+','6-8'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 28}>%s</td>\n' % (['9+','9'  ][stat_type == 'actual'])
	html_file += f' <td {sort_func % 29}>%s</td>\n' % (['10','10' ][stat_type == 'actual'])

	# Gear Tiers
	html_file += f' <td {sort_func % 31}>%s</td>\n' % (['13+','13'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 32}>%s</td>\n' % (['14+','14'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 33}>%s</td>\n' % (['15+','15'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 34}>%s</td>\n' % (['16+','16'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 35}>%s</td>\n' % (['17+','17'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 36}>%s</td>\n' % (['18' ,'18'][stat_type == 'actual'])

	# T4 Abilities
	html_file += f' <td {sort_func % 38}>Bas</td>\n'
	html_file += f' <td {sort_func % 39}>Spc</td>\n'
	html_file += f' <td {sort_func % 40}>Ult</td>\n'
	html_file += f' <td {sort_func % 41}>Pas</td>\n'

	# Simplify inclusion of the sort function code
	sort_func = 'class="%s" onclick="sort(%s,\'%s\',2)"' % ("ltb_btn lvl", '%s', table_id)

	# Level Ranges
	html_file += f' <td {sort_func % 43}>%s</td>\n' % (['70+', '0-74'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 44}>%s</td>\n' % (['75+','75-79'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 45}>%s</td>\n' % (['80+','80-84'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 46}>%s</td>\n' % (['85+','85-89'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 47}>%s</td>\n' % (['90+','90-94'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 48}>%s</td>\n' % (['95+','95-99'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 49}>%s</td>\n' % (['100', '100' ][stat_type == 'actual'])

	html_file += '</tr>\n'
	
	# Start by doing stat analysis.	
	stats = get_roster_stats(alliance_info, stat_type, hist_tab)
	
	# Get the list of Alliance Members 
	member_list = []
	hist_info = alliance_info.get('hist')
	
	if hist_info:
		member_list = list(hist_info[max(hist_info)])
		
	# Get a sorted list of members to use for this table output.
	alliance_order = sorted(alliance_info['members'].keys(), key = lambda x: alliance_info['members'][x].get('tcp',0), reverse=True)
	alliance_order = [member for member in alliance_order if member in member_list]

	# Iterate through each row for members in the table.
	for member in alliance_order:
			member_info = alliance_info['members'][member]
			member_stats = stats.get(member,{})
			stats_range  = stats['range']

			# If Member's roster has grown more than 1% from last sync or hasn't synced in more than a week, indicate it is STALE DATA via Grayscale output.
			stale_data = is_stale(alliance_info, member)

			html_file += '<tr>\n'

			member_url = ' href="https://marvelstrikeforce.com/en/player/%s/characters" target="_blank"' % (alliance_info['members'][member].get('url',''))
			html_file += ' <td class="%s url_btn"><a style="text-decoration:none; color:black;"%s>%s</a></td>\n' % (['name_blue','name_gray'][stale_data], member_url, member)
			
			for key in ['tcp','stp','tcc']:
				html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(stats_range[key], member_stats.get(key,0), stale_data), f'{member_stats[key]:,}')
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Averages
			for key in ['yel', 'red', 'tier', 'lvl', 'iso']:
				html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(stats_range['tot_'+key], member_stats.get('tot_'+key,0), stale_data), f'{member_stats.get("tot_"+key, 0) / max(member_stats["tcc"],1):.2f}')
			html_file += ' <td></td>\n' 										# Vertical Divider
			
			# Yellow Stars
			for key in range(4,8):
				html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(stats_range['yel'][key], member_stats.get('yel',{}).get(key,0), stale_data), member_stats.get('yel',{}).get(key,0))
			html_file += ' <td></td>\n' 										# Vertical Divider                                                            
																																							  
			# Red Stars                                                                                                                                       
			for key in range(4,8):
				html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(stats_range['red'][key], member_stats.get('red',{}).get(key,0), stale_data), member_stats.get('red',{}).get(key,0))
			html_file += ' <td></td>\n' 										# Vertical Divider                             

			# Diamonds
			#for key in range(1,4):
			#	html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(stats_range['dmd'][key], member_stats.get('dmd',{}).get(key,0), stale_data), member_stats.get('dmd',{}).get(key,0))
			#html_file += ' <td></td>\n' 										# Vertical Divider                             

			# ISO Levels                                                                                                       
			for key in [4,5,8,9,10]:
				html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(stats_range['iso'][key], member_stats.get('iso',{}).get(key,0), stale_data), member_stats.get('iso',{}).get(key,0))
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Gear Tiers
			for key in range(13,19):
				html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(stats_range['tier'][key], member_stats.get('tier',{}).get(key,0), stale_data), member_stats.get('tier',{}).get(key,0))
			html_file += ' <td></td>\n' 										# Vertical Divider

			# T4 Abilities
			for key in ['bas','spc','ult','pas']:
				html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(stats_range[key], member_stats.get(key,{}).get(7,0), stale_data), member_stats.get(key,{}).get(7,0))
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Level Ranges
			for key in range(70,105,5):
				html_file += ' <td style="background:%s;">%s</td>\n' % (get_value_color(stats_range['lvl'][key], member_stats.get('lvl',{}).get(key,0), stale_data), member_stats.get('lvl',{}).get(key,0))

			html_file += '</tr>\n'

	html_file += '</table>\n'

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		
		# Add the progressive form in for the tabbed output as well. :)
		if stat_type == 'actual':
			html_file += add_tab_header('ROSTER ANALYSIS (PROGRESSIVE)')
			html_file += generate_roster_analysis(alliance_info, using_tabs=False, stat_type='progressive', hist_tab=False)
	
		html_file += '</div>\n'

	return html_file


# STILL NEED TO WORK ON HISTORICAL PRESENTATION. SHOULD USE PROGRESSIVE STAT CALCULATIONS FOR BOTH TO SUCCESSFULLY COMMUNICATE PROGRESS.

def get_roster_stats(alliance_info, stat_type, hist_tab=''):
	
	stats = {}
	
	hist_info = alliance_info.get('hist',{})
	
	current_rosters = {}
	oldest_rosters  = {}
	
	if hist_info:
		current_rosters = copy.deepcopy(hist_info[max(hist_info)])
		oldest_rosters  = copy.deepcopy(hist_info[min(hist_info)])
	
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

			# Use for Total / Average # columns -- do this BEFORE normalizing data.
			for key in ['yel','red','dmd','tier','lvl','iso']:
				member_stats['tot_'+key] = member_stats.get('tot_'+key,0) + char_stats[key] # - diff_stats[key]

			# If progressive, only report the highest USABLE red star and diamonds only valid if 7R.
			if char_stats['red'] > char_stats['yel']:
				char_stats['red'] = char_stats['yel']
			if char_stats['red'] != 7:
				char_stats['dmd'] = 0
 				
			# Normalize the data.
			# If stat_type = 'actual', combine ISO and LVL columns before tallying
			# If 'progressive', make each entry count in those below it.

			# For either stat_type, combine certain columns for ISO and Level data.
			if char_stats['lvl'] < 74 and stat_type == 'actual':
				char_stats['lvl'] = 70
			else:
				char_stats['lvl'] -= char_stats['lvl']%5			# Round down to nearest multiple of 5.

			if char_stats['iso'] < 4 and stat_type == 'actual':
				char_stats['iso'] = 4
			elif char_stats['iso'] in range(6,9) and stat_type == 'actual':
				char_stats['iso'] = 8

			# Just tally the values in each key. Increment the count of each value found.
			for key in ['yel', 'lvl', 'red', 'dmd', 'tier', 'iso']:
				if stat_type == 'progressive':
					for x in range(0,char_stats[key]+1):
						member_stats.setdefault(key,{})[x] = member_stats.get(key,{}).setdefault(x,0)+1
				else:
					member_stats.setdefault(key,{})[char_stats[key]] = member_stats.get(key,{}).setdefault(char_stats[key],0)+1
					
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

		member_stats['tcp'] = alliance_info['members'].get(member,{}).get('tcp') or sum(member_stats.get('power',[]))
		member_stats['stp'] = alliance_info['members'].get(member,{}).get('stp') or sum(sorted(member_stats.get('power',[]))[-5:])
		member_stats['tcc'] = alliance_info['members'].get(member,{}).get('tcc') or len(member_stats.get('power',[]))

	# Calculate alliance-wide ranges for each statistic. Use min() and max() to determine colors
	stats['range'] = {}
	stats['range']['tcp'] = [stats[member]['tcp'] for member in member_list]
	stats['range']['stp'] = [stats[member]['stp'] for member in member_list]
	stats['range']['tcc'] = [stats[member]['tcc'] for member in member_list]

	# Totals (and create dicts for the rest of the ranges)
	for key in ['yel','red','dmd','tier','lvl','iso']:
		stats['range'][key]  = {}
		stats['range']['tot_'+key]  = [stats[member].get('tot_'+key,0) for member in member_list]
	
	# Yellow and Red Stars
	for key in range(4,8):
		stats['range']['yel'][key] = [stats[member].get('yel',{}).get(key,0) for member in member_list]
		stats['range']['red'][key] = [stats[member].get('red',{}).get(key,0) for member in member_list]

	# Diamonds
	for key in range(1,4):
		stats['range']['dmd'][key] = [stats[member].get('dmd',{}).get(key,0) for member in member_list]

	# ISO Levels
	for key in range(4,11):
		stats['range']['iso'][key] = [stats[member].get('iso',{}).get(key,0) for member in member_list]

	# Gear Tiers
	for key in range(13,19):
		stats['range']['tier'][key] = [stats[member].get('tier',{}).get(key,0) for member in member_list]

	# Level Ranges
	for key in range(65,105,5):
		stats['range']['lvl'][key] = [stats[member].get('lvl',{}).get(key,0) for member in member_list]

	# T4 Abilities
	for key in ['bas','spc','ult','pas']:
		stats['range'][key] = [stats[member].get(key,{}).get(7,0) for member in member_list]

	return stats


# Generate just the Alliance Tab contents.
def generate_alliance_tab(alliance_info, using_tabs=True, html_file=''):

	# Start by sorting members by TCP.
	alliance_order = sorted(alliance_info['members'].keys(), key = lambda x: alliance_info['members'][x].get('tcp',0), reverse=True)
	
	# Build up the list of Alliance Members in the order we will present them.
	member_list =  [alliance_info['leader']] + alliance_info.get('captains',[])
	member_list += [member for member in alliance_order if member not in member_list]

	tot_power = sum([alliance_info['members'][member].get('tcp',0) for member in alliance_info['members']])
	avg_power = int(tot_power/len(alliance_info['members']))

	# See if name includes a color tag.
	alt_color = extract_color(alliance_info['name'])

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file += '<div id="AllianceInfo" class="tabcontent">\n'

	# Generate a table ID to allow sorting. 
	table_id = datetime.datetime.now().strftime('%S%f')
	html_file += '<table id="%s" style="background:#222;">\n' % (table_id)

	html_file += '<tr>\n</tr>\n'

	html_file += '<tr style="font-size:18px;color:white;">\n'
	html_file += ' <td colspan="2" rowspan="2"><img src="https://assets.marvelstrikeforce.com/www/img/logos/logo-en.png" alt=""></td>'
	html_file += ' <td colspan="10" class="alliance_name"%s>%s</td>' % (alt_color, alliance_info['name'].upper())
	html_file += ' <td colspan="2"  rowspan="2"><img src="https://assets.marvelstrikeforce.com/imgs/ALLIANCEICON_%s.png" alt=""/></td>\n' % (alliance_info.get('image','EMBLEM_6_dd63d11b'))
	html_file += '</tr>\n'

	html_file += '<tr style="font-size:18px;color:white;">\n'
	html_file += ' <td colspan="2">Members<br><span style="font-size:24px;"><b>%i/24</b></span></td>\n' % (len(alliance_info['members']))
	html_file += ' <td colspan="2">Total Power<br><span style="font-size:24px;"><b>%s</b></span></td>\n' % (f'{tot_power:,}')
	html_file += ' <td colspan="2">Average Power<br><span style="font-size:24px;"><b>%s</b></span></td>\n' % (f'{avg_power:,}')
	html_file += ' <td colspan="2">Level<br><span style="font-size:24px;"><b>%s</b></span></td>\n' % (alliance_info.get('stark_lvl','80'))
	html_file += ' <td colspan="2">Trophies<br><span style="font-size:24px;"><b>%s</b></span></td>\n' % (alliance_info.get('trophies','n/a'))
	html_file += '</tr>\n'

	# Simplify inclusion of the sort function code
	sort_func = 'class="%s" onclick="sort(%s,\'%s\',4)"' % ("blu_btn", '%s', table_id)

	# Create the headings for the Alliance Info table.
	html_file += '<tr class="header_blue" style="font-size:14pt;">\n'
	html_file += ' <td width="60"></td>\n'
	html_file += f' <td width="215" {sort_func % 1}>Name</td>\n'            
	html_file += f' <td width="110" {sort_func % 2}>Level</td>\n'
	html_file += f' <td width="110" {sort_func % 3}>Role</td>\n'
	html_file += f' <td width="110" {sort_func % 4}>Collection<br>Power</td>\n'
	html_file += f' <td width="110" {sort_func % 5}>Strongest<br>Team</td>\n'
	html_file += f' <td width="110" {sort_func % 6}>Total<br>Collected</td>\n'
	html_file += f' <td width="110" {sort_func % 7}>Max<br>Stars</td>\n'
	html_file += f' <td width="110" {sort_func % 8}>Arena<br>Rank</td>\n'
	html_file += f' <td width="110" {sort_func % 9}>Blitz<br>Wins</td>\n'
	html_file += f' <td width="110" {sort_func % 10}>War<br>MVP</td>\n'
	html_file += f' <td width="110" {sort_func % 11}>Total<br>Stars</td>\n'
	html_file += f' <td width="110" {sort_func % 12}>Total<br>Red</td>\n'
	html_file += f' <td width="215" {sort_func % 13}>Last Updated:</td>\n'
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
		stale_data = is_stale(alliance_info, member)
		
		member_color = ['#B0E0E6','#DCDCDC'][stale_data]

		if member in alliance_info['leader']:
			member_role = '<a> Leader </a>'
		elif member in alliance_info.get('captains',[]):
			member_role = 'Captain'
			member_color = ['#00BFFF','#A9A9A9'][stale_data]		
		else:
			member_role = 'Member'

		html_file += ' <tr style="background:%s;">\n' % (member_color)
		html_file += '  <td style="padding:0px;"><img height="45" src="https://assets.marvelstrikeforce.com/imgs/Portrait_%s.png"/></td>\n' % (member_stats.get('image','ShieldDmg_Defense_3dea00f7'))

		member_url = alliance_info['members'][member].get('url','')
		if member_url:
			member_url = ' href="https://marvelstrikeforce.com/en/player/%s/characters" target="_blank"' % (member_url)

		member_discord = alliance_info['members'][member].get('discord','')
		if member_discord:
			member_discord = f"<br>@{member_discord.get('name','')}"

		html_file += '  <td class="bold url_btn"><a style="text-decoration:none; color:black;"%s>%s%s</a></td>\n' % (member_url, member, member_discord)
		html_file += '  <td>%s</td>\n' % (member_stats.get('level','n/a'))
		html_file += '  <td>%s</td>\n' % (member_role)
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(tcp_range,   member_stats.get('tcp',0),   stale_data), f'{member_stats.get("tcp",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(stp_range,   member_stats.get('stp',0),   stale_data), f'{member_stats.get("stp",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color_ext(max(tcc_range)-5, max(tcc_range),   member_stats.get('tcc',0),   stale_data), f'{member_stats.get("tcc",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(max_range,   member_stats.get('max',0),   stale_data), f'{member_stats.get("max",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color_ext(max(arena_range), min(arena_range), member_stats.get('arena',0), stale_data), f'{member_stats.get("arena",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(blitz_range, member_stats.get('blitz',0), stale_data), f'{member_stats.get("blitz",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(mvp_range,   member_stats.get('mvp',0),   stale_data), f'{member_stats.get("mvp",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(stars_range, member_stats.get('stars',0), stale_data), f'{member_stats.get("stars",0):,}')
		html_file += '  <td style="background:%s;">%s</td>\n' % (get_value_color(red_range,   member_stats.get('red',0),   stale_data), f'{member_stats.get("red",0):,}')

		if 'last_update' in member_stats:
			last_update = datetime.datetime.now() - member_stats['last_update']
			time_color  = get_value_color_ext(4*86400, 0, last_update.total_seconds(), stale_data)
			
			if stale_data:
				time_value = '<b><i> Stale. Please re-sync. </i></b><br>%s, %sd ago' % (member_stats['last_update'].strftime('%a, %b %d'), last_update.days)
				#time_value = '<b><i> Stale. Please re-sync. </i></b> %s, %sd ago' % (member_stats['last_update'].strftime('%a, %b %d'), last_update.days)
			else:
				time_value = '%s%s ago<br>%s' % (['',f'{last_update.days} days, '][not last_update.days], str(last_update).split('.')[0], member_stats['last_update'].strftime('%a, %b %d')) 
				#time_value = f'%s{str(int(last_update.seconds/3600)): >2}h ago, %s' % ([f'{last_update.days}d',''][not last_update.days], member_stats['last_update'].strftime('%a, %b %d')) 
		else:
			time_color = get_value_color_ext(0, 1, 0)
			time_value = 'NEVER<br><b><i>Ask member to sync.</i></b>'
		
		html_file += '  <td style="background:%s;">%s</td>\n' % (time_color, time_value)
		#html_file += '  <td style="background:%s;min-width:200px;">%s</td>\n' % (time_color, time_value)
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
def get_value_color(val_range, value, stale_data, stat='power', under_min=False, hist_tab=''):
	min_val = min(val_range)

	if not min_val:
		new_range = [x for x in val_range if x != 0]
		if new_range:
			min_val = min(new_range)
	
	return get_value_color_ext(min_val, max(val_range), value, stale_data, stat, under_min, hist_tab)

def get_value_color_ext(min, max, value, stale_data=False, stat='power', under_min=False, hist_tab=''):
	
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
				"Pegasus": "PEGASUS",
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
				"XTreme": "X-Treme X-Men",
				"YoungAvenger": "Young<br>Avengers",
				"Captain America (WWII)": "Capt. America (WWII)",
				"Captain America (Sam)": "Capt. America (Sam)",
				"Ms. Marvel (Hard Light)": "Ms. Marvel<br>(Hard Light)",
				"Iron Man (Infinity War)":"Iron Man<br>(Infinity War)",
				"Ironheart (MKII)": "Ironheart<br>(MKII)"}
				

	# Return the translation if available.
	return tlist.get(value, value)

