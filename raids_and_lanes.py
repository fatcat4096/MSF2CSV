# This file contains the list of active formats to be used for output
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
tables = {}

# Meta Heroes for use in Spotlight Raid
tables['spotlight'] = { 'name': 'Spotlight Raid',
					'min_iso': 9,
					'max_others': 5,
					'strike_teams': 'spotlight',
					'inc_dividers': 'spotlight',
					'sort_char_by': 'avail',
					'inc_keys': ['power','lvl','tier','iso'],
					'lanes':[ [
							{'meta': ['Carnage', 'Venom', 'Void Knight', 'Gwenom', 'Red Goblin'], 'label':'Non-Mythic'},
							{'traits': ['SpiderSociety'], 'meta': ['Peni Parker', 'Ghost-Spider', 'Peter B. Parker', 'Spider-Man (Noir)', 'Spider-Man (Pavitr)']},
							{'traits': ['AlphaFlight'], 'meta': ['Wolverine', 'Sunfire', 'Sasquatch', 'Guardian', 'Northstar']},
							{'traits': ['All'],  'label':'Final Boss'},
							] ]
					}

# Meta Heroes for use in Incursion 2 Raid
tables['incur'] = { 'name': 'Incursion 2 Raid',
					'min_iso': 9,
					'max_others': 5,
					'strike_teams': 'incur',
					'sort_char_by': 'avail',
					'inc_keys': ['power','lvl','tier','iso'],
					'lanes':[ [
							{'traits': ['Mystic'], 'meta': ['Beta Ray Bill', 'Loki', 'Loki (Teen)', 'Sylvie', 'Vahl'], 'label':'Mystic<br>(Bifrost)'},
							{'traits': ['Tech'], 'meta': ['Kestrel', 'Rescue', 'Iron Man (Infinity War)', 'Darkhawk', 'Ironheart (MKII)'], 'label':'Tech<br>(Pegasus)'},
							{'traits': ['Mutant'], 'meta': ['Cyclops', 'Gambit', 'Nightcrawler', 'Forge', 'Sunspot'], 'label':'Mutant<br>(X-Treme)'},
							{'traits': ['Bio'], 'meta': ['Carnage', 'Venom', 'Void Knight', 'Gwenom', 'Red Goblin'], 'label':'Bio<br>(Hive-Mind)'},
							{'traits': ['Skill'], 'meta': ['Peni Parker', 'Ghost-Spider', 'Peter B. Parker', 'Spider-Man (Noir)', 'Spider-Man (Pavitr)'], 'label':'Skill<br>(Spider Society)'},
							] ]
					}

# Meta Heroes for use in Incursion 1.x Raid
tables['old_incur'] = { 'name': 'Incursion 1.x Raid',
					'min_iso': 9,
					'max_others': 5,
					'strike_teams': 'incur',
					'sort_char_by': 'avail',
					'inc_dividers': 'incur',
					'lanes':[ [
							{'traits': ['Mutant'], 'meta': ['Archangel', 'Nemesis', 'Dark Beast', 'Psylocke', 'Magneto'], 'label':'Mutant<br>(Deathseed)'},
							{'traits': ['Bio'], 'meta': ['Captain America', 'Captain Carter', 'Super Skrull', 'Winter Soldier', 'U.S. Agent'], 'label':'Bio<br>(Rebirth)'},
							{'traits': ['Skill'], 'meta': ['Nick Fury', 'Captain America (WWII)', 'Iron Fist (WWII)', 'Bucky Barnes', 'Union Jack'], 'label':'Skill<br>(Invaders)'},
							{'traits': ['Mystic'], 'meta': ['Beta Ray Bill', 'Loki', 'Loki (Teen)', 'Sylvie', 'Vahl'], 'label':'Mystic<br>(Bifrost)'},
							{'traits': ['Tech'], 'meta': ['Kestrel', 'Rescue', 'Iron Man (Infinity War)', 'Darkhawk', 'Ironheart (MKII)'], 'label':'Tech<br>(Pegasus)'},
							] ]
					}

