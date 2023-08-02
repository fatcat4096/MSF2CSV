#!/usr/bin/env python3
# Encoding: UTF-8
"""msf2csv.py
Unpacks all MHTML files in the local directory. Searches the MHTML tree to find the character file from MSF.GG. 
Scrapes this file for Roster info (player name, character stats, etc.) and adds everything into a single CSV for the Alliance.
Use pivot tables in a Spreadsheet app to format table with the information relevant to your purpose -- power, gear tier, or ISO 
Derived from mhtifier.py code by Ilan Irad -- https://github.com/Modified/MHTifier
"""

# Standard library modules do the heavy lifting. Ours is all simple stuff.
import email, email.message
import os
import sys
import datetime
import pickle
from bs4 import BeautifulSoup


alliance_name = 'SIGMA_Infamously_Strange'

quiet   = 0
verbose = 1


# We will look for MHTML in the same directory as this file.
try:
	path = os.path.dirname(__file__)+os.sep
# Sourcing locally, no __file__ object.
except:
	path = '.'+os.sep


# Just do it.
def main():
	"""
	History: 
		MSF.gg used to have a CSV download option which made it easy to load up full roster stats for everyone in the alliance. 
		During a recent "upgrade" this button was removed. Likely a temporary issue, but it still leaves Alliance leaders in a bad spot.
		This is a rudimentary solution to the problem. Takes more work, but it does produce a good result.
		Feel free to provide feedback, questions, comments, etc. My username is "fatcat4096" on Discord. 
	
	Requirements:
		1. Install Python
		2. Install Beautiful Soup 4 -- 'pip install beautifulsoup4

	Usage:
		1. From the MSF website Alliance view, navigate into the Roster page for each member of your alliance.
		2. On each member's Roster page, right click on the background and Save As a "Webpage, single file (*.mhtml)"
		3. Actual name of the MHTML file is not critical. Player name for the CSV file is taken from the HTML.
		4. Double click on the mht2csv.py file. 
		
	Output:
		Currently, the script creates multiple output files. Keep or delete whichever you want.
			1. One copy of the CSV in the original format which used to be downloadable from MSF.gg
			2. HTML for a table showing Power for each character for each of the Alliance members
			3. HTML for a table showing Power and Gear Tier (for planning Gamma 4.5, for example)
			4. HTML for a table showing Power and ISO (for planning Incursion Raids)
			5. HTML for a version with all three data points.
			
	"""

	# Extract all the relevant info from MTHML roster files in this directory
	#char_stats,processed_players = process_mhtml()

	# pickle char_stats,processed_players to disk.
	#pickle.dump([char_stats,processed_players],open('sample_data','wb'))
	
	# load sample data from pickled file.
	[char_stats,processed_players] = pickle.load(open('sample_data','rb'))

	# Output selected tables built from the parsd information
	output_files(char_stats, processed_players)



def process_mhtml():

	processed_players = {}
	char_stats = {}
	
	for file in os.listdir(path):
		# Skip if not MHTML
		if file[-5:] != "mhtml":
			continue
		
		# Open the .mhtml file for reading. 
		mht = open(path+file, "rb")

		if not quiet:
			sys.stderr.write("Unpacking "+file+"...\n")

		# Read entire MHT archive -- it's a multipart(/related) message.
		a = email.message_from_bytes(mht.read()) 
		
		parts = a.get_payload() # Multiple parts, usually?
		if not type(parts) is list:
			parts = [a] # Single 'str' part, so convert to list.
																			
		# Look for the 'character' file among the file parts.
		for part in parts: 
			content_type = part.get_content_type() # String coerced to lower case of the form maintype/subtype, else get_default_type().			
			file_path    = part.get("content-location") or "index.html" # File path. Expecting root HTML is only part with no location.

			# Ignore the path, focus on the filename.
			decoded_file = file_path.split('/')[-1]

			# Only the characters.html file has relevant data.
			if decoded_file == 'characters':
				soup = BeautifulSoup(part.get_payload(decode=True), 'html.parser')

				player_name = soup.find('div', attrs = {'class':'player-name is-italic'}).text.strip().title()

				#Skip file if player info already processed.
				if player_name in processed_players:
					continue

				sys.stderr.write("Parsing %s to %s, %d bytes...found %s\n" % (content_type, file_path, len(part.get_payload()), player_name))

				processed_chars  = {}
				
				chars  = soup.findAll('li', attrs = {'class':'character'})

				for char in chars:
					
					# If no char_name defined, last entry on page. Skip.
					char_name = char.find('h4').text.strip()
					if not char_name:
						pass

					toon_stats = char.find('div', attrs = {'id':'toon-stats'})
					
					# Stats available only if character is recruited.
					if toon_stats:
						# Decode Level and Power
						stats = toon_stats.findAll('div', attrs = {'class':''})
						level = stats[0].text.strip().split()[1]
						power = ''.join(stats[1].text.strip().split(','))

						set_min_max(char_stats,char_name,'level',level)
						set_min_max(char_stats,char_name,'power',power)
						
						# Decode Yellow and Red Stars
						stars = str(toon_stats.find('span'))
						redStars = str(stars.count('red'))
						yelStars = str(stars.count('red') + stars.count('orange'))
						
						# Decode Abilities
						abilities = toon_stats.findAll('div', attrs = {'class':'ability-level'})
						basic   = str(abilities[0]).split('-')[3][1]
						special = str(abilities[1]).split('-')[3][1]
						ult = '0'
						if len(abilities)==4:
							ult = str(abilities[-2]).split('-')[3][1]
						passive = str(abilities[-1]).split('-')[3][1]
						
						# Decode Gear Tier
						gear = char.find('div',attrs={'class':'gear-tier-ring'})
						tier = str(gear).split('"g')[2].split('"')[0]

						set_min_max(char_stats,char_name,'tier',tier)
					
						# Decode ISO Level
						iso_info = str(char.find('div',attrs={'class','iso-wrapper'}))
						iso = 0
						if iso_info.find('-pips-') != -1:
							iso = int(iso_info.split('-pips-')[1][0])
						if iso_info.find('blue') != -1:
							iso += 5
						iso = str(iso)

						set_min_max(char_stats,char_name,'iso',iso)

						processed_chars[char_name] = {'level':level,'power':power,'tier':tier,'iso':iso, 'yelStars':yelStars, 'redStars':redStars, 'basic':basic, 'special':special, 'ult':ult, 'passive':passive}

					# Entries for Heroes not yet collected, no name on final entry for page.
					elif char_name:
						processed_chars[char_name] = {'level':'0','power':'0','tier':'0','iso':'0', 'yelStars':'0', 'redStars':'0', 'basic':'0', 'special':'0', 'ult':'0', 'passive':'0'}

					# Add these chars to our list of processed players.
					processed_players[player_name] = processed_chars

	return char_stats,processed_players


