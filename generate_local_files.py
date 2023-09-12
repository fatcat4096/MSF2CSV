#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_local_files.py
Sources strike_teams and raids_and_lanes if they exist locally.  
Builds a new strike_teams.py if a valid file isn't present in the folder. 
Builds a new raids_and_lanes.py if a valid file isn't present in the folder.
"""

import os
import sys


# If not frozen, work in the same directory as this script.
path = os.path.dirname(__file__)

# If frozen, work in the same directory as the executable.
if getattr(sys, 'frozen', False):
	path = os.path.dirname(sys.executable)

# Insert the local directory at the front of path to override packaged versions.
sys.path.insert(0, path)

# If file is invalid/deleted, generate a new one after alliance_info loaded.
try:
	from strike_teams import *
except:
	print ("Missing strike_teams.py...will be regenerated after alliance_members are known.")


try:
	from raids_and_lanes import *
except:
	print ("Missing raids_and_lanes.py...will be regenerated and used next run.")

# Create a new strike_teams.py if an outdated one exists.
def generate_strike_teams(strike_teams={}):
	
	# Create header
	new_file  = '''# This file contains the Strike Teams used for HTML file output.
#
# Move entries between strike teams and reorder players within strike teams.
# Include lane dividers, i.e. "----" to indicate which players are in which lanes/clusters.
#
# Also, you can add entries in strike_teams dict and use them in output in msf2csv.py.
# These teams will be saved and included in cached alliance information.
#
# DELETE THIS FILE TO AUTO-GENERATE A NEW ONE WITH CURRENT ALLIANCE MEMBERS.

strike_teams = {}
'''

	# Create each strike_team definition.
	new_file += generate_strike_team('incur',strike_teams['incur'],'Used for Incursion Raid output.')
	new_file += generate_strike_team('other',strike_teams['other'],'Used for Gamma Raids and other output.')

	# Write it to disk.
	open(path + os.sep + "strike_teams.py", 'w').write(new_file)


# Take the strike_team variable and create the text for the team definition in strike_teams.py
def generate_strike_team(type,strike_team,desc):

	team_def  = '\n# %s\n' % desc
	team_def += 'strike_teams["%s"] = [\n' % type
	
	for team_num in range(len(strike_team)): 
		team_def += '[### Strike team %i ###]\n' % (team_num+1)
		
		for member in strike_team[team_num]:
			team_def += '\t"%s",\n' % member
		
		team_def += ['],\n',']]\n'][team_num == len(strike_team)-1]

	return team_def

	
# Create a local raids_and_lanes.py that users can edit if we are Frozen and one doesn't exist. 
if not os.path.exists(path + os.sep + 'raids_and_lanes.py'):

	# Create header
	new_file  = '''# This file contains the list of active formats to be used for output
# and the definitions of what to include (or filter out) of those files.
#
# Add or remove entries from tables['active'] to control which files are created.
#
# For each table format, you can specify the following arguments:
#
#	* NAME -- This is the label used in the tabs at the top.
#
#	* MIN_TIER and MIN_ISO -- These are filters use to filter out background noise.
#
#		The table output will only include Characters that have been built to at least 
#		this level by at least ONE of the alliance members. Set these for the minimum
#		required by the level of Incursion, Doom, or Gamma raid you are running.
#
#		Note: Character specfied in Meta will ALWAYS be included. Never filtered out.
#
#	* STRIKE_TEAMS -- If not specified, entire alliance member list will be used.
#
#	* KEYS -- Controls which columns are displayed for each member's characters.
#
#		Default is ['power','tier','iso'] if not specified.
#
#   * LANES -- This is a list of Lanes, each lane has a list of sections.
#
#		Each section can include a list of traits and list of meta characters.
#		Traits are ADDITIVE, so ['Xmen','Kree'] includes anyone that has EITHER trait.
#		Meta characters aren't subject to filters. And if Meta characters are specified
#		and the trait indicated doesn't exist, trait will simply be used as a label


# Active tables are the files which will be generated.
'''

	# Active tables are the files which will be generated.
	tables = {'active': ['incur', 'gamma', 'war', 'all']}

	# Meta Heroes for use in Incursion Raid
	tables['incur'] = { 'name': 'Incursion Raid', 'min_tier': 16, 'min_iso': 9, 'strike_teams': 'incur',
						'lanes':[ [
								{'traits': ['Mutant'], 'meta': ['Archangel', 'Nemesis', 'Dark Beast', 'Psylocke', 'Magneto']},
								{'traits': ['Bio'], 'meta': ['Captain America', 'Captain Carter', 'Agent Venom', 'Winter Soldier', 'U.S. Agent']},
								{'traits': ['Skill'], 'meta': ['Nick Fury', 'Captain America (WWII)', 'Iron Fist (WWII)', 'Bucky Barnes', 'Union Jack']},
								{'traits': ['Mystic'], 'meta': ['Beta Ray Bill', 'Loki', 'Loki (Teen)', 'Sylvie', 'Vahl']},
								{'traits': ['Tech'], 'meta': ['Kang the Conqueror', 'Doctor Doom', 'Hulkbuster', 'Viv Vision', 'Vision']},
								] ]
						}

	# Meta Heroes for use in Gamma Raid
	tables['gamma'] = { 'name': 'Gamma Raid', 'min_tier': 16, 'strike_teams': 'other',
						'lanes':[ [
								{'traits': ['Avenger', 'GotG'], 'meta': ['Viv Vision', 'Vision', 'Deathlok', 'Hulkbuster', 'Iron Man']},
								{'traits': ['PymTech', 'Infestation', 'Kree'], 'meta': ['Ghost', 'Yellowjacket', 'Minn-Erva', 'Captain Marvel', 'Phyla-Vell']},
								{'traits': ['Brotherhood', 'Mercenary', 'Xmen'], 'meta': ['Dazzler', 'Fantomex', 'Gambit', 'Rogue', 'Sunfire']},
								{'traits': ['Kree', 'SpiderVerse', 'GotG'], 'meta': ['Ghost-Spider', 'Spider-Man (Miles)', 'Spider-Weaver', 'Spider-Man', 'Scarlet Spider']},
								],[ ### Lane 2 ###
								{'traits': ['Avenger', 'SpiderVerse'], 'meta': ['Viv Vision', 'Vision', 'Deathlok', 'Hulkbuster', 'Iron Man']},
								{'traits': ['PymTech', 'Infestation', 'Wakanda'], 'meta': ['Black Panther', 'Black Panther (1MM)', 'Nakia', 'Okoye', 'Shuri']},
								{'traits': ['Brotherhood', 'Mercenary', 'Xmen'], 'meta': ['Dazzler', 'Fantomex', 'Gambit', 'Rogue', 'Sunfire']},
								{'traits': ['Kree', 'SpiderVerse', 'GotG'], 'meta': ['Ghost-Spider', 'Spider-Man (Miles)', 'Spider-Weaver', 'Spider-Man', 'Scarlet Spider']},
								],[ ### Lane 3 ###
								{'traits': ['Shield', 'Brotherhood'], 'meta': ['Black Widow', 'Captain America', 'Nick Fury', 'Maria Hill', 'Magneto']},
								{'traits': ['Defender', 'Mercenary', 'HeroesForHire'], 'meta': ['Colleen Wing', 'Iron Fist', 'Luke Cage', 'Misty Knight', 'Shang-Chi']},
								{'traits': ['GotG', 'Xmen', 'Mercenary'], 'meta': ['Dazzler', 'Fantomex', 'Gambit', 'Rogue', 'Sunfire']},
								{'traits': ['Brotherhood', 'Mercenary', 'Xmen'], 'meta': ['Dazzler', 'Fantomex', 'Gambit', 'Rogue', 'Sunfire']},
								{'traits': ['Kree', 'SpiderVerse', 'GotG'], 'meta': ['Ghost-Spider', 'Spider-Man (Miles)', 'Spider-Weaver', 'Spider-Man', 'Scarlet Spider']},
								],[ ### Lane 4 ###
								{'traits': ['Shield', 'Aim'], 'meta': ['Black Widow', 'Captain America', 'Nick Fury', 'Maria Hill', 'Hawkeye']},
								{'traits': ['Defender', 'Hydra', 'HeroesForHire'], 'meta': ['Colleen Wing', 'Iron Fist', 'Luke Cage', 'Misty Knight', 'Shang-Chi']},
								{'traits': ['Shield', 'Wakanda', 'Defender', 'HeroesForHire'], 'meta': ['Black Panther', 'Black Panther (1MM)', 'Nakia', 'Okoye', 'Shuri']},
								{'traits': ['Kree', 'SpiderVerse', 'GotG'], 'meta': ['Ghost-Spider', 'Spider-Man (Miles)', 'Spider-Weaver', 'Spider-Man', 'Scarlet Spider']},
								] ]
						}

	# Meta Heroes for use in War
	tables['war'] = { 'name': 'War',
						'lanes':[ [
								{'traits': ['Key<br>Villains'], 'meta': ['Apocalypse', 'Dormammu', 'Doctor Doom', 'Kang the Conqueror', 'Super Skrull']},
								{'traits': ['MastersOfEvil']},
								{'traits': ['Knowhere']},
								{'traits': ['Gamma']},
								{'traits': ['Unlimited']},
								{'traits': ['Deathseed']},
								{'traits': ['Darkhold']},
								{'traits': ['Under-<br>world'], 'meta': ['Kingpin', 'Mister Negative', 'Nobu', 'Taskmaster', 'Green Goblin']},
								{'traits': ['AForce']},
								{'traits': ['WarDog']},
								{'traits': ['WeaponX']},
								{'traits': ['InfinityWatch']},
								{'traits': ['DarkHunter']},
								{'traits': ['Dark<br>Hunters<br>+<br>Quicksilver'], 'meta': ['Doctor Voodoo', 'Elsa Bloodstone', 'Ghost Rider', 'Morbius', 'Quicksilver']},
								{'traits': ['Undying']},
								{'traits': ['TangledWeb']},
								{'traits': ['Eternal']},
								{'traits': ['Invaders'], 'meta': ['Nick Fury', 'Captain America (WWII)', 'Iron Fist (WWII)', 'Bucky Barnes', 'Union Jack']},
								{'traits': ['Bifrost']},
								{'traits': ['Young<br>Avengers'], 'meta': ['America Chavez', 'Echo', 'Kate Bishop', 'Ms. Marvel', 'Squirrel Girl']},
								{'traits': ['Infestation']},
								] ]
						}

	# All Characters
	tables['all'] = { 'name': 'All Characters', 'keys': ['power', 'lvl', 'tier'] }

	new_file += "tables = {'active': " + repr(tables['active']) + "}\n\n\n"

	# Iterate through each of the included tables.
	for raid_type in tables: 
		if raid_type == 'active':
			continue
		
		if raid_type == 'all':
			new_file += "# All Characters\n"
		else:
			new_file += "# Meta Heroes for use in %s\n" % tables[raid_type]['name']

		new_file += "tables['%s'] = { 'name': '%s',\n" % (raid_type, tables[raid_type]['name'])

		# Generic keys, if specified.
		for key in ['min_tier','min_iso','strike_teams','keys']:
			if key in tables[raid_type]:
				new_file += "\t\t\t\t\t'%s': %s,\n" % (key, repr(tables[raid_type][key]))

		# Finally, add the Lanes 
		if 'lanes' in tables[raid_type]:
			new_file += "\t\t\t\t\t'lanes':[ [\n"

			for lane in tables[raid_type]['lanes']:
				for section in lane:
					meta = ''
					if section.get('meta'):
						meta = ", 'meta': %s" % repr(section['meta'])
					new_file += "\t\t\t\t\t\t\t{'traits': %s%s},\n" % (repr(section['traits']), meta)
					
				if lane == tables[raid_type]['lanes'][-1]:
					new_file += "\t\t\t\t\t\t\t] ]\n"
				else:
					new_file += "\t\t\t\t\t\t\t],[ ### Lane %i ###\n" % (tables[raid_type]['lanes'].index(lane)+2)

		# After everything else, close up the raid.  
		new_file += "\t\t\t\t\t}\n\n"

	# Write it to disk.
	open(path + os.sep + "raids_and_lanes.py", 'w').write(new_file)