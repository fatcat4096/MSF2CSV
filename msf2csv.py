#!/usr/bin/env python3
# Encoding: UTF-8
"""msf2csv.py
Transform stats from MSF.gg into readable tables with heatmaps.
"""

# Standard library modules do the heavy lifting. Ours is all simple stuff.
import os
import datetime
import pickle

from process_mhtml import *			# Routines to scrap MHTML web pages.
from gradients import *				# Routines to create color gradient for heat map
from extract_traits import *		# Pull trait info from MSF.gg

# Initialize a few globals.
alliance_name = 'Sample Pivot'

# We will be working in the same directory as this file.
try:
	path = os.path.dirname(__file__)+os.sep
# Sourcing locally, no __file__ object.
except:
	path = '.'+os.sep

# Pull trait info from msf.gg
chars_from_trait = extract_traits()

# Just do it.
def main():
	try:
		# load sample data from cached file instead
		[char_stats,processed_players] = pickle.load(open('cached_data','rb'))

	except:
		# Extract all the relevant info from MTHML roster files in this directory
		char_stats,processed_players = process_mhtml(path)

		# cache char_stats,processed_players to disk.
		pickle.dump([char_stats,processed_players],open('cached_data','wb'))
	
	# Output selected tables built from the parsed information
	output_files(char_stats, processed_players)


def output_files(char_stats,processed_players):

	filename = path+alliance_name+datetime.datetime.now().strftime("-%Y%m%d-")

	# Meta Heroes for use in Incursion
	incur_mutant	=	['Archangel','Nemesis','Dark Beast','Psylocke','Magneto']
	incur_bio		=	['Captain America','Captain Carter','Agent Venom','Winter Soldier','U.S. Agent']
	incur_skill		=	['Nick Fury','Captain America (WWII)','Iron Fist (WWII)','Bucky Barnes','Union Jack']
	incur_mystic	=	['Beta Ray Bill','Loki','Loki (Teen)','Sylvie','Vahl']
	incur_tech		=	['Kang the Conqueror','Doctor Doom','Hulkbuster','Kestrel','Viv Vision','Vision']

	incur_lanes =	[[{'traits':	['Mutant'],	'meta': ['Archangel','Nemesis','Dark Beast','Psylocke','Magneto']},
					  {'traits':	['Bio'],	'meta': ['Captain America','Captain Carter','Agent Venom','Winter Soldier','U.S. Agent']},
					  {'traits':	['Skill'],	'meta': ['Nick Fury','Captain America (WWII)','Iron Fist (WWII)','Bucky Barnes','Union Jack']},
					  {'traits':	['Mystic'],	'meta': ['Beta Ray Bill','Loki','Loki (Teen)','Sylvie','Vahl']},
					  {'traits':	['Tech'],	'meta': ['Kang the Conqueror','Doctor Doom','Hulkbuster','Viv Vision','Vision']}]]

					 # Lane 1
	gamma_lanes =	[[{'traits':	['Avenger','GotG'],									'meta': ['Viv Vision','Vision','Deathlok','Hulkbuster','Iron Man']},
					  {'traits':	['PymTech','Kree'],									'meta': ['Ghost','Yellowjacket','Minn-Erva','Captain Marvel','Phyla-Vell']},
					  {'traits':	['Brotherhood','Mercenary','Xmen'],					'meta': ['Dazzler', 'Fantomex', 'Gambit', 'Rogue', 'Sunfire']},
					  {'traits':	['Kree','SpiderVerse','GotG'],						'meta': ['Ghost-Spider','Spider-Man (Miles)','Spider-Weaver','Spider-Man','Scarlet Spider']}],
					 # Lane 2				
					 [{'traits':	['Avenger','SpiderVerse'],							'meta': ['Viv Vision','Vision','Deathlok','Hulkbuster','Iron Man']},
					  {'traits':	['PymTech','Wakanda'],								'meta': ['Black Panther', 'Black Panther (1MM)', 'Nakia', 'Okoye', 'Shuri']},
					  {'traits':	['Brotherhood','Mercenary','Xmen'],					'meta': ['Dazzler', 'Fantomex', 'Gambit', 'Rogue', 'Sunfire']},
					  {'traits':	['Kree','SpiderVerse','GotG'],						'meta': ['Ghost-Spider','Spider-Man (Miles)','Spider-Weaver','Spider-Man','Scarlet Spider']}],
					 # Lane 3
					 [{'traits':	['Shield','Brotherhood'],							'meta': ['Black Widow','Captain America','Nick Fury','Maria Hill','Magneto']},
					  {'traits':	['Defender','Mercenary','HeroesForHire'],			'meta': ['Colleen Wing', 'Iron Fist', 'Luke Cage', 'Misty Knight', 'Shang-Chi']},
					  {'traits':	['GotG','Xmen','Mercenary'],						'meta': ['Dazzler', 'Fantomex', 'Gambit', 'Rogue', 'Sunfire']},
					  {'traits':	['Brotherhood','Mercenary','Xmen'],					'meta': ['Dazzler', 'Fantomex', 'Gambit', 'Rogue', 'Sunfire']},
					  {'traits':	['Kree','SpiderVerse','GotG'],						'meta': ['Ghost-Spider','Spider-Man (Miles)','Spider-Weaver','Spider-Man','Scarlet Spider']}],
					 # Lane 4
					 [{'traits':	['Shield','Aim'],									'meta': ['Black Widow','Captain America','Nick Fury','Maria Hill','Hawkeye']},
					  {'traits':	['Defender','Hydra','HeroesForHire'],				'meta': ['Colleen Wing', 'Iron Fist', 'Luke Cage', 'Misty Knight', 'Shang-Chi']},
					  {'traits':	['Shield','Wakanda','Defender','HeroesForHire'],	'meta': ['Black Panther', 'Black Panther (1MM)', 'Nakia', 'Okoye', 'Shuri']},
					  {'traits':	['Kree','SpiderVerse','GotG'],						'meta': ['Ghost-Spider','Spider-Man (Miles)','Spider-Weaver','Spider-Man','Scarlet Spider']}]]

	strike_teams = [['FatCat','Joey','Daner','Jutch','sjhughes','Ramalama','DrFett','Evil Dead Rise'],
					['Shammy','HeadHunter2838','keithchyiu','mgmf','BigDiesel','Luthher','EXfieldy','FabiooBessa'],
					['Zen Master','Incredibad','Kal-El','Snicky','Zairyuu','Flashie','Unclad','RadicalEvil']]

	# Tables with just Incursion Meta. 
	html_file = generate_html(processed_players, char_stats, min_iso=9, min_tier=16, lanes=incur_lanes, strike_teams=strike_teams)
	open(filename+"incursion.html", 'w').write(html_file)

	# Tables with just Gamma Lanes. 
	html_file = generate_html(processed_players, char_stats, min_tier=16, lanes=gamma_lanes, strike_teams=strike_teams)
	open(filename+"gamma.html", 'w').write(html_file)

	# Tables for all characters, broken down by Origin. 
	# Filtering with minimum ISO and Gear Tier just to reduce noise from Minions, old heroes, etc.
	html_file = generate_html(processed_players, char_stats, min_iso=9, min_tier=16, strike_teams=strike_teams)
	open(filename+"all.html", 'w').write(html_file)