def output_files(char_stats,processed_players):

	# Pull char_list from char_stats.
	char_list = list(char_stats.keys())
	char_list.remove('all')
	char_list.sort()

	filename = path+alliance_name+datetime.datetime.now().strftime("-%Y%m%d-%H%M-")

	# Write the basic output to a CSV in the local directory.
	keys = ['level','power','tier','iso','yelStars','redStars','basic','special','ult','passive']
	csv_file = ['Player,Character,'+','.join([key.title() for key in keys])]
	player_list = list(processed_players.keys())
	player_list.sort()
	for player_name in player_list:
		processed_chars = processed_players[player_name]
		for char_name in char_list:
			csv_file.append(','.join([player_name, char_name] + [processed_chars[char_name][key] for key in keys]))

	# Original CSV format, all info included. 
	#open(filename+"orig.csv", 'w').write('\n'.join(csv_file))

	# Pivot table with Power only. 
	#html_file = create_pivot_table(processed_players,char_stats)
	#open(filename+"pivot-power.html", 'w').write(html_file)

	# Incursion focused pivot table with Power and ISO. 
	#html_file = create_pivot_table(processed_players,char_stats,['power','iso'])
	#open(filename+"pivot-incursion.html", 'w').write(html_file)

	# Gamma focused pivot table with Power and Gear Tier. 
	#html_file = create_pivot_table(processed_players,char_stats,['power','tier'])
	#open(filename+"pivot-gamma.html", 'w').write(html_file)

	# Full pivot table with all three. 
	html_file = create_pivot_table(processed_players,char_stats,['power','tier','iso'],  min_iso=9, min_tier=16, section_traits = [['Mutant'],['Bio'],['Skill'],['Mystic'],['Tech']])
	open(filename+"pivot-all.html", 'w').write(html_file)


