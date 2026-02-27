#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_alliance_info.py
Generate the tab for Roster Analysis output.  
"""

from log_utils import timed

import copy

from alliance_info import filter_by_traits
from cached_info   import get_cached
from html_cache    import make_next_table_id
from html_shared   import *

# Generate just the Alliance Tab contents.
@timed(level=3)
def generate_roster_analysis(alliance_info, html_cache, hist_date, table_format=None, using_tabs=False):

	# Initialize the mutables
	if table_format is None:
		table_format = {}

	INC_KEYS = table_format.setdefault('inc_keys', ['yel', 'red', 'lvl', 'iso', 'tier', 'abil', 'op'])

	# Keep a copy for control frame 
	table_format.setdefault('profile',{})['inc_keys'] = INC_KEYS[:]

	# Explicitly include 'dmd' if 'red' included
	if 'red' in INC_KEYS and 'dmd' not in INC_KEYS:
		INC_KEYS.insert(INC_KEYS.index('red')+1, 'dmd')

	# Pull formatting info from table_format
	INC_VIEWS = table_format.get('which_views', 2)

	# What Characters should be included in Analysis
	FILTER_BY = table_format.get('filter_by', 'All Chars')

	html_file = []

	if INC_VIEWS != 1:
		html_file += [get_tab_header(f'{FILTER_BY.upper()} ANALYSIS (ACTUAL STATS)')]
		html_file += generate_analysis_table(alliance_info, table_format, html_cache, stat_type='actual')

	# Add the progressive form in as well. :)
	if INC_VIEWS:
		html_file += [get_tab_header(f'{FILTER_BY.upper()} ANALYSIS (PROGRESSIVE)')]
		html_file += generate_analysis_table(alliance_info, table_format, html_cache, stat_type='progressive')
		
	# Add the historical form in if hist_date is available.
	if hist_date:
		html_file += [get_tab_header(f'{FILTER_BY.upper()} HISTORICAL (CHANGES SINCE {hist_date.strftime("%m/%d/%y")})')]
		html_file += generate_analysis_table(alliance_info, table_format, html_cache, stat_type='progressive', hist_date=hist_date)

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file += ['<div id="RosterAnalysis" class="tcon">'] + html_file + ['</div>']

	return '\n'.join(html_file)
		


@timed(level=3)
def generate_analysis_table(alliance_info, table_format, html_cache, stat_type, hist_date=None):

	# Start by doing stat analysis.	
	stats = get_roster_stats(alliance_info, table_format, stat_type, hist_date)

	# Generate the header for the Roster Analysis table
	html_file = generate_analysis_header(table_format, stats, stat_type, html_cache)

	# Format the analyzed data into a table.
	html_file += generate_analysis_body(alliance_info, table_format, stats, hist_date, html_cache)

	return html_file



@timed(level=3)
def generate_analysis_header(table_format, stats, stat_type, html_cache):

	ACTUALS = stat_type == 'actual'

	# Pull max values for each type
	MAX_YEL  = stats.get('MAX_YEL')
	MAX_RED  = stats.get('MAX_RED')
	MAX_DMD  = stats.get('MAX_DMD')
	MAX_ISO  = stats.get('MAX_ISO')
	MIN_ISO  = stats.get('MIN_ISO')
	MAX_TIER = stats.get('MAX_TIER')
	MAX_LVL  = stats.get('MAX_LVL')
	MAX_OP   = stats.get('MAX_OP')

	# Get list of fields to include
	INC_KEYS = table_format.get('inc_keys')

	# Generate a table ID to allow sorting. 
	table_id = make_next_table_id(html_cache) 
	html_file = [f'<table id="{table_id}">\n']

	# Simplify inclusion of the sort function code
	sort_func = f'class="blub nam" onclick="sort(%s,\'{table_id}\',2)"'

	# Create the headings for the Alliance Info table.
	html_file.append('<tr class="hblu" style="font-size:14pt;">')
	html_file.append(f' <td width="200" rowspan="2" {sort_func % 0}>Name</td>')

	# Simplify inclusion of the sort function code
	sort_func = f'class="blub" onclick="sort(%s,\'{table_id}\',2)"'

	html_file.append(f' <td rowspan="2" {sort_func % 1} style="min-width:80px">Total<br>Power</td>')
	html_file.append(f' <td rowspan="2" {sort_func % 2} style="min-width:80px">Strongest<br>Team</td>')
	html_file.append(f' <td rowspan="2" {sort_func % 3} style="min-width:50px">Total<br>Chars</td>')
	html_file.append(f' <td width="2" rowspan="2" style="background:#343734;"></td>') 				# Vertical Divider
	
	# Alter the size of the header based on the information being included.
	AVG_COLS = [key for key in INC_KEYS if key != 'abil']

	if AVG_COLS:
		AVG = 'Avg' if len(AVG_COLS) == 1 else 'Average'
		html_file.append(f' <td width="{len(AVG_COLS)*50}" colspan="{len(AVG_COLS)}">{AVG}</td>')	# All Avg Stats
		html_file.append(f' <td width="2" rowspan="2" style="background:#343734;"></td>') 			# Vertical Divider

	if MAX_YEL:
		html_file.append(f' <td width="180" colspan="4">Stars</td>')								# Yel - 4 cols
		html_file.append(f' <td width="2" rowspan="2" style="background:#343734;"></td>') 			# Vertical Divider

	if MAX_RED:
		html_file.append(f' <td width="180" colspan="4">Red Stars</td>')							# Red - 4 cols
		html_file.append(f' <td width="2" rowspan="2" style="background:#343734;"></td>') 			# Vertical Divider

	if MAX_DMD:
		html_file.append(f' <td width="{40*MAX_DMD}" colspan="{MAX_DMD}">Diamonds</td>')			# Diamonds - 3 cols
		html_file.append(f' <td width="2" rowspan="2" style="background:#343734;"></td>') 			# Vertical Divider

	if MAX_LVL:
		LVL_COLS = get_lvl_cols(MAX_LVL, stats['DETAILS'])
		html_file.append(f' <td width="{len(LVL_COLS)*55}" colspan="{len(LVL_COLS)}">Levels</td>')
		html_file.append(f' <td width="2" rowspan="2" style="background:#343734;"></td>') 			# Vertical Divider

	if MAX_ISO:
		html_file.append(f' <td width="180" colspan="4">ISO</td>')									# ISO - 4 cols
		html_file.append(f' <td width="2" rowspan="2" style="background:#343734;"></td>') 			# Vertical Divider

	if MAX_TIER:
		html_file.append(f' <td width="240" colspan="5">Gear Tier</td>\n')							# Tier - 5 cols
		html_file.append(f' <td width="2" rowspan="2" style="background:#343734;"></td>') 			# Vertical Divider

	if 'abil' in INC_KEYS:
		html_file.append(f' <td width="180" colspan="4">T4 Abilities</td>')							# Bas/Spc/Ult/Pas
		html_file.append(f' <td width="2" rowspan="2" style="background:#343734;"></td>') 			# Vertical Divider

	if MAX_OP:
		html_file.append(f' <td width="180" colspan="4">OP</td>')		   							 # OP - 4 cols
		html_file.append(f'</tr>')

	# Second Row with subheadings.
	html_file.append('<tr>')

	# Simplify inclusion of the sort function code
	sort_func = f'class="ltbb" onclick="sort(%s,\'{table_id}\',2)"'

	BASE_COLS = 5

	# Averages
	if AVG_COLS:
		for idx, key in enumerate(AVG_COLS):
			LABEL = {'iso':'ISO','op':'OP'}.get(key, key.title())
			html_file.append(f' <td {sort_func % (BASE_COLS+idx)}>{LABEL}</td>')
		BASE_COLS += len(AVG_COLS) + 1

	# Yellow Stars
	if MAX_YEL:
		for idx in range(4):
			LABEL = f'{idx + MAX_YEL-3}' + ('+' if idx!=3 and not ACTUALS else '')
			html_file.append(f' <td {sort_func % (BASE_COLS+idx)}>{LABEL}</td>')
		BASE_COLS += 5
	
	# Red Stars
	if MAX_RED:
		for idx in range(4):
			LABEL = f'{idx + MAX_RED-3}' + ('+' if idx!=3 and not ACTUALS else '')
			html_file.append(f' <td {sort_func % (BASE_COLS+idx)}>{LABEL}</td>')
		BASE_COLS += 5

	# Diamonds are included in Red Stars
	if MAX_DMD:
		for idx in range(MAX_DMD):
			html_file.append(f' <td {sort_func % (BASE_COLS+idx)}>{idx+1}&#x1F48E;</td>')
		BASE_COLS += MAX_DMD+1

	# Simplify inclusion of the sort function code
	sort_func = f'class="ltbb lvl" onclick="sort(%s,\'{table_id}\',2)"'

	# Level Ranges
	if MAX_LVL:
		LVL_BASE = MAX_LVL+4 - (MAX_LVL+4)%5 - 5*stats['DETAILS']

		for idx, key in enumerate(LVL_COLS):
			if ACTUALS:
				LABEL = f'-{key+4 if key<100 else (key+4)%10}' if key < LVL_BASE else ''
			else:
				LABEL = '+' if key < MAX_LVL else ''

			html_file.append(f' <td {sort_func % (BASE_COLS+idx)}>{key}{LABEL}</td>')
		BASE_COLS += len(LVL_COLS)+1

	# Simplify inclusion of the sort function code
	sort_func = f'class="ltbb" onclick="sort(%s,\'{table_id}\',2)"'

	# ISO Levels
	if MAX_ISO:
		# First column is slightly different
		LABEL = f'{MIN_ISO}-{MAX_ISO-3}' if ACTUALS else f'{MAX_ISO-3}+'
		html_file.append(f' <td {sort_func % BASE_COLS}>{LABEL}</td>')

		for idx in range(3):
			LABEL = f'{idx + MAX_ISO-2}' + ('+' if idx!=2 and not ACTUALS else '')
			html_file.append(f' <td {sort_func % (BASE_COLS+idx+1)}>{LABEL}</td>')
		BASE_COLS += 5

	# Gear Tiers
	if MAX_TIER:
		for idx in range(5):
			LABEL = f'{idx + MAX_TIER-4}' + ('+' if idx!=4 and not ACTUALS else '')
			html_file.append(f' <td {sort_func % (BASE_COLS+idx)}>{LABEL}</td>')
		BASE_COLS += 6

	# T4 Abilities
	if 'abil' in INC_KEYS:
		html_file.append(f' <td {sort_func % (BASE_COLS)}>Bas</td>')
		html_file.append(f' <td {sort_func % (BASE_COLS+1)}>Spc</td>')
		html_file.append(f' <td {sort_func % (BASE_COLS+2)}>Ult</td>')
		html_file.append(f' <td {sort_func % (BASE_COLS+3)}>Pas</td>')
		BASE_COLS += 5

	# Overpower Levels
	if MAX_OP:
		for idx in range(4):
			LABEL = f'{idx + MAX_OP-3}' + ('+' if idx!=3 and not ACTUALS else '')
			html_file.append(f' <td {sort_func % (BASE_COLS+idx)}>{LABEL}</td>')
		BASE_COLS +=5

	html_file.append('</tr>')
	
	return html_file



@timed(level=3)
def generate_analysis_body(alliance_info, table_format, stats, hist_date, html_cache):

	# Pull formatting info from table_format
	INC_KEYS  = table_format.get('inc_keys')

	# Pull max values for each type
	MAX_YEL  = stats.get('MAX_YEL')
	MAX_RED  = stats.get('MAX_RED')
	MAX_DMD  = stats.get('MAX_DMD')
	MAX_ISO  = stats.get('MAX_ISO')
	MAX_TIER = stats.get('MAX_TIER')
	MAX_LVL  = stats.get('MAX_LVL')
	MAX_OP   = stats.get('MAX_OP')

	html_file = []

	# Get a sorted list of members to use for this table output.
	member_list = sorted(alliance_info['members'], key = lambda x: alliance_info['members'][x].get('tcp',0), reverse=True)

	# Iterate through each row for members in the table.
	for member in member_list:
		member_info  = alliance_info['members'][member]
		member_stats = stats.get(member,{})
		stats_range  = stats['range']

		# If Member's roster has grown more than 1% from last sync or hasn't synced in more than a week, indicate it is STALE DATA via Grayscale output.
		stale_data = member_info['is_stale']

		html_file.append('<tr>')

		member_url = ''
		if member_info.get('avail'):
			member_url = f' href="https://marvelstrikeforce.com/en/member/{member_info.get("url")}/characters" target="_blank"'
	
		field_color = 'ngra' if stale_data else 'nblu'
		html_file.append(f' <td class="{field_color} urlb"><a style="text-decoration:none; color:black;{member_url}>{member_info.get('display_name',member)}</a></td>')
		
		for stat in ['tcp','stp','tcc']:
			html_file += get_member_stat(member_stats, stats_range, html_cache, stale_data, hist_date, stat)
		html_file.append(' <td></td>') 											# Vertical Divider

		# Averages
		AVG_COLS = [key for key in INC_KEYS if key != 'abil']
		if AVG_COLS:
			for stat in AVG_COLS:
				html_file += get_member_stat(member_stats, stats_range, html_cache, stale_data, hist_date, f'avg_{stat}')
			html_file.append(' <td></td>') 										# Vertical Divider
		
		# Yellow Stars
		if MAX_YEL:
			for key in range(4):
				html_file += get_member_stat(member_stats, stats_range, html_cache, stale_data, hist_date, 'yel', key + MAX_YEL-3)
			html_file.append(' <td></td>') 										# Vertical Divider

		# Red Stars
		if MAX_RED:
			for key in range(4):
				html_file += get_member_stat(member_stats, stats_range, html_cache, stale_data, hist_date, 'red', key + MAX_RED-3)
			html_file.append(' <td></td>') 										# Vertical Divider

		# Diamonds are dependent on Red Stars
		if MAX_DMD:
			for key in range(MAX_DMD):
				html_file += get_member_stat(member_stats, stats_range, html_cache, stale_data, hist_date, 'dmd', key+1)
			html_file.append(' <td></td>') 										# Vertical Divider

		# Level Ranges
		if MAX_LVL:
			for key in get_lvl_cols(MAX_LVL, stats['DETAILS']):
				html_file += get_member_stat(member_stats, stats_range, html_cache, stale_data, hist_date, 'lvl', key)
			html_file.append(' <td></td>') 										# Vertical Divider

		# ISO Levels                                                                                                       
		if MAX_ISO:
			for key in range(4):
				html_file += get_member_stat(member_stats, stats_range, html_cache, stale_data, hist_date, 'iso', key + MAX_ISO-3)
			html_file.append(' <td></td>') 										# Vertical Divider

		# Gear Tiers
		if MAX_TIER:
			for key in range(5):
				html_file += get_member_stat(member_stats, stats_range, html_cache, stale_data, hist_date, 'tier', key + MAX_TIER-4)
			html_file.append(' <td></td>') 										# Vertical Divider

		# T4 Abilities
		if 'abil' in INC_KEYS:
			for stat in ['bas','spc','ult','pas']:
				html_file += get_member_stat(member_stats, stats_range, html_cache, stale_data, hist_date, stat, 7)
			html_file.append(' <td></td>') 										# Vertical Divider

		# OP Ranges
		if MAX_OP:
			for key in range(4):
				html_file += get_member_stat(member_stats, stats_range, html_cache, stale_data, hist_date, 'op', key + MAX_OP-3)

		html_file.append('</tr>')

	html_file.append('</table>')

	return html_file



def get_member_stat(member_stats, stats_range, html_cache, stale_data, hist_date, stat, key=None):

	if key is None:
		member_stat = member_stats.get(stat,0)
		stat_range  = stats_range[stat]
	else:
		member_stat = member_stats.get(stat,{}).get(key,0)
		stat_range  = stats_range.get(stat,{}).get(key,[])
	
	if not member_stat:
		field_value = '-'
	elif member_stat == int(member_stat):
		field_value = f"{member_stat:+,}" if hist_date else f"{member_stat:,}"
	elif member_stat > 10:
		field_value = f"{member_stat:+.1f}" if hist_date else f"{member_stat:.1f}"
	else:
		field_value = f"{member_stat:+.2f}" if hist_date else f"{member_stat:.2f}"

	# Force hist_date to none -- makes more sense than historical coloration
	field_color = get_value_color(stat_range, member_stat, html_cache, stale_data, hist_date=None, color_set='set')

	return [f' <td class="{field_color}">{field_value}</td>']



@timed(level=3)
def get_roster_stats(alliance_info, table_format, stat_type, hist_date=None):

	hist = alliance_info.get('hist',{})
	
	# Calculate stats for most recent roster refresh
	stats = analyze_rosters(alliance_info, table_format, stat_type, hist[max(hist)] if hist else {})

	# Pull formatting info from table_format
	INC_KEYS  = table_format.get('inc_keys')

	# If Historical analysis, a little more work to do.
	if hist_date:

		# Start by deleting ranges. We will need to recalculate these
		stats_range = stats['range'] = {}

		# Calculate stats for requested date
		hist_stats = analyze_rosters(alliance_info, table_format, stat_type, hist[hist_date])

		# Find differences between current stats and hist_stats.
		for member in alliance_info['members']:

			stats[member]['tcp'] -= hist_stats[member]['tcp']
			stats[member]['stp'] -= hist_stats[member]['stp']
			stats[member]['tcc'] -= hist_stats[member]['tcc']

			stats_range.setdefault('tcp',[]).append(stats[member]['tcp'])
			stats_range.setdefault('stp',[]).append(stats[member]['stp'])
			stats_range.setdefault('tcc',[]).append(stats[member]['tcc'])

			# Totals (and create dicts for the rest of the ranges)
			for key in [key for key in INC_KEYS if key != 'abil']:
				stats[member]['avg_'+key] -= hist_stats[member].get('avg_'+key, 0)
				stats_range.setdefault('avg_'+key,[]).append(stats[member]['avg_'+key])		
				
			# Yellow Stars
			if stats.get('MAX_YEL'):
				for key in range(4):
					get_stat_diff(stats, hist_stats, member, 'yel', key + stats.get('MAX_YEL')-3)

			# Red Stars
			if stats.get('MAX_RED'):
				for key in range(4):
					get_stat_diff(stats, hist_stats, member, 'red', key + stats.get('MAX_RED')-3)

			# Diamonds
			if stats.get('MAX_DMD'):
				for key in range(1,6):
					get_stat_diff(stats, hist_stats, member, 'dmd', key)

			# ISO Levels
			if stats.get('MAX_ISO'):
				for key in range(4):
					get_stat_diff(stats, hist_stats, member, 'iso', key + stats.get('MAX_ISO')-3)

			# Gear Tiers
			if stats.get('MAX_TIER'):
				for key in range(5):
					get_stat_diff(stats, hist_stats, member, 'tier', key + stats.get('MAX_TIER')-4)

			# Level Ranges
			if stats.get('MAX_LVL'):
				for key in get_lvl_cols(stats.get('MAX_LVL'), stats['DETAILS']):
					get_stat_diff(stats, hist_stats, member, 'lvl', key)

			# OP Ranges
			if stats.get('MAX_OP'):
				for key in range(4):
					get_stat_diff(stats, hist_stats, member, 'op', key + stats.get('MAX_OP')-3)

			# T4 Abilities
			if 'abil' in INC_KEYS:
				for stat in ['bas','spc','ult','pas']:
					get_stat_diff(stats, hist_stats, member, stat, 7)
	
	return stats



# Generate the list of keys used for Level columns
@timed(level=3)
def get_lvl_cols(MAX_LVL, DETAILS):

	# Return the basic five column output if not using Detailed Levels mode
	if not DETAILS:
		return [key*5 + MAX_LVL-20 for key in range(5)]

	# Find the start of the individually reported levels
	LVL_BASE = MAX_LVL+4 - (MAX_LVL+4)%5 - 5

	# List of the individually reported levels
	LVL_COLS = list(range(LVL_BASE, MAX_LVL+1))

	# Calculate the number of 5-level columns required 
	NUM_COLS = 7 - len(LVL_COLS)

	# List of the lower limits of the 5-level ranged columns, i.e. 90 = 90-94
	LVL_REST = list(range(LVL_BASE-5*NUM_COLS, LVL_BASE, 5))

	# Return the combination of ranged and individually reported columns
	return LVL_REST + LVL_COLS



# Calculate differences and add the result to the range lists
def get_stat_diff(stats, hist_stats, member, stat, key):
	stats[member].setdefault(stat,{})[key] = stats[member].get(stat,{}).get(key,0) - hist_stats[member].get(stat,{}).get(key,0)
	stats['range'].setdefault(stat,{}).setdefault(key,[]).append(stats[member][stat][key])



@timed(level=3)
def analyze_rosters(alliance_info, table_format, stat_type, rosters_to_analyze):

	# Pull formatting info from table_format
	INC_KEYS = [key for key in table_format.get('inc_keys') if key != 'abil']
	INC_ABIL = 'abil' in table_format.get('inc_keys')

	# Create stats and stats_range to start
	stats = {}
	stats_range = stats.setdefault('range',{})

	# We'll be making changes, work with a copy.
	rosters_to_analyze = copy.deepcopy(rosters_to_analyze)

	# Which Characters should be included in Analysis
	FILTER_BY = table_format.get('filter_by', 'All Chars')
	filtered_chars = filter_by_traits(FILTER_BY)

	# Find MAX_LVL if Levels included in output
	if 'lvl' in INC_KEYS:

		levels = {member_info['level'] for member_info in alliance_info['members'].values()}

		# Find MAX_LVL based on earned levels, i.e. next multiple of 5
		MAX_LVL = max(levels)+4-(max(levels)+4)%5

		# Detailed levels trigger if a number of criteria met
		# * More than one level is present
		# * All levels are within range MAX_LVL-5 to MAX_LVL

		stats['DETAILS'] = DETAILS = len(levels) > 1 and all(level in range(MAX_LVL-5, MAX_LVL+1) for level in levels)

		# If not DETAILS, MAX_LVL has min value 20
		stats['MAX_LVL'] = MAX_LVL = max(levels) if DETAILS else max(MAX_LVL, 20)

	# Find MAX_ISO if ISO included in output
	if 'iso' in INC_KEYS:

		# MAX_ISO has min value 8
		stats['MAX_ISO'] = MAX_ISO = max({stats.get("iso",0) for processed in rosters_to_analyze.values() for char, stats in processed.items() if char in filtered_chars} | {8})

		# Use MAX_ISO to determine MIN_ISO
		stats['MIN_ISO'] = MIN_ISO = MAX_ISO-(MAX_ISO-1)%5-5 if MAX_ISO > 10 else 1

	# Start by doing stat analysis.	
	for member in alliance_info['members']:

		tot_vals = {'power':[]}
	
		# Get a little closer to our work.
		member_stats = stats.setdefault(member,{})

		# Loop through every char
		for char, char_stats in rosters_to_analyze.get(member,{}).items():

			# Skip processing of anything that isn't in our list
			if char not in filtered_chars:
				continue

			# Use for Total / Average # columns -- do this BEFORE normalizing data
			for key in INC_KEYS:
				tot_vals[key] = tot_vals.get(key,0) + char_stats.get(key,0)

			# Normalize the data.
			# If stat_type = 'actual', combine ISO and LVL columns before tallying
			# If 'progressive', make each entry count in those below it

			# For either stat_type, combine certain columns for ISO and Level data

			# If DETAILS, need to preprocess for 'lvl' < TOP_LVL-5
			# Info from MAX_LVL-5 to MAX_LVL will not be normalized
			if 'lvl' in INC_KEYS and (not DETAILS or char_stats['lvl'] < MAX_LVL-5):

				# Round level down to nearest multiple of 5
				char_stats['lvl'] -= char_stats['lvl']%5			

			# Gather ISO 6-11 into ISO 12
			if 'iso' in INC_KEYS and stat_type == 'actual' and char_stats['iso'] in range(MIN_ISO, MAX_ISO-3):
				char_stats['iso'] = MAX_ISO-3

			# Just tally the values in each key. Increment the count of each value found
			for key in INC_KEYS:
				if stat_type == 'progressive':
					for x in range(0,char_stats.get(key,0)+1):
						member_stats.setdefault(key,{})[x] = member_stats.get(key,{}).setdefault(x,0)+1
				else:
					member_stats.setdefault(key,{})[char_stats.get(key,0)] = member_stats.get(key,{}).setdefault(char_stats.get(key,0),0)+1
					
			# Abilities have to be treated a little differently
			if INC_ABIL:
				bas,abil = divmod(char_stats['abil'],1000)
				spc,abil = divmod(abil,100)
				ult,pas  = divmod(abil,10)
				abil_stats = {'bas':bas, 'spc':spc, 'ult':ult, 'pas':pas}
				
				# Normalize skill data: anything T4 and above is included in level 7
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
		# If no roster data available, use values from alliance_info
		else:
			member_stats['tcp'] = alliance_info['members'].get(member,{}).get('tcp')
			member_stats['stp'] = alliance_info['members'].get(member,{}).get('stp')
			member_stats['tcc'] = alliance_info['members'].get(member,{}).get('tcc')

		# Calculate alliance-wide ranges for each statistic
		stats_range.setdefault('tcp',[]).append(member_stats['tcp'])
		stats_range.setdefault('stp',[]).append(member_stats['stp'])
		stats_range.setdefault('tcc',[]).append(member_stats['tcc'])

		# Calc avg_ values from tot_ values
		for key in INC_KEYS:
			member_stats['avg_'+key] = tot_vals.get(key,0) / max(member_stats['tcc'],1)

			# Add these average to our ranges
			stats_range.setdefault('avg_'+key,[]).append(member_stats['avg_'+key])

			# Build range for each stat as we go
			for entry in member_stats.get(key,{}):
				stats_range.setdefault(key,{}).setdefault(entry,[]).append(member_stats[key][entry])

		# Build ranges for the abilities as well
		if INC_ABIL:
			for key in ['bas','spc','ult','pas']:
				for entry in member_stats.get(key,{}):
					stats_range.setdefault(key,{}).setdefault(entry,[]).append(member_stats[key][entry])

	# Finally, pre-calculate other maxes for each range with set mins
	if 'yel' in INC_KEYS:
		stats['MAX_YEL']  = max(max(stats_range.get('yel', [0])), 4)
	if 'red' in INC_KEYS:	
		stats['MAX_RED']  = max(max(stats_range.get('red', [0])), 4)
		stats['MAX_DMD']  = max(stats_range.get('dmd', [0]))
		stats['MAX_DMD']  = 3 if stats['MAX_DMD'] in (1,2) else stats['MAX_DMD']
	if 'tier' in INC_KEYS:
		stats['MAX_TIER'] = max(max(stats_range.get('tier', [0])), 5)
	if 'op' in INC_KEYS:
		stats['MAX_OP']   = max(max(stats_range.get('op', [0])), 4)

	return stats

