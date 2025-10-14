#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_alliance_info.py
Generate the tab for Roster Analysis output.  
"""

from log_utils import timed

import copy

from cached_info   import get_cached
from html_cache    import make_next_table_id
from html_shared   import *

# Generate just the Alliance Tab contents.
#@timed(level=3)
def generate_roster_analysis(alliance_info, inc_prog=True, using_tabs=False, hist_date=None, html_cache={}, use_range='set'):

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file = '<div id="RosterAnalysis" class="tcon">\n'
	else:
		html_file = get_tab_header('ROSTER ANALYSIS (ACTUAL)')
	html_file += generate_analysis_table(alliance_info, stat_type='actual', html_cache=html_cache, use_range=use_range)

	# Add the progressive form in as well. :)
	if inc_prog:
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

	# Start by doing stat analysis.	
	stats = get_roster_stats(alliance_info, stat_type, hist_date)

	# Generate the header for the Roster Analysis table
	html_file = generate_analysis_header(stats, stat_type, html_cache)

	# Format the analyzed data into a table.
	html_file += generate_analysis_body(alliance_info, stats, hist_date, html_cache, use_range)

	return html_file



def generate_analysis_header(stats, stat_type, html_cache):

	ACTUALS = stat_type == 'actual'

	MAX_YEL  = stats['max_yel'] 
	MAX_RED  = stats['max_red'] 
	MAX_DMD  = stats['max_dmd'] 
	MAX_ISO  = stats['max_iso'] 
	MIN_ISO  = stats['min_iso'] 
	MAX_TIER = stats['max_tier']
	MAX_LVL  = stats['max_lvl']
	MAX_OP   = stats['max_op']  

	# Generate a table ID to allow sorting. 
	table_id = make_next_table_id(html_cache) 
	html_file = '<table id="%s">\n' % (table_id)

	# Simplify inclusion of the sort function code
	sort_func = 'class="%s" onclick="sort(%s,\'%s\',2)"' % ("blub nam", '%s', table_id)

	# Create the headings for the Alliance Info table.
	html_file += '<tr class="hblu" style="font-size:14pt;">\n'
	html_file += f' <td width="200" rowspan="2" {sort_func % 0}>Name</td>\n'          

	# Simplify inclusion of the sort function code
	sort_func = 'class="%s" onclick="sort(%s,\'%s\',2)"' % ("blub", '%s', table_id)

	html_file += f' <td rowspan="2" {sort_func % 1} style="min-width:80px">Total<br>Power</td>\n'
	html_file += f' <td rowspan="2" {sort_func % 2} style="min-width:80px">Strongest<br>Team</td>\n'
	html_file += f' <td rowspan="2" {sort_func % 3} style="min-width:50px">Total<br>Chars</td>\n'
	html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider
	
	html_file += ' <td width="200" colspan="6">Average</td>\n'		# All Avg Stats
	html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider

	html_file += ' <td width="160" colspan="4">Stars</td>\n'		# Yel - 4 cols
	html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider

	html_file += ' <td width="120" colspan="4">Red Stars</td>\n'	# Red - 4 cols
	html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider

	if MAX_DMD:
		html_file += ' <td width="160" colspan="3">Diamonds</td>\n'		# Diamonds - 3 cols
		html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider

	html_file += ' <td width="200" colspan="4">ISO</td>\n'			# ISO - 4 cols
	html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider

	html_file += ' <td width="240" colspan="5">Gear Tier</td>\n'	# Tier - 5 cols
	html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider

	html_file += ' <td width="160" colspan="4">T4 Abilities</td>\n'	# Bas/Spc/Ult/Pas
	html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider

	html_file += ' <td width="350" colspan="5">Levels</td>\n'
	html_file += ' <td width="2" rowspan="2" style="background:#343734;"></td>\n' 				# Vertical Divider

	html_file += ' <td width="350" colspan="4">OP</td>\n'		    # OP - 4 cols
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
	html_file += f' <td {sort_func % 10}>OP</td>\n'
	
	# Yellow Stars
	for idx in range(3,-1,-1):
		html_file += f' <td {sort_func % (15-idx)}>%s</td>\n' % (f'{MAX_YEL-idx}'+['','+'][idx and not ACTUALS])
	
	# Red Stars
	for idx in range(3,-1,-1):
		html_file += f' <td {sort_func % (20-idx)}>%s</td>\n' % (f'{MAX_RED-idx}'+['','+'][idx and not ACTUALS])

	# Diamonds
	if MAX_DMD:
		html_file += f' <td {sort_func % 22}>1&#x1F48E;</td>\n'
		html_file += f' <td {sort_func % 23}>2&#x1F48E;</td>\n'
		html_file += f' <td {sort_func % 24}>3&#x1F48E;</td>\n'

	# Consider missing Diamond columns in Sort routines
	NO_DMD = 0 if MAX_DMD else 4

	# ISO Levels
	html_file += f' <td {sort_func % (26-NO_DMD)}>%s</td>\n' % ([f'{MAX_ISO-3}+',f'{MIN_ISO}-{MAX_ISO-3}'][ACTUALS])
	for idx in range(2,-1,-1):
		html_file += f' <td {sort_func % (29-idx-NO_DMD)}>%s</td>\n' % (f'{MAX_ISO-idx}' + ['','+'][idx and not ACTUALS])

	# Gear Tiers
	for idx in range(4,-1,-1):
		html_file += f' <td {sort_func % (35-idx-NO_DMD)}>%s</td>\n' % (f'{MAX_TIER-idx}'+['','+'][idx and not ACTUALS])

	# T4 Abilities
	html_file += f' <td {sort_func % (37-NO_DMD)}>Bas</td>\n'
	html_file += f' <td {sort_func % (38-NO_DMD)}>Spc</td>\n'
	html_file += f' <td {sort_func % (39-NO_DMD)}>Ult</td>\n'
	html_file += f' <td {sort_func % (40-NO_DMD)}>Pas</td>\n'

	# Simplify inclusion of the sort function code
	sort_func = 'class="%s" onclick="sort(%s,\'%s\',2)"' % ("ltbb lvl", '%s', table_id)

	# Level Ranges
	for idx in range(4,-1,-1):
		LVL_END = ['+',f'-{(MAX_LVL-idx*5+4)%[100,10][MAX_LVL-idx*5>100]}'][ACTUALS] if idx else ''
		html_file += f' <td {sort_func % (46-idx-NO_DMD)}>%s</td>\n' % (f'{MAX_LVL-idx*5}{LVL_END}')

	# Simplify inclusion of the sort function code
	sort_func = 'class="%s" onclick="sort(%s,\'%s\',2)"' % ("ltbb col", '%s', table_id)

	# Overpower Levels
	for idx in range(3,-1,-1):
		html_file += f' <td {sort_func % (51-idx-NO_DMD)}>%s</td>\n' % (f'{MAX_OP-idx}'+['','+'][idx and not ACTUALS])

	html_file += '</tr>\n'
	
	return html_file
	


def generate_analysis_body(alliance_info, stats, hist_date, html_cache, use_range):
	
	# Calculate max values for each type
	MAX_YEL  = stats['max_yel'] 
	MAX_RED  = stats['max_red'] 
	MAX_DMD  = stats['max_dmd'] 
	MAX_ISO  = stats['max_iso'] 
	MAX_TIER = stats['max_tier']
	MAX_LVL  = stats['max_lvl']
	MAX_OP   = stats['max_op']  

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
			for stat in ['yel', 'red', 'tier', 'lvl', 'iso', 'op']:
				html_file += get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, f'avg_{stat}')
			html_file += ' <td></td>\n' 										# Vertical Divider
			
			# Yellow Stars
			for key in range(4):
				html_file += get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, 'yel', key + MAX_YEL-3)
			html_file += ' <td></td>\n' 										# Vertical Divider                                                            
																																							  
			# Red Stars
			for key in range(4):
				html_file += get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, 'red', key + MAX_RED-3)
			html_file += ' <td></td>\n' 										# Vertical Divider                                                            
																																							  
			# Diamonds
			if MAX_DMD:
				for key in range(1,4):
					html_file += get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, 'dmd', key)
				html_file += ' <td></td>\n' 										# Vertical Divider                             

			# ISO Levels                                                                                                       
			for key in range(4):
				html_file += get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, 'iso', key + MAX_ISO-3)
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Gear Tiers
			for key in range(5):
				html_file += get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, 'tier', key + MAX_TIER-4)
			html_file += ' <td></td>\n' 										# Vertical Divider

			# T4 Abilities
			for stat in ['bas','spc','ult','pas']:
				html_file += get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, stat, 7)
			html_file += ' <td></td>\n' 										# Vertical Divider

			# Level Ranges
			for key in range(5):
				html_file += get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, 'lvl', key*5 + MAX_LVL-20)
			html_file += ' <td></td>\n' 										# Vertical Divider

			# OP Ranges
			for key in range(4):
				html_file += get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, 'op', key + MAX_OP-3)

			html_file += '</tr>\n'

	html_file += '</table>\n'

	return html_file



def get_member_stat(member_stats, stats_range, use_range, html_cache, stale_data, hist_date, stat, key=None):

	if key is None:
		member_stat = member_stats.get(stat,0)
		stat_range = stats_range[stat]
	else:
		member_stat = member_stats.get(stat,{}).get(key,0)
		stat_range = stats_range[stat].get(key,[])
	
	if not member_stat:
		field_value = '-'
	elif member_stat == int(member_stat):
		field_value = f"{member_stat:+,}" if hist_date else f"{member_stat:,}"
	else:
		field_value = f"{member_stat:+.2f}" if hist_date else f"{member_stat:.2f}"

	return ' <td class="%s">%s</td>\n' % (get_value_color(stat_range, member_stat, html_cache, stale_data, hist_date=None, use_range=use_range), field_value)	# Force hist_date to none -- makes more sense than historical coloration



#@timed(level=3)
def get_roster_stats(alliance_info, stat_type, hist_date=None):
	
	hist = alliance_info.get('hist',{})
	
	# Calculate stats for most recent roster refresh
	stats = analyze_rosters(alliance_info, stat_type, hist[max(hist)])

	# Determine max values for each
	MAX_YEL  = stats['max_yel'] 
	MAX_RED  = stats['max_red'] 
	MAX_DMD  = stats['max_dmd'] 
	MAX_ISO  = stats['max_iso'] 
	MAX_TIER = stats['max_tier']
	MAX_LVL  = stats['max_lvl']
	MAX_OP   = stats['max_op']  

	# If Historical analysis, a little more work to do.
	if hist_date:

		# Start by deleting ranges. We will need to recalculate these
		stats_range = stats['range'] = {}

		# Calculate stats for requested date
		hist_stats = analyze_rosters(alliance_info, stat_type, hist[hist_date])

		# Get the list of Alliance Members 
		member_list = list(alliance_info.get('members',{}))
		
		# Find differences between current stats and hist_stats.
		for member in member_list:

			stats[member]['tcp'] -= hist_stats[member]['tcp']
			stats[member]['stp'] -= hist_stats[member]['stp']
			stats[member]['tcc'] -= hist_stats[member]['tcc']

			stats_range.setdefault('tcp',[]).append(stats[member]['tcp'])
			stats_range.setdefault('stp',[]).append(stats[member]['stp'])
			stats_range.setdefault('tcc',[]).append(stats[member]['tcc'])

			# Totals (and create dicts for the rest of the ranges)
			for key in ['yel','red','dmd','tier','lvl','iso','op']:
				stats[member]['avg_'+key] -= hist_stats[member].get('avg_'+key, 0)
				stats_range.setdefault('avg_'+key,[]).append(stats[member]['avg_'+key])		
				
			# Yellow Stars
			for key in range(4):
				get_stat_diff(stats, hist_stats, member, 'yel', key + MAX_YEL-3)

			# Red Stars
			for key in range(4):
				get_stat_diff(stats, hist_stats, member, 'red', key + MAX_RED-3)

			# Diamonds
			if MAX_DMD:
				for key in range(1,4):
					get_stat_diff(stats, hist_stats, member, 'dmd', key)

			# ISO Levels
			for key in range(4):
				get_stat_diff(stats, hist_stats, member, 'iso', key + MAX_ISO-3)

			# Gear Tiers
			for key in range(5):
				get_stat_diff(stats, hist_stats, member, 'tier', key + MAX_TIER-4)

			# Level Ranges
			for key in range(5):
				get_stat_diff(stats, hist_stats, member, 'lvl', key*5 + MAX_LVL-20)

			# OP Ranges
			for key in range(4):
				get_stat_diff(stats, hist_stats, member, 'op', key + MAX_OP-3)

			# T4 Abilities
			for stat in ['bas','spc','ult','pas']:
				get_stat_diff(stats, hist_stats, member, stat, 7)
	
	return stats



# Calculate differences and add the result to the range lists
def get_stat_diff(stats, hist_stats, member, stat, key):
	stats[member].setdefault(stat,{})[key] = stats[member].get(stat,{}).get(key,0) - hist_stats[member].get(stat,{}).get(key,0)
	stats['range'].setdefault(stat,{}).setdefault(key,[]).append(stats[member][stat][key])



def analyze_rosters(alliance_info, stat_type, rosters_to_analyze):

	# Create stats and stats_range to start
	stats = {}
	stats_range = stats.setdefault('range',{})

	# We'll be making changes, work with a copy.
	rosters_to_analyze = copy.deepcopy(rosters_to_analyze)

	# Get the list of Alliance Members 
	member_list = list(alliance_info.get('members',{}))

	# Get the list of usable characters for analysis.
	char_list = get_cached('char_list')

	# Initialize MAX_LVL (min value 20)
	MAX_LVL = 20

	# Determine MAX_ISO (min value 8)
	MAX_ISO = 8
	for member in member_list:
		for char in char_list:
			MAX_ISO = max(rosters_to_analyze.get(member,{}).get(char,{}).get('iso',0), MAX_ISO)

	# Use MAX_ISO to determine MIN_ISO
	MIN_ISO = MAX_ISO-(MAX_ISO-1)%5-5 if MAX_ISO > 10 else 1

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
			for key in ['yel','red','dmd','tier','lvl','iso','op']:
				tot_vals[key] = tot_vals.get(key,0) + char_stats.get(key,0)

			# Only report the highest USABLE red star and diamonds only valid if 7R.
			if char_stats['red'] > char_stats['yel']:
				char_stats['red'] = char_stats['yel']
			if char_stats['red'] != 7:
				char_stats['dmd'] = 0
 				
			# Normalize the data.
			# If stat_type = 'actual', combine ISO and LVL columns before tallying
			# If 'progressive', make each entry count in those below it.

			# For either stat_type, combine certain columns for ISO and Level data.

			# Use info before normalization to get MAX_LVL
			MAX_LVL = max(MAX_LVL, (char_stats['lvl']+4)-(char_stats['lvl']+4)%5)

			# Round level down to nearest multiple of 5.
			char_stats['lvl'] -= char_stats['lvl']%5			

			# Gather ISO 6-11 into ISO 12
			if stat_type == 'actual' and char_stats['iso'] in range(MIN_ISO, MAX_ISO-3):
				char_stats['iso'] = MAX_ISO-3

			# Just tally the values in each key. Increment the count of each value found.
			for key in ['yel', 'lvl', 'red', 'dmd', 'tier', 'iso', 'op']:
				if stat_type == 'progressive':
					for x in range(0,char_stats.get(key,0)+1):
						member_stats.setdefault(key,{})[x] = member_stats.get(key,{}).setdefault(x,0)+1
				else:
					member_stats.setdefault(key,{})[char_stats.get(key,0)] = member_stats.get(key,{}).setdefault(char_stats.get(key,0),0)+1
					
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

		# Calculate alliance-wide ranges for each statistic
		stats_range.setdefault('tcp',[]).append(member_stats['tcp'])
		stats_range.setdefault('stp',[]).append(member_stats['stp'])
		stats_range.setdefault('tcc',[]).append(member_stats['tcc'])

		# Calc avg_ values from tot_ values.
		for key in ['yel','red','dmd','tier','lvl','iso','op']:
			member_stats['avg_'+key] = tot_vals.get(key,0) / max(alliance_info['members'].get(member,{}).get('tcc'),1)

			# Add these average to our ranges
			stats_range.setdefault('avg_'+key,[]).append(member_stats['avg_'+key])

			# Build range for each stat as we go
			for entry in member_stats.get(key,{}):
				stats_range.setdefault(key,{}).setdefault(entry,[]).append(member_stats[key][entry])

		# Build ranges for the abilities as well
		for key in ['bas','spc','ult','pas']:
			for entry in member_stats.get(key,{}):
				stats_range.setdefault(key,{}).setdefault(entry,[]).append(member_stats[key][entry])

	# Finally, pre-calculate maxes for each range with set mins
	stats['max_yel']  = max(max(stats_range['yel']),  4)
	stats['max_red']  = max(max(stats_range['red']),  4)
	stats['max_dmd']  = max(stats_range['dmd'])
	stats['max_iso']  = MAX_ISO
	stats['min_iso']  = MIN_ISO
	stats['max_tier'] = max(max(stats_range['tier']), 5)
	stats['max_lvl']  = MAX_LVL
	stats['max_op']   = max(max(stats_range['op']),   4)

	return stats

