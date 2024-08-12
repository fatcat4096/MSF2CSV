#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_alliance_info.py
Generate the tab for Roster Analysis output.  
"""

from log_utils import timed

import copy

from alliance_info import get_char_list
from html_cache    import make_next_table_id
from html_shared   import *


# Generate just the Alliance Tab contents.
@timed(level=3)
def generate_roster_analysis(alliance_info, using_tabs=False, hist_date=None, html_cache={}, use_range='set'):

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file = '<div id="RosterAnalysis" class="tcon">\n'
	else:
		html_file = get_tab_header('ROSTER ANALYSIS (ACTUAL)')
	html_file += generate_analysis_table(alliance_info, stat_type='actual', html_cache=html_cache, use_range=use_range)

	# Add the progressive form in as well. :)
	html_file += get_tab_header('ROSTER ANALYSIS (PROGRESSIVE)')
	html_file += generate_analysis_table(alliance_info, stat_type='progressive', html_cache=html_cache, use_range=use_range)
		
	# Add the historical form in if hist_date is available.
	if hist_date:
		html_file += get_tab_header(f'ROSTER ANALYSIS (CHANGES SINCE {hist_date.strftime("%m/%d/%y")})')
		html_file += generate_analysis_table(alliance_info, stat_type='progressive', hist_date=hist_date, html_cache=html_cache, use_range=use_range)

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file += '</div>\n'

	return html_file
		


def generate_analysis_table(alliance_info, stat_type='actual', hist_date=None, html_cache={}, use_range='set'):

	# Conditionally include Diamonds columns.
	DIAMONDS_ENABLED = True

	# Generate the header for the Roster Analysis table
	html_file = generate_analysis_header(stat_type, DIAMONDS_ENABLED, html_cache)

	# Start by doing stat analysis.	
	stats = get_roster_stats(alliance_info, stat_type, hist_date)

	# Format the analyzed data into a table.
	html_file += generate_analysis_body(alliance_info, stats, DIAMONDS_ENABLED, hist_date, html_cache, use_range)

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
	


def generate_analysis_body(alliance_info, stats, DIAMONDS_ENABLED, hist_date, html_cache, use_range):
	
	html_file = ''

	# Get a sorted list of members to use for this table output.
	member_list = sorted(alliance_info['members'].keys(), key = lambda x: alliance_info['members'][x].get('tcp',0), reverse=True)

	# Iterate through each row for members in the table.
	for member in member_list:
			member_info  = alliance_info['members'][member]
			member_stats = stats.get(member,{})
			stats_range  = stats['range']

			# If Member's roster has grown more than 1% from last sync or hasn't synced in more than a week, indicate it is STALE DATA via Grayscale output.
			stale_data = member_info['is_stale']

			html_file += '<tr>\n'

			member_url = ''
			if member_info.get('avail'):
				member_url = f' href="https://marvelstrikeforce.com/en/member/{member_info.get("url")}/characters" target="_blank"'
		
			html_file += ' <td class="%s urlb"><a style="text-decoration:none; color:black;"%s>%s</a></td>\n' % ('ngra' if stale_data else 'nblu', member_url, member_info.get('display_name',member))
			
			for stat in ['tcp','stp','tcc']:
				html_file += get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, stat)
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Averages
			for stat in ['yel', 'red', 'tier', 'lvl', 'iso']:
				html_file += get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, f'avg_{stat}')
			html_file += ' <td></td>\n' 										# Vertical Divider
			
			# Yellow and Red Stars
			for stat in ['yel','red']:
				for key in range(4,8):
					html_file += get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, stat, key)
				html_file += ' <td></td>\n' 										# Vertical Divider                                                            
																																							  
			# Conditionally include Diamonds columns.
			if DIAMONDS_ENABLED:
				for key in range(1,4):
					html_file += get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, 'dmd', key)
				html_file += ' <td></td>\n' 									# Vertical Divider                             

			# ISO Levels                                                                                                       
			for key in [5,9,10,11,12,13]:
				html_file += get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, 'iso', key)
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Gear Tiers
			for key in range(13,20):
				html_file += get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, 'tier', key)
			html_file += ' <td></td>\n' 										# Vertical Divider

			# T4 Abilities
			for stat in ['bas','spc','ult','pas']:
				html_file += get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, stat, 7)
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Level Ranges
			for key in range(70,105,5):
				html_file += get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, 'lvl', key)

			html_file += '</tr>\n'

	html_file += '</table>\n'

	return html_file



def get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, stat, key=None):

	if key is None:
		member_stat = member_stats.get(stat,0)
		stat_range = stats_range[stat]
	else:
		member_stat = member_stats.get(stat,{}).get(key,0)
		stat_range = stats_range[stat][key]
	
	if not member_stat:
		field_value = '-'
	elif member_stat == int(member_stat):
		field_value = f"{member_stat:+,}" if hist_date else f"{member_stat:,}"
	else:
		field_value = f"{member_stat:+.2f}" if hist_date else f"{member_stat:.2f}"

	return ' <td class="%s">%s</td>\n' % (get_value_color(stat_range, member_stat, html_cache, stale_data, use_range=use_range), field_value)



@timed(level=3)
def get_roster_stats(alliance_info, stat_type, hist_date=''):
	
	hist = alliance_info.get('hist',{})
	
	# Calculate stats for most recent roster refresh
	stats          = analyze_rosters(alliance_info, stat_type, hist[max(hist)])

	# If Historical analysis, a little more work to do.
	if hist_date:

		# Calculate stats for requested date
		hist_stats = analyze_rosters(alliance_info, stat_type, hist[hist_date])

		# Find differences between current stats and hist_stats.
		for member in stats:
			stats[member]['tcp'] -= hist_stats[member]['tcp']
			stats[member]['stp'] -= hist_stats[member]['stp']
			stats[member]['tcc'] -= hist_stats[member]['tcc']

			# Totals (and create dicts for the rest of the ranges)
			for key in ['yel','red','dmd','tier','lvl','iso']:
				stats[member]['avg_'+key] -= hist_stats[member].get('avg_'+key,0)
			
			# Yellow and Red Stars
			for key in range(4,8):
				get_stat_diff(stats, hist_stats, member, 'yel', key)
				get_stat_diff(stats, hist_stats, member, 'red', key)

			# Diamonds
			for key in range(1,4):
				get_stat_diff(stats, hist_stats, member, 'dmd', key)

			# ISO Levels
			for key in range(5,14):
				get_stat_diff(stats, hist_stats, member, 'iso', key)

			# Gear Tiers
			for key in range(13,20):
				get_stat_diff(stats, hist_stats, member, 'tier', key)

			# Level Ranges
			for key in range(65,105,5):
				get_stat_diff(stats, hist_stats, member, 'lvl', key)

			# T4 Abilities
			for stat in ['bas','spc','ult','pas']:
				get_stat_diff(stats, hist_stats, member, stat, 7)

	# Get the list of Alliance Members 
	member_list = list(alliance_info.get('members',{}))

	# Calculate alliance-wide ranges for each statistic. Use min() and max() to determine colors
	stats_range = stats.setdefault('range',{})

	stats_range['tcp'] = [stats[member]['tcp'] for member in member_list]
	stats_range['stp'] = [stats[member]['stp'] for member in member_list]
	stats_range['tcc'] = [stats[member]['tcc'] for member in member_list]

	# Totals (and create dicts for the rest of the ranges)
	for stat in ['yel','red','dmd','tier','lvl','iso']:
		#stats_range[stat]  = {}
		stats_range['avg_'+stat]  = [stats[member].get('avg_'+stat,0) for member in member_list]
	
	# Yellow and Red Stars
	for key in range(4,8):
		get_stat_range(stats, 'yel', key, member_list)
		get_stat_range(stats, 'red', key, member_list)

	# Diamonds
	for key in range(1,4):
		get_stat_range(stats, 'dmd', key, member_list)

	# ISO Levels
	for key in range(5,14):
		get_stat_range(stats, 'iso', key, member_list)

	# Gear Tiers
	for key in range(13,20):
		get_stat_range(stats, 'tier', key, member_list)

	# Level Ranges
	for key in range(65,105,5):
		get_stat_range(stats, 'lvl', key, member_list)

	# T4 Abilities
	for stat in ['bas','spc','ult','pas']:
		get_stat_range(stats, stat, 7, member_list)

	return stats



def get_stat_diff(stats, hist_stats, member, stat, key):
	stats[member].setdefault(stat,{})[key] = stats[member].get(stat,{}).get(key,0) - hist_stats[member].get(stat,{}).get(key,0)



def get_stat_range(stats, stat, key, member_list):
	stats['range'].setdefault(stat,{})[key] = [stats[member].get(stat,{}).get(key,0) for member in member_list]



def analyze_rosters(alliance_info, stat_type, rosters_to_analyze):

	stats = {}
	
	# We'll be making changes, work with a copy.
	rosters_to_analyze = copy.deepcopy(rosters_to_analyze)

	# Get the list of Alliance Members 
	member_list = list(alliance_info.get('members',{}))

	# Get the list of usable characters for analysis.
	char_list = get_char_list(alliance_info)
	
	# Start by doing stat analysis.	
	for member in member_list:
	
		tot_vals = {'power':[]}
	
		# Get a little closer to our work.
		member_stats = stats.setdefault(member,{})
		
		# Don't include stats from heroes that haven't been recruited yet.
		recruited_chars = [char for char in char_list if rosters_to_analyze.get(member,{}).get(char,{}).get('power')]

		# Loop through every char
		for char in recruited_chars:
		
			# Get a little closer to our work.
			char_stats = rosters_to_analyze[member][char]

			# Use for Total / Average # columns -- do this BEFORE normalizing data.
			for key in ['yel','red','dmd','tier','lvl','iso']:
				tot_vals[key] = tot_vals.get(key,0) + char_stats[key]

			# Only report the highest USABLE red star and diamonds only valid if 7R.
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

			# Gather ISO 0-5 into ISO 5.
			if char_stats['iso'] < 5 and stat_type == 'actual':
				char_stats['iso'] = 5
			# Gather ISO 6-9 into ISO 9.
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
			tot_vals['power'].append(char_stats['power'])

		# Calculate TCP, STP, and Total Chars Collected 
		if tot_vals['power']:
			member_stats['tcp'] = sum(tot_vals['power'])
			member_stats['stp'] = sum(sorted(tot_vals['power'])[-5:])
			member_stats['tcc'] = len(tot_vals['power'])
		# If no roster data available, use values from alliance_info.
		else:
			member_stats['tcp'] = alliance_info['members'].get(member,{}).get('tcp')
			member_stats['stp'] = alliance_info['members'].get(member,{}).get('stp')
			member_stats['tcc'] = alliance_info['members'].get(member,{}).get('tcc')

		# Change tot_ values to avg_ values.
		for key in ['yel','red','dmd','tier','lvl','iso']:
			member_stats['avg_'+key] = tot_vals.get(key,0) / max(alliance_info['members'].get(member,{}).get('tcc'),1)
			
	return stats