lane_default = [[{'traits': ['Mutant'],	'meta': []},
				 {'traits': ['Bio'],	'meta': []},
				 {'traits': ['Skill'],	'meta': []},
				 {'traits': ['Mystic'],	'meta': []},
				 {'traits': ['Tech'],	'meta': []}]]


def generate_html(processed_players, char_stats, keys=['power','tier','iso'], min_iso=0, min_tier=0, char_list=[], lanes = lane_default, strike_teams=[]):

	# If no char_list is specified, pull the list of all characters from char_stats
	if not char_list:
		char_list = get_char_list (char_stats)
	
	# Get the list of Alliance Members we will iterate through as rows.	
	player_list = list(processed_players.keys())
	player_list.sort(key=str.lower)

	html_file = '<!doctype html>\n<html>\n'

	# Iterate through all the lanes. Showing tables for each section. 

	for lane in lanes:
		
		lane_lbl = ''
		if len(lanes)>1:
			lane_lbl = '<font size="4">Lane %i:</font><br>' % (lanes.index(lane)+1)

		# Process each section individually, filtering only the specified traits into the Active Chars list.
		for section in lane:
			traits	= section['traits']
			meta	= section['meta']

			# Start with the entire character list.
			# We will filter it down before doing anything.
			active_chars = char_list[:]
			
			# If there are minimums or trait filters for this section, evaluate each character before using the active_chars list.

			if min_iso:
				active_chars = [char for char in active_chars if char_stats[char]['iso']['max'] >= min_iso]

			if min_tier:
				active_chars = [char for char in active_chars if char_stats[char]['tier']['max'] >= min_tier]
			
			# Trait filters are additive.
			if traits:
				for char in active_chars[:]:
					for trait in traits:
						if char in chars_from_trait[trait]:
							# Character has at least one of these traits. Leave it in.
							break
					# Did we find this char in any of the traits?
					if char not in chars_from_trait[trait]:
						active_chars.remove(char)

			# Define Min/max range just using the qualifying heroes in this section.
			#active_stats = {}
			#for char in active_chars:
			#	active_min_max(active_stats,stat

			# Split active_chars into meta_chars and other_chars
			meta_chars  = [char for char in active_chars if char in meta]
			other_chars = [char for char in active_chars if not char in meta]

			# Calculate team power for meta_characters for each player.
			meta_team_pwr = {}

			for player_name in player_list:
				tot_team_pwr = 0

				for char_name in meta_chars:
					tot_team_pwr += int(processed_players[player_name][char_name]['power'])

				meta_team_pwr[player_name] = tot_team_pwr

			# Calculate Strongest Team Power for meta_characters for each player.
			top5_team_pwr = {}
			for player_name in player_list:
				tot_team_pwr = 0

				# Build a list of all character powers, reverse it.
				all_char_pwr = []
				for char_name in meta_chars+other_chars:
					all_char_pwr.append(int(processed_players[player_name][char_name]['power']))
				all_char_pwr.sort(reverse=True)

				# And sum up the Top 5 power entries for STP.
				top5_team_pwr[player_name] = sum(all_char_pwr[:5])

			# Use the full Player List if explicit Strike Teams haven't been defined.
			if not strike_teams:
				strike_teams = [player_list]

			# Start with the Basic Table Lable and Colors.
			table_lbl = '<br>'.join([trans_name(trait) for trait in traits]).upper()
			if lane_lbl:
				table_lbl = lane_lbl+table_lbl

			color_theme = {}
			
			# Only calling it twice if we have meta_chars defined.
			if meta_chars:
				meta_lbl = table_lbl+'<br><font size="4">META</font>'

				html_file += '<table>\n <tr>\n  <td>\n'
				html_file += generate_table(processed_players, char_stats, keys, meta_chars, strike_teams, meta_lbl, color_theme, team_pwr_lbl='Team<br>Power', all_team_pwr=meta_team_pwr)
				html_file += '  </td>\n  <td>\n   <br>\n  </td>\n  <td>\n'

				# Differentiate Others Section from Meta Section
				table_lbl += '<br><font size="4">OTHERS</font>'
				color_theme = { 'lgt_color': "Gainsboro",
								'med_color': "Silver",
								'drk_color': "Black",
								'img_color': "Black",
								'pwr_color': "Maroon" }

			# Always generate the Others table.
			# Only label it as such if Meta section exists.
			html_file += generate_table(processed_players, char_stats, keys, other_chars, strike_teams, table_lbl, color_theme, team_pwr_lbl='STP<br>(Top 5)', all_team_pwr=top5_team_pwr)

			# If in a nested table, close the nested table.
			if meta_chars:
				html_file += '  </td>\n </tr>\n</table>\n'

			# If not the final section, add a divider row. 
			if lane.index(section) != len(lane)-1:
				html_file += '    <p></p>\n'

	# All done with All Lanes. Close the file.
	html_file += '</html>'

	return html_file