def create_pivot_table(processed_players, char_stats, keys=['power'], min_iso=0, min_tier=0, char_list=[], section_traits=[[]]):

	# FUTURE: Allow filters to be passed in and character inclusion to be based upon whether a character has any of those tags. 
	# FUTURE: Define Lanes and Sections that can be processed individually, using the filters. So requesting a type='gamma' raid would generate four lanes with filters for each section. Incursion would generate one lane, with filters for each origin matching each section.
	# FUTURE: After one each run through the files provided, output a text file named alliance_members.txt which has a list of all the members and definitions for Strike Teams 1-3. If edited to place those members in specific Strike Teams, those Strike teams should be used to group output rows.

	# If no char_list is specified, pull the list of all characters from char_stats
	if not char_list:
		char_list = list(char_stats.keys())
		char_list.remove('all')
		char_list.sort()

	
	# Get the list of Alliance Members we will iterate through as rows.	
	player_list = list(processed_players.keys())
	player_list.sort()


	# Write the top lines - char list and then value descriptors
	html_file  = '<table border="1" class="dataframe" style="font-family:verdana">\n'
	html_file += '  <thead>\n'

	for traits in section_traits:

		# Start with the entire character list.
		active_chars = char_list
		
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
		
		# Write the first row. 
		html_file += '    <tr style="text-align: center;">\n'
		html_file += '      <th style="background-color:LightBlue;">'+['Alliance member',', '.join(traits).upper()][len(keys)>1]+'</th>\n'

		for char in active_chars:
			html_file += '      <th style="background-color:LightBlue;" colspan="'+str(len(keys))+'">'+char+'</th>\n'
		
		html_file += '    </tr>\n'

		# Add a line with value descriptors only if more than one item requested.
		if len(keys)>1:
			html_file += '    <tr style="text-align: center;">\n'
			html_file += '      <th style="background-color:MidnightBlue;color:White;">Alliance member</th>\n'
			for char in active_chars:
				for key in keys:
					html_file += '      <th style="background-color:MidnightBlue;color:white;">'+key.title()+'</th>\n'
		
			html_file += '    </tr>\n'

		html_file += '  </thead>\n'
		html_file += '  <tbody>\n'

		# Finally, write the data for each row. Player name then relevant stats for each character.
		for player_name in player_list:
			processed_chars = processed_players[player_name]
			html_file += '    <tr style="text-align: center;">\n'
			html_file += '      <th style="text-align: left; background-color:LightBlue;">'+player_name+'</th>\n'

			for char_name in active_chars:
				for key in keys:
					html_file += '      <td style="background-color:'+get_value_color(char_stats,char_name,key,processed_chars[char_name][key])+';">'+processed_chars[char_name][key]+'</td>\n'
		
			html_file += '    </tr>\n'

		# If not the final section, add a divider row. 
		if traits != section_traits[-1:][-1:]:
			html_file += '    <tr style="text-align: center;">\n'
			html_file += '      <td style="background-color:LightBlue;" colspan="0"></td>\n'
			html_file += '    </tr>\n'		
		
		
	# Close the HTML table at the end of the doc.
	html_file += '  </tbody>\n'
	html_file += '</table >\n'
		
	return html_file


