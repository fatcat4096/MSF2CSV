#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_by_char.py
Generate the tab for By Character output.
"""

try:
	from .log_utils      import timed
	from .alliance_info  import get_hist_date, get_meta_other_chars, get_player_list, get_stp_list, is_under_min
	from .cached_info    import get_cached
	from .html_shared    import translate_name, get_trait_label
	from .generate_table import generate_table
	from .generate_abil  import generate_abil_panel
except ModuleNotFoundError:
	from  log_utils      import timed
	from  alliance_info  import get_hist_date, get_meta_other_chars, get_player_list, get_stp_list, is_under_min
	from  cached_info    import get_cached
	from  html_shared    import translate_name, get_trait_label
	from  generate_table import generate_table
	from  generate_abil  import generate_abil_panel


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
	table_format['inc_keys']  = table_format.get('inc_keys',  ['power','lvl','iso','tier','yel','red','abil'])
	table_format['inc_class'] = table_format.get('inc_class', True)
	
	#if not sort_by specified
	table_format['sort_by'] = table_format.get('sort_by', 'power')

	meta_chars, other_chars = get_meta_other_chars(alliance_info, table, {'meta':[char_list]}, table_format)

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

		# Build stp_list to simplify sort_by='stp'
		stp_list = get_stp_list(alliance_info, [char], hist_date)

		# Generate the left table with current stats.
		html_file += generate_table(alliance_info, table, section, table_format, [char], [member_list], f'{table_lbl}{get_trait_label(char)}', stp_list, html_cache, None, linked_hist=True)

		# Small space between the two tables
		html_file += '  </td>\n  <td><br></td>\n  <td>\n'

		# Generate the right table with historical information if available
		if hist_date:
			# Create a sub-heading for the Table Label
			changes_since = f'<br><br><span class="sub">Changes since:<br>{hist_date}</span>'

			# Generate the Right table with historical stats.
			html_file += generate_table(alliance_info, table, section, table_format, [char], [member_list], f'{table_lbl}{changes_since}', stp_list, html_cache, hist_date, linked_hist=True)

		# Wrap the entire output in a table
		html_file = f'<table>\n <tr>\n  <td>\n{html_file}\n  </td>\n </tr>\n</table>\n'

		# Add the Abil Panel if requested
		if table_format.get('abil_info'):

			# Put everything that's come before into a single row of a new table
			html_file = f' <tr>\n  <td colspan="4">\n{html_file}\n  </td>\n </tr>\n'

			# Wrap all of the above in an enclosing table
			html_file = f'<table>\n{html_file}{generate_abil_panel(alliance_info, html_cache, char, inc_header=False)}\n</table>\n'

		# If not the final section, add a divider row
		if char_list.index(char) != len(char_list)-1:
			html_file += '    <p></p>\n'

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file = f'<div id="ByChar" class="tcon">\n{html_file}</div>\n'

	return html_file
