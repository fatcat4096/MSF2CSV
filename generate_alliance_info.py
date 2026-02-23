#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_alliance_info.py
Generate the tab for Alliance Info output.  
"""

from log_utils import timed

from datetime    import datetime
from file_io     import remove_tags
from html_cache  import make_next_table_id
from html_shared import *


# Generate just the Alliance Tab contents.
@timed(level=3)
def generate_alliance_tab(alliance_info, html_cache, hist_date, using_tabs=False):

	html_file = ''
	
	# Start by sorting members by TCP.
	alliance_order = sorted(alliance_info['members'], key = lambda x: alliance_info['members'][x].get('tcp',0), reverse=True)
	
	# Build up the list of Alliance Members in the order we will present them.
	member_list =  []
	if alliance_info.get('leader'):
		member_list = [alliance_info.get('leader')]
	
	member_list += [member for member in alliance_order if member in alliance_info.get('captains',[])]
	member_list += [member for member in alliance_order if member not in member_list]

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file += '<div id="AllianceInfo" class="tcon">\n'

	# Generate a table ID to allow sorting. 
	table_id = make_next_table_id(html_cache) 
	html_file += f'<table id="{table_id}" style="background:#222";>\n'

	html_file += '<tr>\n</tr>\n'

	html_file += '<tr style="font-size:18px;color:white;">\n'
	html_file += ' <td colspan="2"><img src="https://assets.marvelstrikeforce.com/www/img/logos/logo-en.png" alt=""></td>\n'
	html_file += ' <td colspan="8" class="alliance_name">%s</td>\n' % (remove_tags(alliance_info.get('name','').upper()))
	
	# Frame and Image for Alliance
	EMBLEM_URL = f"https://assets.marvelstrikeforce.com/imgs/ALLIANCEICON_{alliance_info.get('image','EMBLEM_6_dd63d11b')}.png"
	FRAME_URL  = f"https://assets.marvelstrikeforce.com/imgs/ALLIANCEICON_{alliance_info.get('frame','FRAME_15_174f8048')}.png"

	html_file += f' <td colspan="2"><div class="lrg_img" style="background-image:url({EMBLEM_URL});">\n'
	html_file += f'  <div class="lrg_rel"><img class="lrg_rel" src="{FRAME_URL}" alt=""/></div>\n'
	html_file += ' </div></td>\n'
	
	html_file += '</tr>\n'

	# Control column width
	w070 = 'style="min-width:70px;"'
	w110 = 'style="min-width:110px;"'
	w215 = 'style="min-width:215px;"'

	# Simplify inclusion of the sort function code
	sort_func = 'class="%s" onclick="sort(%s,\'%s\',3)"' % ("blub", '%s', table_id)

	# Create the headings for the Alliance Info table
	html_file += '<tr class="hblu" style="font-size:14pt;position:relative;">\n'
	html_file += f' <td {w070}></td>\n'
	html_file += f' <td {sort_func % 1} {w215}>Name</td>\n'            
	html_file += f' <td {sort_func % 2} {w070}>Level</td>\n'
	html_file += f' <td {sort_func % 3} {w110}>Role</td>\n'
	html_file += f' <td {sort_func % 4} {w110}>Collection<br>Power</td>\n'
	html_file += f' <td {sort_func % 5} {w110}>Strongest<br>Team</td>\n'
	html_file += f' <td {sort_func % 6} {w110}>Total<br>Collected</td>\n'
	html_file += f' <td {sort_func % 7} {w070}>Max<br>Stars</td>\n'
	html_file += f' <td {sort_func % 8} {w070}>War<br>MVP</td>\n'
	html_file += f' <td {sort_func % 9} {w070}>Total<br>Stars</td>\n'
	html_file += f' <td {sort_func % 10} {w070}>Total<br>Red</td>\n'
	html_file += f' <td {sort_func % 11} {w215}>Last Updated:</td>\n'
	html_file += '</tr>\n'
	
	# Find ranges to use for color calculations
	tcp_range   = [alliance_info['members'][member].get('tcp',0)   for member in member_list]
	stp_range   = [alliance_info['members'][member].get('stp',0)   for member in member_list]
	tcc_range   = [alliance_info['members'][member].get('tcc',0)   for member in member_list]
	mvp_range   = [alliance_info['members'][member].get('mvp',0)   for member in member_list]
	max_range   = [alliance_info['members'][member].get('max',0)   for member in member_list]
	stars_range = [alliance_info['members'][member].get('stars',0) for member in member_list]
	red_range   = [alliance_info['members'][member].get('red',0)   for member in member_list]

	for member in member_list:
	
		# Get a little closer to what we're working with
		member_stats = alliance_info['members'].get(member,{})
		hist_stats   = alliance_info['hist'][hist_date].get(member,{}) if hist_date else {}

		# Calculate stats if we're working with Historical Data
		hist_calcs = {}
		if hist_stats:
			# Pre-calc stat lists
			powers = [hist_stats.get(char,{}).get('power',0) for char in hist_stats]
			stars  = [hist_stats.get(char,{}).get('yel',0) for char in hist_stats]
			levels = [hist_stats.get(char,{}).get('lvl',0) for char in hist_stats]
			reds   = [hist_stats.get(char,{}).get('red',0) for char in hist_stats]

			# Calculate historical values for these stats using hist snapshots
			hist_calcs['tcp']   = sum(powers)
			hist_calcs['level'] = max(levels)
			hist_calcs['stp']   = sum(sorted(powers, reverse=True)[:5])
			hist_calcs['tcc']   = len([char for char in powers if char])
			hist_calcs['max']   = len([star for star in stars if star==7])
			hist_calcs['stars'] = sum(stars)
			hist_calcs['red']   = sum(reds)			

		# If Member's roster has grown more than 1% from last sync or hasn't synced in more than a week, indicate it is STALE DATA via Grayscale output
		stale_data = member_stats['is_stale']
		
		member_color = ['#B0E0E6','#DCDCDC'][stale_data]

		if member in alliance_info.get('leader',[]):
			member_role = '<a> Leader </a>'
		elif member in alliance_info.get('captains',[]):
			member_role = 'Captain'
			member_color = ['#00BFFF','#A9A9A9'][stale_data]		
		else:
			member_role = 'Member'

		member_url = ''
		if member_stats.get('avail'):
			member_url = f' href="https://marvelstrikeforce.com/en/member/{member_stats.get("url")}/characters" target="_blank"'

		member_name = member_stats.get('display_name',member)

		# Do we need a second line for the Name cell?
		name_second = ''
		lvl_second = ''

		# If no hist_date, see if we have a discord name to include
		if member_stats.get('discord'):
			name_second = f'<br><span class="sub">@{member_stats.get("discord",{}).get("name","")}</span>'
		# If hist_date was requested, add date under the name field
		elif hist_date:
			name_second = f'<br><span class="sub">(since {hist_date.strftime("%m/%d/%y")})</span>'

		# Do we need a second line for the Level cell?
		lvl_second = ''

		# Calculations for previous level
		curr_lvl = member_stats.get('level')
		hist_lvl = hist_calcs.get('level')

		# If hist_date was requested and level has changed, add under the level field
		if curr_lvl and hist_lvl and curr_lvl != hist_lvl:
			lvl_second = f'<br><span class="sub">({curr_lvl-hist_lvl:+,})</span>'

		#
		# STARTING THE TABLE ROWS
		#

		html_file += f' <tr style="background:{member_color}; font-size:22px; line-height:100%; vertical-align:middle;">\n'

		# Frame and Image
		
		IMG_URL = member_stats.get('image','ShieldDmg_Defense_3dea00f7')+'.png'
		IMG_URL = IMG_URL if 'https' in IMG_URL else f'https://assets.marvelstrikeforce.com/imgs/Portrait_{IMG_URL}'
		
		FRAME_URL = f"https://assets.marvelstrikeforce.com/imgs/ICON_FRAME_{member_stats.get('frame','0_ab6f69b8')}.png"
		
		html_file += f'  <td class="hblu"><div class="sml_img" style="background-size:45px;background-image:url({FRAME_URL});">\n'
		html_file += f'   <div class="sml_rel"><img height="45" class="sml_rel" src="{IMG_URL}" alt=""/></div>\n'
		html_file += f'  </div></td>\n'

		# Name Field
		html_file += f'  <td class="urlb"><a class="urlb"{member_url}><span class="bd">{member_name}</span>{name_second}</a></td>\n'

		# Level and Member Role
		html_file += f'  <td>{curr_lvl or "n/a"}{lvl_second}</td>\n'
		html_file += f'  <td>{member_role}</td>\n'

		# Member Stats
		html_file += alliance_info_cell(tcp_range,   'tcp',   member_stats, hist_calcs, html_cache, stale_data)
		html_file += alliance_info_cell(stp_range,   'stp',   member_stats, hist_calcs, html_cache, stale_data)
		html_file += alliance_info_cell(tcc_range,   'tcc',   member_stats, hist_calcs, html_cache, stale_data)
		html_file += alliance_info_cell(max_range,   'max',   member_stats, hist_calcs, html_cache, stale_data)
		html_file += alliance_info_cell(mvp_range,   'mvp',   member_stats, hist_calcs, html_cache, stale_data)
		html_file += alliance_info_cell(stars_range, 'stars', member_stats, hist_calcs, html_cache, stale_data)
		html_file += alliance_info_cell(red_range,   'red',   member_stats, hist_calcs, html_cache, stale_data)

		# Last Update formatting
		if 'last_update' in member_stats:
			last_update = datetime.now() - member_stats['last_update']
			time_color  = get_value_color_ext(4*86400, 0, last_update.total_seconds(), html_cache, stale_data)
			
			if stale_data:
				time_value = f'<b><i> {("Stale. Re-sync.","EMPTY. Please Sync.")[not member_stats.get("tot_power")]} </i></b><br>%s, {last_update.days}d ago' % (member_stats['last_update'].strftime('%b %d'), )
			else:
				time_value = '%s%s ago<br>%s' % (['',f'{last_update.days} days, '][not last_update.days], str(last_update).split('.')[0], member_stats['last_update'].strftime('%a, %b %d')) 
		else:
			time_color = 'xx'
			time_value = 'ROSTER NOT SHARED<br><i>Set to <b>ALLIANCE ONLY</b></i>'
		
		html_file += f'  <td class="{time_color}" style="font-size:18px;white-space:nowrap">{time_value}</td>\n'
		html_file += ' </tr>\n'

	html_file += '</table>\n'
	
	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file += '</div>\n'

	return html_file



def alliance_info_cell(value_range, key, member_stats, hist_calcs, html_cache, stale_data):
	
	curr_value = member_stats.get(key,0)
	hist_value = hist_calcs.get(key,0)

	# Calculate the Difference and see if we need a second line
	diff_value = curr_value-hist_value if hist_value else 0
	diff_value = f'<br><span class="sub"><i>({get_field_value(diff_value, True)})</i></span>' if diff_value else '' 
	
	# Determine field color
	field_color = get_value_color(value_range, curr_value, html_cache, stale_data, color_set='set')

	# Return the completed cell
	return f'  <td class="{field_color}">{curr_value:,}{diff_value}</td>\n'



