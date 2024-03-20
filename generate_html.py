#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_html.py
Takes the processed alliance / roster data and generate readable output to spec.  
"""

# By_Char data should use same hist_date as provided in inc_hist or inline_hist
# Need to fix data normalization routines. All-zero data in the final data frames???
# Change the hist date selection algorithm. Don't just go min if date requested is missing, return slightly older, min if none older.

from log_utils import *

import datetime
import string
import copy

# Routines to create color gradient for heat map
from alliance_info import *
from generate_css  import *
from gradients     import color_scale, darken, grayscale
from html_cache    import *

# Build specific tab output for use in generating PNG graphics.
@timed(level=3)
def generate_html(alliance_info, table, table_format, output=''):

	default_lanes = [[{'traits': ['Mutant']},
					  {'traits': ['Bio']},
					  {'traits': ['Skill']},
					  {'traits': ['Mystic']},
					  {'traits': ['Tech']}]]

	html_files = {}
	html_cache = {}
	
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
			hist_date = get_hist_date(alliance_info, table_format)

			for section_idx in range(0,len(lane),sections_per):

				# Include the label for the lane plus the requested sections.
				html_file = add_tab_header(tab_name)	

				sections = lane[section_idx:section_idx+sections_per]
				for section in sections:
					html_file += generate_lanes(alliance_info, table, [[section]], table_format, html_cache=html_cache)

				# Include the history information if we have it and can include it.
				if hist_date:
					html_file += add_tab_header(get_hist_tab(hist_date, table_format))	
					html_file += generate_lanes(alliance_info, table, [[section]], table_format, hist_date, html_cache=html_cache)

				# Wrap it up and add it to the collection.
				section_num = ''
				if only_section or sections_per != len(lane):
					section_num += [f'-s{only_section:02}', f'-s{section_idx+1:02}'][not only_section]
					if len(sections) != 1:
						section_num += f'-{section_idx+len(sections):02}'

				# Include scripts to support sorting.
				html_file += add_sort_scripts()

				# Finsh it by adding the CSS to the top with all the defined colors.
				html_file  = add_css_header(table_name, html_cache=html_cache) + html_file + '</body>\n</html>\n'		
				html_files[output+'%s%s.html' % (file_num, section_num)] = html_file
		
	# If not, it's one of the supporting tabs.
	else:
		html_file = ''
		
		# Generate the appropriate midsection, either Roster Analysis...
		if output == 'roster_analysis':
			html_file += add_tab_header('ROSTER ANALYSIS (ACTUALS)')
			html_file += generate_roster_analysis(alliance_info, stat_type='actual', html_cache=html_cache)
			html_file += add_tab_header('ROSTER ANALYSIS (PROGRESSIVE)')
			html_file += generate_roster_analysis(alliance_info, stat_type='progressive', html_cache=html_cache)

			# Generate a label for the History Tab if we have History.
			hist_date = get_hist_date(alliance_info, table_format)
			if hist_date:
				html_file += add_tab_header(get_hist_tab(hist_date, table_format))	
				html_file += generate_roster_analysis(alliance_info, stat_type='progressive', hist_date=hist_date, html_cache=html_cache)
		
		# ...or Alliance Info. Don't use the tab labels for Alliance Info
		elif output == 'alliance_info':
			html_file += generate_alliance_tab(alliance_info, html_cache=html_cache)

		# ...or Alliance Info. Don't use the tab labels for Alliance Info
		elif output == 'by_char':
			html_file += generate_by_char_tab(alliance_info, table_format, html_cache=html_cache)

		# Include scripts to support sorting.
		html_file += add_sort_scripts()

		report_descriptions = {	'roster_analysis':'Roster Analysis',
								'alliance_info'  :'Alliance Info',
								'by_char'        :'Info by Char'}

		# Finish by adding the CSS Header to the top.
		html_file = add_css_header(report_descriptions[output], html_cache=html_cache) + html_file

		# Wrap it up and add it to the collection.
		html_file += '</body>\n</html>\n'
		html_files[output+'.html'] = html_file	

	return html_files


# Build the entire file -- headers, footers, and tab content for each lane and the Alliance Information.
@timed(level=3)
def generate_tabbed_html(alliance_info, table, table_format):

	html_cache = {}

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
	hist_date = get_hist_date(alliance_info, table_format)
	hist_tab  = get_hist_tab(hist_date, table_format, lanes, tabbed=True)

	# Add a tab for each lane. 
	html_file = generate_lanes(alliance_info, table, lanes, table_format, using_tabs=True, html_cache=html_cache)

	# Add a historical info tab.
	if hist_date:
		html_file += generate_lanes(alliance_info, table, lanes, table_format, hist_date, using_tabs=True, html_cache=html_cache)

	# After all Lanes are added, add the Roster Analysis, Alliance Info, and ByChars tabs.
	html_file += generate_roster_analysis(alliance_info, using_tabs=True, html_cache=html_cache)
	html_file += generate_alliance_tab   (alliance_info, using_tabs=True, html_cache=html_cache)
	html_file += generate_by_char_tab    (alliance_info, using_tabs=True, html_cache=html_cache)
	
	# If we want to remove whitespace for --publish, this is where we do it.
	#print ("BEFORE:",len(html_file))
	#html_file = ''.join([line.strip() for line in html_file.split('\n')])
	#print ("AFTER:",len(html_file))
	
	# My thoughts about --publish. 
	# Do the Alliance Info and Roster Analysis as separate HTML.
	# Remove them from all the other tabbed files.
	
	# Include scripts to support sorting.
	html_file += add_sort_scripts()

	# Finally, add the Javascript to control tabbed display.
	html_file += add_tabbed_footer()
		
	# Finish it with the CSS Header at the top and final lines on the end.
	html_file = add_css_header(table_name, len(lanes), hist_tab, html_cache=html_cache) + html_file + '</body>\n</html>\n'

	return html_file


# If we're doing a single lane format and we have history, let's generate a historical data tab. 
@timed(level=3)
def get_hist_tab(hist_date, table_format, lanes=[], tabbed=False):

	# Default it to empty.
	hist_tab = ''

	# If this format qualifies for History and it's being requested, generate the tab label.
	if hist_date:
		if (tabbed and len(lanes) == 1) or (not tabbed and table_format.get('only_section') or table_format.get('sections_per') == 1):
			hist_tab = "CHANGES SINCE %s" % hist_date

	return hist_tab


# Just hide the messiness.
@timed(level=3)
def add_tab_header(content):
	return '<table>\n<tr><td class="tlnk" style="width:100%;">'+content+'</td></tr>\n</table>'


# Generate the contents for each lane.
@timed(level=3)
def generate_lanes(alliance_info, table, lanes, table_format, hist_date=None, using_tabs=False, html_cache={}):

	html_file = ''

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
	if (not strike_teams or only_team == 0) and not table_format.get('sort_by'):
		table_format['sort_by'] = 'stp'

	# Sort player list if requested.
	sort_by = get_table_value(table_format, table, key='sort_by')

	# Use the full Player List sorted by stp if explicit Strike Teams haven't been defined.
	if not strike_teams or only_team == 0:
		strike_teams = [get_player_list(alliance_info, sort_by)]

	# Special handling required if inline_hist.
	inline_hist = get_table_value(table_format, table, key='inline_hist')

	# Iterate through all the lanes. Showing tables for each section. 
	for lane in lanes:

		# Display each lane in a separate tab.
		divider_id = ['Hist','Lane'][not hist_date] + str(lanes.index(lane)+1)
		
		# Only include Dividers if using as part of a multi-tab document
		if using_tabs:
			html_file += '<div id="%s" class="tcon">\n' % (divider_id)

		# Process each section individually, filtering only the specified traits into the Active Chars list.
		for section in lane:

			last_section = lane.index(section) == len(lane)-1
		
			meta_chars, other_chars = get_meta_other_chars(alliance_info, table, section, table_format)

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

			max_others = get_table_value(table_format, table, section, key='max_others')

			# Only building meta table if we have meta_chars defined.
			if meta_chars:
				meta_lbl = table_lbl+'<br><span class="sub">META</span>'

				stp_list = get_stp_list(alliance_info, meta_chars, hist_date)
				
				# If inline_hist, need to generate STP entries for the historical date as well.
				if inline_hist:
					stp_list = get_stp_list(alliance_info, meta_chars, inline_hist)

				html_file += generate_table(alliance_info, table, section, table_format, meta_chars, strike_teams, meta_lbl, stp_list, html_cache, hist_date)

				html_file += '  </td>\n  <td><br></td>\n  <td>\n'

				# Only differentiate Others Section from Meta Section if Meta Section exists.
				table_lbl += '<br><span class="sub">OTHERS</span>'

			# Flag the table_lbl to indicate these are META character requests
			# even if they've been swapped to the Others section.
			elif section.get('meta'):
				table_lbl += '<br><span class="sub">META</span>'

			# If Others, and max_others specified, indicate this.
			elif max_others:
				table_lbl += f'<br><span class="sub">TOP {len(other_chars)}</span>'

			# Generate stp_list dict for the Other Table calls.
			stp_list = get_stp_list(alliance_info, meta_chars+other_chars, hist_date)
			
			# If inline_hist, need to generate STP entries for the historical date as well.
			if inline_hist:
				stp_list = get_stp_list(alliance_info, meta_chars+other_chars, inline_hist)

			span_data = get_table_value(table_format, table, section, key='span', default=False)

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
					html_file += generate_table(alliance_info, table, section, table_format, other_chars, strike_team, table_lbl, stp_list, html_cache, hist_date)
					html_file += '  </td>\n  <td><br></td>\n  <td>\n'

			# We are NOT spanning. Standard table generation.
			else:
				html_file += generate_table(alliance_info, table, section, table_format, other_chars, strike_teams, table_lbl, stp_list, html_cache, hist_date)

			# End every section the same way.
			html_file += '  </td>\n </tr>\n</table>\n'

			# If not the final section, add a divider row. 
			if not last_section:
				html_file += '    <p></p>\n'

		# After Lane content is done, close the div for the Tab implementation.
		if using_tabs:
			html_file += '</div>\n'

	return html_file


'''
def team_power_report(alliance_info, lane, table_format, team_list):
		
	
	for section in lane:
		unformatted_label = get_section_label(section)
		if unformatted_label in team_list:
'''		


# Generate individual tables for Meta/Other chars for each raid section.
@timed(level=3)
def generate_table(alliance_info, table, section, table_format, char_list, strike_teams, table_lbl, stp_list, html_cache={}, hist_date=None, linked_hist=None):

	# Pick a color scheme.
	if 'OTHERS' not in table_lbl:
		title_cell    = 'tblk'
		table_header  = 'hblu'
		name_cell     = 'nblu'
		name_cell_dim = 'nblud'
		name_alt      = 'nalt'
		name_alt_dim  = 'naltd'
		button_hover  = 'blub'
		
	else:
		title_cell    = 'tgra'
		table_header  = 'hgra'
		name_cell     = 'ngra'
		name_cell_dim = 'ngrad'
		name_alt      = 'ngalt'
		name_alt_dim  = 'ngaltd'
		button_hover  = 'blkb'

	# Sort player list if requested.
	sort_by = get_table_value(table_format, table, section, key='sort_by', default='')

	# Get the list of Alliance Members we will iterate through as rows.	
	player_list = get_player_list (alliance_info, sort_by, stp_list)

	# If there are no players in this table, don't generate a table.
	using_players = [player for player in sum(strike_teams, []) if player in player_list]
	if not using_players:
		return ''
		
	# See if we need to pare the included characters even further.
	using_chars = char_list[:]

	# Find out whether inline history has been requested for this report.
	inline_hist = get_table_value(table_format, table, section, key='inline_hist')
	
	# Pare any missing heroes if these aren't Meta entries.
	if 'META' not in table_lbl and len(using_chars) > 5:
		using_chars = remove_min_iso_tier(alliance_info, table_format, table, section, using_players, using_chars)			

		# if inline_hist, only want heroes that have actually been changed.
		if inline_hist:

			# min_change_filter specifies how much change is required to be considered 'intentionally built'. 
			min_change_filter = get_table_value(table_format, table, section, key='min_change_filter', default=0)

			# If a value is specified, strip any character that hasn't been built at least that amount over time.
			if min_change_filter:
				using_chars = [char for char in using_chars if max([find_value_or_diff(alliance_info, player, char, 'power', hist_date=inline_hist)[0]/find_value_or_diff(alliance_info, player, char, 'power')[0] for player in using_players]) >= min_change_filter]

	# If there are no characters in this table, don't generate a table.
	if not using_chars:
		return ''
		
	# Generate a table ID to allow sorting. 
	
	# If linked_hist is False, this is a standard table on the reports tab.
	if not linked_hist:
		table_id = make_next_table_id(html_cache) 
	
	# If linked_hist, we are building tables for the ByChar page. Let's see if we have an anchor definition.
	else:
		anchor, table_id, linked_id = lookup_table_ids(html_cache, char_list, hist_date)
		
	# Let's get this party started!
	html_file = '   <table id="%s">\n' % (table_id)

	# SEE IF WE NEED MULTIPLE LINES. WE MAY NEED TO BREAK UP USING_CHARS INTO CHUNKS.
	line_wrap = 20

	# Initialize the row count. Will add to it with each strike_team section.
	row_idx = 1

	while using_chars:
		line_chars, using_chars = using_chars[:line_wrap],using_chars[line_wrap:]

		# WRITE THE IMAGES ROW. #############################################
		html_file += '    <tr class="%s">\n' % (title_cell) 
		html_file += '     <td>%s</td>\n' % (table_lbl)

		# Include Available, Include Position, and Include ISO Class flags
		# Get value from table_format/table, with defaults if necessary.

		inc_avail = get_table_value(table_format, table, section, key='inc_avail', default=False) and 'OTHERS' not in table_lbl
		inc_pos   = get_table_value(table_format, table, section, key='inc_pos',   default=False) and 'OTHERS' not in table_lbl
		inc_class = get_table_value(table_format, table, section, key='inc_class', default=False) and not hist_date

		# Include a column for "# Pos" info if requested.
		if inc_pos:
			html_file += '     <td></td>\n'

		# Include a column for "# Avail" info if requested.
		if inc_avail:
			html_file += '     <td></td>\n'

		# Get keys from table_format/table, with defaults if necessary.
		keys = get_table_value(table_format, table, section, key='inc_keys', default=['power','tier','iso'])

		# Treat 'abil' as 4 separate entries.
		if 'abil' in keys:
			idx = keys.index('abil')
			keys = keys[:idx] + ['bas', 'spc', 'ult', 'pas'] + keys[idx+1:]

		# Number of columns under each Character entry.
		num_cols = len(keys) + inc_class

		# Include Images for each of the Characters.
		for char in line_chars:
			url = f"https://assets.marvelstrikeforce.com/imgs/Portrait_{alliance_info['portraits'][char]}.png"

			# Default value to start
			onclick = ''

			# We are doing a ByChar table in a tabbed file, link back to the report tabs.
			if linked_hist and anchor:
				# Finally, connect back to the info in the raid.
				onclick =  ' onclick="toTable(this,\'%s\')"' % (anchor.get('from')) 

			# If we don't have linked_hist, then we're on the reports tab.
			elif not linked_hist:

				# Create new anchor entry to link Report and Bychar tabs. 
				anchor = make_next_anchor_id(html_cache, char, table_id)
				onclick = ' onclick="toTable(this,\'%s\')"' % (anchor.get('to')) 

			html_file += '     <td class="img" colspan="%s"%s><div class="cont"><div class="%s"><img src="%s" alt="" width="100"></div><div class="cent">%s</div></div></td>\n' % (num_cols, onclick, ['',' zoom'][not hist_date], url, translate_name(char))

		# Include a Team Power column if we have more than one.
		if len(char_list)>1:
			html_file += '     <td></td>\n'

		html_file += '    </tr>\n'
		# DONE WITH THE IMAGES ROW. #########################################

		# Include the Image row and Column headers in the row count.
		row_idx += 1

		# Find max available heroes for stats/color. Anything under 5 is forced to red.
		if inc_avail:
			max_avail = max([len([char for char in table.get('under_min',{}).get(player,{}) if not table.get('under_min',{}).get(player,{}).get(char)]) for player in player_list])

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
				
				# This divider is a little different. Go ahead and add it back in after sorting.
				inc_dividers = get_table_value(table_format, table, section, key='inc_dividers', default='other')
				if inc_dividers == '53':
						strike_team = insert_dividers([strike_team], inc_dividers)[0]

			# FINALLY, WRITE THE DATA FOR EACH ROW. #########################
			alt_color = False
			for player_name in strike_team:
			
				# If strike_team name not in the player_list, it's a divider.
				# Toggle a flag for each divider to change the color of Player Name slightly
				if player_name not in player_list:
					alt_color = not alt_color
					continue

				# See whether this person has 5 heroes in either meta or other that meet the minimum requirements for this raid section/game mode.
				num_avail = len([char for char in table.get('under_min',{}).get(player_name,{}) if not table.get('under_min',{}).get(player_name,{}).get(char)])

				# If less than 5 characters, this just doesn't apply.
				not_ready = num_avail < 5 if len(char_list) >= 5 else False

				# If inline_hist is requested, we will loop through this code twice for each user.
				# First pass will generate normal output and second one will generate historical data. 
				if inline_hist:
					hist_list = [hist_date,inline_hist]
				else:
					hist_list = [hist_date]
					
				for use_hist_date in hist_list:

					# Find min/max for meta/strongest team power in the Alliance
					# This will be used for color calculation for the Team Power column.
					stp_range = [stp_list[use_hist_date][player_name] for player_name in player_list]

					if inline_hist and use_hist_date:
						name_field = f'<span style="font-weight:normal;"><i>(since {use_hist_date.strftime("%m/%d/%y")})</i></span>'
					else:
						name_field = player_name.replace('Commander','Cmdr.')

					# Player Name, then relevant stats for each character.
					st_html += '    <tr%s>\n' % [' class="hist"',''][not use_hist_date]
					st_html += '     <td class="%s">%s</td>\n' % ([name_cell, name_alt, name_cell_dim, name_alt_dim][alt_color+2*not_ready], name_field)

					# If Member's roster has grown more than 1% from last sync or hasn't synced in more than a week, indicate it is STALE DATA via Grayscale output.
					stale_data = alliance_info['members'][player_name]['is_stale']

					# Include "# Pos" info if requested.
					if inc_pos:
						pos_num = get_player_list(alliance_info, sort_by='stp', stp_list=stp_list).index(player_name)+1
						st_html += '     <td class="bd %s">%s</td>\n' % (get_value_color_ext(25, 1, pos_num, html_cache, stale_data), pos_num)

					# Include "# Avail" info if requested.
					if inc_avail:
						st_html += '     <td class="bd %s">%s</td>\n' % (get_value_color_ext(0, max_avail, [num_avail,-1][not_ready], html_cache, stale_data), num_avail)

					# Write the stat values for each character.
					for char_name in line_chars:

						# Load up arguments from table, with defaults if necessary.
						under_min = table.get('under_min',{}).get(player_name,{}).get(char_name)

						for key in keys:

							# Get the range of values for this character for all rosters.
							# If historical, we want the diff between the current values and the values in the oldest record
							key_range = [find_value_or_diff(alliance_info, player, char_name, key, use_hist_date)[0] for player in player_list]

							# Only look up the key_val if we have a roster.
							key_val = 0
							other_diffs = ''
							if player_name in player_list:
							
								# Standard lookup. Get the key_val for this character stat from this player's roster.
								# If historical, we look for the first time this member appears in the History, and then display the difference between the stat in that record and this one.
								key_val,other_diffs = find_value_or_diff(alliance_info, player_name, char_name, key, use_hist_date)

							need_tt = key=='power' and key_val != 0 and not linked_hist

							if key_val == 0 and use_hist_date:
								style = ''
							else:
								# Note: We are using the tt class to get black text on fields in the Hist tab.
								field_color = get_value_color(key_range, key_val, html_cache, stale_data, key, under_min, use_hist_date)
								style = ' class="%s%s"' % (field_color, ['', ' tt'][need_tt or use_hist_date is not None])    

							# Determine what value should be displayed in data field. Add + if historical data, use '-' if empty value.
							if key_val:
								field_value = f'{key_val:+}' if use_hist_date else f'{key_val}'
							else:
								field_value = '-'

							st_html += '     <td%s>%s%s</td>\n' % (style, field_value, ['',other_diffs][need_tt])

						# Include ISO class information if requested
						if inc_class:

							# Get the ISO Class in use for this member's toon.
							iso_code  = (alliance_info['members'][player_name].get('other_data',{}).get(char_name,0)&15)%6								# -- REMOVE THE &15 EVENTUALLY. NO LONGER COLLECTING THIS DATA.
							
							# Translate it to a code to specify the correct CSS URI.
							iso_class = ['','fortifier','healer','skirmisher','raider','striker'][iso_code]
							
							# Do a quick tally of all the ISO Classes in use. Remove the '0' entries from consideration.
							all_iso_codes = [(alliance_info['members'][player].get('other_data',{}).get(char_name,0)&15)%6 for player in player_list]	# -- REMOVE THE &15 EVENTUALLY. NO LONGER COLLECTING THIS DATA.
							all_iso_codes = [code for code in all_iso_codes if code]
							
							# Calculate a confidence for this code based on the tally of all codes in use.
							iso_conf = 0
							if all_iso_codes:
								iso_conf  = int((all_iso_codes.count(iso_code)/len(all_iso_codes))*100)

							# Include the graphic via CSS and use the confidence for background color.
							if iso_class:
								field_color = get_value_color_ext(0, 100, iso_conf, html_cache, stale_data, under_min=under_min)
								tool_tip = f'<span class="ttt"><b>{iso_class.title()}:</b><br>{iso_conf}%</span>'
								st_html += f'     <td class="{iso_class[:4]} tt {field_color}">{tool_tip}</td>\n'
							else:
								st_html += '     <td class="hist">-</td>\n'

					# Include the Strongest Team Power column.
					if len(char_list)>1:
						player_stp = stp_list.get(use_hist_date,{}).get(player_name,0)

						# Determine what value should be displayed in STP field. Add + if historical data, use '-' if empty value.
						if player_stp:
							field_value = f'{player_stp:+}' if use_hist_date else f'{player_stp}'
						else:
							field_value = '-'

						st_html += '     <td class="bd %s">%s</td>\n' % (get_value_color(stp_range, player_stp, html_cache, stale_data), field_value)
					
					st_html += '    </tr>\n'
					
					# Increment the count of data rows by one.
					st_rows += 1
			# DONE WITH THE DATA ROWS FOR THIS STRIKE TEAM ##################

			# WRITE THE HEADING ROW WITH VALUE DESCRIPTORS ##################
			# (only if more than one item requested)
			if num_cols>1 or len(strike_teams)>1:
				html_file += '    <tr class="%s">\n' % table_header

				# Simplify inclusion of the sort function code
				if linked_hist:
					sort_func = 'onclick="sortl(%s,\'%s\',%s,%s,\'%s\')"' % ('%s', table_id, row_idx, st_rows, linked_id)
				else:
					sort_func = 'onclick="sortx(%s,\'%s\',%s,%s)"' % ('%s', table_id, row_idx, st_rows)

				if len(strike_teams)>1:
					html_file += f'     <td class="{button_hover}" {sort_func % 0}>STRIKE TEAM {team_num}</td>\n'
				else:
					html_file += f'     <td class="{button_hover}" {sort_func % 0}>Member</td>\n'

				col_idx = 1

				# Include header if "# Pos" info requested.
				if inc_pos:
					html_file += f'     <td class="{button_hover}" {sort_func % col_idx}>Rank</td>\n'
					col_idx += 1

				# Include header if "# Avail" info requested.
				if inc_avail:
					html_file += f'     <td class="{button_hover}" {sort_func % col_idx}>Avail</td>\n'
					col_idx += 1

				# Insert stat headings for each included Character.
				for char in line_chars:
					for key in keys:
						width = 'p' if key == 'power' else ''
						html_file += f'     <td class="{button_hover}{width}" %s>%s</td>\n' % (sort_func % col_idx, {'iso':'ISO'}.get(key,key.title()))
						col_idx += 1

					# Include a header for ISO Class info if requested.
					if inc_class:
						html_file += '     <td>Cls</td>\n'
						col_idx += 1
				
				# Insert the Team Power column.
				if len(char_list)>1:
					html_file += f'     <td class="redb" {sort_func % col_idx}>STP</td>\n'

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
@timed(level=3)
def generate_roster_analysis(alliance_info, using_tabs=False, stat_type='actual', hist_date='', html_cache={}):

	html_file=''

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file += '<div id="RosterAnalysis" class="tcon">\n'

	# Generate a table ID to allow sorting. 
	table_id = make_next_table_id(html_cache) 
	html_file += '<table id="%s">\n' % (table_id)

	# Simplify inclusion of the sort function code
	sort_func = 'class="%s" onclick="sort(%s,\'%s\',2)"' % ("blub nam", '%s', table_id)

	# Create the headings for the Alliance Info table.
	html_file += '<tr class="hblu" style="font-size:14pt;">\n'
	html_file += f' <td width="200" rowspan="2" {sort_func % 0}>Name</td>\n'          

	# Simplify inclusion of the sort function code
	sort_func = 'class="%s" onclick="sort(%s,\'%s\',2)"' % ("blub tot", '%s', table_id)

	html_file += f' <td width="80" rowspan="2" {sort_func % 1}>Total<br>Power</td>\n'
	html_file += f' <td width="80" rowspan="2" {sort_func % 2}>Strongest<br>Team</td>\n'
	html_file += f' <td width="80" rowspan="2" {sort_func % 3}>Total<br>Chars</td>\n'
	html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider
	
	html_file += ' <td width="200" colspan="5">Average</td>\n'	# All Avg Stats
	html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider

	html_file += ' <td width="160" colspan="4">Stars</td>\n'		# Yel 4-7
	html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider

	html_file += ' <td width="120" colspan="4">Red Stars</td>\n'	# Red 4-7
	html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider

	#html_file += ' <td width="160" colspan="3">Diamonds</td>\n'	# Red 4-7
	#html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider

	html_file += ' <td width="200" colspan="5">ISO</td>\n'			# ISO 1-4,5,6-8,9,10
	html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider

	html_file += ' <td width="240" colspan="6">Gear Tier</td>\n'	# Tier 13-18
	html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider

	html_file += ' <td width="160" colspan="4">T4 Abilities</td>\n'	# Bas/Spc/Ult/Pas
	html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider

	html_file += ' <td width="350" colspan="7">Levels</td>\n'		# <65,66-70,71-75,76-80,81-85,86-90,91-95
	html_file += '</tr>\n'

	# Second Row with subheadings.
	html_file += '<tr>\n'

	# Simplify inclusion of the sort function code
	sort_func = 'class="%s" onclick="sort(%s,\'%s\',2)"' % ("ltbb col", '%s', table_id)

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
	html_file += f' <td {sort_func % 21}>%s</td>\n' % (['4+','0-4'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 22}>%s</td>\n' % (['5+','5'  ][stat_type == 'actual'])
	html_file += f' <td {sort_func % 23}>%s</td>\n' % (['8+','6-8'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 24}>%s</td>\n' % (['9+','9'  ][stat_type == 'actual'])
	html_file += f' <td {sort_func % 25}>%s</td>\n' % (['10','10' ][stat_type == 'actual'])

	# Gear Tiers
	html_file += f' <td {sort_func % 27}>%s</td>\n' % (['13+','13'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 28}>%s</td>\n' % (['14+','14'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 29}>%s</td>\n' % (['15+','15'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 30}>%s</td>\n' % (['16+','16'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 31}>%s</td>\n' % (['17+','17'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 32}>%s</td>\n' % (['18' ,'18'][stat_type == 'actual'])

	# T4 Abilities
	html_file += f' <td {sort_func % 34}>Bas</td>\n'
	html_file += f' <td {sort_func % 35}>Spc</td>\n'
	html_file += f' <td {sort_func % 36}>Ult</td>\n'
	html_file += f' <td {sort_func % 37}>Pas</td>\n'

	# Simplify inclusion of the sort function code
	sort_func = 'class="%s" onclick="sort(%s,\'%s\',2)"' % ("ltbb lvl", '%s', table_id)

	# Level Ranges
	html_file += f' <td {sort_func % 39}>%s</td>\n' % (['70+', '0-74'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 40}>%s</td>\n' % (['75+','75-79'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 41}>%s</td>\n' % (['80+','80-84'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 42}>%s</td>\n' % (['85+','85-89'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 43}>%s</td>\n' % (['90+','90-94'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 44}>%s</td>\n' % (['95+','95-99'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 45}>%s</td>\n' % (['100', '100' ][stat_type == 'actual'])

	html_file += '</tr>\n'
	
	# Start by doing stat analysis.	
	stats = get_roster_stats(alliance_info, stat_type, hist_date)
	
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
			stale_data = member_info['is_stale']

			html_file += '<tr>\n'

			member_url = ' href="https://marvelstrikeforce.com/en/player/%s/characters" target="_blank"' % (alliance_info['members'][member].get('url',''))
			html_file += ' <td class="%s urlb"><a style="text-decoration:none; color:black;"%s>%s</a></td>\n' % (['nblu','ngra'][stale_data], member_url, member)
			
			for key in ['tcp','stp','tcc']:
				html_file += ' <td class="%s">%s</td>\n' % (get_value_color(stats_range[key], member_stats.get(key,0), html_cache, stale_data), f'{member_stats[key]:,}')
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Averages
			for key in ['yel', 'red', 'tier', 'lvl', 'iso']:
				html_file += ' <td class="%s">%s</td>\n' % (get_value_color(stats_range['tot_'+key], member_stats.get('tot_'+key,0), html_cache, stale_data), f'{member_stats.get("tot_"+key, 0) / max(member_stats["tcc"],1):.2f}')
			html_file += ' <td></td>\n' 										# Vertical Divider
			
			# Yellow Stars
			for key in range(4,8):
				html_file += ' <td class="%s">%s</td>\n' % (get_value_color(stats_range['yel'][key], member_stats.get('yel',{}).get(key,0), html_cache, stale_data), member_stats.get('yel',{}).get(key,0))
			html_file += ' <td></td>\n' 										# Vertical Divider                                                            
																																							  
			# Red Stars                                                                                                                                       
			for key in range(4,8):
				html_file += ' <td class="%s">%s</td>\n' % (get_value_color(stats_range['red'][key], member_stats.get('red',{}).get(key,0), html_cache, stale_data), member_stats.get('red',{}).get(key,0))
			html_file += ' <td></td>\n' 										# Vertical Divider                             

			# Diamonds
			#for key in range(1,4):
			#	html_file += ' <td class="%s">%s</td>\n' % (get_value_color(stats_range['dmd'][key], member_stats.get('dmd',{}).get(key,0), html_cache, stale_data), member_stats.get('dmd',{}).get(key,0))
			#html_file += ' <td></td>\n' 										# Vertical Divider                             

			# ISO Levels                                                                                                       
			for key in [4,5,8,9,10]:
				html_file += ' <td class="%s">%s</td>\n' % (get_value_color(stats_range['iso'][key], member_stats.get('iso',{}).get(key,0), html_cache, stale_data), member_stats.get('iso',{}).get(key,0))
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Gear Tiers
			for key in range(13,19):
				html_file += ' <td class="%s">%s</td>\n' % (get_value_color(stats_range['tier'][key], member_stats.get('tier',{}).get(key,0), html_cache, stale_data), member_stats.get('tier',{}).get(key,0))
			html_file += ' <td></td>\n' 										# Vertical Divider

			# T4 Abilities
			for key in ['bas','spc','ult','pas']:
				html_file += ' <td class="%s">%s</td>\n' % (get_value_color(stats_range[key], member_stats.get(key,{}).get(7,0), html_cache, stale_data), member_stats.get(key,{}).get(7,0))
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Level Ranges
			for key in range(70,105,5):
				html_file += ' <td class="%s">%s</td>\n' % (get_value_color(stats_range['lvl'][key], member_stats.get('lvl',{}).get(key,0), html_cache, stale_data), member_stats.get('lvl',{}).get(key,0))

			html_file += '</tr>\n'

	html_file += '</table>\n'

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		
		# Add the progressive form in for the tabbed output as well. :)
		if stat_type == 'actual':
			html_file += add_tab_header('ROSTER ANALYSIS (PROGRESSIVE)')
			html_file += generate_roster_analysis(alliance_info, stat_type='progressive', hist_date=None, html_cache=html_cache)
	
		html_file += '</div>\n'

	return html_file


# STILL NEED TO WORK ON HISTORICAL PRESENTATION. SHOULD USE PROGRESSIVE STAT CALCULATIONS FOR BOTH TO SUCCESSFULLY COMMUNICATE PROGRESS.

@timed(level=3)
def get_roster_stats(alliance_info, stat_type, hist_date=''):
	
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
		recruited_chars = [char for char in char_list if current_rosters[member].get(char,{}).get('power')]

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
@timed(level=3)
def generate_alliance_tab(alliance_info, using_tabs=False, html_cache={}):

	html_file = ''

	# Start by sorting members by TCP.
	alliance_order = sorted(alliance_info['members'], key = lambda x: alliance_info['members'][x].get('tcp',0), reverse=True)
	
	# Build up the list of Alliance Members in the order we will present them.
	member_list =  []
	if alliance_info.get('leader'):
		member_list = [alliance_info.get('leader')]
	
	member_list += [member for member in alliance_order if member in alliance_info.get('captains',[])]
	member_list += [member for member in alliance_order if member not in member_list]

	tot_power = sum([alliance_info['members'][member].get('tcp',0) for member in alliance_info['members']])
	avg_power = int(tot_power/len(alliance_info['members']))

	# See if name includes a color tag.
	alt_color = extract_color(alliance_info['name'])

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file += '<div id="AllianceInfo" class="tcon">\n'

	# Generate a table ID to allow sorting. 
	table_id = make_next_table_id(html_cache) 
	html_file += '<table id="%s" style="background:#222";>\n' % (table_id)

	html_file += '<tr>\n</tr>\n'

	html_file += '<tr style="font-size:18px;color:white;">\n'
	html_file += ' <td colspan="2"><img src="https://assets.marvelstrikeforce.com/www/img/logos/logo-en.png" alt=""></td>\n'
	html_file += ' <td colspan="10" class="alliance_name"%s>%s</td>\n' % (alt_color, alliance_info['name'].upper())
	html_file += ' <td colspan="2"><div style="image-rendering:crisp-edges; transform:scale(1.5);"><img src="https://assets.marvelstrikeforce.com/imgs/ALLIANCEICON_%s.png" alt=""/></div></td>\n' % (alliance_info.get('image','EMBLEM_6_dd63d11b'))
	html_file += '</tr>\n'

	# Simplify inclusion of the sort function code
	sort_func = 'class="%s" onclick="sort(%s,\'%s\',3)"' % ("blub", '%s', table_id)

	# Create the headings for the Alliance Info table.
	html_file += '<tr class="hblu" style="font-size:14pt;position:relative;">\n'
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
		stale_data = member_stats['is_stale']
		
		member_color = ['#B0E0E6','#DCDCDC'][stale_data]

		if member in alliance_info.get('leader',[]):
			member_role = '<a> Leader </a>'
		elif member in alliance_info.get('captains',[]):
			member_role = 'Captain'
			member_color = ['#00BFFF','#A9A9A9'][stale_data]		
		else:
			member_role = 'Member'

		html_file += ' <tr style="background:%s; font-size:22px;">\n' % (member_color)
		html_file += '  <td style="padding:0px;"><img height="45" src="https://assets.marvelstrikeforce.com/imgs/Portrait_%s.png"/></td>\n' % (member_stats.get('image','ShieldDmg_Defense_3dea00f7'))

		member_url = alliance_info['members'][member].get('url','')
		if member_url:
			member_url = ' href="https://marvelstrikeforce.com/en/player/%s/characters" target="_blank"' % (member_url)

		member_discord = alliance_info['members'][member].get('discord','')
		if member_discord:
			member_discord = f'<br><span style="font-size:16px">@{member_discord.get("name","")}</span>'

		html_file += '  <td class="urlb"><span class="bd"><a style="text-decoration:none; color:black;"%s>%s</span>%s</a></td>\n' % (member_url, member, member_discord)
		html_file += '  <td>%s</td>\n' % (member_stats.get('level','n/a'))
		html_file += '  <td>%s</td>\n' % (member_role)
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(tcp_range,   member_stats.get('tcp',0),   html_cache, stale_data), f'{member_stats.get("tcp",0):,}')
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(stp_range,   member_stats.get('stp',0),   html_cache, stale_data), f'{member_stats.get("stp",0):,}')
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color_ext(max(tcc_range)-5, max(tcc_range),   member_stats.get('tcc',0),   html_cache, stale_data), f'{member_stats.get("tcc",0):,}')
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(max_range,   member_stats.get('max',0),   html_cache, stale_data), f'{member_stats.get("max",0):,}')
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color_ext(max(arena_range), min(arena_range), member_stats.get('arena',0), html_cache, stale_data), f'{member_stats.get("arena",0):,}')
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(blitz_range, member_stats.get('blitz',0), html_cache, stale_data), f'{member_stats.get("blitz",0):,}')
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(mvp_range,   member_stats.get('mvp',0),   html_cache, stale_data), f'{member_stats.get("mvp",0):,}')
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(stars_range, member_stats.get('stars',0), html_cache, stale_data), f'{member_stats.get("stars",0):,}')
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(red_range,   member_stats.get('red',0),   html_cache, stale_data), f'{member_stats.get("red",0):,}')

		if 'last_update' in member_stats:
			last_update = datetime.datetime.now() - member_stats['last_update']
			time_color  = get_value_color_ext(4*86400, 0, last_update.total_seconds(), html_cache, stale_data)
			
			if stale_data:
				time_value = f'<b><i> {("Stale. Please re-sync.","EMPTY. Please Sync.")[not member_stats.get("tot_power")]} </i></b><br>%s, %sd ago' % (member_stats['last_update'].strftime('%a, %b %d'), last_update.days)
			else:
				time_value = '%s%s ago<br>%s' % (['',f'{last_update.days} days, '][not last_update.days], str(last_update).split('.')[0], member_stats['last_update'].strftime('%a, %b %d')) 
		else:
			time_color = get_value_color_ext(0, 1, 0, html_cache)
			time_value = 'NEVER<br><b><i>Ask member to sync.</i></b>'
		
		html_file += '  <td class="%s" style="font-size:16px;">%s</td>\n' % (time_color, time_value)
		html_file += ' </tr>\n'


	html_file += '</table>\n'
	
	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file += '</div>\n'

	return html_file


# Generate just the Alliance Tab contents.
@timed(level=3)
def generate_by_char_tab(alliance_info, table_format={}, using_tabs=False, html_cache={}):

	html_file = ''

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file += '<div id="ByChar" class="tcon">\n'

	# Get the list of usable characters for analysis.
	char_list = sorted(html_cache.get('chars',{}))
	if not char_list:
		char_list = table_format.get('inc_chars',get_char_list(alliance_info))

	table = {}

	# Why aren't we getting any info from the command line?
	
	# Always include history if it's available.
	table_format['inc_hist'] = True

	# Get the hist_date if historical information was requested.
	hist_date = get_hist_date(alliance_info, table_format)

	# Get keys using the lookup. If undefined, 
	table_format['inc_keys']  = ['power','lvl','iso','tier','yel','red','abil']
	table_format['inc_class'] = True
	
	#if not sort_by specified
	table_format['sort_by'] = 'stp'

	meta_chars, other_chars = get_meta_other_chars(alliance_info, table, {'meta':[char_list]}, table_format)
	
	# Iterate through the list of character, generating the same detailed information for each character.
	# Maybe we can pass in an explicit Char List or Trait List to generate the Chars instead of ALL. 
	# This way we could pass in just the characters actually mentioned on the report. 

	for char in char_list:
		
		# Just specify the Character name for the table title
		table_lbl = translate_name(char).upper()

		# Build stp_list to simplify sort_by='stp'.
		stp_list = get_stp_list(alliance_info, [char])

		# Get the list of Alliance Members 
		member_list = get_player_list(alliance_info)

		# Let's make it easy on ourselves. Start every section the same way.
		html_file += '<table>\n <tr>\n  <td>\n'

		# By default, no section-specific formatting
		section={}

		# Generate the left table with current stats.
		html_file += generate_table(alliance_info, table, section, table_format, [char], [member_list], table_lbl, stp_list, html_cache, None, linked_hist=True)

		# Small space between the two tables.
		html_file += '  </td>\n  <td><br></td>\n  <td>\n'

		# Generate the right table with historical information if available.
		if hist_date:
			table_lbl += f'<br><span class="sub">Changes since:<br>{hist_date}</span>'
			html_file += generate_table(alliance_info, table, section, table_format, [char], [member_list], table_lbl, stp_list, html_cache, hist_date, linked_hist=True)
			
		# End every section the same way.
		html_file += '  </td>\n </tr>\n</table>\n'

		# If not the final section, add a divider row. 
		if char_list.index(char) != len(char_list)-1:
			html_file += '    <p></p>\n'

	# After Lane content is done, close the div for the Tab implementation.
	if using_tabs:
		html_file += '</div>\n'

	return html_file


@timed
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


# Insert dividers based on the type of team. 
@timed
def insert_dividers(strike_teams, raid_type):

	# Start with a copy, just to be safe.
	strike_teams = copy.deepcopy(strike_teams)

	for team in strike_teams:

		# Use 2-3-3 lanes if Incursion 1.x.
		if raid_type == 'incur':
			if len(team) > 2:
				team.insert(2,'----')
			if len(team) > 6:
				team.insert(6,'----')

		# Use 5/3 split for Sort by STP within Strike Teams.
		elif raid_type == '53':
			if len(team) > 5:
				team.insert(5,'----')

		# Put a divider in the middle to reflect left/right symmetry of raids.
		else:
			if len(team) > 4:
				team.insert(4,'----')

	return strike_teams
	

# Translate value to a color from the Heat Map gradient.
def get_value_color(val_range, value, html_cache, stale_data, stat='power', under_min=False, hist_date=''):
	min_val = min(val_range) if val_range else 0
	max_val = max(val_range) if val_range else 0

	if not min_val:
		new_range = [x for x in val_range if x != 0]
		if new_range:
			min_val = min(new_range)
	
	return get_value_color_ext(min_val, max_val, value, html_cache, stale_data, stat, under_min, hist_date)


def get_value_color_ext(min, max, value, html_cache, stale_data=False, stat='power', under_min=False, hist_date=''):
	
	# Special treatment for the '0' fields. 
	if not value:
		return 'hist'

	max_colors  = len(color_scale)-1
	
	#Tweak gradients for Tier, ISO, Level, and Red/Yellow stars.
	if stat=='iso':
		if not hist_date:
			scaled_value = int(((value**3)/10**3) * max_colors)
		else:
			scaled_value = [int((0.6 + 0.4 * ((value**3)/10**3)) * max_colors),0][value<0]
	elif stat=='tier':
		if not hist_date and value <= 16:
			scaled_value = int(((value**2)/16**2)*0.50 * max_colors)
		elif not hist_date:
			scaled_value = int((0.65 + 0.35 * ((value-17)/2)) * max_colors)
		else:
			scaled_value = int((0.60 + 0.40 * ((value**2)/19**2)) * max_colors)
	elif stat=='lvl':
		if not hist_date and value <= 85:
			scaled_value = int(((value**2)/85**2)*0.50 * max_colors)
		elif not hist_date:
			scaled_value = int((0.65 + 0.35 * ((value-85)/20)) * max_colors)
		else:
			scaled_value = int((0.60 + 0.40 * ((value**2)/100**2)) * max_colors)
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
	if under_min and not hist_date:
		color = darken(color)

	# If data is more than a week old, make grayscale to indicate stale data.
	if stale_data:
		color = grayscale(color)

	# Cache this color away for class definitions later.
	return make_next_color_id(html_cache, color)


# Generate Labels for each section from either label info or trait names.
def get_section_label(section):
	
	# If a label specified, use it.
	if section.get('label'):
		return section.get('label','').replace('-<br>','').replace('<br>',' ')

	# Otherwise, just join the translated traits.
	return ', '.join([translate_name(trait) for trait in section['traits']]).replace('-<br>','').replace('<br>',' ')



# Quick and dirty translation to shorter or better names.
def translate_name(value):
	TRANSLATE_NAME = {	"Avenger": "Avengers",
						"AForce": "A-Force",
						"Asgard": "Asgardians",
						"Astonishing": "Astonishing<br>X-Men",
						"BionicAvenger": "Bionic<br>Avengers",
						"BlackOrder": "Black<br>Order",
						"Brotherhood": "B'Hood",
						"DarkHunter": "Dark<br>Hunters",
						"Defender": "Defenders",
						"Eternal": "Eternals",
						"FantasticFour": "Fantastic<br>Four",
						"HeroesForHire": "H4H",
						"Hydra Armored Guard": "Hydra Arm Guard",
						"InfinityWatch": "Infinity<br>Watch",
						"Invader": "Invaders",
						"OutOfTime": "Out of Time",
						"MastersOfEvil": "Masters<br>Of Evil",
						"Mercenary": "Mercs",
						"NewAvenger": "New<br>Avengers",
						"NewWarrior": "New<br>Warriors",
						"Pegasus": "PEGASUS",
						"PowerArmor": "Power Armor",
						"PymTech": "Pym Tech",
						"Ravager": "Ravagers",
						"SecretAvenger": "Secret<br>Avengers",
						"SecretDefender": "Secret<br>Defenders",
						"SinisterSix": "Sinister<br>Six",
						"SpiderVerse": "Spiders",
						"SuperiorSix": "Superior<br>Six",
						"Symbiote": "Symbiotes",
						"TangledWeb": "Tangled<br>Web",
						"WarDog": "War Dogs",
						"Wave1Avenger": "Wave 1<br>Avengers",
						"WeaponX": "Weapon X",
						"WebWarrior": "Web<br>Warriors",
						"XFactor": "X-Factor",
						"Xforce": "X-Force",
						"Xmen": "X-Men",
						"XTreme": "X-Treme X-Men",
						"YoungAvenger": "Young<br>Avengers",
						"A.I.M. Monstrosity":"A.I.M.<br>Monstrosity",
						"A.I.M. Researcher":"A.I.M.<br>Researcher",
						"Agatha Harkness":"Agatha<br>Harkness",
						"Black Panther (1MM)":"Black<br>Panther (1MM)",
						"Captain America":"Captain<br>America",
						"Captain America (Sam)":"Capt. America<br>(Sam)",
						"Captain America (WWII)":"Capt. America<br>(WWII)",
						"Doctor Octopus":"Doctor<br>Octopus",
						"Doctor Strange":"Doctor<br>Strange",
						"Doctor Voodoo":"Doctor<br>Voodoo",
						"Elsa Bloodstone":"Elsa<br>Bloodstone",
						"Ghost Rider (Robbie)":"Ghost Rider<br>(Robbie)",
						"Green Goblin (Classic)":"Green Goblin<br>(Classic)",
						"Hand Blademaster":"Hand<br>Blademaster",
						"Hand Sorceress":"Hand<br>Sorceress",
						"Hydra Armored Guard":"Hydra<br>Arm Guard",
						"Hydra Grenadier":"Hydra<br>Grenadier",
						"Hydra Rifle Trooper":"Hydra<br>Rifle Trooper",
						"Hydra Scientist":"Hydra<br>Scientist",
						"Invisible Woman":"Invisible<br>Woman",
						"Iron Man (Infinity War)":"Iron Man<br>(Infinity War)",
						"Iron Man (Zombie)":"Iron Man<br>(Zombie)",
						"Ironheart (MKII)": "Ironheart<br>(MKII)",
						"Juggernaut (Zombie)":"Juggernaut<br>(Zombie)",
						"Kang the Conqueror":"Kang<br>the Conqueror",
						"Korath the Pursuer":"Korath<br>the Pursuer",
						"Kraven the Hunter":"Kraven<br>the Hunter",
						"Kree Royal Guard":"Kree<br>Royal Guard",
						"Lady Deathstrike":"Lady<br>Deathstrike",
						"Madelyne Pryor":"Madelyne<br>Pryor",
						"Mercenary Lieutenant":"Mercenary<br>Lieutenant",
						"Mercenary Riot Guard":"Mercenary<br>Riot Guard",
						"Mercenary Sniper":"Mercenary<br>Sniper",
						"Mercenary Soldier":"Mercenary<br>Soldier",
						"Mister Fantastic":"Mister<br>Fantastic",
						"Mister Negative":"Mister<br>Negative",
						"Mister Sinister":"Mister<br>Sinister",
						"Ms. Marvel (Hard Light)": "Ms. Marvel<br>(Hard Light)",
						"Proxima Midnight":"Proxima<br>Midnight",
						"Ravager Boomer":"Ravager<br>Boomer",
						"Ravager Bruiser":"Ravager<br>Bruiser",
						"Ravager Stitcher":"Ravager<br>Stitcher",
						"Rocket Raccoon":"Rocket<br>Raccoon",
						"Ronan the Accuser":"Ronan<br>the Accuser",
						"S.H.I.E.L.D. Assault":"S.H.I.E.L.D.<br>Assault",
						"S.H.I.E.L.D. Medic":"S.H.I.E.L.D.<br>Medic",
						"S.H.I.E.L.D. Operative":"S.H.I.E.L.D.<br>Operative",
						"S.H.I.E.L.D. Security":"S.H.I.E.L.D.<br>Security",
						"S.H.I.E.L.D. Trooper":"S.H.I.E.L.D.<br>Trooper",
						"Scientist Supreme":"Scientist<br>Supreme",
						"Spider-Man (Big Time)":"Spider-Man<br>(Big Time)",
						"Spider-Man (Miles)":"Spider-Man<br>(Miles)",
						"Spider-Man (Noir)":"Spider-Man<br>(Noir)",
						"Spider-Man (Symbiote)":"Spider-Man<br>(Symbiote)",
						"Spider-Man 2099":"Spider-Man<br>2099",
						"Star-Lord (Annihilation)":"Star-Lord<br>(Annihilation)",
						"Star-Lord (T'Challa)":"Star-Lord<br>(T'Challa)",
						"Strange (Heartless)":"Strange<br>(Heartless)",
						"Thor (Infinity War)":"Thor<br>(Infinity War)",
						}
	return TRANSLATE_NAME.get(value,value)