# Meta Heroes for use in Dark Dimension 8
tables['dd8'] = { 'name': 'Dark Dimension 8',
					'min_tier': 19,
					'min_iso': 13,
					'max_others': 10,
					'sort_by': 'avail',
					'sort_char_by': 'avail',
					'inc_avail': True,
					'traits_req': 'all', 
					'lanes':[ [
							{'traits': ['Non-Legendary', 'City', 'Villain'],   'label':'City Villain'},
							{'traits': ['Non-Legendary', 'City', 'Hero'],      'label':'City Hero'},
							{'traits': ['Non-Legendary', 'Global', 'Villain'], 'label':'Global Villain'},
							{'traits': ['Non-Legendary', 'City', 'Hero'],      'label':'Global Hero'},
							{'traits_req':'any', 'traits': ['Cosmic', 'Legendary'],   'label':'Cosmic or<br>Legendary'},
							] ]
					}

# Meta Heroes for use in Dark Dimension 7
tables['dd7'] = { 'name': 'Dark Dimension 7',
					'min_tier': 19,
					'max_others': 10,
					'sort_by': 'avail',
					'sort_char_by': 'avail',
					'inc_avail': True,
					'traits_req': 'all', 
					'lanes':[ [
							{'traits': ['All'], 'label':'Gear Tier 19'},
							{'traits': ['Non-Legendary', 'Non-Mythic', 'City'],   'label':'City'},
							{'traits': ['Non-Legendary', 'Non-Mythic', 'Global'], 'label':'Global'},
							{'traits': ['Non-Legendary', 'Non-Mythic', 'Cosmic'], 'label':'Cosmic'},
							{'traits': ['Legendary'], 'label':'Legendary'},
							{'traits': ['Mythic'],    'label':'Mythic'},
							] ]
					}

# Meta Heroes for use in Dark Dimension 6
tables['dd6'] = { 'name': 'Dark Dimension 6',
					'min_tier': 18,
					'max_others': 10,
					'sort_by': 'avail',
					'sort_char_by': 'avail',
					'inc_avail': True,
					'traits_req': 'all', 
					'lanes':[ [
							{'traits': ['Non-Legendary', 'Global'],   'label':'Global'},
							{'traits': ['Non-Legendary', 'Cosmic'],   'label':'Cosmic'},
							{'traits': ['Non-Legendary', 'City'],     'label':'City'},
							{'traits': ['Non-Horseman', 'Legendary'], 'label':'Legendary<br>Non-Horseman'},
							{'traits_req':'any', 'traits': ['Legendary', 'Apocalypse'],   'label':'Legendary<br>+ Apoc'},
							] ]
					}

# Meta Heroes for use in Dark Dimension 5
tables['dd5'] = { 'name': 'Dark Dimension 5',
					'min_tier': 16,
					'max_others': 10,
					'sort_by': 'avail',
					'sort_char_by': 'avail',
					'inc_avail': True,
					'traits_req': 'all', 
					'lanes':[ [
							{'traits': ['Non-Legendary', 'Global'],   'label':'Global'},
							{'traits': ['Non-Legendary', 'Cosmic'],   'label':'Cosmic'},
							{'traits': ['Non-Legendary', 'City'],     'label':'City'},
							{'traits': ['Legendary']},
							] ]
					}

# Meta Heroes for use in Teams
tables['teams'] = { 'name': 'Teams',
					'sort_by': 'stp',
					'span': True,
					'lanes':[ [  
							{'traits': ['AForce']},
							{'traits': ['AlphaFlight'], 'meta': ['Wolverine', 'Sunfire', 'Sasquatch', 'Guardian', 'Northstar']},
							{'traits': ['Astonishing']},
							{'traits': ['Annihilator'], 'meta': ['Ultimus', 'Silver Surfer', 'Gladiator', 'Gorr', 'Thanos (Endgame)']},
							{'traits': ['Bifrost']},
							{'traits': ['BionicAvenger']},
							{'traits': ['BlackOrder','Thanos']},
							{'traits': ['Cabal']},
							{'traits': ['Darkhold']},
							{'traits': ['DarkHunter']},
							{'traits': ['Deathseed']},
							{'traits': ['Eternal']},
							{'traits': ['Gamma'], 'meta': ['Red Hulk', 'Hulk', 'She-Hulk', 'Abomination', 'Brawn']},
							{'traits': ['HeroesForHire']},
							{'traits': ['HiveMind']},
							{'traits': ['Illuminati'], 'meta': ['Iron Man', 'Black Bolt', 'Mister Fantastic', 'Black Panther (Shuri)', 'Captain Britain', 'Hank Pym']},
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

# Meta Heroes for use in All Characters
tables['all_chars'] = { 'name': 'All Characters',
					'max_others': 0,
					'sort_by': 'tcp',
					'inc_keys': ['power','tier','iso'],
					'inc_class': True,
					}

