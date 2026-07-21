#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_by_char.py
Generate the tab for By Character output.
"""

try:
	from .log_utils      import timed
	from .alliance_info  import get_hist_date, get_meta_other_chars, get_player_list, get_stp_list, is_under_min
	from .cached_info    import get_cached
	from .html_shared    import translate_name
	from .generate_table import generate_table
except ModuleNotFoundError:
	from  log_utils      import timed
	from  alliance_info  import get_hist_date, get_meta_other_chars, get_player_list, get_stp_list, is_under_min
	from  cached_info    import get_cached
	from  html_shared    import translate_name
	from  generate_table import generate_table


# By_Char data should use same hist_date as provided in inc_hist or inline_hist

# Generate just the Alliance Tab contents
@timed(level=3)
def generate_by_char_tab(alliance_info, html_cache, hist_date=True, table_format=None, using_tabs=False):

	# Initialize the mutables
	if table_format is None:
		table_format = {}

	html_file = ''

	# Get the list of usable characters for analysis
	char_list = sorted(html_cache.get('chars',{}))
	if not char_list:
		char_list = table_format.get('inc_chars',get_cached('char_list'))

	table = {}

	# Include history by default if it's available
	if table_format.get('inc_hist') is None:
		table_format['inc_hist'] = hist_date

	# Get the hist_date if historical information was requested
	hist_date = get_hist_date(alliance_info, table_format)

	# Initialize inc_keys if necessary
	#table_format['inc_keys']  = table_format.get('inc_keys',  ['power','lvl','iso','tier','yel','red','abil','op'])
	table_format['inc_keys']  = table_format.get('inc_keys',  ['power','lvl','iso','tier','yel','red','abil'])
	table_format['inc_class'] = table_format.get('inc_class', True)
	
	#if not sort_by specified
	table_format['sort_by'] = 'stp'

	meta_chars, other_chars = get_meta_other_chars(alliance_info, table, {'meta':[char_list]}, table_format)

	# Get the list of traits to allow us to include Trait information
	extracted_traits = get_cached('traits')

	# Get the list of Alliance Members 
	member_list = get_player_list(alliance_info)
	
	# Iterate through the list of characters, generating the same detailed information for each character
	for char in char_list:
		
		# Just specify the Character name for the table title
		table_lbl = translate_name(char).upper()

		# By default, no section-specific formatting
		section={}

		# Add under_min information
		for player_name in member_list:
			is_under_min(alliance_info, player_name, char, table_format, table, section) 

		# Create a sub-heading for the Table Label
		traits = [translate_name(key).replace('<br>',' ') for key in extracted_traits if extracted_traits[key].get(char)]
		
		# Just hide certain traits -- no one cares
		for to_filter in ['Chaos Team', 'Mercenary', 'Military', 'MSF Original', 'Dark Promotions', 'Spider-Verse', 'Annihilation Wave', 'Tower Challenger', 'Sentry Challengers', 'Conqueror', 'Harbingers', 'Stormbound', 'Anxiety', 'Fear', 'Panic', 'Terror', 'Best Buddies', 'Best Avenger Buddies', 'Best Mutant Buddies', 'Best Spider Buddies', 'Best Villain Buddies']:
			if to_filter in traits:
				traits.remove(to_filter)

		# Filter rendundant traits
		for to_filter in ['Avengers', 'A-Force', 'Defenders', 'Fantastic Four', 'X-Men']:
			if to_filter in traits and len([x for x in traits if to_filter in x]) > 1:
				traits.remove(to_filter)
		
		traits = f'<br><span class="sub">{", ".join(traits)}</span>'
		
		# Build stp_list to simplify sort_by='stp'
		stp_list = get_stp_list(alliance_info, [char], hist_date)

		# Generate the left table with current stats.
		html_file += generate_table(alliance_info, table, section, table_format, [char], [member_list], f'{table_lbl}{traits}', stp_list, html_cache, None, linked_hist=True)

		# Small space between the two tables
		html_file += '  </td>\n  <td><br></td>\n  <td>\n'

		# Generate the right table with historical information if available
		if hist_date:
			# Create a sub-heading for the Table Label
			changes_since = f'<br><span class="sub">Changes since:<br>{hist_date}</span>'

			# Generate the Right table with historical stats.
			html_file += generate_table(alliance_info, table, section, table_format, [char], [member_list], f'{table_lbl}{changes_since}', stp_list, html_cache, hist_date, linked_hist=True)

		# Wrap the entire output in a table
		html_file = f'<table>\n <tr>\n  <td>\n{html_file}\n  </td>\n </tr>\n</table>\n'

		# Add the Abil Panel if I'm speshul
		if 0 and 'FatCat' in member_list:

			# Put everything that's come before into a single row of a new table
			html_file = f' <tr>\n  <td colspan="4">\n{html_file}\n  </td>\n </tr>\n'

			# Wrap all of the above in an enclosing table
			html_file = f'<table>\n{html_file}{generate_abil_panel(char)}\n</table>\n'

		# If not the final section, add a divider row
		if char_list.index(char) != len(char_list)-1:
			html_file += '    <p></p>\n'

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file = f'<div id="ByChar" class="tcon">\n{html_file}</div>\n'

	return html_file


	
def generate_abil_panel(char='', table_format={}):

	# Extract char list from table_format if no character explicitly specified
	if not char:
		char_list = table_format.get('inc_chars',get_cached('char_list'))
		return '\n'.join([generate_abil_panel(char) for char in char_list if char])

	# Get cached info to allow us to include ability information
	extra_info = get_cached('extra_info')

	abil_map  = {'basic':'bas', 'special':'spc', 'ultimate':'ult', 'passive':'pas'}

	# Determine how info is laid out
	long_descs = False
	for abil in abil_map:
		levels = extra_info.get(char,{}).get('abil',{}).get(abil_map[abil],{}).get('levels',{})
		if levels and levels.get(max(levels), {}).get('description','').count('\n') > 5:
			long_descs = True
			break

	html_row = []

	# Add rows for each ability
	for abil in abil_map:
		
		# Bail if we don't have info for this character / ability
		abil_info = extra_info.get(char,{}).get('abil',{}).get(abil_map[abil])
		if not abil_info:
			continue

		url = abil_info.get('icon')

		levels = abil_info.get('levels',{})
		level  = levels.get(max(levels), {})

		desc   = level.get('description')
		cost   = f'<br><span style="text-align:center;">⚡{level.get('startEnergy',0)}/{level.get('costEnergy')}</span>' if level.get('costEnergy') else ''

		width = 'width:15%;' if long_descs else 'width:10%;'

		html_row.append('    <tr class="abil">')
		html_row.append(f'     <td style="vertical-align:top;{width}">')
		html_row.append('      <div>')
		html_row.append(f'       <div class="cont"><img style="border-radius: 10px;" src="{url}" alt="" width="100"></div>')
		html_row.append(f'       <div class="cent">{abil.upper()}</div>')
		html_row.append('      </div>')

		if long_descs:
			html_row.append('     <br>')
		else:
			html_row.append('     </td>')
			html_row.append('     <td style="width:15%">')

		html_row.append(f'     <div><span style="font-size:1.5rem;">{abil_info.get('name').upper()}</span>{cost}</div>')
		html_row.append('     </td>')
		if desc:
			desc = desc.replace('\n','<br>').replace('</color>','</span>').replace('color=#86e619','span style="color:#86e619;"').replace('color=#fff568','span style="color:#fff568;"')
		html_row.append(f'     <td style="width:80%;text-align:left;">{desc}</td>')
		html_row.append('    </tr>')

		html_file = f'<table style="border-spacing:10px;">\n{'\n'.join(html_row)}\n</table>'

	return html_file 

