#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_table.py
Generate one table of roster information per requested specifications.
"""

from log_utils import *

from alliance_info import *
from html_cache    import *
from html_shared   import *

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
	player_list = get_player_list(alliance_info, sort_by, stp_list, table, char_list)

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
							if key=='red' and key_val>7:
								field_value = f'<span class="dmd">{key_val-7}&#x1F48E;</span>'
							else:
								field_value = get_field_value(key_val, use_hist_date)

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
					if team_power_summary:
						# Need to subtract Hist value if use_hist_date
						player_tcp = alliance_info['members'][player_name].get('tcp',0)

						# Get the TCP range for heat map shading.
						tcp_range = [alliance_info['members'][player_name].get('tcp',0) for player_name in strike_team]

						# Determine what value should be displayed in STP field. Add + if historical data, use '-' if empty value.
						field_value = get_field_value(player_tcp, use_hist_date)
	
						st_html += '     <td class="bd %s">%s</td>\n' % (get_value_color(tcp_range, player_tcp, html_cache, stale_data, use_range='set'), field_value)
					
					elif len(char_list)>1:
						player_stp = stp_list.get(use_hist_date,{}).get(player_name,0)

						# Determine what value should be displayed in STP field. Add + if historical data, use '-' if empty value.
						field_value = get_field_value(player_stp, use_hist_date)
	
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
			if team_power_summary:
				html_file += f'     <td class="redb" {sort_func % col_idx}>TCP</td>\n'
			elif len(char_list)>1:
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



def get_field_value(value, hist_date):
	if value:
		if value > 10**6:
			field_value = f'{value/10**6:+.2f}M' if hist_date else f'{value/10**6:.2f}M'
		elif value > 1000:
			field_value = f'{value/1000:+.0f}K'  if hist_date else f'{value/1000:.0f}K'
		else:
			field_value = f'{value:+}' if hist_date else f'{value}'
	else:
		field_value = '-'

	return field_value