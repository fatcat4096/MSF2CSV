#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_html.py
Takes the processed alliance / roster data and generate readable output to spec.  
"""

from log_utils import *

import copy

# Supporting routines
from alliance_info import *
from generate_css  import *
from html_cache    import *
from html_shared   import *

# Routines to create html files.
from generate_alliance_info   import *
from generate_roster_analysis import *
from generate_by_char         import *
from generate_table           import *


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

		# Make a copy before we make any changes.
		table = copy.deepcopy(table)

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

		# Are we rendering this in sections?
		start_lane    = table_format.get('lane_idx',0)
		start_section = table_format.get('section_idx',0)
	
		# Special handling if we want each section individually in a single lane format -- process each section individually.
		for lane_idx in range(start_lane,len(lanes)):

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
			side_hist = get_table_value(table_format, table, key='side_hist', default=False)

			# If side_hist request, send hist_date in this instead.
			if side_hist:
				side_hist, hist_date = hist_date, False

			for section_idx in range(start_section, len(lane), sections_per):

				# If we're rendering in sections, see whether we've rendered enough.
				if table_format.get('render_sections') and (len(html_files)==4 or (len(html_files)==1 and not start_lane and not start_section)):

					# That's it. Insert bookmarks and bail.
					table_format['lane_idx']    = lane_idx
					table_format['section_idx'] = section_idx
					return html_files

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
						html_file += generate_lanes(alliance_info, table, [[section]], table_format, side_hist=side_hist, html_cache=html_cache)

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

			# Manually resetting the loop.
			start_section = 0

	# If not, it's one of the supporting tabs.
	else:
		html_file = ''
		
		hist_date = get_hist_date(alliance_info, table_format)

		# Generate the appropriate midsection, either Roster Analysis...
		if output == 'roster_analysis':
			use_range = table_format.get('use_range','set')
			html_file += generate_roster_analysis(alliance_info, hist_date=hist_date, html_cache=html_cache, use_range=use_range)

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

	if 'render_sections' in table_format:
		del table_format['render_sections']

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

	# If side_hist request, send hist_date in this instead.
	side_hist = get_table_value(table_format, table, key='side_hist', default=False)
	if side_hist:
		side_hist, hist_date = hist_date, False

	# Add a tab for each lane. 
	html_file = generate_lanes(alliance_info, table, lanes, table_format, using_tabs=True, side_hist=side_hist, html_cache=html_cache)

	# Add a historical info tab.
	if hist_date:
		html_file += generate_lanes(alliance_info, table, lanes, table_format, hist_date, using_tabs=True, html_cache=html_cache)

	# After all Lanes are added, add the Roster Analysis, Alliance Info, and ByChars tabs.
	html_file += generate_roster_analysis(alliance_info, using_tabs=True, hist_date=hist_date or side_hist, html_cache=html_cache)
	html_file += generate_alliance_tab   (alliance_info, using_tabs=True, hist_date=hist_date or side_hist, html_cache=html_cache)
	html_file += generate_by_char_tab    (alliance_info, using_tabs=True, hist_date=hist_date or side_hist, html_cache=html_cache)
	
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



# Generate the contents for each lane.
@timed(level=3)
def generate_lanes(alliance_info, table, lanes, table_format, hist_date=None, side_hist=None, using_tabs=False, html_cache={}):

	html_file = ''

	# Calculate strike teams
	strike_teams = get_strike_teams(alliance_info, table, table_format)

	# Values do not change from section to section
	only_team    = get_table_value(table_format, table, key='only_team')
	only_members = get_table_value(table_format, table, key='only_members')
	only_side    = get_table_value(table_format, table, key='only_side')

	# Special handling required if inline_hist.
	inline_hist = get_table_value(table_format, table, key='inline_hist')

	# Find out whether we're including Team Power Summary at top.
	inc_summary = get_table_value(table_format, table, key='inc_summary')

	# Iterate through all the lanes. Showing tables for each section. 
	for lane_idx, lane in enumerate(lanes):
	
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
			html_file += generate_team_power_summary(alliance_info, table, [lane], table_format, team_list, strike_teams, hist_date or side_hist, html_cache=html_cache)

		# Process each section individually, filtering only the specified traits into the Active Chars list.
		for section_idx, section in enumerate(lane):

			last_section = section_idx == len(lane)-1
		
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
			html_file += '<table>\n <tr style="vertical-align:top">\n  <td>\n'

			max_others = get_table_value(table_format, table, section, key='max_others')

			# Only building meta table if we have meta_chars defined.
			if meta_chars:
				meta_lbl = table_lbl+'<br><span class="sub">META</span>'

				stp_list = get_stp_list(alliance_info, meta_chars, hist_date)

				# If inline_hist, need to generate STP entries for the historical date as well.
				if inline_hist:
					stp_list = get_stp_list(alliance_info, meta_chars, inline_hist)

				html_file += generate_table(alliance_info, table, section, table_format, meta_chars, strike_teams, meta_lbl, stp_list, html_cache, hist_date, side_hist)

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
			if other_chars and not meta_chars and len(other_chars) <= 5 and span_data and not (only_team or only_members or only_side):

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

			# Split raid format requested. Generate info from two different lane definitions
			elif other_chars and not meta_chars and only_side and [x for x in strike_teams if '----' in x]:

				# Truncate if only_side is 'left' or 'right' -- 'left' == keep first block, 'right' == keep last block.
				if only_side in ('left','right'):

					# Flip the order if we're keeping right.
					if only_side == 'right':
						for x in strike_teams:
							x.reverse()
					
					strike_teams = [x[:x.index('----')] for x in strike_teams]

					# Flip it back if we were working on right.
					if only_side == 'right':
						for x in strike_teams:
							x.reverse()

				# How many iterations? 
				block_idx = [[0]+[i for i,e in enumerate(x) if e == '----']+[len(x)] for x in strike_teams]
				block_cnt = len(block_idx[0])-1

				# Finally, generate blocks for each section
				for idx in range(block_cnt):
					strike_temp = [strike_teams[x][block_idx[x][idx] : block_idx[x][idx+1]] for x in range(len(strike_teams))]
					html_file += generate_table(alliance_info, table, section, table_format, other_chars, strike_temp, table_lbl, stp_list, html_cache, hist_date)
					
					# Generate divider if more to come
					if idx != block_cnt-1:
						html_file += '  </td>\n  <td><br></td>\n  <td>\n'

			# We are NOT spanning. Standard table generation.
			else:
				html_file += generate_table(alliance_info, table, section, table_format, other_chars, strike_teams, table_lbl, stp_list, html_cache, hist_date, linked_hist=side_hist is not None)
				
				# History to the side also requested.
				if side_hist:
					
					# Small space between the two tables.
					html_file += '  </td>\n  <td><br></td>\n  <td>\n'

					# Generate the right table with historical information if available.
					stp_list = get_stp_list(alliance_info, meta_chars+other_chars, side_hist)
					table_lbl = table_lbl.replace('META',f'Changes since:<br>{side_hist}')
					table_lbl = table_lbl.replace('OTHER',f'Changes since:<br>{side_hist}')
					html_file += generate_table(alliance_info, table, section, table_format, other_chars, strike_teams, table_lbl, stp_list, html_cache, side_hist, linked_hist=True)

			# End every section the same way.
			html_file += '  </td>\n </tr>\n</table>\n'

			# If not the final section, add a divider row. 
			if not last_section:
				html_file += '    <p></p>\n'

		# After Lane content is done, close the div for the Tab implementation.
		if using_tabs:
			html_file += '</div>\n'

	return html_file



# Generate Labels for each section from either label info or trait names.
def get_section_label(section):
	
	# If a label specified, use it.
	if section.get('label'):
		return section.get('label','').replace('-<br>','').replace('<br>',' ')

	# Otherwise, just join the translated traits.
	return ', '.join([translate_name(trait) for trait in section['traits']]).replace('-<br>','').replace('<br>',' ')



# Team Report Summary suggestions
# * Include graphics for teams in Team Report Summary?
# * Better team name formatting? 
# * Can we avoid using deepcopy for everything?
# * Allow summary_keys to be specified
# * Change last column to TCP? Sort by TCP?
# * Dim if <5 available? 
# * Dim member if <5 available for any entry?

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
		table_format['inc_keys'] = ['power','rank']
		table_format['sort_by'] = 'tcp'
		
		team_power_summary = True
		
		# Generate a table.
		html_file += generate_table(alliance_info, table, section, table_format, team_list, strike_teams, table_lbl, stp_list, html_cache, hist_date, team_power_summary=team_power_summary)
		
		# End every section the same way.
		html_file += '  </td>\n </tr>\n</table>\n'

	# Nothing more to do.
	if 'render_sections' in table_format:
		del table_format['render_sections']

	return html_file