traits_from_char = {"Abomination":				["Villain","Global","Bio","Brawler","Gamma"],																			
					"Absorbing Man":			["Villain","Global","Mystic","Protector","MastersOfEvil"],
					"Adam Warlock":				["Hero","Cosmic","Mystic","Support","InfinityWatch","Legendary"],
					"Agatha Harkness":			["Villain","Global","Mystic","Support","Darkhold"],
					"Agent Coulson":			["Hero","Global","Tech","Controller","Avenger","Shield"],
					"Agent Venom":				["Hero","Global","Bio","Blaster","SpiderVerse","Symbiote","Rebirth"],
					"A.I.M. Infector":			["Villain","Global","Bio","Controller","Aim","Minion"],
					"A.I.M. Monstrosity":		["Villain","Global","Bio","Brawler","Aim","Minion"],
					"A.I.M. Assaulter":			["Villain","Global","Tech","Blaster","Aim","Minion"],
					"A.I.M. Researcher":		["Villain","Global","Skill","Support","Aim","Minion"],
					"A.I.M. Security":			["Villain","Global","Tech","Protector","Aim","Minion"],
					"America Chavez":			["Hero","Cosmic","Mystic","Brawler","YoungAvenger"],
					"Ant-Man":					["Hero","Global","Tech","Controller","Avenger","PymTech","Infestation"],
					"Anti-Venom":				["Hero","City","Bio","Support","SpiderVerse","Symbiote"],
					"Apocalypse":				["Villain","Global","Mutant","Support"],
					"Archangel":				["Villain","Global","Mutant","Blaster","Deathseed","Horseman","Legendary"],
					"Baron Zemo":				["Villain","Global","Skill","Controller","Hydra"],
					"Beast":					["Hero","Global","Mutant","Support","Uncanny","Astonishing"],
					"Beta Ray Bill":			["Hero","Cosmic","Mystic","Protector","Bifrost","Asgard"],
					"Bishop":					["Hero","Cosmic","Mutant","Blaster","Astonishing"],
					"Black Bolt":				["Hero","Cosmic","Bio","Blaster","Inhuman","Legendary"],
					"Black Panther":			["Hero","Global","Mystic","Brawler","Avenger","Wakanda","WarDog"],
					"Black Panther (1MM)":		["Hero","Global","Mystic","Brawler","Wakanda","WarDog"],
					"Black Widow":				["Hero","Global","Skill","Controller","Shield","Wave1Avenger","Military","Infestation"],
					"Blob":						["Villain","Global","Mutant","Protector","Brotherhood"],
					"Brawn":					["Hero","Global","Bio","Support","Gamma"],
					"Bucky Barnes":				["Hero","Global","Skill","Blaster","Invader"],
					"Bullseye":					["Villain","City","Skill","Blaster","Mercenary"],
					"Cable":					["Hero","Cosmic","Mutant","Blaster","Xforce"],
					"Captain America":			["Hero","Global","Bio","Protector","Shield","Military","Wave1Avenger","Rebirth"],
					"Captain America (Sam)":	["Hero","Global","Skill","Protector","SecretAvenger"],
					"Captain America (WWII)":	["Hero","Global","Skill","Controller","Invader"],
					"Captain Carter":			["Hero","Global","Bio","Support","Rebirth"],
					"Captain Marvel":			["Hero","Cosmic","Bio","Brawler","Kree","Military","AForce"],
					"Carnage":					["Villain","City","Bio","Brawler","SpiderVerse","Symbiote"],
					"Cloak":					["Hero","City","Mystic","Controller","NewWarrior"],
					"Colleen Wing":				["Hero","City","Skill","Brawler","HeroesForHire"],
					"Colossus":					["Hero","Global","Mutant","Protector","Uncanny"],
					"Corvus Glaive":			["Villain","Cosmic","Skill","Brawler","BlackOrder"],
					"Cosmo":					["Hero","Cosmic","Bio","Support","GotG","Knowhere"],
					"Crossbones":				["Villain","Global","Tech","Protector","Hydra"],
					"Crystal":					["Hero","Cosmic","Bio","Blaster","Inhuman"],
					"Cull Obsidian":			["Villain","Cosmic","Bio","Protector","BlackOrder"],
					"Cyclops":					["Hero","Global","Mutant","Blaster","Uncanny"],
					"Dagger":					["Hero","City","Mystic","Support","NewWarrior"],
					"Daredevil":				["Hero","City","Bio","Brawler","Defender","Shadowland"],
					"Dark Beast":				["Villain","Global","Mutant","Controller","Deathseed"],
					"Dazzler":					["Hero","Global","Mutant","Controller","Unlimited"],
					"Deadpool":					["Hero","Global","Mutant","Brawler","Xforce","Mercenary"],
					"Deathlok":					["Hero","Global","Tech","Blaster","BionicAvenger"],
					"Deathpool":				["Hero","Cosmic","Mystic","Brawler","NewWarrior"],
					"Doctor Doom":				["Villain","Global","Tech","Mystic","Controller"],
					"Doctor Octopus":			["Villain","City","Tech","Support","SpiderVerse","SinisterSix","Legendary"],
					"Doctor Strange":			["Hero","Cosmic","Mystic","Support","Supernatural"],
					"Doctor Voodoo":			["Hero","Global","Support","Mystic","DarkHunter"],
					"Domino":					["Hero","Global","Mutant","Controller","Xforce"],
					"Dormammu":					["Villain","Cosmic","Mystic","Support"],
					"Drax":						["Hero","Cosmic","Bio","Protector","GotG"],
					"Ebony Maw":				["Villain","Cosmic","Mystic","Support","BlackOrder","Legendary"],
					"Echo":						["Hero","Global","Skill","Brawler","YoungAvenger"],
					"Electro":					["Villain","City","Bio","Blaster","SpiderVerse","SinisterSix"],
					"Elektra":					["Villain","City","Mystic","Brawler","Hand","Shadowland"],
					"Elsa Bloodstone":			["Hero","Global","Mystic","Blaster","Supernatural","DarkHunter"],
					"Emma Frost":				["Villain","Global","Mutant","Controller"],
					"Falcon":					["Hero","Global","Tech","Blaster","Avenger","PowerArmor"],
					"Fantomex":					["Hero","Global","Mutant","Blaster","Unlimited"],
					"Firestar":					["Hero","City","Mutant","Blaster","NewWarrior"],
					"Gambit":					["Hero","Global","Mutant","Blaster","Unlimited"],
					"Gamora":					["Hero","Cosmic","Skill","Brawler","GotG","InfinityWatch"],
					"Ghost":					["Villain","Global","Tech","Controller","PymTech"],
					"Ghost Rider":				["Hero","City","Mystic","Brawler","Supernatural","DarkHunter"],
					"Ghost-Spider":				["Hero","City","Bio","Controller","SpiderVerse","WebWarrior"],
					"Graviton":					["Villain","Global","Bio","Controller","Aim"],
					"Green Goblin":				["Villain","City","Bio","Blaster","SpiderVerse","SinisterSix","Underworld"],
					"Groot":					["Hero","Cosmic","Bio","Support","GotG"],
					"Gwenpool":					["Hero","City","Mystic","Brawler","NewWarrior"],
					"Hand Assassin":			["Villain","City","Mystic","Controller","Hand","Minion"],
					"Hand Blademaster":			["Villain","City","Skill","Brawler","Hand","Minion"],
					"Hand Archer":				["Villain","City","Skill","Blaster","Hand","Minion"],
					"Hand Sorceress":			["Villain","City","Mystic","Support","Hand","Minion"],
					"Hand Sentry":				["Villain","City","Mystic","Protector","Hand","Minion"],
					"Hawkeye":					["Hero","Global","Skill","Controller","Shield","Wave1Avenger"],
					"Heimdall":					["Hero","Cosmic","Mystic","Brawler","Asgard"],
					"Hela":						["Villain","Cosmic","Mystic","Controller","Asgard","Undying"],
					"Hulk":						["Hero","Global","Bio","Protector","Wave1Avenger","Gamma"],
					"Hulkbuster":				["Hero","Global","Tech","Protector","BionicAvenger"],
					"Human Torch":				["Hero","Cosmic","Bio","Blaster","FantasticFour"],
					"Hydra Grenadier":			["Villain","Global","Tech","Blaster","Hydra","Minion"],
					"Hydra Rifle Trooper":		["Villain","Global","Tech","Blaster","Hydra","Minion"],
					"Hydra Sniper":				["Villain","Global","Tech","Blaster","Hydra","Minion"],
					"Hydra Scientist":			["Villain","Global","Skill","Support","Hydra","Minion"],
					"Hydra Armored Guard":		["Villain","Global","Tech","Protector","Hydra","Minion"],
					"Iceman":					["Hero","Global","Mutant","Controller","Astonishing"],
					"Ikaris":					["Hero","Cosmic","Mystic","Blaster","Eternal"],
					"Invisible Woman":			["Hero","Cosmic","Bio","Protector","FantasticFour","Legendary"],
					"Iron Fist":				["Hero","City","Mystic","Brawler","Defender","HeroesForHire"],
					"Iron Fist (WWII)":			["Hero","Global","Skill","Support","Invader"],
					"Iron Man":					["Hero","Global","Tech","Blaster","Wave1Avenger","PowerArmor","BionicAvenger","Legendary"],
					"Iron Man (Zombie)":		["Villain","Global","Bio","Brawler","Undying"],
					"Ironheart":				["Hero","Global","Tech","Blaster","PowerArmor"],
					"Jessica Jones":			["Hero","City","Bio","Controller","Defender","AForce"],
					"Jubilee":					["Hero","Global","Mutant","Controller","Astonishing","Legendary"],
					"Juggernaut":				["Villain","Global","Mystic","Protector","Brotherhood"],
					"Kang the Conqueror":		["Villain","Cosmic","Tech","Blaster","MastersOfEvil"],
					"Karnak":					["Hero","Cosmic","Skill","Controller","Inhuman"],
					"Kate Bishop":				["Hero","Global","Tech","Controller","YoungAvenger"],
					"Kestrel":					["Hero","Cosmic","Tech","Skill","Blaster"],
					"Killmonger":				["Villain","Global","Skill","Blaster","Wakanda","Mercenary","Military"],
					"Kingpin":					["Villain","City","Skill","Protector","SpiderVerse","Underworld"],
					"Kitty Pryde":				["Hero","Global","Mutant","Protector","Astonishing"],
					"Korath the Pursuer":		["Villain","Cosmic","Tech","Blaster","Kree","Mercenary"],
					"Korg":						["Hero","Cosmic","Bio","Protector","Knowhere"],
					"Kree Noble":				["Villain","Cosmic","Bio","Controller","Kree","Minion"],
					"Kree Cyborg":				["Villain","Cosmic","Tech","Blaster","Kree","Minion"],
					"Kree Reaper":				["Villain","Cosmic","Bio","Brawler","Kree","Minion"],
					"Kree Oracle":				["Villain","Cosmic","Tech","Support","Kree","Minion"],
					"Kree Royal Guard":			["Villain","Cosmic","Bio","Protector","Kree","Minion"],
					"Lady Deathstrike":			["Villain","Global","Tech","Brawler","WeaponX"],
					"Loki":						["Villain","Cosmic","Mystic","Controller","Asgard","Bifrost"],
					"Loki (Teen)":				["Villain","Cosmic","Mystic","Support","Bifrost","Asgard"],
					"Longshot":					["Hero","Cosmic","Mutant","Blaster","XFactor"],
					"Luke Cage":				["Hero","City","Bio","Protector","Defender","HeroesForHire"],
					"M'Baku":					["Hero","Global","Mystic","Protector","Wakanda"],
					"Madelyne Pryor":			["Villain","Global","Mutant","Controller","Marauders"],
					"Magik":					["Hero","Cosmic","Mutant","Support","Uncanny"],
					"Magneto":					["Villain","Global","Controller","Mutant","Brotherhood","Deathseed","Legendary"],
					"Mantis":					["Hero","Cosmic","Bio","Controller","GotG"],
					"Maria Hill":				["Hero","Global","Skill","Support","Shield","SecretAvenger"],
					"Mercenary Soldier":		["Villain","City","Skill","Blaster","Mercenary","Minion","Military"],
					"Mercenary Sniper":			["Villain","City","Tech","Blaster","Mercenary","Minion"],
					"Mercenary Lieutenant":		["Villain","City","Tech","Support","Mercenary","Minion"],
					"Mercenary Riot Guard":		["Villain","City","Skill","Protector","Mercenary","Minion","Summon","Underworld"],
					"Mighty Thor":				["Hero","Cosmic","Mystic","Controller","Asgard"],
					"Minn-Erva":				["Villain","Cosmic","Support","Tech","Kree"],
					"Mister Fantastic":			["Hero","Cosmic","Bio","Controller","FantasticFour"],
					"Mister Negative":			["Villain","City","Mystic","Controller","SpiderVerse","Underworld"],
					"Mister Sinister":			["Villain","Global","Mutant","Marauders","Support"],
					"Misty Knight":				["Hero","City","Tech","Controller","HeroesForHire"],
					"Moon Knight":				["Hero","City","Mystic","Brawler","Shadowland"],
					"Moondragon":				["Hero","Cosmic","Skill","Support","InfinityWatch"],
					"Moonstone":				["Villain","Global","Bio","Controller","MastersOfEvil"],
					"Morbius":					["Villain","City","Controller","Mystic","SpiderVerse","DarkHunter"],
					"Mordo":					["Villain","Cosmic","Mystic","Controller","Supernatural","DarkHunter"],
					"Morgan Le Fay":			["Villain","Global","Mystic","Controller","Darkhold","Horseman","Legendary"],
					"Ms. Marvel":				["Hero","City","Bio","Brawler","Inhuman","YoungAvenger"],
					"Multiple Man":				["Hero","City","Mutant","Protector","XFactor"],
					"Mysterio":					["Villain","City","Tech","Controller","SpiderVerse","SinisterSix"],
					"Mystique":					["Villain","Global","Mutant","Controller","Brotherhood","Marauders"],
					"Nakia":					["Hero","Global","Skill","Controller","Wakanda","WarDog"],
					"Namor":					["Villain","Global","Mutant","Brawler"],
					"Nebula":					["Villain","Cosmic","Tech","Brawler","InfinityWatch","GotG"],
					"Negasonic":				["Hero","Global","Mutant","Blaster","Xforce"],
					"Nemesis":					["Villain","Global","Mutant","Support","Deathseed"],
					"Nick Fury":				["Hero","Global","Skill","Support","Avenger","Shield","Legendary","Invader"],
					"Nico Minoru":				["Hero","City","Mystic","Controller","AForce"],
					"Night Nurse":				["Hero","City","Skill","Support","Shadowland"],
					"Nobu":						["Villain","City","Mystic","Controller","Hand","Underworld"],
					"Nova":						["Hero","Cosmic","Bio","Blaster","Knowhere","Legendary"],
					"Okoye":					["Hero","Global","Skill","Controller","Wakanda","WarDog"],
					"Omega Red":				["Villain","Global","Mutant","Controller","WeaponX","Legendary"],
					"Phoenix":					["Hero","Global","Mutant","Controller","Uncanny","Legendary"],
					"Phyla-Vell":				["Hero","Cosmic","Bio","Protector","InfinityWatch","Kree"],
					"Polaris":					["Hero","Global","Controller","Mutant","XFactor"],
					"Proxima Midnight":			["Villain","Cosmic","Skill","Controller","BlackOrder"],
					"Psylocke":					["Hero","Global","Mutant","Brawler","Uncanny","Deathseed"],
					"Punisher":					["Hero","City","Skill","Blaster","Military"],
					"Pyro":						["Villain","Global","Mutant","Blaster","Brotherhood"],
					"Quake":					["Hero","Global","Bio","Controller","Shield","Inhuman"],
					"Quicksilver":				["Hero","Global","Mystic","Brawler"],
					"Ravager Boomer":			["Villain","Cosmic","Tech","Blaster","Ravager","Minion"],
					"Ravager Stitcher":			["Villain","Cosmic","Tech","Support","Ravager","Minion"],
					"Ravager Bruiser":			["Villain","Cosmic","Bio","Protector","Ravager","Minion"],
					"Red Guardian":				["Hero","Global","Skill","Protector","Military"],
					"Red Hulk":					["Hero","Global","Bio","Brawler","Gamma","Horseman","Legendary"],
					"Red Skull":				["Villain","Global","Bio","Controller","Hydra"],
					"Rescue":					["Hero","Global","Tech","Support","PowerArmor"],
					"Rhino":					["Villain","City","Bio","Protector","SpiderVerse","SinisterSix"],
					"Rocket Raccoon":			["Hero","Cosmic","Tech","Blaster","GotG"],
					"Rogue":					["Hero","Global","Mutant","Protector","Unlimited","Horseman","Legendary"],
					"Ronan the Accuser":		["Villain","Cosmic","Mystic","Controller","Kree"],
					"Sabretooth":				["Villain","Global","Mutant","Brawler","Brotherhood","Marauders","WeaponX"],
					"Scarlet Spider":			["Hero","City","Bio","Brawler","SpiderVerse","WebWarrior"],
					"Scarlet Witch":			["Hero","Global","Mystic","Controller","Avenger","Supernatural","Darkhold"],
					"Scientist Supreme":		["Villain","Global","Tech","Support","Aim"],
					"Scream":					["Villain","City","Bio","Controller","SpiderVerse","Symbiote"],
					"Sersi":					["Hero","Cosmic","Mystic","Controller","Eternal"],
					"Shang-Chi":				["Hero","City","Skill","Brawler","HeroesForHire"],
					"Sharon Carter":			["Hero","Global","Skill","Controller","SecretAvenger"],
					"Shatterstar":				["Hero","Cosmic","Mutant","Brawler","XFactor"],
					"She-Hulk":					["Hero","City","Bio","Protector","Gamma"],
					"S.H.I.E.L.D. Assault":		["Hero","Global","Skill","Blaster","Shield","Minion"],
					"S.H.I.E.L.D. Trooper":		["Hero","Global","Skill","Blaster","Shield","Minion"],
					"S.H.I.E.L.D. Medic":		["Hero","Global","Skill","Support","Shield","Minion"],
					"S.H.I.E.L.D. Operative":	["Hero","Global","Skill","Support","Shield","Minion"],
					"S.H.I.E.L.D. Security":	["Hero","Global","Skill","Protector","Shield","Minion"],
					"Shocker":					["Villain","City","Tech","Blaster","SpiderVerse","SinisterSix"],
					"Shuri":					["Hero","Global","Tech","Support","Wakanda","WarDog","Legendary"],
					"Sif":						["Hero","Cosmic","Skill","Protector","Asgard"],
					"Silver Samurai":			["Villain","Global","Mutant","Protector","WeaponX"],
					"Silver Surfer":			["Hero","Cosmic","Mystic","Blaster"],
					"Spider-Man":				["Hero","City","Bio","Brawler","SpiderVerse","WebWarrior"],
					"Spider-Man (Big Time)":	["Hero","City","Tech","Controller","SpiderVerse","Infestation"],
					"Spider-Man (Miles)":		["Hero","City","Bio","Brawler","SpiderVerse","YoungAvenger","WebWarrior"],
					"Spider-Man (Noir)":		["Hero","City","Mystic","Blaster","SpiderVerse","TangledWeb"],
					"Spider-Man (Symbiote)":	["Hero","City","Bio","Brawler","SpiderVerse","Symbiote"],
					"Spider-Man 2099":			["Hero","City","Bio","Controller","SpiderVerse","TangledWeb"],
					"Spider-Punk":				["Hero","City","Bio","Brawler","SpiderVerse","WebWarrior"],
					"Spider-Weaver":			["Hero","Global","Mystic","Protector","SpiderVerse","TangledWeb"],
					"Spider-Woman":				["Hero","City","Bio","Blaster","AForce"],
					"Squirrel Girl":			["Hero","City","Bio","Support","YoungAvenger"],
					"Star-Lord":				["Hero","Cosmic","Tech","Controller","GotG","Legendary"],
					"Star-Lord (Annihilation)":	["Hero","Cosmic","Skill","Brawler","GotG","Knowhere"],
					"Star-Lord (T'Challa)":		["Hero","Cosmic","Tech","Blaster","Ravager"],
					"Stature":					["Hero","Global","Bio","Protector","PymTech"],
					"Storm":					["Hero","Global","Mutant","Controller","Uncanny"],
					"Strange (Heartless)":		["Villain","Cosmic","Mystic","Blaster","Darkhold"],
					"Stryfe":					["Villain","Global","Mutant","Protector","Marauders"],
					"Sunfire":					["Hero","Global","Mutant","Blaster","Unlimited"],
					"Super Skrull":				["Villain","Cosmic","Bio","Brawler"],
					"Swarm":					["Villain","City","Bio","Controller","SpiderVerse","SinisterSix","Infestation"],
					"Sylvie":					["Villain","Cosmic","Mystic","Controller","Bifrost","Asgard"],
					"Taskmaster":				["Villain","Global","Skill","Controller","Mercenary","Underworld"],
					"Thanos":					["Villain","Cosmic","Mystic","Protector"],
					"The Thing":				["Hero","Cosmic","Bio","Brawler","FantasticFour"],
					"Thor":						["Hero","Cosmic","Mystic","Blaster","Asgard","Wave1Avenger"],
					"Thor (Infinity War)":		["Hero","Cosmic","Mystic","Brawler","Avenger","Asgard","Knowhere"],
					"Titania":					["Villain","Global","Bio","Brawler","MastersOfEvil"],
					"Toad":						["Villain","Global","Mutant","Controller","Brotherhood"],
					"U.S. Agent":				["Villain","Global","Bio","Controller","Rebirth"],
					"Ultimus":					["Villain","Cosmic","Mystic","Brawler","Kree"],
					"Ultron":					["Villain","Global","Tech","Blaster","Ultron","MastersOfEvil"],
					"Union Jack":				["Hero","Global","Skill","Blaster","Invader"],
					"Vahl":						["Hero","Cosmic","Mystic","Brawler","Bifrost","Asgard"],
					"Valkyrie":					["Hero","Cosmic","Skill","Brawler","Asgard"],
					"Venom":					["Villain","City","Bio","Controller","SpiderVerse","Symbiote"],
					"Vision":					["Hero","Global","Tech","Controller","BionicAvenger"],
					"Viv Vision":				["Hero","Global","Tech","Support","BionicAvenger"],
					"Vulture":					["Villain","City","Tech","Brawler","SpiderVerse","SinisterSix"],
					"War Machine":				["Hero","Global","Tech","Blaster","Avenger","Military","PowerArmor"],
					"Wasp":						["Hero","Global","Tech","Blaster","PymTech"],
					"White Tiger":				["Hero","City","Mystic","Brawler","Shadowland"],
					"Winter Soldier":			["Villain","Global","Bio","Blaster","Hydra","Military","Rebirth"],
					"Wolverine":				["Hero","Global","Mutant","Brawler","Uncanny","WeaponX"],
					"Wong":						["Hero","Global","Mystic","Protector","Darkhold"],
					"X-23":						["Hero","Global","Mutant","Brawler","Xforce","Xmen"],
					"Yelena Belova":			["Hero","Global","Skill","Blaster","Military"],
					"Yellowjacket":				["Villain","Global","Tech","Blaster","PymTech","Infestation"],
					"Yo-Yo":					["Hero","Global","Bio","Protector","Shield","Inhuman"],
					"Yondu":					["Villain","Cosmic","Mystic","Support","Ravager"]}