def generate_table(processed_players, char_stats, keys=['power','tier','iso'], char_list=[], strike_teams = [], table_lbl='', color_theme= {}, team_pwr_lbl='', all_team_pwr={}, html_file = ''):

	# Get the list of Alliance Members we will iterate through as rows.	
	player_list = list(processed_players.keys())
	player_list.sort(key=str.lower)

	# If different theme passed in, use those instead. 
	if color_theme:
		lgt_color = color_theme['lgt_color']
		med_color = color_theme['med_color']
		drk_color = color_theme['drk_color']
		img_color = color_theme['img_color']
		pwr_color = color_theme['pwr_color']
	else:
		lgt_color= "PowderBlue"
		med_color= "SkyBlue"
		drk_color= "MidnightBlue"
		img_color= "Black"
		pwr_color= "Maroon"

	# Let's get this party started!
	html_file += '   <table border="1" style="font-family:verdana; text-align: center;  font-size: 12;">\n'

	# WRITE THE IMAGES ROW. 
	html_file += '    <tr style="background-color:%s;">\n' % lgt_color
	html_file += '     <th style="font-size: 18pt;">%s</th>\n' % table_lbl

	# Include Images for each of the Characters.
	for char in char_list:
		html_file += '     <th style="background-color:%s;" colspan="%i"><img src="%s" alt="" width="100"></th>\n' % (img_color, len(keys), char_stats[char]['portrait'])

	# If we have all_team_pwr info, need a Team Power column.
	if all_team_pwr:
		html_file += '     <th></th>\n'
		
	html_file += '    </tr>\n'
	# DONE WITH THE IMAGES ROW. 


	# WRITE THE CHARACTER NAMES ROW. 
	html_file += '    <tr style="background-color:%s;">\n' % med_color
	
	if len(keys)>1 and len(strike_teams)>1:
		html_file += '     <th nowrap width="150">Alliance<br>Member</th>\n'
	else:
		html_file += '     <th nowrap width="150"></th>\n'

	# Include information for the Meta Characters.
	for char in char_list:
		html_file += '     <th colspan="%i" width="100">%s</th>\n' % (len(keys), trans_name(char))

	# If we have all_team_pwr info, need a Team Power column.
	if all_team_pwr:
		html_file += '     <th></th>\n' 
	
	html_file += '    </tr>\n'
	# DONE WITH THE CHARACTER NAMES ROW. 


	# Iterate through each Strike Team.
	for team in strike_teams:

		# Find min/max for meta/strongest team power in this Strike Team
		# This will be used for color calculation for the Team Power column.
		min_team_pwr = 0
		max_team_pwr = 0
		if all_team_pwr:
			for player_name in player_list:
				if player_name in team:
					tot_team_pwr = all_team_pwr[player_name]
					min_team_pwr = [min_team_pwr,tot_team_pwr][tot_team_pwr < min_team_pwr or not min_team_pwr]
					max_team_pwr = [max_team_pwr,tot_team_pwr][tot_team_pwr > max_team_pwr]

		# WRITE THE HEADING ROW WITH VALUE DESCRIPTORS
		# (only if more than one item requested)
		if len(keys)>1 or len(strike_teams)>1:
			html_file += '    <tr style="background-color:%s; color:White;">\n' % drk_color
			
			if len(strike_teams)>1:
				html_file += '     <th>STRIKE TEAM %i</th>\n' % (strike_teams.index(team)+1)
			else:
				html_file += '     <th>Alliance<br>Member</th>\n'

			# Insert stat headings for each included Character.
			for char in char_list:
				for key in keys:
					html_file += '     <th>%s</th>\n' % key.title()

			# If we have all_team_pwr info, need a Team Power column.
			if all_team_pwr:
				html_file += '     <th style="background-color:%s;">%s</th>\n' % (pwr_color,team_pwr_lbl)
	
			html_file += '    </tr>\n'
		# DONE WITH THE HEADING ROW FOR THIS STRIKE TEAM


		# FINALLY, WRITE THE DATA FOR EACH ROW. Player Name, then relevant stats for each character.
		for player_name in player_list:
			if player_name in team:
				processed_chars = processed_players[player_name]
				team_pwr        = all_team_pwr[player_name]
				
				html_file += '    <tr style="text-align: center;">\n'
				html_file += '     <th style="background-color:%s;">%s</th>\n' % (lgt_color, player_name)

				# Write the stat values for each character.
				for char_name in char_list:
					for key in keys:
						min = char_stats[char_name][key]['min']
						max = char_stats[char_name][key]['max']
						value = processed_chars[char_name][key]
						
						html_file += '     <td style="background-color:%s;">%s</td>\n' % (get_value_color(min,max,value,key), value)

				# If we have all_team_pwr info, need a Team Power column.
				if all_team_pwr:
					html_file += '     <th style="background-color:%s;">%i</th>\n' % (get_value_color(min_team_pwr, max_team_pwr, team_pwr),team_pwr)
				
				html_file += '    </tr>\n'
		# DONE WITH THE DATA ROWS FOR THIS STRIKE TEAM

	# Close the Table, we are done with this chunk.
	html_file += '   </table >\n'

	return html_file
																				
																				
