#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_by_char.py
Generate the tab for By Character output.
"""

from datetime import date

try:
	from .log_utils      import timed
	from .cached_info    import get_cached
	from .html_shared    import translate_name, get_trait_label
	from .generate_table import get_config, generate_images_row
except ModuleNotFoundError:
	from  log_utils      import timed
	from  cached_info    import get_cached
	from  html_shared    import translate_name, get_trait_label
	from  generate_table import get_config, generate_images_row


# Generate just the Ability Panel contents
@timed(level=3)
def generate_abil_panel(alliance_info, html_cache, char='', table_format=None, inc_header=True):

	# Extract char list from table_format if no character explicitly specified
	if not char:
		char_list = table_format.get('inc_chars', get_cached('char_list'))
		return '\n'.join([generate_abil_panel(alliance_info, html_cache, char) for char in char_list if char])

	# Manually build pieces to use
	table        = {}
	table_format = {}
	section      = {}
	char_list    = [char]
	strike_teams = {}
	stp_list     = {}

	# Generate a label for the table
	table_lbl = translate_name(char).upper() + get_trait_label(char)

	# Force inclusion of ISO Class info
	table_format['inc_class'] = True
	table_format['inc_keys'] = range(10)

	# Force inclusion of Unique Info
	hist_date = date.today()
	
	config = get_config(alliance_info, table, section, table_format, char_list, strike_teams, table_lbl, stp_list, html_cache, hist_date, linked_hist=None, team_power_summary=None, force=True)

	# Let's get started
	html_row = []

	# Don't dim anything
	config['dim_image'] = {}

	if inc_header:
		html_row += generate_images_row(html_cache, [char], config)

	# Get cached info to allow us to include ability information
	char_lookup = get_cached('char_lookup')
	extra_info = get_cached('extra_info').get(char_lookup.get(char), {})

	abil_map  = {'basic':'bas', 'special':'spc', 'ultimate':'ult', 'passive':'pas'}

	# Add rows for each ability
	for abil in abil_map:
		
		# Bail if we don't have info for this character / ability
		abil_info = extra_info.get('abil',{}).get(abil_map[abil])
		if not abil_info:
			continue

		url = abil_info.get('icon')

		levels = abil_info.get('levels',{})
		level  = levels.get(max(levels), {})

		desc   = level.get('description')
		cost   = f'<br><span style="text-align:center;">⚡{level.get('startEnergy',0)}/{level.get('costEnergy')}</span>' if level.get('costEnergy') else ''

		html_row.append('    <tr class="abil">')
		html_row.append(f'     <td style="vertical-align:top;width:15%;">')


		html_row.append('      <div>')
		html_row.append(f'       <div class="cont"><img style="border-radius: 10px;" src="{url}" alt="" width="100"></div>')
		html_row.append(f'       <div class="cent">{abil.upper()}</div>')
		html_row.append('      </div>')

		html_row.append('     <br>')

		html_row.append(f'     <div><span style="font-size:1.5rem;">{abil_info.get('name').upper()}</span>{cost}</div>')
		html_row.append('     </td>')
		if desc:

			# Format bulleted points
			desc = '<br>'.join([f'<ul><li>{_.strip()[2:]}</li></ul>' if _.strip().startswith('> ') else _ for _ in desc.split('\n')])

			# Fix vertical spacing
			desc = desc.replace('<br><ul>','<ul>').replace('</ul><ul>','').replace('</ul><br>','</ul>').replace('</ul><br>','</ul>')

			# Fix color tags
			desc = desc.replace('</color>','</span>').replace('color=#86e619','span style="color:#86e619;"').replace('color=#fff568','span style="color:#fff568;"')
			
		html_row.append(f'     <td colspan="10" class="desc">{desc}</td>')
		html_row.append('    </tr>')

	html_file = f'<table style="border-spacing:10px;">\n{'\n'.join(html_row)}\n</table>'

	return html_file 