# Turn this info inside-out
chars_from_trait = {}
for char in traits_from_char:
	for trait in traits_from_char[char]:
		chars_from_trait.setdefault(trait,{})
		chars_from_trait[trait][char]=1


def hex_to_RGB(hex):
	''' "#FFFFFF" -> [255,255,255] '''
	# Pass 16 to the integer function for change of base
	return [int(hex[i:i+2], 16) for i in range(1,6,2)]


def RGB_to_hex(RGB):
	''' [255,255,255] -> "#FFFFFF" '''
	# Components need to be integers for hex to make sense
	RGB = [int(x) for x in RGB]
	return "#"+"".join(["0{0:x}".format(v) if v < 16 else
						 "{0:x}".format(v) for v in RGB])

def color_dict(gradient):
	''' Takes in a list of RGB sub-lists and returns dictionary of
		colors in RGB and hex form for use in a graphing function
		defined later on '''
	return {"hex":[RGB_to_hex(RGB) for RGB in gradient],
			"r":[RGB[0] for RGB in gradient],
			"g":[RGB[1] for RGB in gradient],
			"b":[RGB[2] for RGB in gradient]}


def linear_gradient(start_hex, finish_hex="#FFFFFF", n=10):
	''' returns a gradient list of (n) colors between
		two hex colors. start_hex and finish_hex
		should be the full six-digit color string,
		inlcuding the number sign ("#FFFFFF") '''
	# Starting and ending colors in RGB form
	s = hex_to_RGB(start_hex)
	f = hex_to_RGB(finish_hex)
	# Initilize a list of the output colors with the starting color
	RGB_list = [s]
	# Calcuate a color at each evenly spaced value of t from 1 to n
	for t in range(1, n):
		# Interpolate RGB vector for color at the current value of t
		curr_vector = [
			int(s[j] + (float(t)/(n-1))*(f[j]-s[j]))
			for j in range(3)
		]
	# Add it to our list of output colors
		RGB_list.append(curr_vector)
	return color_dict(RGB_list)