# Linear gradient from red, to yellow, to green. 
# Costly to calculate, so only doing it once.
color_scale = polylinear_gradient(['#FF866F','#F6FF6F','#6FFF74'],1000)['hex']
max_colors  = len(color_scale)-1


# Translate value to a color from the Heat Map gradient.
def get_value_color(min, max, value, stat='power'):
	
	# Just in case passed a string.
	value = int(value)
	
	if not value:
		return 'Beige'

	#Tweak gradients for Tier and ISO
	if stat=='iso':
		return color_scale[int( ((value**3)/10**3) *max_colors)]

	elif stat=='tier':
		if value <= 15:
			return color_scale[int( ((value**2)/15**2) *0.50 *max_colors)]
		else:
			return color_scale[int((0.65+((value-16)/3)*0.35)*max_colors)]

	# Everything else.
	return color_scale[int((value-min)/(max-min)*max_colors)]


# Bring back a sorted list of characters from our char_stats
def get_char_list(char_stats):
	char_list = list(char_stats.keys())

	# Prune the unsummoned characters.
	for char in char_list[:]:
		if 'iso' not in char_stats[char].keys():
			char_list.remove(char)

	char_list.sort()

	return char_list


# Quick and dirty translation to shorter or better names.
def trans_name(value):

	tlist = {	"Avenger": "Avengers",
				"Brotherhood": "B'Hood",
				"HeroesForHire": "H4H",
				"Mercenary": "Mercs",
				"PymTech": "Pym Tech",
				"SpiderVerse": "Spiders",
				"Xmen": "X-Men",
				"Captain America (WWII)": "Capt. America (WWII)",
				"Captain America (Sam)": "Capt. America (Sam)"}

	#Return the translation
	if value in tlist:
		return tlist[value]
	
	# No change.
	return value


if __name__ == "__main__":
	main() # Just run myself

