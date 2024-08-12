#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_alliance_info.py
Generate the tab for Alliance Info output.  
"""

from log_utils import timed

import datetime

from html_cache  import make_next_table_id
from html_shared import *


# Generate just the Alliance Tab contents.
@timed(level=3)
def generate_alliance_tab(alliance_info, using_tabs=False, hist_date=None, html_cache={}):

	html_file = ''
	
	# Conditionally include Arena/Blitz columns.
	ARENA_BLITZ_ENABLED = False

	# Start by sorting members by TCP.
	alliance_order = sorted(alliance_info['members'], key = lambda x: alliance_info['members'][x].get('tcp',0), reverse=True)
	
	# Build up the list of Alliance Members in the order we will present them.
	member_list =  []
	if alliance_info.get('leader'):
		member_list = [alliance_info.get('leader')]
	
	member_list += [member for member in alliance_order if member in alliance_info.get('captains',[])]
	member_list += [member for member in alliance_order if member not in member_list]

	tot_power = sum([alliance_info['members'][member].get('tcp',0) for member in alliance_info['members']])
	avg_power = int(tot_power/len(alliance_info['members']))

	# See if name includes a color tag.
	alt_color = extract_color(alliance_info['name'])

	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file += '<div id="AllianceInfo" class="tcon">\n'

	# Generate a table ID to allow sorting. 
	table_id = make_next_table_id(html_cache) 
	html_file += '<table id="%s" style="background:#222";>\n' % (table_id)

	html_file += '<tr>\n</tr>\n'

	html_file += '<tr style="font-size:18px;color:white;">\n'
	html_file += ' <td colspan="2"><img src="https://assets.marvelstrikeforce.com/www/img/logos/logo-en.png" alt=""></td>\n'
	html_file += ' <td colspan="%s" class="alliance_name"%s>%s</td>\n' % (8+ 2*ARENA_BLITZ_ENABLED, alt_color, alliance_info['name'].upper())
	html_file += ' <td colspan="2"><div style="image-rendering:crisp-edges; transform:scale(1.5);"><img src="https://assets.marvelstrikeforce.com/imgs/ALLIANCEICON_%s.png" alt=""/></div></td>\n' % (alliance_info.get('image','EMBLEM_6_dd63d11b'))
	html_file += '</tr>\n'

	# Simplify inclusion of the sort function code
	sort_func = 'class="%s" onclick="sort(%s,\'%s\',3)"' % ("blub", '%s', table_id)

	# Create the headings for the Alliance Info table.
	html_file += '<tr class="hblu" style="font-size:14pt;position:relative;">\n'
	html_file += ' <td width="60"></td>\n'
	html_file += f' <td width="215" {sort_func % 1}>Name</td>\n'            
	html_file += f' <td width="110" {sort_func % 2}>Level</td>\n'
	html_file += f' <td width="110" {sort_func % 3}>Role</td>\n'
	html_file += f' <td width="110" {sort_func % 4}>Collection<br>Power</td>\n'
	html_file += f' <td width="110" {sort_func % 5}>Strongest<br>Team</td>\n'
	html_file += f' <td width="110" {sort_func % 6}>Total<br>Collected</td>\n'
	html_file += f' <td width="110" {sort_func % 7}>Max<br>Stars</td>\n'

	# Conditionally include columns.
	if ARENA_BLITZ_ENABLED:
		html_file += f' <td width="110" {sort_func % 8}>Arena<br>Rank</td>\n'
		html_file += f' <td width="110" {sort_func % 9}>Blitz<br>Wins</td>\n'

	# Change the sort routine depending on whether Arena/Blitz columns present.
	sort_func = 'class="%s" onclick="sort(%s+%s,\'%s\',3)"' % ("blub", '%s', ARENA_BLITZ_ENABLED*2, table_id)

	html_file += f' <td width="110" {sort_func % 8}>War<br>MVP</td>\n'
	html_file += f' <td width="110" {sort_func % 9}>Total<br>Stars</td>\n'
	html_file += f' <td width="110" {sort_func % 10}>Total<br>Red</td>\n'
	html_file += f' <td width="215" {sort_func % 11}>Last Updated:</td>\n'
	html_file += '</tr>\n'
	
	tcp_range   = [alliance_info['members'][member].get('tcp',0)   for member in member_list]
	stp_range   = [alliance_info['members'][member].get('stp',0)   for member in member_list]
	tcc_range   = [alliance_info['members'][member].get('tcc',0)   for member in member_list]
	mvp_range   = [alliance_info['members'][member].get('mvp',0)   for member in member_list]
	max_range   = [alliance_info['members'][member].get('max',0)   for member in member_list]
	
	# Conditionally include columns.
	if ARENA_BLITZ_ENABLED:
		arena_range = [alliance_info['members'][member].get('arena',0) for member in member_list]
		blitz_range = [alliance_info['members'][member].get('blitz',0) for member in member_list]
	
	stars_range = [alliance_info['members'][member].get('stars',0) for member in member_list]
	red_range   = [alliance_info['members'][member].get('red',0)   for member in member_list]
	
	for member in member_list:
		# Get a little closer to what we're working with.
		member_stats = alliance_info['members'][member]

		# If Member's roster has grown more than 1% from last sync or hasn't synced in more than a week, indicate it is STALE DATA via Grayscale output.
		stale_data = member_stats['is_stale']
		
		member_color = ['#B0E0E6','#DCDCDC'][stale_data]

		if member in alliance_info.get('leader',[]):
			member_role = '<a> Leader </a>'
		elif member in alliance_info.get('captains',[]):
			member_role = 'Captain'
			member_color = ['#00BFFF','#A9A9A9'][stale_data]		
		else:
			member_role = 'Member'

		html_file += ' <tr style="background:%s; font-size:22px;">\n' % (member_color)
		html_file += '  <td style="padding:0px;"><img height="45" src="https://assets.marvelstrikeforce.com/imgs/Portrait_%s.png"/></td>\n' % (member_stats.get('image','ShieldDmg_Defense_3dea00f7'))

		member_url = ''
		if member_stats.get('avail'):
			member_url = f' href="https://marvelstrikeforce.com/en/member/{member_stats.get("url")}/characters" target="_blank"'

		# If hist_date was requested, add date under the name field.
		second_line = ''
		# If no hist_date, see if we have a discord name to include.
		if member_stats.get('discord'):
			second_line = f'<br><span style="font-size:16px">@{member_stats.get("discord",{}).get("name","")}</span>'

		#
		# Can we wrap this STYLE inside of the class? 
		#

		html_file += '  <td class="urlb"><a style="text-decoration:none; color:black;"%s><span class="bd">%s</span>%s</a></td>\n' % (member_url, member_stats.get('display_name',member), second_line)

		html_file += '  <td>%s</td>\n' % (member_stats.get('level','n/a'))
		html_file += '  <td>%s</td>\n' % (member_role)
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(tcp_range,   member_stats.get('tcp',0),   html_cache, stale_data), f'{member_stats.get("tcp",0):,}')
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(stp_range,   member_stats.get('stp',0),   html_cache, stale_data), f'{member_stats.get("stp",0):,}')
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color_ext(max(tcc_range)-5, max(tcc_range),   member_stats.get('tcc',0),   html_cache, stale_data), f'{member_stats.get("tcc",0):,}')
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(max_range,   member_stats.get('max',0),   html_cache, stale_data), f'{member_stats.get("max",0):,}')

		# Conditionally include columns.
		if ARENA_BLITZ_ENABLED:
			html_file += '  <td class="%s">%s</td>\n' % (get_value_color_ext(max(arena_range), min(arena_range), member_stats.get('arena',0), html_cache, stale_data), f'{member_stats.get("arena",0):,}')
			html_file += '  <td class="%s">%s</td>\n' % (get_value_color(blitz_range, member_stats.get('blitz',0), html_cache, stale_data), f'{member_stats.get("blitz",0):,}')
			
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(mvp_range,   member_stats.get('mvp',0),   html_cache, stale_data), f'{member_stats.get("mvp",0):,}')
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(stars_range, member_stats.get('stars',0), html_cache, stale_data), f'{member_stats.get("stars",0):,}')
		html_file += '  <td class="%s">%s</td>\n' % (get_value_color(red_range,   member_stats.get('red',0),   html_cache, stale_data), f'{member_stats.get("red",0):,}')

		if 'last_update' in member_stats:
			last_update = datetime.datetime.now() - member_stats['last_update']
			time_color  = get_value_color_ext(4*86400, 0, last_update.total_seconds(), html_cache, stale_data)
			
			if stale_data:
				time_value = f'<b><i> {("Stale. Re-sync.","EMPTY. Please Sync.")[not member_stats.get("tot_power")]} </i></b><br>%s, %sd ago' % (member_stats['last_update'].strftime('%b %d'), last_update.days)
			else:
				time_value = '%s%s ago<br>%s' % (['',f'{last_update.days} days, '][not last_update.days], str(last_update).split('.')[0], member_stats['last_update'].strftime('%a, %b %d')) 
		else:
			time_color = get_value_color_ext(0, 1, 0, html_cache)
			time_value = 'ROSTER NOT SHARED<br><b><i>Set to ALLIANCE ONLY.</i></b>'
		
		html_file += '  <td class="%s" style="font-size:18px;">%s</td>\n' % (time_color, time_value)
		html_file += ' </tr>\n'

	html_file += '</table>\n'
	
	# Only include Dividers if using as part of a multi-tab document
	if using_tabs:
		html_file += '</div>\n'

	return html_file