def polylinear_gradient(colors, n):
	''' returns a list of colors forming linear gradients between
		all sequential pairs of colors. "n" specifies the total
		number of desired output colors '''
	# The number of colors per individual linear gradient
	n_out = int(float(n) / (len(colors) - 1))
	# returns dictionary defined by color_dict()
	gradient_dict = linear_gradient(colors[0], colors[1], n_out)
	#
	if len(colors) > 1:
		for col in range(1, len(colors) - 1):
			next = linear_gradient(colors[col], colors[col+1], n_out)
			for k in ("hex", "r", "g", "b"):
				# Exclude first point to avoid duplicates
				gradient_dict[k] += next[k][1:]
	#
	return gradient_dict


# Linear gradient from red, to yellow, to green.
color_scale = polylinear_gradient(['#FF866F','#F6FF6F','#6FFF74'],1000)['hex']


def set_min_max(char_stats,char_name,stat,value):
	value = int(value)

	# Set min/max stats for this specific toon.
	char_stats.setdefault(char_name,{})
	char_stats[char_name].setdefault(stat,{'min':[value-1,0][stat=='iso'],'max':value})

	if value<char_stats[char_name][stat]['min']:
		char_stats[char_name][stat]['min'] = value

	if value>char_stats[char_name][stat]['max']:
		char_stats[char_name][stat]['max'] = value

	# Do the same bookkeeping across all toons.
	char_stats.setdefault('all',{})

	char_stats['all'].setdefault(stat,{'min':[value-1,0][stat=='iso'],'max':value})

	if value<char_stats['all'][stat]['min']:
		char_stats['all'][stat]['min'] = value
	if value>char_stats['all'][stat]['max']:
		char_stats['all'][stat]['max'] = value


def get_value_color(char_stats,char_name,stat,value):
	value = int(value)
	#char_stats.setdefault(char_name,{})
	#char_stats[char_name].setdefault(stat,{'min':value-1,'max':value})
	
	if not value:
		return 'Beige'

	max_colors = len(color_scale)-1

	# Use the min/max in 'all' for calculating heat maps.
	min = char_stats['all'][stat]['min']
	max = char_stats['all'][stat]['max']
	
	if stat=='iso':
		return color_scale[int( ((value**3)/10**3) *max_colors)]

	if stat=='tier':
		if value <= 15:
			return color_scale[int( ((value**2)/15**2) *0.50 *max_colors)]
		else:
			return color_scale[int((0.65+((value-16)/3)*0.35)*max_colors)]

	return color_scale[int((value-min)/(max-min)*max_colors)]


if __name__ == "__main__":
	main() # Just run myself

