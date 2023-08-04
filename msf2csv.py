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
alliance_name = 'SIGMA_Infamously_Strange'

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
	# Extract all the relevant info from MTHML roster files in this directory
	#char_stats,processed_players = process_mhtml(path)

	# cache char_stats,processed_players to disk.
	#pickle.dump([char_stats,processed_players],open('sample_data','wb'))
	
	# load sample data from cached file instead
	[char_stats,processed_players] = pickle.load(open('sample_data','rb'))

	# Output selected tables built from the parsd information
	output_files(char_stats, processed_players)


def output_files(char_stats,processed_players):

	# Pull char_list from char_stats.
	char_list = get_char_list (char_stats)

	filename = path+alliance_name+datetime.datetime.now().strftime("-%Y%m%d-")

	# Meta Heroes for use in Incursion
	mutant	=	['Archangel','Nemesis','Dark Beast','Psylocke','Magneto']
	bio		=	['Captain America','Captain Carter','Agent Venom','Winter Soldier','U.S. Agent']
	skill	=	['Nick Fury','Captain America (WWII)','Iron Fist (WWII)','Bucky Barnes','Union Jack']
	mystic	=	['Beta Ray Bill','Loki','Loki (Teen)','Sylvie','Vahl']
	tech	=	['Kang the Conqueror','Doctor Doom','Hulkbuster','Kestrel','Viv Vision','Vision']

	# Tables with just Incursion Meta. 
	html_file = create_pivot_table(processed_players, char_stats, char_list = mutant+bio+skill+mystic+tech)
	open(filename+"pivot-incursion.html", 'w').write(html_file)

	# Tables for all characters, broken down by Origin. 
	# Filtering with minimum ISO and Gear Tier just to reduce noise from Minions, old heroes, etc.
	html_file = create_pivot_table(processed_players, char_stats, min_iso=9, min_tier=16,)
	open(filename+"pivot-all.html", 'w').write(html_file)


def create_pivot_table(processed_players, char_stats, keys=['power','tier','iso'], min_iso=0, min_tier=0, char_list=[], section_traits = [['Mutant'],['Bio'],['Skill'],['Mystic'],['Tech']]):

	# If no char_list is specified, pull the list of all characters from char_stats
	if not char_list:
		char_list = get_char_list (char_stats)
	
	# Get the list of Alliance Members we will iterate through as rows.	
	player_list = list(processed_players.keys())
	player_list.sort(key=str.lower)

	html_file = '<!doctype html>\n<html>\n'

	for traits in section_traits:

		# Write the top lines - char list and then value descriptors
		html_file += '<table border="1" style="background-color:cornflower; font-family:verdana; font-size: 12">\n'
		html_file += '  <thead>\n'

		# Start with the entire character list.
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
						# Character has at least one of these trait. Leave it in.
						break
				# Did we find this char in any of the traits?
				if char not in chars_from_trait[trait]:
					active_chars.remove(char)
		
		# Write the images row. 
		html_file += '    <tr style="background-color:LightBlue; text-align: center;">\n'
		html_file += '      <th>'+', '.join(traits).upper()+'</th>\n'

		for char in active_chars:
			html_file += '      <th style="background-color:Black;" colspan="'+str(len(keys))+'"><img src="'+char_stats[char]['portrait']+'" alt="" width="100"></th>\n'
		
		html_file += '    </tr>\n'

		# Write the character names row. 
		html_file += '    <tr style="background-color:LightBlue; text-align: center;">\n'
		html_file += '      <th nowrap width="150">'+['Alliance Member',''][len(keys)>1]+'</th>\n'

		for char in active_chars:
			html_file += '      <th colspan="'+str(len(keys))+'" width="100">'+char+'</th>\n'
		
		html_file += '    </tr>\n'

		# Add a line with value descriptors only if more than one item requested.
		if len(keys)>1:
			html_file += '    <tr style="background-color:MidnightBlue; color:White;">\n'
			html_file += '      <th>Alliance Member</th>\n'
			for char in active_chars:
				for key in keys:
					html_file += '      <th>'+key.title()+'</th>\n'
		
			html_file += '    </tr>\n'

		html_file += '  </thead>\n'
		html_file += '  <tbody style="background-color:LightBlue; style="text-align: center; font-size: 12">\n'

		# Finally, write the data for each row. Player name then relevant stats for each character.
		for player_name in player_list:
			processed_chars = processed_players[player_name]
			html_file += '    <tr">\n'
			html_file += '      <th style="text-align: left; font-size: 12">'+player_name+'</th>\n'

			for char_name in active_chars:
				for key in keys:
					html_file += '      <td style="text-align: center; font-size: 12; background-color:'+get_value_color(char_stats,char_name,key,processed_chars[char_name][key])+';">'+processed_chars[char_name][key]+'</td>\n'
		
			html_file += '    </tr>\n'

		# Close the HTML table at the end of the doc.
		html_file += '  </tbody>\n'
		html_file += '</table >\n'

		# If not the final section, add a divider row. 
		if traits != section_traits[-1:][-1:][0]:
			html_file += '    <p></p>\n'

	html_file += '</html>'
		
	return html_file
																				
																				
# Linear gradient from red, to yellow, to green. 
# Costly to calculate, so only doing it once.
color_scale = polylinear_gradient(['#FF866F','#F6FF6F','#6FFF74'],1000)['hex']																																												

# Translate value to a color from the Heat Map gradient.
def get_value_color(char_stats,char_name,stat,value):
	value = int(value)
	
	if not value:
		return 'Beige'

	max_colors = len(color_scale)-1

	# Use the min/max in 'all' for calculating heat maps.
	min = char_stats['all'][stat]['min']
	max = char_stats['all'][stat]['max']

	#Tweak gradients for Tier and ISO
	if stat=='iso':
		return color_scale[int( ((value**3)/10**3) *max_colors)]

	if stat=='tier':
		if value <= 15:
			return color_scale[int( ((value**2)/15**2) *0.50 *max_colors)]
		else:
			return color_scale[int((0.65+((value-16)/3)*0.35)*max_colors)]

	return color_scale[int((value-min)/(max-min)*max_colors)]


# Bring back a sorted list of characters from our 
def get_char_list(char_stats):
	char_list = list(char_stats.keys())
	#
	char_list.remove('all')
	#
	# Prune the unsummoned characters.
	for char in char_list[:]:
		if 'iso' not in char_stats[char].keys():
			char_list.remove(char)
	#
	char_list.sort()
	#
	return char_list


if __name__ == "__main__":
	main() # Just run myself

