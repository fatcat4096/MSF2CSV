#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_html.py
Takes the processed alliance / roster data and generate readable output to spec.  
"""

# By_Char data should use same hist_date as provided in inc_hist or inline_hist

# Team Report Summary suggestions
# * Include graphics for teams in Team Report Summary?
# * Better team name formatting? 
# * Can we avoid using deepcopy for everything?
# * Allow summary_keys to be specified
# * Change last column to TCP? Sort by TCP?
# * Dim if <5 available? 
# * Dim member if <5 available for any entry?

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

				# Find out whether we're including Team Power Summary.
				inc_summary  = get_table_value(table_format, table, key='inc_summary')
				only_summary = get_table_value(table_format, table, key='only_summary')

				if only_summary:
					tab_name = tab_name.replace('INFO','SUMMARY')

				# Include the label for the lane plus the requested sections.
				html_file = get_tab_header(tab_name)	

				# Insert summary if requested, but only if generating entire lane.
				if only_summary or (inc_summary and not only_section and sections_per == len(lane)):

					# Team List == full lane, means we will report on every entry.
					team_list = [get_section_label(section) for section in lane]

					# Calculate strike teams
					strike_teams = get_strike_teams(alliance_info, table, table_format)

					# Add the table to the top!
					html_file += generate_team_power_summary(alliance_info, table, [lane], table_format, team_list, strike_teams, hist_date, html_cache=html_cache)

				# If not only summary, generate the rest of the lane.
				section_num = ''
				if not only_summary:

					# Process the lane, section by section.
					sections = lane[section_idx:section_idx+sections_per]
					for section in sections:
						html_file += generate_lanes(alliance_info, table, [[section]], table_format, html_cache=html_cache)

						# Include the history information if we have it and can include it.
						if hist_date:
							html_file += get_tab_header(get_hist_tab(hist_date, table_format))	
							html_file += generate_lanes(alliance_info, table, [[section]], table_format, hist_date, html_cache=html_cache)

					# Wrap it up and add it to the collection.
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
		
		hist_date = get_hist_date(alliance_info, table_format)
		
		# Generate the appropriate midsection, either Roster Analysis...
		if output == 'roster_analysis':
			html_file += generate_roster_analysis(alliance_info, hist_date=hist_date, html_cache=html_cache)

		# ...or Alliance Info. Don't use the tab labels for Alliance Info
		elif output == 'alliance_info':
			html_file += generate_alliance_tab(alliance_info, hist_date=hist_date, html_cache=html_cache)

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
	html_file += generate_roster_analysis(alliance_info, using_tabs=True, hist_date=hist_date, html_cache=html_cache)
	html_file += generate_alliance_tab   (alliance_info, using_tabs=True, hist_date=hist_date, html_cache=html_cache)
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
def get_tab_header(content):
	return '<table>\n<tr><td class="tlnk" style="width:100%;">'+content+'</td></tr>\n</table>'



# Generate the contents for each lane.
@timed(level=3)
def generate_lanes(alliance_info, table, lanes, table_format, hist_date=None, using_tabs=False, html_cache={}):

	html_file = ''

	# Calculate strike teams
	strike_teams = get_strike_teams(alliance_info, table, table_format)

	# Values do not change from section to section
	only_team    = get_table_value(table_format, table, key='only_team')
	only_members = get_table_value(table_format, table, key='only_members')

	# Special handling required if inline_hist.
	inline_hist = get_table_value(table_format, table, key='inline_hist')

	# Find out whether we're including Team Power Summary at top.
	inc_summary = get_table_value(table_format, table, key='inc_summary')

	# Iterate through all the lanes. Showing tables for each section. 
	for lane in lanes:

		# Display each lane in a separate tab.
		divider_id = ['Hist','Lane'][not hist_date] + str(lanes.index(lane)+1)
		
		# Only include Dividers if using as part of a multi-tab document
		if using_tabs:
			html_file += '<div id="%s" class="tcon">\n' % (divider_id)

		# Insert the team_power_summary at the top if requested.
		# Only use if using_tabs because generate_lanes() is called MULTIPLE TIMES if not in a tabbed environment
		
		if inc_summary and using_tabs:

			# Team List == full lane, means we will report on every entry.
			team_list = [get_section_label(section) for section in lane]

			# Add the table to the top!
			html_file += generate_team_power_summary(alliance_info, table, [lane], table_format, team_list, strike_teams, hist_date, html_cache=html_cache)

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
			if other_chars and not meta_chars and len(other_chars) <= 5 and span_data and not (only_team or only_members):

				# If strike_team is just the entire player list, break it up into 3 groups.
				if len(strike_teams) == 1 or only_team == 0:
					
					# Need to do a new sort for strike_teams if sort_by is STP.
					sort_by = get_table_value(table_format, table, key='sort_by')
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



@timed(level=3)
def generate_team_power_summary(alliance_info, table, lanes, table_format, team_list, strike_teams, hist_date=None, html_cache={}):

	html_file = ''

	# Likely need to deep copy here before moving on -- we're adding elements to the existing dicts.
	table         = copy.deepcopy(table)
	alliance_info = copy.deepcopy(alliance_info)
	table_format  = copy.deepcopy(table_format)
	
	# Generate a separate table for each lane. 
	for lane in lanes:

		# Pre-process the information for the lane, calculating STPs, num_avail, and rank.
		for section in lane:
			section_label = get_section_label(section)
			if section_label in team_list or 1:
			
				# Filter down the character list to only those in this section
				meta_chars,other_chars = get_meta_other_chars(alliance_info, table, section, table_format)

				# Get the STPs for this team. 
				stp_list = get_stp_list(alliance_info, meta_chars+other_chars, hist_date)

				# Get the rank for this team. 
				
				for member in alliance_info['members']:
					if 'processed_chars' in alliance_info['members'][member]:

						# Pull it from the calculated STP list.
						stp = stp_list[hist_date][member]

						# Get the num_avail for this team. 
						avail = len([char for char in table.get('under_min',{}).get(member,{}) if not table.get('under_min',{}).get(member,{}).get(char)])
						rank  = get_player_list(alliance_info, sort_by='stp', stp_list=stp_list).index(member)+1
					
						alliance_info['members'][member]['processed_chars'][section_label] = {'power':stp, 'avail':avail, 'rank':rank}

		stp_list = get_stp_list(alliance_info, [get_section_label(section) for section in lane], hist_date)

		# Let's make it easy on ourselves. Start every section the same way.
		html_file += '<table>\n <tr>\n  <td>\n'

		section = {}
		
		table_lbl = 'Team<br>Power<br>Summary'
		table_format['inc_keys'] = ['power','avail']
		table_format['sort_by'] = 'stp'
		
		team_power_summary = True
		
		# Generate a table.
		html_file += generate_table(alliance_info, table, section, table_format, team_list, strike_teams, table_lbl, stp_list, html_cache, hist_date, team_power_summary=team_power_summary)
		
		# End every section the same way.
		html_file += '  </td>\n </tr>\n</table>\n'

	return html_file



# Generate individual tables for Meta/Other chars for each raid section.
@timed(level=3)
def generate_table(alliance_info, table, section, table_format, char_list, strike_teams, table_lbl, stp_list, html_cache={}, hist_date=None, linked_hist=None, team_power_summary=False):

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
	player_list = get_player_list (alliance_info, sort_by, stp_list, table)

	# If there are no players in this table, don't generate a table.
	using_players = [player for player in sum(strike_teams, []) if player in player_list]
	if not using_players:
		return ''
		
	# See if we need to pare the included characters even further.
	using_chars = char_list[:]

	# Find out whether inline history has been requested for this report.
	inline_hist = get_table_value(table_format, table, section, key='inline_hist')

	# Pare any missing heroes if these aren't Meta entries.
	if 'META' not in table_lbl and len(using_chars) > 5 and not team_power_summary:
		using_chars = remove_min_iso_tier(alliance_info, table_format, table, section, using_players, using_chars)			

		# if inline_hist, only want heroes that have actually been changed.
		if inline_hist:

			# min_change_filter specifies how much change is required to be considered 'intentionally built'. 
			min_change_filter = get_table_value(table_format, table, section, key='min_change_filter', default=0)

			# If a value is specified, strip any character that hasn't been built at least that amount over time.
			if min_change_filter:
				filtered_chars = []

				for char in using_chars:
					for player in using_players:

						# Get current power for this toon.
						curr_power = find_value_or_diff(alliance_info, player, char, 'power')[0]

						# If not summoned yet, move on to next player.
						if not curr_power:
							continue

						# Get historical power for this toon.
						hist_diff = find_value_or_diff(alliance_info, player, char, 'power', hist_date=inline_hist)[0]
						
						# If relevant growth, include and move to next char
						if hist_diff/curr_power > min_change_filter:
							filtered_chars.append(char)
							break

				using_chars = filtered_chars

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

	# Automate the line_wrap selection.
	wrap_after = 12
	lines_used  = 1

	# Calculate an optimal number of lines to wrap to.
	while len(using_chars) > wrap_after * lines_used:
		lines_used += 1
		wrap_after = int( (wrap_after * 4 / 3) + 0.49)

	# Calculate the line_wrap to best fill this number of lines
	line_wrap = round(len(using_chars)/lines_used + 0.49)
	
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
		inc_rank  = get_table_value(table_format, table, section, key='inc_rank',  default=False) and 'OTHERS' not in table_lbl
		inc_class = get_table_value(table_format, table, section, key='inc_class', default=False) and not hist_date

		# Include a column for "# Pos" info if requested.
		if inc_rank:
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

			# Do special things if this is the team power report.
			if team_power_summary:
				html_file += f'     <td colspan="{num_cols}"><div class="summ">{translate_name(char).replace(", ","<br>")}</div></td>\n'
				
			else:
				url = f"https://assets.marvelstrikeforce.com/imgs/Portrait_{alliance_info['portraits'].get(char,'')}.png"

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
				
				# If inc_dividers is '53', this divider is a little different. Go ahead and add it back in after sorting.
				inc_dividers = get_table_value(table_format, table, section, key='inc_dividers', default='other')
				if inc_dividers == '53':
						strike_team = insert_dividers([strike_team], inc_dividers)[0]

			# BUILD A BLOCK WITH THE DATA FOR EACH ROW. #########################
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
				hist_list = [hist_date]
				if inline_hist:
					hist_list.append(inline_hist)
					
				for use_hist_date in hist_list:

					# Find min/max for meta/strongest team power in the Alliance
					# This will be used for color calculation for the Team Power column.
					stp_range = [stp_list[use_hist_date][player_name] for player_name in player_list]

					# Standard Name field content. 
					name_field = alliance_info['members'][player_name].get('display_name',player_name).replace('Commander','Cmdr.')

					# If inline_hist was requested, add content to the Name field for the second line and make this and several other fields span both lines.
					rowspan = ''
					if inline_hist and not use_hist_date:
						name_field = f'{name_field}<br><span style="font-weight:normal;"><i>(since {inline_hist.strftime("%m/%d/%y")})</i></span>'
						rowspan = '" rowspan="2'

					# Player Name, then relevant stats for each character.
					st_html += '    <tr%s>\n' % [' class="hist"',''][not use_hist_date]

					inline_hist_row = inline_hist and use_hist_date

					# Skip this cell if on Inline Hist line.
					if not inline_hist_row:
						st_html += '     <td class="%s">%s</td>\n' % ([name_cell, name_alt, name_cell_dim, name_alt_dim][alt_color+2*not_ready]+rowspan, name_field)

					# If Member's roster has grown more than 1% from last sync or hasn't synced in more than a week, indicate it is STALE DATA via Grayscale output.
					stale_data = alliance_info['members'][player_name]['is_stale']

					# Include "# Pos" info if requested.
					if inc_rank and not inline_hist_row:
						rank_num = get_player_list(alliance_info, sort_by='stp', stp_list=stp_list).index(player_name)+1
						st_html += '     <td class="bd %s">%s</td>\n' % (get_value_color_ext(25, 1, rank_num, html_cache, stale_data)+rowspan, rank_num)

					# Include "# Avail" info if requested.
					if inc_avail and not inline_hist_row:
						st_html += '     <td class="bd %s">%s</td>\n' % (get_value_color_ext(0, max_avail, [num_avail,-1][not_ready], html_cache, stale_data)+rowspan, num_avail)

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
								if key=='red' and key_val>7:
									field_value = f'<span class="dmd">{key_val-7}&#x1F48E;</span>'
								else:
									field_value = f'{key_val:+}' if use_hist_date else f'{key_val}'

							else:
								field_value = '-'

							st_html += '     <td%s>%s%s</td>\n' % (style, field_value, ['',other_diffs][need_tt])

						# Include ISO class information if requested
						if inc_class and not inline_hist_row:

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
								st_html += f'     <td class="{iso_class[:4]} tt {field_color+rowspan}">{tool_tip}</td>\n'
							else:
								st_html += f'     <td class="hist{rowspan}">-</td>\n'

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

			# FINALLY WRITE THE HEADING ROW AND PUT IT ALL TOGETHER #########
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
			if inc_rank:
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
					html_file += f'     <td class="{button_hover}{width}" %s>%s</td>\n' % (sort_func % col_idx, {'iso':'ISO','stp':'STP'}.get(key,key.title()))
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
def generate_roster_analysis(alliance_info, using_tabs=False, hist_date=None, html_cache={}):

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file = '<div id="RosterAnalysis" class="tcon">\n'
	else:
		html_file = get_tab_header('ROSTER ANALYSIS (ACTUAL)')
	html_file += generate_analysis_table(alliance_info, stat_type='actual', html_cache=html_cache)

	# Add the progressive form in as well. :)
	html_file += get_tab_header('ROSTER ANALYSIS (PROGRESSIVE)')
	html_file += generate_analysis_table(alliance_info, stat_type='progressive', html_cache=html_cache)
	
	# Add the historical form in if hist_date is available.
	if hist_date:
		html_file += get_tab_header(f'ROSTER ANALYSIS (SINCE {hist_date.strftime("%m/%d/%y")})')
		html_file += generate_analysis_table(alliance_info, stat_type='progressive', hist_date=hist_date, html_cache=html_cache)

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file += '</div>\n'

	return html_file
		


def generate_analysis_table(alliance_info, stat_type='actual', hist_date=None, html_cache={}):

	# Conditionally include Diamonds columns.
	DIAMONDS_ENABLED = True

	# Generate the header for the Roster Analysis table
	html_file = generate_analysis_header(stat_type, DIAMONDS_ENABLED, html_cache)

	# Start by doing stat analysis.	
	stats = get_roster_stats(alliance_info, stat_type, hist_date)

	# Format the analyzed data into a table.
	html_file += generate_analysis_body(alliance_info, stats, DIAMONDS_ENABLED, hist_date, html_cache)

	return html_file



def generate_analysis_header(stat_type, DIAMONDS_ENABLED, html_cache):

	# Generate a table ID to allow sorting. 
	table_id = make_next_table_id(html_cache) 
	html_file = '<table id="%s">\n' % (table_id)

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

	# Conditionally include Diamonds columns.
	if DIAMONDS_ENABLED:
		html_file += ' <td width="160" colspan="3">Diamonds</td>\n'	# Red 4-7
		html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider

	html_file += ' <td width="200" colspan="6">ISO</td>\n'			# ISO 1-4,5,6-8,9,10
	html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider

	html_file += ' <td width="240" colspan="7">Gear Tier</td>\n'	# Tier 13-19
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

	# Conditionally include Diamonds columns.
	if DIAMONDS_ENABLED:
		html_file += f' <td {sort_func % 21}>1&#x1F48E;</td>\n'
		html_file += f' <td {sort_func % 22}>2&#x1F48E;</td>\n'
		html_file += f' <td {sort_func % 23}>3&#x1F48E;</td>\n'

	# Simplify inclusion of the sort function code
	sort_func = 'class="%s" onclick="sort(%s+%s,\'%s\',2)"' % ("ltbb col", '%s', DIAMONDS_ENABLED*4, table_id)

	# ISO Levels
	html_file += f' <td {sort_func % 21}>%s</td>\n' % (['5+', '0-5' ][stat_type == 'actual'])
	html_file += f' <td {sort_func % 22}>%s</td>\n' % (['9+', '6-9' ][stat_type == 'actual'])
	html_file += f' <td {sort_func % 23}>%s</td>\n' % (['10+','10'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 24}>%s</td>\n' % (['11+','11'  ][stat_type == 'actual'])
	html_file += f' <td {sort_func % 25}>%s</td>\n' % (['12+','12'  ][stat_type == 'actual'])
	html_file += f' <td {sort_func % 26}>%s</td>\n' % (['13', '13'  ][stat_type == 'actual'])

	# Gear Tiers
	html_file += f' <td {sort_func % 28}>%s</td>\n' % (['13+','13'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 29}>%s</td>\n' % (['14+','14'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 30}>%s</td>\n' % (['15+','15'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 31}>%s</td>\n' % (['16+','16'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 32}>%s</td>\n' % (['17+','17'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 33}>%s</td>\n' % (['18+','18'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 34}>%s</td>\n' % (['19' ,'19'][stat_type == 'actual'])

	# T4 Abilities
	html_file += f' <td {sort_func % 36}>Bas</td>\n'
	html_file += f' <td {sort_func % 37}>Spc</td>\n'
	html_file += f' <td {sort_func % 38}>Ult</td>\n'
	html_file += f' <td {sort_func % 39}>Pas</td>\n'

	# Simplify inclusion of the sort function code
	sort_func = 'class="%s" onclick="sort(%s+%s,\'%s\',2)"' % ("ltbb lvl", '%s', DIAMONDS_ENABLED*4, table_id)

	# Level Ranges
	html_file += f' <td {sort_func % 41}>%s</td>\n' % (['70+', '0-74'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 42}>%s</td>\n' % (['75+','75-79'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 43}>%s</td>\n' % (['80+','80-84'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 44}>%s</td>\n' % (['85+','85-89'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 45}>%s</td>\n' % (['90+','90-94'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 46}>%s</td>\n' % (['95+','95-99'][stat_type == 'actual'])
	html_file += f' <td {sort_func % 47}>%s</td>\n' % (['100', '100' ][stat_type == 'actual'])

	html_file += '</tr>\n'
	
	return html_file
	


def generate_analysis_body(alliance_info, stats, DIAMONDS_ENABLED, hist_date, html_cache):
	
	html_file = ''

	#
	# BRINGING IN HIST_DATE FOR TWO REASONS
	# * PASS IN ON get_value_color() SO IT KNOWS TO BE GENEROUS IN COLOR SCALING.
	# * USE ITS PRESENCE TO TRIGGER + INDICATIONS IN F-STRING FORMATTING
	#

	# Get a sorted list of members to use for this table output.
	member_list = sorted(alliance_info['members'].keys(), key = lambda x: alliance_info['members'][x].get('tcp',0), reverse=True)

	# Iterate through each row for members in the table.
	for member in member_list:
			member_info = alliance_info['members'][member]
			member_stats = stats.get(member,{})
			stats_range  = stats['range']

			# If Member's roster has grown more than 1% from last sync or hasn't synced in more than a week, indicate it is STALE DATA via Grayscale output.
			stale_data = member_info['is_stale']

			html_file += '<tr>\n'

			member_url = ''
			if member_info.get('avail'):
				member_url = f' href="https://marvelstrikeforce.com/en/member/{member_info.get("url")}/characters" target="_blank"'
		
			html_file += ' <td class="%s urlb"><a style="text-decoration:none; color:black;"%s>%s</a></td>\n' % (['nblu','ngra'][stale_data], member_url, member_info.get('display_name',member))
			
			for key in ['tcp','stp','tcc']:
				html_file += ' <td class="%s">%s</td>\n' % (get_value_color(stats_range[key], member_stats.get(key,0), html_cache, stale_data, hist_date=hist_date), f'{member_stats.get(key,0):,}')
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Averages
			for key in ['yel', 'red', 'tier', 'lvl', 'iso']:
				html_file += ' <td class="%s">%s</td>\n' % (get_value_color(stats_range['tot_'+key], member_stats.get('tot_'+key,0), html_cache, stale_data, hist_date=hist_date), f'{member_stats.get("tot_"+key, 0) / max(member_stats.get("tcc",0),1):.2f}')
			html_file += ' <td></td>\n' 										# Vertical Divider
			
			# Yellow Stars
			for key in range(4,8):
				html_file += ' <td class="%s">%s</td>\n' % (get_value_color(stats_range['yel'][key], member_stats.get('yel',{}).get(key,0), html_cache, stale_data, hist_date=hist_date), member_stats.get('yel',{}).get(key,0))
			html_file += ' <td></td>\n' 										# Vertical Divider                                                            
																																							  
			# Red Stars                                                                                                                                       
			for key in range(4,8):
				html_file += ' <td class="%s">%s</td>\n' % (get_value_color(stats_range['red'][key], member_stats.get('red',{}).get(key,0), html_cache, stale_data, hist_date=hist_date), member_stats.get('red',{}).get(key,0))
			html_file += ' <td></td>\n' 										# Vertical Divider                             

			# Conditionally include Diamonds columns.
			if DIAMONDS_ENABLED:
				for key in range(1,4):
					html_file += ' <td class="%s">%s</td>\n' % (get_value_color(stats_range['dmd'][key], member_stats.get('dmd',{}).get(key,0), html_cache, stale_data, hist_date=hist_date), member_stats.get('dmd',{}).get(key,0))
				html_file += ' <td></td>\n' 									# Vertical Divider                             

			# ISO Levels                                                                                                       
			for key in [5,9,10,11,12,13]:
				html_file += ' <td class="%s">%s</td>\n' % (get_value_color(stats_range['iso'][key], member_stats.get('iso',{}).get(key,0), html_cache, stale_data, hist_date=hist_date), member_stats.get('iso',{}).get(key,0))
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Gear Tiers
			for key in range(13,20):
				html_file += ' <td class="%s">%s</td>\n' % (get_value_color(stats_range['tier'][key], member_stats.get('tier',{}).get(key,0), html_cache, stale_data, hist_date=hist_date), member_stats.get('tier',{}).get(key,0))
			html_file += ' <td></td>\n' 										# Vertical Divider

			# T4 Abilities
			for key in ['bas','spc','ult','pas']:
				html_file += ' <td class="%s">%s</td>\n' % (get_value_color(stats_range[key], member_stats.get(key,{}).get(7,0), html_cache, stale_data, hist_date=hist_date), member_stats.get(key,{}).get(7,0))
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Level Ranges
			for key in range(70,105,5):
				html_file += ' <td class="%s">%s</td>\n' % (get_value_color(stats_range['lvl'][key], member_stats.get('lvl',{}).get(key,0), html_cache, stale_data, hist_date=hist_date), member_stats.get('lvl',{}).get(key,0))

			html_file += '</tr>\n'

	html_file += '</table>\n'

	return html_file



# STILL NEED TO WORK ON HISTORICAL PRESENTATION. SHOULD USE PROGRESSIVE STAT CALCULATIONS FOR BOTH TO SUCCESSFULLY COMMUNICATE PROGRESS.

@timed(level=3)
def get_roster_stats(alliance_info, stat_type, hist_date=''):
	
	stats = {}
	
	hist_info = alliance_info.get('hist',{})
	
	current_rosters = copy.deepcopy(hist_info[max(hist_info)])
	
	# Get the list of Alliance Members 
	member_list = list(alliance_info.get('members',{}))

	# Get the list of usable characters for analysis.
	char_list = get_char_list(alliance_info)
	
	# Start by doing stat analysis.	
	for member in member_list:
	
		# Get a little closer to our work.
		member_stats = stats.setdefault(member,{})
		
		# Don't include stats from heroes that haven't been recruited yet.
		recruited_chars = [char for char in char_list if current_rosters.get(member,{}).get(char,{}).get('power')]

		# Loop through every char
		for char in recruited_chars:
		
			# Get a little closer to our work.
			char_stats = current_rosters[member][char]

			# Use for Total / Average # columns -- do this BEFORE normalizing data.
			for key in ['yel','red','dmd','tier','lvl','iso']:
				member_stats['tot_'+key] = member_stats.get('tot_'+key,0) + char_stats[key]

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

			# Gather 0-5 into 5.
			if char_stats['iso'] < 5 and stat_type == 'actual':
				char_stats['iso'] = 5
			# Gather 6-9 into 9.
			elif char_stats['iso'] in range(6,10) and stat_type == 'actual':
				char_stats['iso'] = 9

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
	for key in range(5,14):
		stats['range']['iso'][key] = [stats[member].get('iso',{}).get(key,0) for member in member_list]

	# Gear Tiers
	for key in range(13,20):
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
def generate_alliance_tab(alliance_info, using_tabs=False, hist_date=None, html_cache={}):

	html_file = ''
	
	# Conditionally include Arena/Blitz columns.
	ARENA_BLITZ_ENABLED = False

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
	html_file += ' <td colspan="%s" class="alliance_name"%s>%s</td>\n' % (8+ 2*ARENA_BLITZ_ENABLED, alt_color, alliance_info['name'].upper())
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

	# Conditionally include columns.
	if ARENA_BLITZ_ENABLED:
		html_file += f' <td width="110" {sort_func % 8}>Arena<br>Rank</td>\n'
		html_file += f' <td width="110" {sort_func % 9}>Blitz<br>Wins</td>\n'

	# Change the sort routine depending on whether Arena/Blitz columns present.
	sort_func = 'class="%s" onclick="sort(%s+%s,\'%s\',3)"' % ("blub", '%s', ARENA_BLITZ_ENABLED*2, table_id)

	html_file += f' <td width="110" {sort_func % 8}>War<br>MVP</td>\n'
	html_file += f' <td width="110" {sort_func % 9}>Total<br>Stars</td>\n'
	html_file += f' <td width="110" {sort_func % 10}>Total<br>Red</td>\n'
	html_file += f' <td width="215" {sort_func % 11}>Last Updated:</td>\n'
	html_file += '</tr>\n'
	
	tcp_range   = [alliance_info['members'][member].get('tcp',0)   for member in member_list]
	stp_range   = [alliance_info['members'][member].get('stp',0)   for member in member_list]
	tcc_range   = [alliance_info['members'][member].get('tcc',0)   for member in member_list]
	mvp_range   = [alliance_info['members'][member].get('mvp',0)   for member in member_list]
	max_range   = [alliance_info['members'][member].get('max',0)   for member in member_list]
	
	# Conditionally include columns.
	if ARENA_BLITZ_ENABLED:
		arena_range = [alliance_info['members'][member].get('arena',0) for member in member_list]
		blitz_range = [alliance_info['members'][member].get('blitz',0) for member in member_list]
	
	stars_range = [alliance_info['members'][member].get('stars',0) for member in member_list]
	red_range   = [alliance_info['members'][member].get('red',0)   for member in member_list]
	
	# If we've asked for Historical analysis, we need to do a little additional work.
	if hist_date:

		hist_diff = {}

		# Get a little closer to our work.
		hist = alliance_info.get('hist')

		# Ensure we have a good date.
		if hist_date not in hist:
			hist_date = min(hist)

		for member,processed_chars in hist.get(hist_date).items():
		
			member_diff = {}
			member_info = alliance_info['members'][member]
		
			# Calculate inferred level and diff -- don't split this cell if diff is 0.
			member_diff['tcp']   = member_info.get('tcp',  0) - sum([processed_chars[char].get('power',0) for char in processed_chars])
			member_diff['stp']   = member_info.get('stp',  0) - sum(sorted([processed_chars[char]['power'] for char in processed_chars], reverse=True)[:5])
			member_diff['tcc']   = member_info.get('tcc',  0) - len([char for char in processed_chars if processed_chars[char]['power']])
			member_diff['max']   = member_info.get('max',  0) - len([char for char in processed_chars if processed_chars[char]['yel']==7])
			member_diff['stars'] = member_info.get('stars',0) - sum([processed_chars[char]['yel'] for char in processed_chars])
			member_diff['red']   = member_info.get('red',  0) - sum([processed_chars[char]['red'] for char in processed_chars])

			hist_diff[member] = member_diff
			
		hist_range = {}
			
		hist_range['tcp']   = [hist_diff[member].get('tcp',0)   for member in member_list]
		hist_range['stp']   = [hist_diff[member].get('stp',0)   for member in member_list]
		hist_range['tcc']   = [hist_diff[member].get('tcc',0)   for member in member_list]
		hist_range['max']   = [hist_diff[member].get('max',0)   for member in member_list]
		hist_range['stars'] = [hist_diff[member].get('stars',0) for member in member_list]
		hist_range['red']   = [hist_diff[member].get('red',0)   for member in member_list]

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

		member_url = ''
		if member_stats.get('avail'):
			member_url = f' href="https://marvelstrikeforce.com/en/member/{member_stats.get("url")}/characters" target="_blank"'

		# If hist_date was requested, add date under the name field.
		second_line = ''
		if hist_date:
			second_line = f'<br><span style="font-weight:normal;"><i>(since {hist_date.strftime("%m/%d/%y")})</i></span>'
		# If no hist_date, see if we have a discord name to include.
		elif member_stats.get('discord'):
			second_line = f'<br><span style="font-size:16px">@{member_stats.get("discord",{}).get("name","")}</span>'

		html_file += '  <td class="urlb"><a style="text-decoration:none; color:black;"%s><span class="bd">%s</span>%s</a></td>\n' % (member_url, member_stats.get('display_name',member), second_line)

		html_file += '  <td>%s</td>\n' % (member_stats.get('level','n/a'))
		html_file += '  <td>%s</td>\n' % (member_role)
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(tcp_range,   member_stats.get('tcp',0),   html_cache, stale_data), f'{member_stats.get("tcp",0):,}')
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(stp_range,   member_stats.get('stp',0),   html_cache, stale_data), f'{member_stats.get("stp",0):,}')
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color_ext(max(tcc_range)-5, max(tcc_range),   member_stats.get('tcc',0),   html_cache, stale_data), f'{member_stats.get("tcc",0):,}')
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(max_range,   member_stats.get('max',0),   html_cache, stale_data), f'{member_stats.get("max",0):,}')

		# Conditionally include columns.
		if ARENA_BLITZ_ENABLED:
			html_file += '  <td class="%s">%s</td>\n' % (get_value_color_ext(max(arena_range), min(arena_range), member_stats.get('arena',0), html_cache, stale_data), f'{member_stats.get("arena",0):,}')
			html_file += '  <td class="%s">%s</td>\n' % (get_value_color(blitz_range, member_stats.get('blitz',0), html_cache, stale_data), f'{member_stats.get("blitz",0):,}')
			
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(mvp_range,   member_stats.get('mvp',0),   html_cache, stale_data), f'{member_stats.get("mvp",0):,}')
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(stars_range, member_stats.get('stars',0), html_cache, stale_data), f'{member_stats.get("stars",0):,}')
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(red_range,   member_stats.get('red',0),   html_cache, stale_data), f'{member_stats.get("red",0):,}')

		if 'last_update' in member_stats:
			last_update = datetime.datetime.now() - member_stats['last_update']
			time_color  = get_value_color_ext(4*86400, 0, last_update.total_seconds(), html_cache, stale_data)
			
			if stale_data:
				time_value = f'<b><i> {("Stale. Re-sync.","EMPTY. Please Sync.")[not member_stats.get("tot_power")]} </i></b><br>%s, %sd ago' % (member_stats['last_update'].strftime('%b %d'), last_update.days)
			else:
				time_value = '%s%s ago<br>%s' % (['',f'{last_update.days} days, '][not last_update.days], str(last_update).split('.')[0], member_stats['last_update'].strftime('%a, %b %d')) 
		else:
			time_color = get_value_color_ext(0, 1, 0, html_cache)
			time_value = 'NEVER<br><b><i>Ask member to sync.</i></b>'
		
		html_file += '  <td class="%s" style="font-size:18px;">%s</td>\n' % (time_color, time_value)
		html_file += ' </tr>\n'



		# History requested. Do a second row with differences.
		if hist_date:
			html_file += ' <tr style="background:%s; font-size:22px;">\n' % (member_color)
		
			html_file += '  <td class="%s">%s</td>\n' % (get_value_color(hist_range['tcp'],   hist_diff[member].get('tcp',0),   html_cache, stale_data), f'{hist_diff[member].get("tcp",  0):,}')
			html_file += '  <td class="%s">%s</td>\n' % (get_value_color(hist_range['stp'],   hist_diff[member].get('stp',0),   html_cache, stale_data), f'{hist_diff[member].get("stp",  0):,}')
			html_file += '  <td class="%s">%s</td>\n' % (get_value_color(hist_range['tcc'],   hist_diff[member].get('tcc',0),   html_cache, stale_data), f'{hist_diff[member].get("tcc",  0):,}')
			html_file += '  <td class="%s">%s</td>\n' % (get_value_color(hist_range['max'],   hist_diff[member].get('max',0),   html_cache, stale_data), f'{hist_diff[member].get("max",  0):,}')
			html_file += '  <td class="%s">%s</td>\n' % (get_value_color(hist_range['stars'], hist_diff[member].get('stars',0), html_cache, stale_data), f'{hist_diff[member].get("stars",0):,}')
			html_file += '  <td class="%s">%s</td>\n' % (get_value_color(hist_range['red'],   hist_diff[member].get('red',0),   html_cache, stale_data), f'{hist_diff[member].get("red",  0):,}')
		
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
			stp_list = get_stp_list(alliance_info, [char], hist_date)	
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



# Translate value to a color from the Heat Map gradient.
def get_value_color(val_range, value, html_cache, stale_data, stat='power', under_min=False, hist_date=''):
	min_val = min(val_range) if val_range else 0
	max_val = max(val_range) if val_range else 0

	if not min_val:
		new_range = [x for x in val_range if x != 0]
		if new_range:
			min_val = min(new_range)
	
	return get_value_color_ext(min_val, max_val, value, html_cache, stale_data, stat, under_min, hist_date)



def get_value_color_ext(min_val, max_val, value, html_cache, stale_data=False, stat='power', under_min=False, hist_date=''):
	
	# If we've specified an inverted range, flip the calculation on its head.
	if min_val > max_val:
		min_val, max_val = max_val, min_val

		# 0 Stays 0, max_val goes to 1, 1 goes to mex_value
		if value:
			value = (max_val - value) + 1

	# Special treatment for the '0' fields. 
	if not value:
		return 'hist'

	# Special treatment if there's only a single value.
	value += min_val == max_val
	
	# Tweak gradients for Tier, ISO, Level, and Red/Yellow stars.

	# Midpoint = ISO 8
	if stat == 'iso':
		color = get_scaled_value(0, 8, 10, value, hist_date)
	# ISO Level midpoint = Tier 15
	elif stat == 'tier':
		color = get_scaled_value(0, 15, 19, value, hist_date)
	# Gear Tier midpoint = Level 85
	elif stat == 'lvl':
		color = get_scaled_value(0, 85, 100, value, hist_date)
	# Ability midpoint = Level 5
	elif stat in ('bas','spc','ult'):
		color = get_scaled_value(0, 5, 7, value, hist_date)
	# Passive midpoint = Level 3
	elif stat == 'pas':
		color = get_scaled_value(0, 3, 5, value, hist_date)
	elif stat in ('red','yel'):
		color = get_scaled_value(0, 5, 7, value, hist_date)
	elif stat == 'rank':
		color = get_scaled_value(1, 13, 25, (25-value), hist_date)
	elif stat == 'avail':
		color = get_scaled_value(0, 5, 15, value, hist_date)
	# Everything else, generic handling.
	else:
		mid_val = (((max_val-min_val)*0.5)+min_val)
		color = get_scaled_value(min_val, mid_val, max_val, value, hist_date)
	
	# Dim values slightly if under the minimum specified for the report.
	if under_min and not hist_date:
		color = darken(color)

	# If data is more than a week old, make grayscale to indicate stale data.
	if stale_data:
		color = grayscale(color)

	# Cache this color away for class definitions later.
	return make_next_color_id(html_cache, color)



# Do the ugly calculations here.
def get_scaled_value(min_val, mid_val, max_val, value, hist_date=None):

	# If Hist Date, any growth is a positive. Start with +1 as yellow and go to top of range as green
	if hist_date:
		mid_val = min_val

	# Define midpoint once, in case we'd like to skew it.
	yellow_point = 0.5
	
	# If we're in the lower "half" of our range, calculate the spread from red to yellow
	if value <= mid_val:
		scaled_value = ((value-min_val)/max(1,mid_val-min_val)) * yellow_point
	# Top "half" is yellow to green.
	else:
		scaled_value = ((value-mid_val)/max(1,max_val-mid_val)) * (1-yellow_point) + yellow_point 

	# Ensure the scaled_value is between 0% and 100%
	scaled_value = max(0, scaled_value)		# min of 0%
	scaled_value = min(1, scaled_value)		# max of 100%

	# Translate the scaled_value into a color from the color_scale list.
	max_colors   = len(color_scale)-1
	scaled_value = int(scaled_value * max_colors)
	
	return color_scale[scaled_value]



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
						"AlphaFlight": "Alpha Flight",
						"Asgard": "Asgardians",
						"Astonishing": "Astonishing<br>X-Men",
						"Astonishing X-Men": "Astonishing<br>X-Men",
						"BionicAvenger": "Bionic<br>Avengers",
						"Bionic Avengers": "Bionic<br>Avengers",
						"BlackOrder": "Black<br>Order",
						"Brotherhood": "B'Hood",
						"DarkHunter": "Dark<br>Hunters",
						"Defender": "Defenders",
						"Eternal": "Eternals",
						"FantasticFour": "Fantastic<br>Four",
						"HeroesForHire": "H4H",
						"HiveMind": "Hive-Mind",
						"InfinityWatch": "Infinity<br>Watch",
						"Infinity Watch": "Infinity<br>Watch",
						"Invader": "Invaders",
						"MastersOfEvil": "Masters<br>Of Evil",
						"Masters Of Evil": "Masters<br>Of Evil",
						"Mercenary": "Mercs",
						"MercsForMoney": "Mercs For<br>Money",
						"Mercs For Money": "Mercs For<br>Money",
						"NewAvenger": "New<br>Avengers",
						"New Avengers": "New<br>Avengers",
						"NewWarrior": "New<br>Warriors",
						"New Warriors": "New<br>Warriors",
						"OutOfTime": "Out of Time",
						"Pegasus": "PEGASUS",
						"PowerArmor": "Power Armor",
						"PymTech": "Pym Tech",
						"Ravager": "Ravagers",
						"SecretAvenger": "Secret<br>Avengers",
						"SecretDefender": "Secret<br>Defenders",
						"Secret Defenders": "Secret<br>Defenders",
						"SinisterSix": "Sinister<br>Six",
						"Sinister Six": "Sinister<br>Six",
						"SpiderVerse": "Spiders",
						"SpiderSociety": "Spider<br>Society",
						"Spider Society": "Spider<br>Society",
						"SuperiorSix": "Superior<br>Six",
						"Symbiote": "Symbiotes",
						"TangledWeb": "Tangled<br>Web",
						"Unlimited": "Unlimited<br>X-Men",
						"Unlimited X-Men": "Unlimited<br>X-Men",
						"WarDog": "War Dogs",
						"Wave1Avenger": "Wave 1<br>Avengers",
						"WeaponX": "Weapon X",
						"WebWarrior": "Web<br>Warriors",
						"XFactor": "X-Factor",
						"Xforce": "X-Force",
						"Xmen": "X-Men",
						"XTreme": "X-Treme X-Men",
						"X-Treme X-Men": "X-Treme<br>X-Men",
						"YoungAvenger": "Young<br>Avengers",
						"Young Avengers": "Young<br>Avengers",
						"A.I.M. Monstrosity":"A.I.M.<br>Monstrosity",
						"A.I.M. Researcher":"A.I.M.<br>Researcher",
						"Agatha Harkness":"Agatha<br>Harkness",
						"Black Panther (1MM)":"Black Panther<br>(1MM)",
						'Black Panther (Shuri)':'Black Panther<br>(Shuri)',
						"Captain America":"Captain<br>America",
						"Captain America (Sam)":"Capt. America<br>(Sam)",
						"Captain America (WWII)":"Capt. America<br>(WWII)",
						'Captain Britain':'Captain<br>Britain',
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
						"Spider-Man (Pavitr)":"Spider-Man<br>(Pavitr)",
						"Spider-Man (Symbiote)":"Spider-Man<br>(Symbiote)",
						"Spider-Man 2099":"Spider-Man<br>2099",
						"Star-Lord (Annihilation)":"Star-Lord<br>(Annihilation)",
						"Star-Lord (T'Challa)":"Star-Lord<br>(T'Challa)",
						"Strange (Heartless)":"Strange<br>(Heartless)",
						"Thor (Infinity War)":"Thor<br>(Infinity War)",
						"X23":"X-23",
						}
	return TRANSLATE_NAME.get(value,value)