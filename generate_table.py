#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_table.py
Generate one table of roster information per requested specifications.
"""


try:
	from .log_utils     import *
	from .alliance_info import *
	from .html_cache    import *
	from .html_shared   import *
	from .cached_info   import get_cached
	from .file_io       import local_img_cache
except ModuleNotFoundError:
	from  log_utils     import *
	from  alliance_info import *
	from  html_cache    import *
	from  html_shared   import *
	from  cached_info   import get_cached
	from  file_io       import local_img_cache


# Gold cost cache, rebuilt each run in real time
cached_costs = {}


# Generate individual tables for Meta/Other chars for each raid section.
@timed(level=3)
def generate_table(alliance_info, table, section, table_format, char_list, strike_teams, table_lbl, stp_list, html_cache, hist_date=None, linked_hist=None, team_power_summary=False):

	config = get_config(alliance_info, table, section, table_format, char_list, strike_teams, table_lbl, stp_list, html_cache, hist_date, linked_hist, team_power_summary)
	if not config:
		return ''

	using_chars = config['using_chars']

	# Generate the HTML for the table
	row_idx = 1
	html_file = [f'   <table id="{config['table_id']}">']

	while using_chars:
		line_chars, using_chars = using_chars[:config['line_wrap']], using_chars[config['line_wrap']:]

		# Generate images row
		html_file.extend(generate_images_row(html_cache, line_chars, config))
		row_idx += 1

		# Generate data block for each Strike Team
		for strike_team in strike_teams:

			# Honor only_team requests, also skip if no strike team is defined
			team_num = strike_teams.index(strike_team) + 1
			only_team = table_format.get('only_team')
			if not strike_team or (only_team and only_team != team_num):
				continue

			# Last minute sort if proscribed by the table format.
			if config['sort_by']:
				strike_team = final_strike_team_sort(table_format, table, section, strike_team, config['player_list'])

			# Calculate the number of lines in the data block 
			row_count = len([x for x in strike_team if x in config['player_list']]) * len(config['date_list'])
	
			# Generate heading row for each Strike Team
			html_file.extend(generate_heading_row(line_chars, row_idx, team_num, row_count, config))
			row_idx += 1

			# Add data rows
			html_file.extend(generate_data_rows(html_cache, line_chars, strike_team, alliance_info, config))
			row_idx += row_count

	# Close the table
	html_file.append('   </table>')

	return '\n'.join(html_file)


def final_strike_team_sort(table_format, table, section, strike_team, player_list):
				
	strike_team = [member for member in player_list if member in strike_team]

	# If inc_dividers is '53', needs to be added back in after sorting.
	inc_dividers = get_table_value(table_format, table, section, key='inc_dividers', default='other')
	if inc_dividers == '53':
		strike_team = insert_dividers([strike_team], inc_dividers)[0]

	return strike_team



  #8888b.  8888888888 88888888888       .d8888b.   .d88888b.  888b    888 8888888888 8888888 .d8888b.  
#88P  Y88b 888            888          d88P  Y88b d88P" "Y88b 8888b   888 888          888  d88P  Y88b 
#88    888 888            888          888    888 888     888 88888b  888 888          888  888    888 
#88        8888888        888          888        888     888 888Y88b 888 8888888      888  888        
#88  88888 888            888          888        888     888 888 Y88b888 888          888  888  88888 
#88    888 888            888          888    888 888     888 888  Y88888 888          888  888    888 
#88b  d88P 888            888          Y88b  d88P Y88b. .d88P 888   Y8888 888          888  Y88b  d88P 
 #Y8888P88 8888888888     888           "Y8888P"   "Y88888P"  888    Y888 888        8888888 "Y8888P88 



# Pre-calculate all the information used to actually generate the table
def get_config(alliance_info, table, section, table_format, char_list, strike_teams, table_lbl, stp_list, html_cache, hist_date, linked_hist, team_power_summary):

	portraits   = get_cached('portraits')
	iso_classes = get_cached('iso_classes')

	# Determine color scheme using table label
	color_scheme = get_color_scheme(table_lbl)

	# Reset cached MINs before each table
	MIN = get_min_values(table_format, table, section)

	# Sort of player list requested?
	sort_by = get_table_value(table_format, table, section, key='sort_by', default='')

	# Get the list of Alliance Members we will iterate through as rows
	player_list = get_player_list(alliance_info, sort_by, stp_list, section, char_list)

	# If there are no players in this table, don't generate a table
	using_players = {player for player in sum(strike_teams, []) if player in player_list}
	if not using_players:
		return

	# See if we need to pare the included characters even further
	using_chars = get_using_chars(alliance_info, table, section, table_format, using_players, char_list, team_power_summary)

	# If there are no characters in this table, don't generate a table
	if not using_chars:
		return

	# If char_limit, exit without output; communicate results via table_format
	if get_table_value(table_format, table, section, 'char_limit'):
		table_format['using_chars'] = len(using_chars)
		return

	# Dim Image if under_min but still included
	dim_image = remove_min_iso_tier(alliance_info, table_format, table, section, using_players, using_chars)
	dim_image = {char for char in using_chars if char not in dim_image}

	# Get a table_id to allow sorting. If a /by_char page, check for an anchor as well
	table_id, anchor, linked_id = lookup_table_ids(linked_hist, html_cache, char_list, hist_date)

	# Add requirements to table label if show_reqs is True
	show_reqs = get_table_value(table_format, table, section, key='show_reqs')

	# Note whether HTML output has been requested
	req_html = table_format.get('output_format') in ('html', 'tabbed')

	# Add requirements if requested, image in background if a character is named
	table_lbl = enhance_table_lbl(table_lbl, show_reqs, MIN, portraits, req_html)

	# Define these once
	key_labels = {'power':'Pwr', 'op':'OP', 'iso':'ISO', 'stp':'STP'}

	# Standard order for these columns
	key_order = ('power', 'lvl', 'tier', 'iso', 'yel', 'red', 'bas', 'spc', 'ult', 'pas', 'op', 'gold')

	# Get keys from table_format/table, with defaults if necessary
	keys = get_keys(table_format, table, section, hist_date, linked_hist)

	# Calculate gold requirements at last minute and only as required
	tot_gold = calculate_tot_gold(keys, alliance_info, using_chars, using_players, MIN)

	# Set the key_order based on the keys requested and presented
	key_order = keys if team_power_summary else [x for x in key_order if x in keys]

	# Find out whether inline history has been requested for this report
	inline_hist = get_table_value(table_format, table, section, key='inline_hist')

	print (f'{inline_hist=}')

	# If inline_hist is requested, we will loop through this code twice for each user
	date_list = [hist_date, inline_hist] if inline_hist else [hist_date]

	print (f'{date_list=}')

	# Pre-calculate key ranges for each character
	precalculate_ranges(alliance_info, table_format, using_chars, keys, date_list, player_list, using_players)

	# Get inclusion flags
	inc_avail = get_table_value(table_format, table, section, key='inc_avail', default=False, profile=True) and 'OTHERS' not in table_lbl
	inc_rank  = get_table_value(table_format, table, section, key='inc_rank',  default=False, profile=True) and 'OTHERS' not in table_lbl and not team_power_summary
	inc_class = get_table_value(table_format, table, section, key='inc_class', default=False, profile=True) and not (team_power_summary or (hist_date and linked_hist))
	inc_comp  = get_table_value(table_format, table, section, key='summary_comp')
	spec_ops  = get_table_value(table_format, table, section, key='spec_ops')

	# If a line_wrap hasn't been explicitly set, auto-calculate optimal value 
	line_wrap = get_table_value(table_format, table, section, key='line_wrap') 
	if not line_wrap:
		line_wrap = calculate_line_wrap(table_format, table, section, using_players, using_chars, player_list, key_order, inc_class) 

	# Only require 4 for Table=='DD7' section=='Mythic'
	DD7 = table.get('name') == 'Dark Dimension 7'

	# Calculate the minimum required to be ready for a section
	min_count = calculate_min_count(team_power_summary, table_format, section, DD7)

	# Find max available heroes for stats/color. Anything under 5 is forced to red
	avail_range = get_avail_range(team_power_summary, player_list, char_list, alliance_info, inc_avail, section, sort_by)

	return locals()


def get_color_scheme(table_lbl):
	"""Setup color scheme based on table label"""

	if 'OTHERS' in table_lbl:
		return {
			'title_cell'   : 'tgra',
			'table_header' : 'hgra',
			'name_cell'    : 'ngra',
			'name_cell_dim': 'ngrad',
			'name_alt'     : 'ngalt',
			'name_alt_dim' : 'ngaltd',
			'button_hover' : 'blkb'
		}
	else:
		return {
			'title_cell'   : 'tblk',
			'table_header' : 'hblu',
			'name_cell'    : 'nblu',
			'name_cell_dim': 'nblud',
			'name_alt'     : 'nalt',
			'name_alt_dim' : 'naltd',
			'button_hover' : 'blub'
		}


def get_min_values(table_format, table, section):
	"""Setup minimum values for filtering"""
	MIN = table_format.setdefault('profile', {})['min'] = {}
	for key in ('lvl', 'tier', 'iso', 'yel', 'red'):
		MIN[key] = get_table_value(table_format, table, section, key=f'min_{key}', default=0)
	return MIN


def get_using_chars(alliance_info, table, section, table_format, using_players, char_list, team_power_summary):
	"""Filter the list of characters to include."""
	using_chars = char_list[:]

	# Is this the OTHER CHARS section? If so, reduce the entries based on min/max others
	if 'META' not in table_format.get('table_lbl', '') and len(using_chars) > 5 and not team_power_summary:
		using_chars = sort_and_filter_others(alliance_info, table, section, table_format, using_players, using_chars)

	return using_chars


# Explicitly indicate required mins for each section. Used by Spec Ops
def enhance_table_lbl(table_lbl, show_reqs, MIN, portraits, req_html):

	# Add requirements to Table label if show_reqs is True
	if 'META' in table_lbl and show_reqs:

		min_reqs = []

		if MIN['lvl']:
			min_reqs.append(f'L{MIN['lvl']}')
		if MIN['tier']:
			min_reqs.append(f'T{MIN['tier']}')
		if MIN['yel']:
			yellow_star = '<span style="color:yellow;">&#x2605;</span>'
			min_reqs.append(f'{MIN['yel']}{yellow_star}')
		if MIN['red']:
			red_star = '<span style="color:red;">&#x2605;</span>'
			min_reqs.append(f'{(MIN['red']+6)%7+1}{red_star if MIN['red'] <= 7 else "&#x1F48E;"}')
		if MIN['iso']:
			min_reqs.append(f'ISO{int((MIN['iso']+4)/5)}-{(MIN['iso']+4)%5+1}')
		
		table_lbl = table_lbl.replace('META', f'<b>Req: {" ".join(min_reqs)}</b>')

	# Replace table_lbl with fancy entry if label includes a char name
	for char_name in portraits:
		if table_lbl.startswith(char_name.upper() + ':<BR>'):
			url = local_img_cache(portraits[char_name], req_html)
			table_lbl = table_lbl.removeprefix(f'{char_name.upper()}:<BR>').upper().replace(" (", "<BR>(").replace('-', '&#8209;')
			table_lbl = f'<div class="img cont"><img src="{url}" alt="" width="60"></div><div class="cent" style="font-size:12px;">{translate_name(char_name)}</div><div class="summ">{table_lbl}</div>'
			break

	return table_lbl


# Determine which keys should be included in the table
def get_keys(table_format, table, section, hist_date, linked_hist):

	# Start with the explicitly specified keys
	keys = get_table_value(table_format, table, section, key='inc_keys', default=['power', 'lvl', 'tier', 'iso'], profile=True)

	# Treat 'abil' as 4 separate entries
	if 'abil' in keys:
		idx = keys.index('abil')
		keys = keys[:idx] + ['bas', 'spc', 'ult', 'pas'] + keys[idx+1:]

	# No relevance to historical data -- remove completely if possible
	if 'gold' in keys and hist_date and linked_hist:
		keys.remove('gold')

	return keys


# Calculate gold requirements at last minute and only as required
def calculate_tot_gold(keys, alliance_info, using_chars, using_players, MIN):

	global cached_costs

	tot_gold = {}

	if 'gold' in keys:
		gold_costs = get_cached('gold_costs')
		for char in using_chars:
			for player in using_players:

				# Bail if calculation has previously been made
				char_info = alliance_info['members'][player].get('processed_chars', {}).setdefault(char_name, {})
				if char_info.get('gold') is not None:
					continue
					
				# Initialize to zero, we are calculating value
				char_info['gold'] = 0
				for key in ('lvl','tier'):

					# Bail if no min
					if not MIN[key]:
						continue

					# Bail if over min
					val = find_roster_value(alliance_info, player, char_name, key)
					if val >= MIN[key]:
						continue

					# Under min, how much gold will it cost to level up?	
					char = None if key == 'lvl' else char_name
					char_info['gold'] += cached_costs.setdefault((char, val, MIN[key]), sum([gold_costs.get(char, {}).get(x,0) for x in range(val, MIN[key])]))					

		# Calc tot_gold for the toons requiring upgrade for this player
		for player in using_players:
			char_info = alliance_info['members'][player].get('processed_chars', {})
			tot_gold[player] = sum([char_info.get(char, {}).get('gold', 0) for char in using_chars])

	return tot_gold


# Pre-calculate key ranges for each character
def precalculate_ranges(alliance_info, table_format, using_chars, keys, date_list, player_list, using_players):

	# Are we displaying everyone or just a subset?
	inc_all_players = using_players == set(player_list)

	for hist_date in date_list:
		# Only profile non-historical data
		profile_keys = {} if hist_date else {'yel', 'red', 'lvl', 'tier', 'iso'}

		# Create space to store profiled values
		PROFILE = table_format['profile'].setdefault('val', {key: {*()} for key in profile_keys})

		# Which are usable as is, which need to be done separately?
		profile_during = {key for key in profile_keys if inc_all_players and key in keys}
		profile_after  = {key for key in profile_keys if key not in profile_during}

		for char_name in using_chars:
			key_ranges = table_format.setdefault('key_ranges', {}).setdefault(hist_date, {}).setdefault(char_name, {})
			pre_ranges = alliance_info.setdefault('key_ranges', {}).setdefault(char_name, {})

			for key in keys:
				# Have we already cached this range in table_format?
				if key not in key_ranges:
					# If pre-calculated, cached ranges are available, use them
					if key in pre_ranges and not hist_date:
						key_ranges[key] = pre_ranges[key]
					# Otherwise, gotta compile them from scratch
					else:
						key_ranges[key] = [find_roster_value(alliance_info, player, char_name, key, hist_date, set() if key == 'avail' else 0) for player in player_list]

				# Just use this info for PROFILE if all users are being shown
				if key in profile_during:
					PROFILE[key] |= set(key_ranges[key])

		# Add the other fields to PROFILE as well
		for key in profile_after:
			PROFILE[key] |= {find_roster_value(alliance_info, player, char_name, key, hist_date, set() if key=='avail' else 0) for player in using_players}


# Auto-calc the best value for line wrap length
def calculate_line_wrap(table_format, table, section, using_players, using_chars, player_list, key_order, inc_class):
	less_players = len(using_players) != len(player_list)
	more_keys    = len(key_order)+inc_class>6

	if less_players:
		wrap_after = 5 if more_keys else 10
	else:
		wrap_after = 6 if more_keys else 12

	ratio_used = 1.1 if less_players else 1.333

	# Start with a single line
	lines_used = 1

	# Calculate an optimal number of lines to wrap to.
	while len(using_chars) > wrap_after * lines_used:
		lines_used += 1
		wrap_after = int( (wrap_after * ratio_used) + 0.49)

	# Calculate the line_wrap to best fill this number of lines
	return round(len(using_chars)/lines_used + 0.49)


# Calculate the minimum required to be ready for a section
def calculate_min_count(team_power_summary, table_format, section, DD7):
	if team_power_summary:
		return table_format.get('output') not in ['battleworld','teams'] + [f'battleworld_zone{x}' for x in range(1,5)] and 5
	else:
		return table_format.get('output') not in ('battleworld','all_chars','by_trait','teams') and 5 - (DD7 and section.get('label')=='Mythic')


# Find max available heroes for stats/color. Anything under 5 is forced to red
def get_avail_range(team_power_summary, player_list, char_list, alliance_info, inc_avail, section, sort_by):

	avail_range = {}

	if team_power_summary:
		for player in player_list:

			# char_list == teams/sections
			avail_set = set()
			for sect in char_list:
				avail_set.update(find_roster_value(alliance_info, player, sect, 'avail', False, set()))

			avail_range[player] = len(avail_set)
			
		# Once total available found, we can sort players properly.
		if sort_by == 'avail':
			player_list = sorted(player_list, key = lambda x : f'{avail_range[x]:03}{alliance_info["members"][x].get("tcp",0):012}', reverse = True)

	elif inc_avail:
		avail_range = {player:len([char for char in section.get('under_min', {}).get(player, {}) if not section.get('under_min', {}).get(player, {}).get(char)]) for player in player_list}

	return avail_range



  #8888b.  8888888888 888b    888 8888888888 8888888b.         d8888 88888888888 8888888888      8888888 888b     d888        d8888  .d8888b.  8888888888 .d8888b.       8888888b.   .d88888b.  888       888 
#88P  Y88b 888        8888b   888 888        888   Y88b       d88888     888     888               888   8888b   d8888       d88888 d88P  Y88b 888       d88P  Y88b      888   Y88b d88P" "Y88b 888   o   888 
#88    888 888        88888b  888 888        888    888      d88P888     888     888               888   88888b.d88888      d88P888 888    888 888       Y88b.           888    888 888     888 888  d8b  888 
#88        8888888    888Y88b 888 8888888    888   d88P     d88P 888     888     8888888           888   888Y88888P888     d88P 888 888        8888888    "Y888b.        888   d88P 888     888 888 d888b 888 
#88  88888 888        888 Y88b888 888        8888888P"     d88P  888     888     888               888   888 Y888P 888    d88P  888 888  88888 888           "Y88b.      8888888P"  888     888 888d88888b888 
#88    888 888        888  Y88888 888        888 T88b     d88P   888     888     888               888   888  Y8P  888   d88P   888 888    888 888             "888      888 T88b   888     888 88888P Y88888 
#88b  d88P 888        888   Y8888 888        888  T88b   d8888888888     888     888               888   888   "   888  d8888888888 Y88b  d88P 888       Y88b  d88P      888  T88b  Y88b. .d88P 8888P   Y8888 
 #Y8888P88 8888888888 888    Y888 8888888888 888   T88b d88P     888     888     8888888888      8888888 888       888 d88P     888  "Y8888P88 8888888888 "Y8888P"       888   T88b  "Y88888P"  888P     Y888 



def generate_images_row(html_cache, line_chars, config):
	"""Generate the images row HTML."""
	html_row = []

	html_row.append(f'    <tr class="{config['color_scheme']['title_cell']}">')
	html_row.append(f'     <td class="tlbl">{config['table_lbl']}</td>')

	# Include a column for "# Pos" info if requested.
	if config['inc_rank']:
		html_row.append(f'     <td></td>')

	# Include a column for "# Avail" info if requested.
	if config['inc_avail']:
		html_row.append(f'     <td></td>')

	# If Summary, create the Label for each section header instead of an Image for each toon.
	for char in line_chars:
		if config['team_power_summary']:
			html_row.extend(generate_team_power_image(char, config))
		# Otherwise, include Images for each of the Characters.
		else:
			html_row.extend(generate_character_image(html_cache, char, config))

	# Include an image of the completion reward if provided.
	if config['team_power_summary'] and config['inc_comp']:
		url = local_img_cache(config['portraits'].get(config['inc_comp']), config['req_html'])
		html_row.append(f'     <td class="img">')
		html_row.append(f'      <div class="cont"><img src="{url}" alt="" width="100"></div>')
		html_row.append(f'      <div class="cent">{translate_name(config['inc_comp'])}</div>')
		html_row.append(f'     </td>')

	# Include a Team Power column if we have more than one character being displayed
	if len(config['char_list'])>1:
		# Include a Tot Gold column for last two cols if gold is being displayed.
		if 'gold' in config['keys']:
			html_row.append(f'    <td class="img" colspan="2"><div class="cont"><div><img src="../images/src/gold.png" alt="" width="90"></div></div></td>')
		else:
			html_row.append('     <td></td>')

	html_row.append('    </tr>')

	return html_row


def generate_team_power_image(char, config):
	"""Generate image cell for team power summary."""
	html_cells = []

	# If the Section Name starts with a Character, use that toon's image for the background.
	for char_name in config['portraits']:

		# Found a matching entry, generate the cell and bail
		if char.startswith(char_name+':'):
			section_name = char.removeprefix(f'{char_name}:').upper().replace(' (','<br>(').replace('-','&#8209;')

			html_cells.append(f'     <td class="img" colspan="{len(config['keys'])}">')
			html_cells.append(f'      <div class="cont"><img src="{local_img_cache(config['portraits'][char_name], config['req_html'])}" alt="" width="60"></div>')
			html_cells.append(f'      <div class="cent" style="font-size:12px;">{translate_name(char_name)}</div>')
			html_cells.append(f'      <div class="summ">{section_name}</div>')
			html_cells.append(f'     </td>')
			break

	# Standard text-based title cell
	if not html_cells:
		section_name = translate_name(char).upper().replace(" OR ","<br>OR<br>").replace(" AND ","<br>AND<br>").replace(" (","<br>(").replace(" NON-","<br>NON-").replace(", ",",<br>").replace('-','&#8209;')
		html_cells.append(f'     <td colspan="{len(config['keys'])}">')
		html_cells.append(f'      <div class="summ">{section_name}</div>')
		html_cells.append(f'     </td>')

	return html_cells


def generate_character_image(html_cache, char, config):
	"""Generate image for character."""
	html_cells = []

	url = local_img_cache(config['portraits'][char], config['req_html'])

	# No default value to start
	onclick = ''

	# We are doing a ByChar table in a tabbed file, link back to the report tabs
	if config['linked_hist'] and config['anchor']:
		onclick = f' onclick="toTable(this,\'{config['anchor'].get("from")}\')"' 

	# If we don't have linked_hist, then we're on the reports tab
	elif not config['linked_hist']:

		# Create new anchor entry to link Report and Bychar tabs 
		anchor = make_next_anchor_id(html_cache, char, config['table_id'])
		onclick = f' onclick="toTable(this,\'{anchor.get("to")}\')"' 

	# Control background color of Character image if Spec Ops report
	bg_color = ' '+spec_ops_bg(config['section'], char, config['player_list'], html_cache) if config['spec_ops'] else ''

	# Dim image if under_min
	bg_color += ' dim_img' if char in config['dim_image'] else ''

	# Number of columns under each Character entry
	num_cols = len(config['keys']) + config['inc_class']

	# Do we have ISO information for this character yet?
	iso_char = config['iso_classes'].get(char)

	# Adjust the width of the ISO Class Info based on the width of the char info
	if config['inc_class'] and iso_char:
		class_cols = 0 if num_cols < 5 else 1 if num_cols == 5 else 2
		num_cols -= class_cols

	html_cells.append(f'     <td class="img" colspan="{num_cols}"{onclick}>')
	html_cells.append(f'      <div class="cont{bg_color}">')
	html_cells.append(f'       <div class="{"" if config['hist_date'] else "zoom"}"><img src="{url}" alt="" width="100"></div>')
	html_cells.append(f'       <div class="cent">{translate_name(char)}</div>')
	html_cells.append(f'      </div>')
	html_cells.append(f'     </td>')

	# If we had room for ISO info, let's add a title and the ISO info now
	if config['inc_class'] and iso_char and class_cols:

		# If we had room for two columns, add a title/header
		if class_cols == 2:
			html_cells.append(f'     <td class="isot">J<br>A<br>R<br>V<br>I<br>S</td>')

		iso_column = []

		# And finally, add the actual ISO adoption rates in order from the MSF API
		for iso in sorted(iso_char, key=lambda x: iso_char[x], reverse=True):

			# Determine color for each sub-cell
			iso_color = get_value_color(iso_char.values(), iso_char[iso], html_cache, stat='class')

			# Include the sub-cell definition
			iso_column.append(f'<div class="{iso_color}{bg_color} isoc">{round(iso_char[iso])}%<br><span class="{iso[:4]}">{"&nbsp;"*4}</span></div>')

		html_cells.append(f"     <td>{''.join(iso_column)}</td>")

	return html_cells


# Hide the messy calculations behind Spec Ops background color_scheme
def spec_ops_bg(section, char, player_list, html_cache):

	# Find num above mins for this toon
	avail_count = 24-sum([section.get('under_min', {}).get(player, {}).get(char,False) for player in player_list])

	# Only dim the background if near the top of the range.
	darken_amt  = 0 if avail_count<14 else (((avail_count-14)/10)**2) * 0.6
	
	# Skew color range and bend color curve to steer mid-range toward yellows
	return get_value_color_ext(-15**3, 24**3, -25**3 if avail_count<5 else avail_count**3, html_cache, darken_amt=darken_amt)



  #8888b.  8888888888 888b    888 8888888888 8888888b.         d8888 88888888888 8888888888      888    888 8888888888        d8888 8888888b. 8888888 888b    888  .d8888b.       8888888b.   .d88888b.  888       888 
#88P  Y88b 888        8888b   888 888        888   Y88b       d88888     888     888             888    888 888              d88888 888  "Y88b  888   8888b   888 d88P  Y88b      888   Y88b d88P" "Y88b 888   o   888 
#88    888 888        88888b  888 888        888    888      d88P888     888     888             888    888 888             d88P888 888    888  888   88888b  888 888    888      888    888 888     888 888  d8b  888 
#88        8888888    888Y88b 888 8888888    888   d88P     d88P 888     888     8888888         8888888888 8888888        d88P 888 888    888  888   888Y88b 888 888             888   d88P 888     888 888 d888b 888 
#88  88888 888        888 Y88b888 888        8888888P"     d88P  888     888     888             888    888 888           d88P  888 888    888  888   888 Y88b888 888  88888      8888888P"  888     888 888d88888b888 
#88    888 888        888  Y88888 888        888 T88b     d88P   888     888     888             888    888 888          d88P   888 888    888  888   888  Y88888 888    888      888 T88b   888     888 88888P Y88888 
#88b  d88P 888        888   Y8888 888        888  T88b   d8888888888     888     888             888    888 888         d8888888888 888  .d88P  888   888   Y8888 Y88b  d88P      888  T88b  Y88b. .d88P 8888P   Y8888 
 #Y8888P88 8888888888 888    Y888 8888888888 888   T88b d88P     888     888     8888888888      888    888 8888888888 d88P     888 8888888P" 8888888 888    Y888  "Y8888P88      888   T88b  "Y88888P"  888P     Y888 



def generate_heading_row(line_chars, row_idx, team_num, row_count, config):
	"""Generate the heading row for a strike team."""
	html_row = [f'    <tr class="{config['color_scheme']['table_header']}">']

	# Simplify inclusion of the sort function code
	if config['linked_hist']:
		sort_str = f'onclick="sortl(%s,\'{config['table_id']}\',{row_idx},{row_count},\'{config['linked_id']}\')"'
	else:
		sort_str = f'onclick="sortx(%s,\'{config['table_id']}\',{row_idx},{row_count})"'

	sort_func = lambda x: sort_str % (len(x)-1)

	if len(config['strike_teams']) > 1:
		html_row.append(f'     <td class="{config['color_scheme']['button_hover']}" {sort_func(html_row)}>STRIKE TEAM {team_num}</td>')
	else:
		html_row.append(f'     <td class="{config['color_scheme']['button_hover']}" {sort_func(html_row)}>Member</td>')

	# Include header if "# Pos" info requested.
	if config['inc_rank']:
		html_row.append(f'     <td class="{config['color_scheme']['button_hover']}" {sort_func(html_row)}>Rank</td>')

	# Include header if "# Avail" info requested.
	if config['inc_avail']:
		html_row.append(f'     <td class="{config['color_scheme']['button_hover']}" {sort_func(html_row)}>Avail</td>')

	# Insert stat headings for each included Character.
	for char in line_chars:
		for key in config['key_order']:
			width = 'p' if key == 'power' else ''
			html_row.append(f'     <td class="{"goldb" if key=="gold" else config['color_scheme']["button_hover"]}{width}" {sort_func(html_row)}>{config['key_labels'].get(key, key.title())}</td>')

		# Include a header for ISO Class info if requested.
		if config['inc_class']:
			html_row.append('     <td>Cls</td>')

	# Insert the Completed? column for Summary reports
	if config['team_power_summary'] and config['inc_comp']:
		html_row.append('     <td>Complete?</td>')

	# Insert the Team Power column.
	if config['team_power_summary']:
		html_row.append(f'     <td class="redb" {sort_func(html_row)}>TCP</td>')

	# Include STP and TOT GOLD only if more than one character displayed
	elif len(config['char_list']) > 1:
		html_row.append(f'     <td class="redb" {sort_func(html_row)}>STP</td>')

		# Include Tot Gold column only if 'gold' is being displayed
		if 'gold' in config['keys']:
			html_row.append(f'     <td class="goldb" {sort_func(html_row)}>Total<br>Gold</td>')

	html_row.append('    </tr>')
	return html_row



  #8888b.  8888888888 888b    888 8888888888 8888888b.         d8888 88888888888 8888888888      8888888b.        d8888 88888888888     d8888      8888888b.   .d88888b.  888       888  .d8888b.  
#88P  Y88b 888        8888b   888 888        888   Y88b       d88888     888     888             888  "Y88b      d88888     888        d88888      888   Y88b d88P" "Y88b 888   o   888 d88P  Y88b 
#88    888 888        88888b  888 888        888    888      d88P888     888     888             888    888     d88P888     888       d88P888      888    888 888     888 888  d8b  888 Y88b.      
#88        8888888    888Y88b 888 8888888    888   d88P     d88P 888     888     8888888         888    888    d88P 888     888      d88P 888      888   d88P 888     888 888 d888b 888  "Y888b.   
#88  88888 888        888 Y88b888 888        8888888P"     d88P  888     888     888             888    888   d88P  888     888     d88P  888      8888888P"  888     888 888d88888b888     "Y88b. 
#88    888 888        888  Y88888 888        888 T88b     d88P   888     888     888             888    888  d88P   888     888    d88P   888      888 T88b   888     888 88888P Y88888       "888 
#88b  d88P 888        888   Y8888 888        888  T88b   d8888888888     888     888             888  .d88P d8888888888     888   d8888888888      888  T88b  Y88b. .d88P 8888P   Y8888 Y88b  d88P 
 #Y8888P88 8888888888 888    Y888 8888888888 888   T88b d88P     888     888     8888888888      8888888P" d88P     888     888  d88P     888      888   T88b  "Y88888P"  888P     Y888  "Y8888P"  
 
 

# Generate the actual data rows for the table
def generate_data_rows(html_cache, line_chars, strike_team, alliance_info, config):
	"""Generate data rows for the table"""

	html_rows = []

	alt_color = False
	for player_name in strike_team:

		# Toggle player name color each time we find a divider
		if player_name not in config['player_list']:
			if player_name:
				alt_color = not alt_color
			continue

		# Get pre-calculated value for available for this section (summary will return a set)
		num_avail = config['avail_range'].get(player_name,5)
		if type(num_avail) is set:
			num_avail = len(num_avail)

		# Check whether this player has enough toons to play section
		not_ready = calculate_not_ready(player_name, line_chars, config)

		# Flag if a roster is stale so we can output in grayscale
		stale_data = alliance_info['members'][player_name].get('is_stale', False)

		print (f'{config['date_list']=}')

		# Hist List has two entries if Inline Hist is included
		for hist_date in config['date_list']:

			# Find min/max for meta/strongest team power in the Alliance
			# This will be used for color calculation for the Team Power column.
			stp_range = [config['stp_list'][hist_date][player_name] for player_name in config['player_list']]

			# Standard Name field content. 
			name_field = get_name_field(alliance_info, player_name, hist_date, config['inline_hist'])

			# If inline_hist was requested, add content to the Name field for the second line and make this and several other fields span both lines.
			rowspan = '" rowspan="2' if config['inline_hist'] and not hist_date else ''

			# Player Name, then relevant stats for each character
			style = ' class="xx"' if hist_date else ''
			html_rows.append(f'    <tr{style}>')

			inline_hist_row = config['inline_hist'] and hist_date

			# Skip this cell if on Inline Hist line.
			if not inline_hist_row:
				field_color = get_name_field_color(alt_color, not_ready, config['color_scheme'])
				html_rows.append(f'     <td class="{field_color}{rowspan}">{name_field}</td>')

			# Include "# Pos" info if requested.
			if config['inc_rank'] and not inline_hist_row:
				rank_num = get_player_list(alliance_info, sort_by='stp', stp_list=config['stp_list']).index(player_name)+1
				field_color = get_value_color_ext(25, 1, rank_num, html_cache, stale_data)
				html_rows.append(f'     <td class="bd {field_color}{rowspan}">{rank_num}</td>')

			# Include "# Avail" info if requested.
			if config['inc_avail'] and not inline_hist_row:
				field_color = get_value_color(config['avail_range'].values(), -1 if not_ready and not config['team_power_summary'] else num_avail, html_cache, stale_data)
				html_rows.append(f'     <td class="bd {field_color}{rowspan}">{num_avail}</td>')

			# Include the stats requested
			for char_name in line_chars:
				# Should these cells be dimmed?
				under_min = calculate_under_min(alliance_info, player_name, char_name, config)

				# Include requested info in specific order
				html_rows.extend(generate_char_data_cells(html_cache, alliance_info, player_name, char_name, stale_data, under_min, hist_date, config))

				# Include ISO class information if requested
				if config['inc_class'] and not inline_hist_row:
					html_rows.extend(generate_iso_class_cell(html_cache, alliance_info, player_name, char_name, stale_data, under_min, hist_date))

			# Dark Dimension Completed Column
			if config['team_power_summary'] and config['inc_comp']:
				completed = get_summary_comp(alliance_info, player_name, config['inc_comp'])
				field_value = '&#x1f7e2;' if completed == 7 else '&#x1f7e1;' if completed == 5 else '&#x274C;'
				html_rows.append(f'     <td class="xx">{field_value}</td>')

			# Include the Strongest Team Power column for Summary
			if config['team_power_summary']:
				player_tcp = alliance_info['members'][player_name].get('tcp',0)
				tcp_range = [alliance_info['members'][player_name].get('tcp',0) for player_name in strike_team]
				field_value = get_field_value(player_tcp, hist_date)
				field_color = get_value_color(tcp_range, player_tcp, html_cache, stale_data, color_set='set')
				html_rows.append(f'     <td class="bd {field_color}">{field_value}</td>')

			# Include STP and/or TOT GOLD only if there's more than one character displayed
			elif len(config['char_list'])>1:
				player_stp = config['stp_list'].get(hist_date, {}).get(player_name,0)
				field_value = get_field_value(player_stp, hist_date)
				field_color = get_value_color(stp_range, player_stp, html_cache, stale_data)
				html_rows.append(f'     <td class="bd {field_color}">{field_value}</td>')

				# TOT GOLD Column
				if 'gold' in config['keys']:
					field_value = get_field_value(config['tot_gold'].get(player_name))
					field_color = get_value_color(config['tot_gold'].values(), config['tot_gold'].get(player_name), html_cache, stale_data, stat='gold')
					html_rows.append(f'     <td class="bd {field_color}">{field_value}</td>')

			html_rows.append('    </tr>')

	return html_rows


def calculate_not_ready(player_name, line_chars, config): 
	"""Calculate if player is not ready."""

	# Dim the name if less than 5 heroes that meet min reqs
	if config['team_power_summary']:
		config['not_completed'] = not get_summary_comp(config['alliance_info'], player_name, config['inc_comp'])
		not_ready = (
			config['min_count'] and config['not_completed'] and 
			any([len(find_roster_value(config['alliance_info'], player_name, char_name, 'avail', False, set())) < config['min_count'] - (config['DD7'] and char_name == 'Mythic') for char_name in config['char_list']])
		)
	# If Strike Teams are in use, this is raid output -- verify all team members are available.
	elif len(config['strike_teams']) > 1:
		num_avail = sum([not config['section'].get('under_min', {}).get(player_name, {}).get(char_name) for char_name in config['section'].get('section_chars', line_chars)])
		not_ready = num_avail < 5
	# Otherwise, check for Dark Dimension readiness.
	else:
		num_avail = len([char for char in config['section'].get('under_min', {}).get(player_name, {}) if not config['section'].get('under_min', {}).get(player_name, {}).get(char)])
		not_ready = num_avail < config['min_count'] and len(line_chars) >= config['min_count']

	return not_ready


# Return the # of Yellow Stars on the completion reward if specified.
def get_summary_comp(alliance_info, player_name, inc_comp):
	return find_roster_value(alliance_info, player_name, inc_comp, 'yel') if inc_comp else None


def get_name_field(alliance_info, player_name, hist_date, inline_hist):
	"""Generate the name field for a player."""
	name_field = alliance_info['members'][player_name].get('display_name',player_name).replace('Commander','Cmdr.')

	print (f'{inline_hist=} {hist_date=}')

	# Add date for second line if Inline Hist
	if inline_hist and not hist_date:
		name_field = f'{name_field}<br><span style="font-weight:normal;"><i>(since {inline_hist.strftime("%m/%d/%y")})</i></span>'

	return name_field


def get_name_field_color(alt_color, not_ready, color_scheme):
	"""Get the color for the name field."""
	if alt_color:
		return color_scheme['name_alt_dim'] if not_ready else color_scheme['name_alt']
	else:
		return color_scheme['name_cell_dim'] if not_ready else color_scheme['name_cell']


def calculate_under_min(alliance_info, player_name, char_name, config):
	"""Calculate if character is under minimum."""
	if config['team_power_summary']:
		return config['not_completed'] and config['min_count'] and len(find_roster_value(alliance_info, player_name, char_name, 'avail', False, set())) < config['min_count'] - (config['DD7'] and char_name=='Mythic')
	else:
		return config['section'].get('under_min', {}).get(player_name, {}).get(char_name)


def generate_char_data_cells(html_cache, alliance_info, player_name, char_name, stale_data, under_min, hist_date, config):
	"""Generate data cells for a character."""
	html_cells = []

	# Get the range of values for all stats for this char for all rosters
	# If historical, get diff between current values and requested record
	key_ranges = config['table_format']['key_ranges'][hist_date][char_name]

	# Include requested info in specific order
	for key in config['key_order']:

		# Standard lookup. Get the key_val for this character stat from this player's roster
		# If historical, display the difference between the stat in hist record and current
		key_val, other_diffs = find_roster_value(alliance_info, player_name, char_name, key, hist_date, other_info=True) if player_name in alliance_info['members'] else (0, '')
		need_tt = key=='power' and key_val != 0 and not config['linked_hist']

		# Summary info will return a set
		if type(key_val) is set:
			key_val = len(key_val)

		if key_val == 0 and hist_date:
			style = ''
		else:
			# Note: We are using the T class to get black text on fields in the Hist tab.
			field_color = get_value_color(key_ranges[key], key_val, html_cache, stale_data, key, under_min and key != 'gold', hist_date)
			style = f' class="{field_color}{" T" if need_tt or hist_date is not None else ""}"'

		# Determine what value should be displayed in data field. Add + if historical data, use '-' if empty value.
		field_value = format_field_value(key, key_val, hist_date)
		html_cells.append(f'     <td{style}>{field_value}{other_diffs if need_tt else ""}</td>')

	return html_cells


# Determine what value should be displayed in data field. Add + if historical data, use '-' if empty value.
def format_field_value(key, key_val, hist_date):
	"""Get the display value for a field."""
	if key == 'red' and key_val > 7 and not hist_date:
		return f'<span class="dmd">{key_val - 7}&#x1F48E;</span>'
	elif key == 'iso' and key_val and not hist_date:
		return f'{(key_val + 4) % 5 + 1}'
	else:
		return get_field_value(key_val, hist_date)


# Include ISO class information if requested
def generate_iso_class_cell(html_cache, alliance_info, player_name, char_name, stale_data, under_min, hist_date):
	"""Generate ISO class cells."""
	html_cells = []

	# Get the ISO Class in use for this member's toon.
	iso_code = alliance_info['members'][player_name].get('other_data', {}).get(char_name,0)%6

	# Translate it to a code to specify the correct CSS URI.
	iso_class = ('','fort','healer','skirm','raider','striker')[iso_code]

	if iso_class:
		# Do a quick tally of all the ISO Classes in use. Remove the '0' entries from consideration.
		all_iso_codes = [alliance_info['members'][player].get('other_data', {}).get(char_name,0)%6 for player in alliance_info['members']]
		all_iso_codes = [code for code in all_iso_codes if code]

		# Calculate a confidence for this code based on the tally of all codes in use.
		iso_conf = int((all_iso_codes.count(iso_code)/len(all_iso_codes))*100) if all_iso_codes else 0

		# Include the graphic via CSS and use the confidence for background color.
		field_color = get_value_color_ext(0, 100, iso_conf, html_cache, stale_data, under_min=under_min)
		tool_tip = f'<span class="TT">{iso_class.title()}:<br>{iso_conf}%</span>'
		html_cells.append(f'     <td class="{iso_class[:4]} T {field_color}">{tool_tip}</td>')
	else:
		html_cells.append(f'     <td class="xx">-</td>')

	return html_cells
