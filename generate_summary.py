#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_html.py
Summarize STP, Rank, and Available chars for each section included in a lane.  
"""

from log_utils import *

import copy

# Supporting routines
from html_shared    import *
from generate_table import *

@timed(level=3)
def generate_summary(alliance_info, table, lanes, table_format, team_list, strike_teams, hist_date=None, html_cache={}):

	html_file = ''

	# Likely need to deep copy here before moving on -- we're adding elements to the existing dicts
	alliance_info = copy.deepcopy(alliance_info)
	table         = copy.deepcopy(table)
	lanes         = copy.deepcopy(lanes)
	table_format  = copy.deepcopy(table_format)

	# Generate a separate table for each lane. 
	for lane in lanes:

		# Pre-process the information for the lane, calculating STPs, num_avail, and rank.
		for section in lane:
			section_label = get_section_label(section)

			if section_label in team_list:

				# Force get_meta_other_chars to return ALL valid characters
				section['max_others'] = 0

				# Filter down the character list to only those in this section
				meta_chars,other_chars = get_meta_other_chars(alliance_info, table, section, table_format)

				# Get the STPs for this team. 
				stp_list = get_stp_list(alliance_info, meta_chars+other_chars, hist_date)

				# Get the rank and available counts for this team. 
				for member in alliance_info['members']:
					if 'processed_chars' in alliance_info['members'][member]:

						# Pull STP from the calculated STP list.
						stp = stp_list[hist_date][member]

						# Get the num_avail for this section
						avail = set([char for char in table.get('under_min',{}).get(member,{}) if char in meta_chars+other_chars and not table.get('under_min',{}).get(member,{}).get(char)])

						# Find Rank for this member's team
						rank  = get_player_list(alliance_info, sort_by='stp', stp_list=stp_list).index(member)+1
					
						# Create a fake entry for this section using the section label as the "Character Name" in processed_chars.
						alliance_info['members'][member]['processed_chars'][section_label] = {'stp':stp, 'avail':avail, 'rank':rank}

		# Create an STP list of the meta "characters" we just generated.
		stp_list = get_stp_list(alliance_info, [get_section_label(section) for section in lane], hist_date)

		# Just create an empty section entry.
		section = {}
		
		table_lbl = table['name'].upper().replace(' ','<br>',table['name'].partition('Raid')[0].count(' '))

		# Find any defined keys specified for given format. Default to including STP and rank
		table_format['inc_keys'] = get_table_value(table_format, table, section, key='summary_keys', default=['stp','rank'])

		# Sort by TCP by default. If 'avail' is included, assume this is the sort_by
		table_format['sort_by'] = ['tcp','avail']['avail' in table_format['inc_keys']]

		# Let's make it easy on ourselves. Start every section the same way.
		html_file += '<table>\n <tr>\n  <td>\n'

		# Generate a table.
		html_file += generate_table(alliance_info, table, section, table_format, team_list, strike_teams, table_lbl, stp_list, html_cache, hist_date, team_power_summary=True)
		
		# End every section the same way.
		html_file += '  </td>\n </tr>\n</table>\n'

	# No segmented rendering for this output.
	table_format.pop('render_sections', None)

	return html_file