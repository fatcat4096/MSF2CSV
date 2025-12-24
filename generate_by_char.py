#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_by_char.py
Generate the tab for By Character output.
"""

from log_utils import *

from alliance_info  import *
from cached_info    import get_cached
from html_shared    import *
from generate_table import *


# By_Char data should use same hist_date as provided in inc_hist or inline_hist

# Generate just the Alliance Tab contents.
@timed(level=3)
def generate_by_char_tab(alliance_info, html_cache, hist_date=True, table_format=None, using_tabs=False):

	# Initialize the mutables
	if table_format is None:
		table_format = {}

	html_file = ''

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file += '<div id="ByChar" class="tcon">\n'

	# Get the list of usable characters for analysis.
	char_list = sorted(html_cache.get('chars',{}))
	if not char_list:
		char_list = table_format.get('inc_chars',get_cached('char_list'))

	table = {}

	# Include history by default if it's available.
	if table_format.get('inc_hist') is None:
		table_format['inc_hist'] = hist_date

	# Get the hist_date if historical information was requested.
	hist_date = get_hist_date(alliance_info, table_format)

	# Get keys using the lookup. If undefined, 
	table_format['inc_keys']  = ['power','lvl','iso','tier','yel','red','abil']
	table_format['inc_class'] = True
	
	#if not sort_by specified
	table_format['sort_by'] = 'stp'

	meta_chars, other_chars = get_meta_other_chars(alliance_info, table, {'meta':[char_list]}, table_format)

	# Get the list of traits to allow us to include Trait information
	extracted_traits = get_cached('traits')
	
	# Iterate through the list of character, generating the same detailed information for each character.
	for char in char_list:
		
		# Just specify the Character name for the table title
		table_lbl = translate_name(char).upper()

		# Build stp_list to simplify sort_by='stp'.
		stp_list = get_stp_list(alliance_info, [char], hist_date)
	
		# Get the list of Alliance Members 
		member_list = get_player_list(alliance_info)

		# Let's make it easy on ourselves. Start every section the same way.
		html_file += '<table>\n <tr>\n  <td>\n'

		# By default, no section-specific formatting
		section={}

		# Create a sub-heading for the Table Label
		traits = [translate_name(key).replace('<br>',' ') for key in extracted_traits if extracted_traits[key].get(char)]
		
		# Just hide certain traits -- no one cares
		for to_filter in ['Chaos Team', 'Harbinger', 'Mercenary', 'Military', 'MSF Original', 'Spider-Verse']:
			if to_filter in traits:
				traits.remove(to_filter)

		# Filter rendundant traits
		for to_filter in ['Avengers', 'A-Force', 'Defenders', 'Fantastic Four', 'X-Men']:
			if to_filter in traits and len([x for x in traits if to_filter in x]) > 1:
				traits.remove(to_filter)
		
		traits = f'<br><span class="sub">{", ".join(traits)}</span>'
		
		# Generate the left table with current stats.
		html_file += generate_table(alliance_info, table, section, table_format, [char], [member_list], f'{table_lbl}{traits}', stp_list, html_cache, None, linked_hist=True)

		# Small space between the two tables.
		html_file += '  </td>\n  <td><br></td>\n  <td>\n'

		# Generate the right table with historical information if available.
		if hist_date:
			# Create a sub-heading for the Table Label
			changes_since = f'<br><span class="sub">Changes since:<br>{hist_date}</span>'

			# Generate the Right table with historical stats.
			html_file += generate_table(alliance_info, table, section, table_format, [char], [member_list], f'{table_lbl}{changes_since}', stp_list, html_cache, hist_date, linked_hist=True)
			
		# End every section the same way.
		html_file += '  </td>\n </tr>\n</table>\n'

		# If not the final section, add a divider row. 
		if char_list.index(char) != len(char_list)-1:
			html_file += '    <p></p>\n'

	# After Lane content is done, close the div for the Tab implementation.
	if using_tabs:
		html_file += '</div>\n'

	return html_file


