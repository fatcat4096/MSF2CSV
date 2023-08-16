#!/usr/bin/env python3
# Encoding: UTF-8
"""msf2csv.py
Transform stats from MSF.gg into readable tables with heatmaps.
"""

# Standard library modules do the heavy lifting. Ours is all simple stuff.
import os
import datetime
import pickle

from process_mhtml import *         # Routines to get Roster data from MHTML.
from process_website import *       # Routines to get Roster data from website
from generate_html import *         # Routines to generate the finished tables.		


# You'll want to edit this. 
incur_strike_teams = [ ['Joey', 'FatCat', 'Venom 4 Life', 'Ramalama', '----',
						'Jutch', 'sjhughes', 'Daner', 'DrFett'],
						['Shammy', 'BigDiesel', 'EXfieldy', 'mgmf', '----',
						'HeadHunter2838', 'Luthher', 'keithchyiu', 'FabiooBessa'],
						['Zen Master', 'RadicalEvil', 'Kal-El', 'Snicky', '----',
						'Zairyuu', 'Unclad', 'Incredibad', 'Flashie']]

strike_teams = [['FatCat', 'Joey', 'Daner', 'Jutch', 'sjhughes', 'Ramalama', 'DrFett', 'Venom 4 Life'],
				['Shammy', 'HeadHunter2838', 'keithchyiu', 'mgmf', 'BigDiesel', 'Luthher', 'EXfieldy', 'FabiooBessa'],
				['Zen Master', 'Incredibad', 'Kal-El', 'Snicky', 'Zairyuu', 'Flashie', 'Unclad', 'RadicalEvil']]

# We will be working in the same directory as this file.
try:
	path = os.path.dirname(__file__)+os.sep
# Sourcing locally, no __file__ object.
except:
	path = '.'+os.sep


# Just do it.
def main():

	processed_players = {}	# roster stats for each player
	char_stats = {}			# min/max stats and portrait path for individual heroes

	try:
		# Load roster info from pickled data, this is possibly stale, but we will attempt to refresh.
		[char_stats,processed_players] = pickle.load(open('cached_data','rb'))
	except:
		pass
	
	# Load roster info from the MHTML files present.
	#char_stats,processed_players = process_mhtml(path)

	# Load roster info directly from the website.
	#process_website(char_stats,processed_players)

	# cache the updated roster info to disk.
	pickle.dump([char_stats,processed_players],open('cached_data','wb'))
	
	alliance_name = processed_players['alliance_info']['name']
	filename = path+alliance_name+datetime.datetime.now().strftime("-%Y%m%d-")

	# Meta Heroes for use in Incursion
	incur_lanes =	[[{'traits': ['Mutant'], 'meta': ['Archangel','Nemesis','Dark Beast','Psylocke','Magneto']},
					  {'traits': ['Bio'],    'meta': ['Captain America','Captain Carter','Agent Venom','Winter Soldier','U.S. Agent']},
					  {'traits': ['Skill'],  'meta': ['Nick Fury','Captain America (WWII)','Iron Fist (WWII)','Bucky Barnes','Union Jack']},
					  {'traits': ['Mystic'], 'meta': ['Beta Ray Bill','Loki','Loki (Teen)','Sylvie','Vahl']},
					  {'traits': ['Tech'],   'meta': ['Kang the Conqueror','Doctor Doom','Hulkbuster','Viv Vision','Vision']}]]
								 
	# Meta Heroes for use in Gamma 
					 # Lane 1    
	gamma_lanes =	[[{'traits': ['Avenger','GotG'],								'meta': ['Viv Vision','Vision','Deathlok','Hulkbuster','Iron Man']},
					  {'traits': ['PymTech','Kree'],								'meta': ['Ghost','Yellowjacket','Minn-Erva','Captain Marvel','Phyla-Vell']},
					  {'traits': ['Brotherhood','Mercenary','Xmen'],				'meta': ['Dazzler', 'Fantomex', 'Gambit', 'Rogue', 'Sunfire']},
					  {'traits': ['Kree','SpiderVerse','GotG'],						'meta': ['Ghost-Spider','Spider-Man (Miles)','Spider-Weaver','Spider-Man','Scarlet Spider']}],
					 # Lane 2	 		
					 [{'traits': ['Avenger','SpiderVerse'],							'meta': ['Viv Vision','Vision','Deathlok','Hulkbuster','Iron Man']},
					  {'traits': ['PymTech','Wakanda'],								'meta': ['Black Panther', 'Black Panther (1MM)', 'Nakia', 'Okoye', 'Shuri']},
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

	print ("Writing pivot tables to:",path)

	# Tables with just Incursion 1.4 Meta. Requires ISO 2-4 and Gear Tier 16.
	html_file = generate_html(processed_players, char_stats, incur_strike_teams, incur_lanes, min_iso=9, min_tier=16)
	open(filename+"incursion.html", 'w').write(html_file)    
                                                             
	# Tables with just Gamma Lanes. Only limit is Gear Tier 16.
	html_file = generate_html(processed_players, char_stats, strike_teams, gamma_lanes, min_tier=16)
	open(filename+"gamma.html", 'w').write(html_file)

	# Tables for all characters, broken down by Origin. 
	# Filtering with minimum ISO and Gear Tier just to reduce noise from Minions, old heroes, etc.
	html_file = generate_html(processed_players, char_stats, strike_teams, min_iso=9, min_tier=16)
	open(filename+"all.html", 'w').write(html_file)


if __name__ == "__main__":
	main() # Just run myself

