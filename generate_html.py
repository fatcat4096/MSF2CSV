#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_html.py
Takes the processed alliance / roster data and generate readable output to spec.  
"""

import datetime

# Routines to create color gradient for heat map
from gradients import *	


# Build the entire file -- headers, footers, and tab content for each lane and the Alliance Information.
def generate_html(alliance_info, nohist, table):

	default_lanes = [[{'traits': ['Mutant']},
					  {'traits': ['Bio']},
					  {'traits': ['Skill']},
					  {'traits': ['Mystic']},
					  {'traits': ['Tech']}]]

	lanes      = table.get('lanes',default_lanes)
	table_name = table.get('name','')
	
	# If we're doing a single lane format and we have history, let's generate a historical data tab. 
	hist_tab = ''
	if len(lanes) == 1 and len(alliance_info['hist'])>1 and {'power','tier','iso','lvl'}.issuperset(table.get('keys',[])) and not nohist:
		hist_tab = "CHANGES SINCE %s" % min(alliance_info['hist'])

	# Gotta start somewhere.
	html_file = '<!doctype html>\n<html lang="en">\n'

	# Add a header to give us a tabbed interface.
	html_file += add_tabbed_header(len(lanes), hist_tab, table_name)
	
	# Add a tab for each lane. 
	html_file += generate_lanes(alliance_info, table, lanes)

	# Add a historical info tab.
	if hist_tab:
		html_file += generate_lanes(alliance_info, table, lanes, hist_tab)

	# After all Lanes are added, add the Alliance Info tab.
	html_file += generate_alliance_tab(alliance_info)

	# Finally, add the Javascript to control tabbed display.
	html_file += add_tabbed_footer()
	
	# All done with All Lanes. Close the file.
	html_file += '</html>\n'

	return html_file


# Generate the contents for each lane.
def generate_lanes(alliance_info, table, lanes, hist_tab = '', html_file = ''):

	# Iterate through all the lanes. Showing tables for each section. 
	for lane in lanes:
		
		# Display each lane in a separate tab.
		lane_num = lanes.index(lane)+1
		html_file += '<div id="%s%i" class="tabcontent">\n' % (['Hist','Lane'][not hist_tab], lane_num)

		# Process each section individually, filtering only the specified traits into the Active Chars list.
		for section in lane:
		
			meta_chars, other_chars = get_meta_other_chars(alliance_info, table, section, hist_tab)
			keys = table.get('keys',['power','tier','iso'])

			# Use the full Player List if explicit Strike Teams haven't been defined.
			strike_teams = alliance_info['strike_teams'].get(table.get('strike_teams'), [get_player_list(alliance_info)])

			# Start with the Basic Table Label and Colors.
			table_lbl = '<br>'.join([translate_name(trait) for trait in section['traits']]).upper()

			# Only calling it twice if we have meta_chars defined.
			if meta_chars:
				meta_lbl = table_lbl+'<br><span class="table_subtitle">META</span>'

				html_file += '<table>\n <tr>\n  <td>\n'
				html_file += generate_table(alliance_info, keys, meta_chars, strike_teams, meta_lbl, get_stp_list(alliance_info, meta_chars, hist_tab), hist_tab)
				html_file += '  </td>\n  <td>\n   <br>\n  </td>\n  <td>\n'

				# Differentiate Others Section from Meta Section
				table_lbl += '<br><span class="table_subtitle">OTHERS</span>'

			# Always generate the Others table.
			# Only label it as such if Meta section exists.
			html_file += generate_table(alliance_info, keys, other_chars, strike_teams, table_lbl, get_stp_list(alliance_info, meta_chars+other_chars, hist_tab), hist_tab)

			# If in a nested table, close the nested table.
			if meta_chars:
				html_file += '  </td>\n </tr>\n</table>\n'

			# If not the final section, add a divider row. 
			if lane.index(section) != len(lane)-1:
				html_file += '    <p></p>\n'

		# After Lane content is done, close the div for the Tab implementation.
		html_file += '</div>\n'

	return html_file


# Split meta chars from other chars. Filter others based on provided traits.
def get_meta_other_chars(alliance_info, table, section, hist_tab):

	# Get the list of usable characters
	char_list = get_char_list (alliance_info)

	# Meta Chars not subject to min requirements. Filter out only uncollected heroes.
	meta_chars = section.get('meta',[])
	meta_chars.sort()
	meta_chars = [char for char in char_list if char in meta_chars]

	# Other is everything left over. 
	other_chars = [char for char in char_list if not char in meta_chars]

	# Load up arguments from table, with defaults if necessary.
	min_iso  = table.get('min_iso', 0)
	min_tier = table.get('min_tier',0)

	# Get the list of Alliance Members we will iterate through as rows.	
	player_list = get_player_list (alliance_info)

	# If there are minimums or trait filters for this section, evaluate each character before using the active_chars list.
	if min_iso:
		other_chars = [char for char in other_chars if max([int(alliance_info['members'][player]['processed_chars'][char]['iso']) for player in player_list]) >= min_iso]

	if min_tier:
		other_chars = [char for char in other_chars if max([int(alliance_info['members'][player]['processed_chars'][char]['tier']) for player in player_list]) >= min_tier]
	
	# Get extracted_traits from alliance_info
	extracted_traits = alliance_info['extracted_traits']
	
	# Trait filters are additive. Only filter other_chars.
	traits = section['traits']
	if traits:
		for char in other_chars[:]:
			for trait in traits:
				if trait in extracted_traits and char in extracted_traits[trait]:
					# Character has at least one of these traits. Leave it in.
					break
			# Did we find this char in any of the traits?
			if trait not in extracted_traits or char not in extracted_traits[trait]:
				other_chars.remove(char)

	# Filter out anyone with zero power, i.e. which no one has summoned.
	meta_chars  = [char for char in meta_chars  if sum([int(alliance_info['members'][player]['processed_chars'][char]['power']) for player in player_list])]
	other_chars = [char for char in other_chars if sum([int(alliance_info['members'][player]['processed_chars'][char]['power']) for player in player_list])]

	# If historical, filter out anyone who's had zero change in power. 
	if hist_tab:
		meta_chars  = [char for char in meta_chars  if sum([int(alliance_info['members'][player]['processed_chars'][char]['power'])-int(find_oldest_val(alliance_info, player, char, 'power')) for player in player_list])]
		other_chars = [char for char in other_chars if sum([int(alliance_info['members'][player]['processed_chars'][char]['power'])-int(find_oldest_val(alliance_info, player, char, 'power')) for player in player_list])]

	# If only meta specified, just move it to others so we don't have to do anything special.
	if meta_chars and not other_chars:
		other_chars, meta_chars = meta_chars, other_chars
		
	return meta_chars, other_chars


# Generate individual tables for Meta/Other chars for each raid section.
def generate_table(alliance_info, keys=['power','tier','iso'], char_list=[], strike_teams = [], table_lbl='', all_team_pwr={}, hist_tab = '', html_file = ''):

	# Get the list of Alliance Members we will iterate through as rows.	
	player_list = get_player_list (alliance_info)

	if table_lbl.find('OTHERS') == -1:
		title_cell    = 'title_cell_blue'
		table_header  = 'table_header_blue'
		char_cell     = 'char_cell_blue'
		name_cell     = 'name_cell_blue'
		name_cell_alt = 'name_cell_blue_alt'
		team_pwr_lbl  = 'Team<br>Power'
	else:
		title_cell    = 'title_cell_gray'
		table_header  = 'table_header_gray'
		char_cell     = 'char_cell_gray'
		name_cell     = 'name_cell_gray'
		name_cell_alt = 'name_cell_gray_alt'
		team_pwr_lbl  = 'STP<br>(Top 5)'

	# Let's get this party started!
	html_file += '   <table>\n'

	# WRITE THE IMAGES ROW. #############################################
	html_file += '    <tr class="%s">\n' % (title_cell) 
	html_file += '     <td>%s</td>\n' % (table_lbl)

	# Include Images for each of the Characters.
	for char in char_list:
		html_file += '     <th class="image_cell" colspan="%i"><img src="https://assets.marvelstrikeforce.com/imgs/Portrait_%s" alt="" width="100"></th>\n' % (len(keys), alliance_info['portraits'][char])

	# Include a Team Power column.
	html_file += '     <td></td>\n'
	html_file += '    </tr>\n'
	# DONE WITH THE IMAGES ROW. #########################################

	# WRITE THE CHARACTER NAMES ROW. ####################################
	html_file += '    <tr class="%s">\n' % (char_cell)
	
	if len(keys)>1 and len(strike_teams)>1:
		html_file += '     <th>Alliance<br>Member</th>\n'
	else:
		html_file += '     <td></td>\n'

	# Include information for the Meta Characters.
	for char in char_list:
		html_file += '     <th colspan="%i" width="100">%s</th>\n' % (len(keys), translate_name(char))

	# Include the Team Power column.
	html_file += '     <th></th>\n' 
	html_file += '    </tr>\n'
	# DONE WITH THE CHARACTER NAMES ROW. ################################

	# Iterate through each Strike Team.
	for team in strike_teams:

		# Find min/max for meta/strongest team power in this Strike Team
		# This will be used for color calculation for the Team Power column.
		tot_team_pwr = [all_team_pwr[player_name] for player_name in player_list if player_name in team]
		min_team_pwr = min(tot_team_pwr)
		max_team_pwr = max(tot_team_pwr)

		# WRITE THE HEADING ROW WITH VALUE DESCRIPTORS ##################
		# (only if more than one item requested)
		if len(keys)>1 or len(strike_teams)>1:
			html_file += '    <tr class="%s">\n' % table_header
			
			if len(strike_teams)>1:
				html_file += '     <td>STRIKE TEAM %i</td>\n' % (strike_teams.index(team)+1)
			else:
				html_file += '     <td>Alliance<br>Member</td>\n'

			# Insert stat headings for each included Character.
			for char in char_list:
				for key in keys:
					html_file += '     <td>%s</td>\n' % {'lvl':'Level'}.get(key,key.title())

			# Insert the Team Power column.
			html_file += '     <td class="power_header">%s</td>\n' % (team_pwr_lbl)
			html_file += '    </tr>\n'
		# DONE WITH THE HEADING ROW FOR THIS STRIKE TEAM ################

		# FINALLY, WRITE THE DATA FOR EACH ROW. #########################
		# Player Name, then relevant stats for each character.
		alt_color = False
		for player_name in team:
		
			# If can't find the specified player name, let's check to see if it's a simple issue of capitalization.
			if player_name not in player_list:

				# Maybe they just got the wrong case? Fix it silently, if so.
				player_lower = [player.lower() for player in player_list]
				if player_name.lower() in player_lower:
					player_name = player_list[player_lower.index(player_name.lower())]

				# Maybe we just haven't gotten a roster yet?
				elif player_name in alliance_info['members']:
					pass

				# Toggle a flag for each divider to change the color of Player Name slightly
				else:
					alt_color = not alt_color

			# Time to build the row.
			if player_name in player_list:
				html_file += '    <tr style="text-align: center;">\n'
				html_file += '     <th class="%s">%s</th>\n' % ([name_cell, name_cell_alt][alt_color], player_name)

				# Write the stat values for each character.
				for char_name in char_list:

					for key in keys:

						# Standard lookup. Get the range of values for this character for all rosters.
						if not hist_tab:
							key_vals = [int(alliance_info['members'][player]['processed_chars'][char_name][key]) for player in player_list]

						# If historical, we want the diff between the current values and the values in the oldest record
						else:
							key_vals = [int(alliance_info['members'][player]['processed_chars'][char_name][key]) - int(find_oldest_val(alliance_info, player_name, char_name, key)) for player in player_list]

						min_val = min(key_vals)
						max_val = max(key_vals)

						# Only look up the value if we have a roster.
						value = 0
						if player_name in player_list:
						
							# Standard lookup. Get the value for this character stat from this player's roster.
							if not hist_tab:
								value = alliance_info['members'][player_name]['processed_chars'][char_name][key]
							# If historical, we look for the first time this member appears in the History, and then display the difference between the stat in that record and this one.
							else:
								value = int(alliance_info['members'][player_name]['processed_chars'][char_name][key]) - int(find_oldest_val(alliance_info, player_name, char_name, key))
						
						html_file += '     <td style="background-color:%s;">%s</td>\n' % (get_value_color(min_val, max_val, value, key, hist_tab), [value,'-'][value in (0,'0')])

				# Include the Team Power column.
				team_pwr = all_team_pwr.get(player_name,0)
				html_file += '     <td class="bold_text" style="background-color:%s;">%s</td>\n' % (get_value_color(min_team_pwr, max_team_pwr, team_pwr), [team_pwr,'-'][team_pwr in (0,'0')])
				html_file += '    </tr>\n'
		# DONE WITH THE DATA ROWS FOR THIS STRIKE TEAM ##################

	# Close the Table, we are done with this chunk.
	html_file += '   </table>\n'

	return html_file


# Find this member's oldest entry in our historical entries.
def find_oldest_val(alliance_info, player_name, char_name, key):
	dates = list(alliance_info['hist'])

	# Start with the oldest entry in 'hist', looking for this member's stats.
	while dates:
		min_date = min(dates)
		if player_name in alliance_info['hist'][min_date]:
			# Found a valid record, return the value in 'key'
			if char_name in alliance_info['hist'][min_date][player_name]:
				return alliance_info['hist'][min_date][player_name][char_name][key]
			# This character has been added since oldest history record.
			return '0'

		# Oldest entry didn't have it, go one newer.
		dates.remove(min_date)

	# Should not happen. Should always at least find this member in the most recent run.
	return '0'


# Generate just the Alliance Tab contents.
def generate_alliance_tab(alliance_info, html_file=''):

	tot_power = sum([alliance_info['members'][member]['tcp'] for member in alliance_info['members']])
	avg_power = int(tot_power/len(alliance_info['members']))

	# Use this flag to determine which header information is displayed.
	extras_avail = alliance_info.get('trophies')
	
	html_file += '<div id="AllianceInfo" class="tabcontent">\n'
	html_file += '<table style="background-color:SteelBlue;">\n'

	html_file += '<tr>\n</tr>\n'

	html_file += '<tr style="font-size:18px;">\n'
	html_file += ' <td colspan="2"  rowspan="2"><img src="https://assets.marvelstrikeforce.com/imgs/ALLIANCEICON_%s"/></td>\n' % (alliance_info['image'])
	html_file += ' <td colspan="10" rowspan="%s" class="alliance_name">%s</td>' % (['1','2'][not extras_avail], alliance_info['name'].upper())
	
	if extras_avail:	html_file += ' <td colspan="2" rowspan="2"><span class="bold_text" style="font-size:24px">Alliance Message:</span><br>%s</td>' % (alliance_info.get('desc',''))
	else:				html_file += ' <td colspan="2">Total Power<br><span style="font-size:24px;"><b>%s</b></span></td>\n' % (f'{tot_power:,}')

	html_file += '</tr>\n'

	html_file += '<tr style="font-size:18px;">\n'
	if extras_avail:	html_file += ' <td colspan="2">Members<br><span style="font-size:24px;"><b>%i/24</b></span></td>\n' % (len(alliance_info['members']))
	if extras_avail:	html_file += ' <td colspan="2">Total Power<br><span style="font-size:24px;"><b>%s</b></span></td>\n' % (f'{tot_power:,}')
	html_file += ' <td colspan="2">Average Collection Power<br><span style="font-size:24px;"><b>%s</b></span></td>\n' % (f'{avg_power:,}')
	if extras_avail:	html_file += ' <td colspan="2">Level<br><span style="font-size:24px;"><b>%s</b></span></td>\n' % (alliance_info.get('stark_lvl',''))
	if extras_avail:	html_file += ' <td colspan="2">Trophies<br><span style="font-size:24px;"><b>%s</b></span></td>\n' % (alliance_info.get('trophies',''))
	html_file += '</tr>\n'
	
	# Create the headings for the Alliance Info table.
	html_file += '<tr class="table_header_blue" style="font-size:14pt;">\n'
	html_file += ' <td width="60" ></td>\n'
	html_file += ' <td width="215">Name</td>\n'            
	html_file += ' <td width="110">Level</td>\n'
	html_file += ' <td width="110">Role</td>\n'
	html_file += ' <td width="110">Collection<br>Power</td>\n'
	html_file += ' <td width="110">Strongest<br>Team</td>\n'
	html_file += ' <td width="110">War<br>MVP</td>\n'
	html_file += ' <td width="110">Total<br>Collected</td>\n'
	html_file += ' <td width="110">Max<br>Stars</td>\n'
	html_file += ' <td width="110">Arena<br>Rank</td>\n'
	html_file += ' <td width="110">Blitz<br>Wins</td>\n'
	html_file += ' <td width="110">Total<br>Stars</td>\n'
	html_file += ' <td width="110">Total<br>Red</td>\n'
	html_file += ' <td width="215">Last Updated:</td>\n'
	html_file += '</tr>\n'
	
	alliance_order = sorted(alliance_info['members'].keys(), key = lambda x: alliance_info['members'][x]['tcp'], reverse=True)
	
	# Build up the list of Alliance Members
	member_list =  [alliance_info['leader']] + alliance_info['captains']
	member_list += [member for member in alliance_order if member not in member_list]

	tcp_range   = [alliance_info['members'][member]['tcp']   for member in member_list]
	stp_range   = [alliance_info['members'][member]['stp']   for member in member_list]
	mvp_range   = [alliance_info['members'][member]['mvp']   for member in member_list]
	tcc_range   = [alliance_info['members'][member]['tcc']   for member in member_list]
	max_range   = [alliance_info['members'][member]['max']   for member in member_list]
	arena_range = [alliance_info['members'][member]['arena'] for member in member_list]
	blitz_range = [alliance_info['members'][member]['blitz'] for member in member_list]
	stars_range = [alliance_info['members'][member]['stars'] for member in member_list]
	red_range   = [alliance_info['members'][member]['red']   for member in member_list]

	for member in member_list:
		# Get a little closer to what we're working with.
		member_stats = alliance_info['members'][member]
		
		if member in alliance_info['leader']:
			member_role = 'Leader'
		elif member in alliance_info['captains']:
			member_role = 'Captain'
		else:
			member_role = 'Member'

		member_color = {'Leader':  'PowderBlue',
						'Captain': 'DeepSkyBlue',
						'Member':  'PowderBlue' }[member_role]

		html_file += ' <tr style="background-color:%s;">\n' % (member_color)
		html_file += '  <td style="padding:0px;"><img height="45" src="https://assets.marvelstrikeforce.com/imgs/Portrait_%s"/></td>\n' % (member_stats['image'])
		html_file += '  <td class="bold_text">%s</td>\n' % (member)
		html_file += '  <td>%i</td>\n' % (member_stats['level'])
		html_file += '  <td>%s</td>\n' % (member_role)
		html_file += '  <td style="background-color:%s;">%s</td>\n' % (get_value_color(min(tcp_range),   max(tcp_range),   member_stats['tcp']),   f'{member_stats["tcp"]:,}')
		html_file += '  <td style="background-color:%s;">%s</td>\n' % (get_value_color(min(stp_range),   max(stp_range),   member_stats['stp']),   f'{member_stats["stp"]:,}')
		html_file += '  <td style="background-color:%s;">%s</td>\n' % (get_value_color(min(mvp_range),   max(mvp_range),   member_stats['mvp']),   f'{member_stats["mvp"]:,}')
		html_file += '  <td style="background-color:%s;">%s</td>\n' % (get_value_color(max(tcc_range)-5, max(tcc_range),   member_stats['tcc']),   f'{member_stats["tcc"]:,}')
		html_file += '  <td style="background-color:%s;">%s</td>\n' % (get_value_color(min(max_range),   max(max_range),   member_stats['max']),   f'{member_stats["max"]:,}')
		html_file += '  <td style="background-color:%s;">%s</td>\n' % (get_value_color(max(arena_range), min(arena_range), member_stats['arena']), f'{member_stats["arena"]:,}')
		html_file += '  <td style="background-color:%s;">%s</td>\n' % (get_value_color(min(blitz_range), max(blitz_range), member_stats['blitz']), f'{member_stats["blitz"]:,}')
		html_file += '  <td style="background-color:%s;">%s</td>\n' % (get_value_color(min(stars_range), max(stars_range), member_stats['stars']), f'{member_stats["stars"]:,}')
		html_file += '  <td style="background-color:%s;">%s</td>\n' % (get_value_color(min(red_range),   max(red_range),   member_stats['red']),   f'{member_stats["red"]:,}')

		time_since_last = 4*86400
		time_value      = 'Never<br>Member needs to re-sync their roster.'
		if member in alliance_info['members'] and 'processed_chars' in member_stats:
			time_since_last = datetime.datetime.now() - member_stats['processed_chars']['last_update']
			time_value = '%s,<br>%s ago' % (member_stats['processed_chars']['last_update'].strftime('%A, %B %d'), str(time_since_last).split('.')[0])
			time_since_last = time_since_last.total_seconds()
		
		time_color = get_value_color(0, 4*86400, (4*86400)-time_since_last)
		html_file += '  <td style="background-color:%s;">%s</td>\n' % (time_color, time_value)
		html_file += ' </tr>\n'

	html_file += '</table>\n'
	html_file += '</div>\n'

	return html_file


# Including this here for expedience.
def generate_csv(alliance_info):
	# Write the basic output to a CSV in the local directory.
	keys = ['fav','lvl','power','yel','red','tier','bas','spec','ult','pass','class','iso','iso','iso','iso','iso','iso']
	
	csv_file = ['Name,AllianceName,CharacterId,Favorite,Level,Power,Stars,RedStar,GearLevel,Basic,Special,Ultimate,Passive,ISO Class,ISO Level,ISO Armor,ISO Damage,ISO Focus,ISO Health,ISO Resist']
	
	player_list = get_player_list(alliance_info)
	char_list   = get_char_list (alliance_info)
		
	alliance_name = alliance_info['name']
			
	for player_name in player_list:
		processed_chars = alliance_info['members'][player_name]['processed_chars']

		# Only include entries for recruited characters.
		for char_name in char_list:
			if processed_chars[char_name]['lvl'] != '0':
				csv_file.append(','.join([player_name, alliance_name, char_name] + [processed_chars[char_name][key] for key in keys]))

	return '\n'.join(csv_file)


# Linear gradient from red, to yellow, to green. 
# Costly to calculate, so only doing it once.
color_scale = polylinear_gradient(['#FF866F','#F6FF6F','#6FFF74'],1000)['hex']
max_colors  = len(color_scale)-1


# Translate value to a color from the Heat Map gradient.
def get_value_color(min, max, value, stat='power', hist_tab=''):
	
	# Just in case passed a string.
	value = int(value)
	
	# Special treatment for the '0' fields. 
	if not value:
		return '#282828;color:#919191;'

	#Tweak gradients for Tier, ISO, Level, and Red/Yellow stars.
	if stat=='iso':
		if not hist_tab:
			scaled_value = int(((value**3)/10**3) * max_colors)
		else:
			scaled_value = [int((0.6 + 0.4 * ((value**3)/10**3)) * max_colors),0][value<0]
	elif stat=='tier':
		if not hist_tab and value <= 15:
			scaled_value = int(((value**2)/15**2)*0.50 * max_colors)
		elif not hist_tab:
			scaled_value = int((0.65 + 0.35 * ((value-16)/3)) * max_colors)
		else:
			scaled_value = int((0.60 + 0.40 * ((value**2)/17**2)) * max_colors)
	elif stat=='lvl':
		if not hist_tab and value <= 75:
			scaled_value = int(((value**2)/75**2)*0.50 * max_colors)
		elif not hist_tab:
			scaled_value = int((0.65 + 0.35 * ((value-75)/20)) * max_colors)
		else:
			scaled_value = int((0.60 + 0.40 * ((value**2)/95**2)) * max_colors)
	elif stat in ('red','yel'):
		min = 2
		max = 7
		scaled_value = int((value-min)/(max-min) * max_colors)
	# Everything else.
	else:
		if min == max:
			scaled_value = max_colors
		else:
			scaled_value = int((value-min)/(max-min) * max_colors)
	
	if scaled_value < 0:
		scaled_value = 0
	elif scaled_value > max_colors:
		scaled_value = max_colors

	return color_scale[scaled_value]


# Pull out STP values from either Meta Chars or all Active Chars.
def get_stp_list(alliance_info, char_list, hist_tab='', team_pwr_dict={}):
	
	# Get the list of Alliance Members 
	player_list = get_player_list (alliance_info)

	for player_name in player_list:

		# Build a list of all character powers.
		all_char_pwr = [int(alliance_info['members'][player_name]['processed_chars'][char_name]['power']) for char_name in char_list]
		all_char_pwr.sort()

		# And sum up the Top 5 power entries for STP.
		team_pwr_dict[player_name] = sum(all_char_pwr[-5:])

		# Get power of all heroes in the char_list from earliest entry in history. We will sum these and subtract from entry below. 
		if hist_tab:
			old_char_pwr = [int(find_oldest_val(alliance_info, player_name, char_name, 'power')) for char_name in char_list]
			old_char_pwr.sort()
			
			# Use the difference between the new STP and the old value.
			team_pwr_dict[player_name] -= sum(old_char_pwr[-5:])
			
	return team_pwr_dict


# Bring back a sorted list of characters from alliance_info
def get_char_list(alliance_info):

	# We only keep images for heroes that at least one person has recruited.
	char_list = list(alliance_info['portraits'])
	char_list.sort()

	return char_list


# Bring back a sorted list of players from alliance_info
def get_player_list(alliance_info):

	# Only include members that actually have processed_char information attached.
	player_list = [member for member in alliance_info['members'] if 'processed_chars' in alliance_info['members'][member]]
	player_list.sort(key=str.lower)
	
	return player_list


# Quick and dirty translation to shorter or better names.
def translate_name(value):

	tlist = {	"Avenger": "Avengers",
				"AForce": "A-Force",
				"BionicAvenger": "Bionic<br>Avengers",
				"BlackOrder": "Black<br>Order",
				"Brawler": "Brawlers",
				"Brotherhood": "B'Hood",
				"DarkHunter": "Dark<br>Hunters",
				"Defender": "Defenders",
				"Eternal": "Eternals",
				"HeroesForHire": "H4H",
				"Hydra Armored Guard": "Hydra Arm Guard",
				"InfinityWatch": "Infinity<br>Watch",
				"Invader": "Invaders",
				"MastersOfEvil": "Masters<br>Of Evil",
				"Mercenary": "Mercs",
				"NewAvenger": "New<br>Avengers",
				"NewWarrior": "New<br>Warriors",
				"PymTech": "Pym Tech",
				"Ravager": "Ravagers",
				"SecretAvenger": "Secret<br>Avengers",
				"SecretDefender": "Secret<br>Defenders",
				"SinisterSix": "Sinister<br>Six",
				"SpiderVerse": "Spiders",
				"Symbiote": "Symbiotes",
				"TangledWeb": "Tangled<br>Web",
				"WarDog": "War Dogs",
				"WeaponX": "Weapon X",
				"WebWarrior": "Web<br>Warriors",
				"XFactor": "X-Factor",
				"Xforce": "X-Force",
				"Xmen": "X-Men",
				"YoungAvenger": "Young<br>Avengers",
				"Captain America (WWII)": "Capt. America (WWII)",
				"Captain America (Sam)": "Capt. America (Sam)"}

	# Return the translation if available.
	return tlist.get(value, value)


# Quick and dirty CSS to allow Tabbed implementation for raids with lanes.
def add_tabbed_header(num_lanes, hist_tab, table_name = ''):

		html_file = '''
<head>
<title>'''+table_name+''' Info</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fira+Sans+Condensed:wght@400;700;900&display=swap" rel="stylesheet">
<style>

/* Style tab links */
.tablink {
  background-color : #888;
  color            : white;
  float            : left;
  border           : none;
  outline          : none;
  cursor           : pointer;
  padding          : 14px 16px;
  font-size        : 24px;
  font-family      : 'Fira Sans Condensed';
  font-weight      : 900;
  width            : '''+str(int(100/(num_lanes+[2,1][not hist_tab]))) +'''%;	# Adding 1 for Alliance Info tab, 2 if there's also history.
}
.tablink:hover {
  background-color : #555;
}
.tabcontent {
  background-color : #343734;
  display          : none;
  padding          : 70px 20px;
  height           : 100%;
}

/* Styles for table cells */

.bold_text {
  font-weight      : bold;
}
.alliance_name {
  font-weight      : 700;
  font-size        : 36pt;
}
.title_cell_blue {
  font-weight      : 700;
  font-size        : 14pt;
  background-color : PowderBlue;
}
.title_cell_gray {
  font-weight      : 700;
  font-size        : 14pt;
  background-color : Gainsboro;
}
.table_header_blue {
  font-weight      : 700;
  background-color : MidnightBlue;
  color            : white;
  white-space      : nowrap;
}
.table_header_gray {
  font-weight      : 700;
  background-color : Black;
  color            : white;
  white-space      : nowrap;
}
.char_cell_blue {
  font-weight      : 700;
  background-color : SkyBlue;
}
.char_cell_gray {
  font-weight      : 700;
  background-color : Silver;
}
.name_cell_blue {
  font-weight      : 700;
  background-color : PowderBlue;
  white-space      : nowrap;
}
.name_cell_blue_alt {
  font-weight      : 700;
  background-color : DeepSkyBlue;
  white-space      : nowrap;
}
.name_cell_gray {
  font-weight      : 700;
  background-color : Gainsboro;
  white-space      : nowrap;
}
.name_cell_gray_alt {
  font-weight      : 700;
  background-color : DarkGray;
  white-space      : nowrap;
}
.table_subtitle {
  font-size        : 12pt;
  font-weight      : normal;
}
.image_cell {
  background-color : Black;
}
.power_header {
  font-weight      : 700;
  background-color : Maroon;
  color            : white;
}
'''

		for num in range(num_lanes):
			html_file += '#Lane%i {background-color: #343734;}\n' % (num+1)

		if hist_tab:
			html_file += '#Hist {background-color: #343734;}\n'

		html_file += '#AllianceInfo {background-color: #343734;}\n'	

		html_file += '</style>\n'
		html_file += '</head>\n'
		html_file += '<body style="background-color: #343734; font-family: \'Fira Sans Condensed\', sans-serif; text-align:center;">\n'

		for num in range(num_lanes):
			tab_name = ['ROSTER INFO', 'LANE %i' % (num+1)][num_lanes>1]

			if table_name:
				tab_name = '%s %s' % (table_name.upper(), tab_name)

			html_file += '''<button class="tablink" onclick="openPage('Lane%i', this)" %s>%s</button>''' % (num+1,['','id="defaultOpen"'][not num],tab_name) + '\n'

		if hist_tab:
			html_file += '''<button class="tablink" onclick="openPage('Hist1', this)">%s</button>''' % (hist_tab) + '\n'

		# And a tab for Alliance Info
		html_file += '''<button class="tablink" onclick="openPage('AllianceInfo', this)">ALLIANCE INFO</button>''' + '\n'

		return html_file


# Quick and dirty Javascript to allow Tabbed implementation for raids with lanes.
def add_tabbed_footer():
		return '''
<script>
function openPage(pageName,elmnt) {
  var i, tabcontent, tablinks;
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
	tabcontent[i].style.display = "none";
  }
  tablinks = document.getElementsByClassName("tablink");
  for (i = 0; i < tablinks.length; i++) {
	tablinks[i].style.backgroundColor = "";
  }
  document.getElementById(pageName).style.display = "block";
  elmnt.style.backgroundColor = "#343734";
}

// Get the element with id="defaultOpen" and click on it
document.getElementById("defaultOpen").click();
</script>
</body>
'''