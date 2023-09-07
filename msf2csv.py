#!/usr/bin/env python3
# Encoding: UTF-8
"""msf2csv.py
Transform stats from MSF.gg into readable tables with heatmaps.
"""

import os
import datetime
import sys

from process_website import *       # Routines to get Roster data from website
from generate_html import *         # Routines to generate the finished tables.		


# If not frozen, work in the same directory as this script.
path = os.path.dirname(__file__)
# If frozen, work in the same directory as the executable.
if getattr(sys, 'frozen', False):
	path = os.path.dirname(sys.executable)


# If no name specified, default to the alliance for the Login player 
def main(alliance_name=''):

	# Load roster info directly from cached data or the website.
	alliance_info = get_alliance_info(alliance_name)

	# Meta Heroes for use in Incursion
	incur_lanes =	[[{'traits': ['Mutant'], 'meta': ['Archangel','Nemesis','Dark Beast','Psylocke','Magneto']},
					  {'traits': ['Bio'],    'meta': ['Captain America','Captain Carter','Agent Venom','Winter Soldier','U.S. Agent']},
					  {'traits': ['Skill'],  'meta': ['Nick Fury','Captain America (WWII)','Iron Fist (WWII)','Bucky Barnes','Union Jack']},
					  {'traits': ['Mystic'], 'meta': ['Beta Ray Bill','Loki','Loki (Teen)','Sylvie','Vahl']},
					  {'traits': ['Tech'],   'meta': ['Kang the Conqueror','Doctor Doom','Hulkbuster','Viv Vision','Vision']}]]
								 
	# Meta Heroes for use in Gamma 
					 # Lane 1    
	gamma_lanes =	[[{'traits': ['Avenger','GotG'],								'meta': ['Viv Vision','Vision','Deathlok','Hulkbuster','Iron Man']},
					  {'traits': ['PymTech','Infestation','Kree'],					'meta': ['Ghost','Yellowjacket','Minn-Erva','Captain Marvel','Phyla-Vell']},
					  {'traits': ['Brotherhood','Mercenary','Xmen'],				'meta': ['Dazzler', 'Fantomex', 'Gambit', 'Rogue', 'Sunfire']},
					  {'traits': ['Kree','SpiderVerse','GotG'],						'meta': ['Ghost-Spider','Spider-Man (Miles)','Spider-Weaver','Spider-Man','Scarlet Spider']}],
					 # Lane 2	 		
					 [{'traits': ['Avenger','SpiderVerse'],							'meta': ['Viv Vision','Vision','Deathlok','Hulkbuster','Iron Man']},
					  {'traits': ['PymTech','Infestation','Wakanda'],				'meta': ['Black Panther', 'Black Panther (1MM)', 'Nakia', 'Okoye', 'Shuri']},
					  {'traits': ['Brotherhood','Mercenary','Xmen'],				'meta': ['Dazzler', 'Fantomex', 'Gambit', 'Rogue', 'Sunfire']},
					  {'traits': ['Kree','SpiderVerse','GotG'],						'meta': ['Ghost-Spider','Spider-Man (Miles)','Spider-Weaver','Spider-Man','Scarlet Spider']}],
					 # Lane 3    
					 [{'traits': ['Shield','Brotherhood'],							'meta': ['Black Widow','Captain America','Nick Fury','Maria Hill','Magneto']},
					  {'traits': ['Defender','Mercenary','HeroesForHire'],			'meta': ['Colleen Wing', 'Iron Fist', 'Luke Cage', 'Misty Knight', 'Shang-Chi']},
					  {'traits': ['GotG','Xmen','Mercenary'],						'meta': ['Dazzler', 'Fantomex', 'Gambit', 'Rogue', 'Sunfire']},
					  {'traits': ['Brotherhood','Mercenary','Xmen'],				'meta': ['Dazzler', 'Fantomex', 'Gambit', 'Rogue', 'Sunfire']},
					  {'traits': ['Kree','SpiderVerse','GotG'],						'meta': ['Ghost-Spider','Spider-Man (Miles)','Spider-Weaver','Spider-Man','Scarlet Spider']}],
					 # Lane 4    
					 [{'traits': ['Shield','Aim'],									'meta': ['Black Widow','Captain America','Nick Fury','Maria Hill','Hawkeye']},
					  {'traits': ['Defender','Hydra','HeroesForHire'],				'meta': ['Colleen Wing', 'Iron Fist', 'Luke Cage', 'Misty Knight', 'Shang-Chi']},
					  {'traits': ['Shield','Wakanda','Defender','HeroesForHire'],	'meta': ['Black Panther', 'Black Panther (1MM)', 'Nakia', 'Okoye', 'Shuri']},
					  {'traits': ['Kree','SpiderVerse','GotG'],						'meta': ['Ghost-Spider','Spider-Man (Miles)','Spider-Weaver','Spider-Man','Scarlet Spider']}]]


	war_lanes =	    [[{'traits': ['Key<br>Villains'],       'meta': ['Apocalypse','Dormammu','Doctor Doom','Kang the Conqueror', 'Super Skrull']},
                      {'traits': ['MastersOfEvil']},
                      {'traits': ['Knowhere']},
                      {'traits': ['Gamma']},
                      {'traits': ['Unlimited']},
                      {'traits': ['Deathseed']},
                      {'traits': ['Darkhold']},
                      {'traits': ['Under-<br>world'],    'meta': ['Kingpin','Mister Negative','Nobu','Taskmaster','Green Goblin']},
                      {'traits': ['AForce']},
                      {'traits': ['WarDog']},
                      {'traits': ['WeaponX']},
                      {'traits': ['InfinityWatch']},
                      {'traits': ['DarkHunter']},
                      {'traits': ['Dark<br>Hunters<br>+<br>Quicksilver'],       'meta': ['Doctor Voodoo','Elsa Bloodstone','Ghost Rider','Morbius','Quicksilver']},
                      {'traits': ['Undying']},
                      {'traits': ['TangledWeb']},
                      {'traits': ['Eternal']},
                      {'traits': ['Invaders'],       'meta': ['Nick Fury','Captain America (WWII)','Iron Fist (WWII)','Bucky Barnes','Union Jack']},
                      {'traits': ['Bifrost']},
                      {'traits': ['Young<br>Avengers'],  'meta': ['America Chavez','Echo','Kate Bishop','Ms. Marvel','Squirrel Girl']},
                      {'traits': ['Infestation']}]]
								 

	print ("Writing pivot tables to:",path)

	filename = path + os.sep + alliance_info['name'] + datetime.datetime.now().strftime("-%Y%m%d-")

	# Tables with just Incursion 1.4 Meta. Requires ISO 2-4 and Gear Tier 16.
	html_file = generate_html(alliance_info, alliance_info['strike_teams']['incur'], incur_lanes, min_iso=9, min_tier=16, table_name='Incursion Raid')
	open(filename+"incursion.html", 'w', encoding='utf-16').write(html_file)    
                                                             
	# Tables with just Gamma Lanes. Only limit is Gear Tier 16.
	html_file = generate_html(alliance_info, alliance_info['strike_teams']['other'], gamma_lanes, min_tier=16, table_name='Gamma Raid')
	open(filename+"gamma.html", 'w', encoding='utf-16').write(html_file)

	# Tables with typical War Teams.
	html_file = generate_html(alliance_info, alliance_info['strike_teams']['other'], war_lanes, table_name='War')
	open(filename+"war.html", 'w', encoding='utf-16').write(html_file)  
	
	# Tables for all characters, broken down by Origin. 
	# Filtering with minimum ISO and Gear Tier just to reduce noise from Minions, old heroes, etc.
	#html_file = generate_html(alliance_info, alliance_info['strike_teams']['other'], keys=['power','tier','iso'], min_iso=9, min_tier=16)
	#open(filename+"all.html", 'w', encoding='utf-16').write(html_file)

	# Original file format. Requested for input to projects using old CSV format.
	#csv_file = generate_csv(alliance_info)
	#open(filename+"original.csv", 'w', encoding='utf-16').write(csv_file)


if __name__ == "__main__":
	main() # Just run myself

