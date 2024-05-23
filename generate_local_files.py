#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_local_files.py
Sources strike_teams and raids_and_lanes if they exist locally.  
Builds a new strike_teams.py if a valid file isn't present in the folder. 
Builds a new raids_and_lanes.py if a valid file isn't present in the folder.
"""

from file_io import *

# If file is invalid/deleted, generate a new one after alliance_info loaded.
try:	from strike_teams import *
except:	print ("Missing strike_teams.py...will be regenerated after alliance_members are known.")

# If file is invalid/deleted, generate a new one now.
try:	from raids_and_lanes import *
except:	print ("Missing raids_and_lanes.py...will be regenerated and used next run.")

import inspect

# Create a new strike_teams.py if an outdated one exists.
def generate_strike_teams(alliance_info):

	strike_teams = alliance_info.setdefault('strike_teams',{})

	for raid_type in ('incur','spotlight'):

		if not strike_teams.get(raid_type):

			# If not there, just put the member list in generic groups of 8.
			print (f"Valid {raid_type} strike_team definition not found. Creating default strike_team from member list.")
			
			# Get member_list and sort them.
			members = sorted(alliance_info['members'],key=str.lower)

			# Break it up into chunks and add the appropriate dividers.
			if raid_type == 'spotlight':
				strike_teams[raid_type] = [members[:6], members[6:12], members[12:18], members[18:]]
			else:
				strike_teams[raid_type] = [members[:8], members[8:16], members[16:]]
	
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
	new_file += generate_strike_team('incur', strike_teams['incur'], 'Used for Incursion Raid output.')
	new_file += generate_strike_team('spotlight', strike_teams['spotlight'], 'Used for Spotlight Raids and other output.')

	# Write it to disk.

	# If we're updating a local strike_teams.py, overwrite the existing module.
	if 'strike_temp' in globals():
		write_file(inspect.getfile(strike_temp), new_file)

	# Otherwise, just write it into the local path.
	else:
		write_file(get_local_path()+'strike_teams.py', new_file)
		

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
if not os.path.exists(get_local_path() + 'raids_and_lanes.py'):

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
#	* SORT_BY -- Sort the alliance members before display. Options include 'stp' and 'tcp'. 
#
#		If not specified, uses order in strike_team definitions
#		(or alphabetical order if no strike_teams are specified)
#
#	* FORMAT -- Only alternate format is currently 'span', used by War output.
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

	tables = {}


	# Meta Heroes for use in Spotlight Raid
	tables['spotlight'] = { 'name': 'Spotlight Raid',
						'min_iso': 9,
						'max_others': 5,
						'strike_teams': 'incur',
						'sort_char_by': 'avail',
						'inc_dividers': 'spotlight',
						'inc_keys': ['power','lvl','tier','iso'],
						'lanes':[ [
								{'traits': ['Non-Mythic'], 'label':'Non-Mythic'},
								{'traits': ['SpiderSociety']},
								{'traits': ['AlphaStar'], 'meta': ['Wolverine', 'Sunfire', 'Sasquatch', 'Guardian', 'Northstar']},
								{'traits': ['All'],  'label':'Final Boss'},
								] ]
						}

	# Meta Heroes for use in Incursion 2 Raid
	tables['incur'] = { 'name': 'Incursion 2 Raid', 'min_iso': 9, 'max_others': 5, 'sort_char_by': 'avail', 'sort_char_by': 'avail', 'strike_teams': 'incur',
						'lanes':[ [
								{'traits': ['Mystic'], 'meta': ['Beta Ray Bill', 'Loki', 'Loki (Teen)', 'Sylvie', 'Vahl'], 'label':'Mystic<br>(Bifrost)'},
								{'traits': ['Tech'], 'meta': ['Kestrel', 'Rescue', 'Iron Man (Infinity War)', 'Darkhawk', 'Ironheart (MKII)'], 'label':'Tech<br>(Pegasus)'},
								{'traits': ['Mutant'], 'meta': ['Cyclops', 'Gambit', 'Nightcrawler', 'Forge', 'Sunspot'], 'label':'Mutant<br>(X-Treme)'},
								{'traits': ['Bio'], 'meta': ['Carnage', 'Venom', 'Void Knight', 'Gwenom', 'Red Goblin'], 'label':'Bio<br>(Hive-Mind)'},
								{'traits': ['Skill'], 'meta': ['Peni Parker', 'Ghost-Spider', 'Peter B. Parker', 'Spider-Man (Noir)', 'Spider-Man (Pavitr)'], 'label':'Skill<br>(Spider Society)'},
								] ]
						}

	# Meta Heroes for use in Incursion 1.x Raid
	tables['old_incur'] = { 'name': 'Incursion 1.x Raid', 'min_iso': 9, 'max_others': 5, 'sort_char_by': 'avail', 'sort_char_by': 'avail', 'strike_teams': 'incur', 'inc_dividers':'incur',
							'lanes':[ [
									{'traits': ['Mutant'], 'meta': ['Archangel', 'Nemesis', 'Dark Beast', 'Psylocke', 'Magneto'], 'label':'Mutant<br>(Deathseed)'},
									{'traits': ['Bio'], 'meta': ['Captain America', 'Captain Carter', 'Super Skrull', 'Winter Soldier', 'U.S. Agent'], 'label':'Bio<br>(Rebirth)'},
									{'traits': ['Skill'], 'meta': ['Nick Fury', 'Captain America (WWII)', 'Iron Fist (WWII)', 'Bucky Barnes', 'Union Jack'], 'label':'Skill<br>(Invaders)'},
									{'traits': ['Mystic'], 'meta': ['Beta Ray Bill', 'Loki', 'Loki (Teen)', 'Sylvie', 'Vahl'], 'label':'Mystic<br>(Bifrost)'},
									{'traits': ['Tech'], 'meta': ['Kestrel', 'Rescue', 'Iron Man (Infinity War)', 'Darkhawk', 'Ironheart (MKII)'], 'label':'Tech<br>(Pegasus)'},
									] ]
							}

	# Meta Heroes for use in Dark Dimension 7
	tables['dd7'] = { 'name': 'Dark Dimension 7',
						'min_tier': 19,
						'max_others': 10,
						'sort_by': 'stp',
						'sort_char_by': 'avail',
						'inc_avail': True,
						'lanes':[ [
								{'traits': ['All'], 'label':'Gear Tier 19'},
								{'traits': ['Non-Legendary', 'Non-Mythic', 'City'],   'label':'City'},
								{'traits': ['Non-Legendary', 'Non-Mythic', 'Global'], 'label':'Global'},
								{'traits': ['Non-Legendary', 'Non-Mythic', 'Cosmic'], 'label':'Cosmic'},
								{'traits': ['Legendary'], 'label':'Legendary'},
								{'traits': ['Mythic'],    'label':'Mythic'},
								] ]
						}

	# Meta Heroes for use in DD6 report
	tables['dd6'] = { 'name': 'Dark Dimension 6', 'min_tier': 18, 'max_others': 10, 'sort_by': 'stp', 'sort_char_by': 'avail','inc_avail': True, 
						'lanes':[ [
								{'traits': ['Non-Legendary', 'Global'],   'label':'Global'},
								{'traits': ['Non-Legendary', 'Cosmic'],   'label':'Cosmic'},
								{'traits': ['Non-Legendary', 'City'],     'label':'City'},
								{'traits': ['Non-Horseman', 'Legendary'], 'label':'Legendary<br>Non-Horseman'},
								{'traits': ['Legendary', 'Apocalypse'],   'label':'Legendary<br>+ Apoc'},
								] ]
						}

	# Meta Heroes for use in Dark Dimension 5
	tables['dd5'] = { 'name': 'Dark Dimension 5', 'min_tier': 16, 'max_others': 10, 'sort_by': 'stp', 'sort_char_by': 'avail', 'inc_avail': True,
						'lanes':[ [
								{'traits': ['Non-Legendary', 'Global'],   'label':'Global'},
								{'traits': ['Non-Legendary', 'Cosmic'],   'label':'Cosmic'},
								{'traits': ['Non-Legendary', 'City'],     'label':'City'},
								{'traits': ['Legendary']},
								] ]
						}

	# Meta Heroes for use in Teams
	tables['teams'] = { 'name': 'Teams', 'sort_by': 'stp', 'span': True,
						'lanes':[ [  
								{'traits': ['AForce']},
								{'traits': ['AlphaStar'], 'meta': ['Wolverine', 'Sunfire', 'Sasquatch', 'Guardian', 'Northstar']},
								{'traits': ['Astonishing']},
								{'traits': ['Bifrost']},
								{'traits': ['BionicAvenger']},
								{'traits': ['BlackOrder','Thanos']},
								{'traits': ['Cabal']},
								{'traits': ['Darkhold']},
								{'traits': ['DarkHunter']},
								{'traits': ['Deathseed']},
								{'traits': ['Eternal']},
								{'traits': ['Gamma']},
								{'traits': ['HeroesForHire']},
								{'traits': ['Infestation']},
								{'traits': ['InfinityWatch']},
								{'traits': ['Invader']},
								{'traits': ['Knowhere']},
								{'traits': ['MastersOfEvil']},
								{'traits': ['MercsForMoney']},
								{'traits': ['NewAvenger']},
								{'traits': ['NewWarrior']},
								{'traits': ['OutOfTime']},
								{'traits': ['Pegasus']},
								{'traits': ['PymTech']},
								{'traits': ['Rebirth']},
								{'traits': ['SecretDefender']},
								{'traits': ['Shadowland']},
								{'traits': ['SpiderSociety']},
								{'traits': ['SuperiorSix']},
								{'traits': ['Uncanny']},
								{'traits': ['Under-<br>world'], 'meta': ['Kingpin', 'Mister Negative', 'Nobu', 'Taskmaster', 'Green Goblin']},
								{'traits': ['Undying']},
								{'traits': ['Unlimited']},
								{'traits': ['WarDog']},
								{'traits': ['WeaponX']},
								{'traits': ['XTreme']},
								{'traits': ['Young<br>Avengers'], 'meta': ['America Chavez', 'Echo', 'Kate Bishop', 'Ms. Marvel', 'Squirrel Girl']},	
								{'traits': ['Horseman', 'Mythic', 'Black Cat', 'Quicksilver', 'Green Goblin (Classic)', 'Spider-Man (Big Time)', 'Juggernaut (Zombie)', 'Iron Man (Zombie)'], 'label':'DPC Chars', 'inc_keys':['power', 'red'], 'max_others':0},
								] ]
						}

	# All Characters
	tables['all_chars'] = { 'name': 'All Characters', 'sort_by':'tcp', 'max_others':0, 'inc_class': True, 'inc_keys': ['power','tier','iso'] }

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
		for key in ['min_tier', 'min_iso', 'max_others', 'strike_teams', 'inc_dividers', 'sort_by', 'sort_char_by', 'span', 'inc_keys', 'inc_avail', 'inc_class']:
			if key in tables[raid_type]:
				new_file += "\t\t\t\t\t'%s': %s,\n" % (key, repr(tables[raid_type][key]))

		# Finally, add the Lanes 
		if 'lanes' in tables[raid_type]:
			new_file += "\t\t\t\t\t'lanes':[ [\n"

			for lane in tables[raid_type]['lanes']:
				for section in lane:
					meta  = [f", 'meta': {repr(section.get('meta'))}",''][not section.get('meta')]
					label = [f", 'label': {repr(section.get('label'))}",''][not section.get('label')]
					new_file += "\t\t\t\t\t\t\t{'traits': %s%s%s},\n" % (repr(section['traits']), meta, label)
					
				if lane == tables[raid_type]['lanes'][-1]:
					new_file += "\t\t\t\t\t\t\t] ]\n"
				else:
					new_file += "\t\t\t\t\t\t\t],[ ### Lane %i ###\n" % (tables[raid_type]['lanes'].index(lane)+2)

		# After everything else, close up the raid.  
		new_file += "\t\t\t\t\t}\n\n"

	# Write it to disk.
	write_file(get_local_path() + "raids_and_lanes.py", new_file)
