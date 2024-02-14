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

# Meta Heroes for use in Incursion 2 Raid
tables['incur'] = { 'name': 'Incursion 2 Raid',
					'min_iso': 9,
					'max_others': 5,
					'strike_teams': 'incur',
					'sort_char_by': 'avail',
					'inc_keys': ['power','lvl','tier','iso'],
					'lanes':[ [
							{'traits': ['Mystic'], 'meta': ['Beta Ray Bill', 'Loki', 'Loki (Teen)', 'Sylvie', 'Vahl']},
							{'traits': ['Tech'], 'meta': ['Kestrel', 'Rescue', 'Iron Man (Infinity War)', 'Darkhawk', 'Ironheart (MKII)']},
							{'traits': ['Mutant'], 'meta': ['Cyclops', 'Gambit', 'Nightcrawler', 'Forge', 'Sunspot']},
							{'traits': ['Bio'], 'meta': ['Carnage', 'Venom', 'Void Knight', 'Gwenom', 'Red Goblin']},
							{'traits': ['Bio'], 'meta': ['Captain America', 'Captain Carter', 'Super Skrull', 'Winter Soldier', 'U.S. Agent'], 'label':'Bio<br>(Rebirth)'},
							{'traits': ['Skill'], 'meta': ['Nick Fury', 'Captain America (WWII)', 'Iron Fist (WWII)', 'Bucky Barnes', 'Union Jack']},
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
							{'traits': ['Mutant'], 'meta': ['Archangel', 'Nemesis', 'Dark Beast', 'Psylocke', 'Magneto']},
							{'traits': ['Bio'], 'meta': ['Captain America', 'Captain Carter', 'Super Skrull', 'Winter Soldier', 'U.S. Agent']},
							{'traits': ['Skill'], 'meta': ['Nick Fury', 'Captain America (WWII)', 'Iron Fist (WWII)', 'Bucky Barnes', 'Union Jack']},
							{'traits': ['Mystic'], 'meta': ['Beta Ray Bill', 'Loki', 'Loki (Teen)', 'Sylvie', 'Vahl']},
							{'traits': ['Tech'], 'meta': ['Kestrel', 'Rescue', 'Iron Man (Infinity War)', 'Darkhawk', 'Ironheart (MKII)']},
							] ]
					}

# Meta Heroes for use in Gamma Raid
tables['gamma'] = { 'name': 'Gamma Raid',
					'min_tier': 16,
					'max_others': 10,
					'strike_teams': 'gamma',
					'sort_char_by': 'avail',
					'inc_avail': True,
					'lanes':[ [
							{'traits': ['Avenger', 'GotG']},
							{'traits': ['PymTech', 'Infestation', 'Kree']},
							{'traits': ['Brotherhood', 'Mercenary', 'Xmen']},
							{'traits': ['Kree', 'SpiderVerse', 'GotG']},
							],[ ### Lane 2 ###
							{'traits': ['Avenger', 'SpiderVerse']},
							{'traits': ['PymTech', 'Infestation', 'Wakanda']},
							{'traits': ['Brotherhood', 'Mercenary', 'Xmen']},
							{'traits': ['Kree', 'SpiderVerse', 'GotG']},
							],[ ### Lane 3 ###
							{'traits': ['Shield', 'Brotherhood']},
							{'traits': ['Defender', 'Mercenary', 'HeroesForHire']},
							{'traits': ['GotG', 'Xmen', 'Mercenary']},
							{'traits': ['Brotherhood', 'Mercenary', 'Xmen']},
							{'traits': ['Kree', 'SpiderVerse', 'GotG']},
							],[ ### Lane 4 ###
							{'traits': ['Shield', 'Aim']},
							{'traits': ['Defender', 'Hydra', 'HeroesForHire']},
							{'traits': ['Shield', 'Wakanda', 'Defender', 'HeroesForHire']},
							{'traits': ['Kree', 'SpiderVerse', 'GotG']},
							] ]
					}

# Meta Heroes for use in Dark Dimension 6
tables['dd6'] = { 'name': 'Dark Dimension 6',
					'min_tier': 18,
					'sort_by': 'stp',
					'sort_char_by': 'avail',
					'inc_avail': True,
					'lanes':[ [
							{'traits': ['Non-Legendary', 'Global'],   'label':'Global'},
							{'traits': ['Non-Legendary', 'Cosmic'],   'label':'Cosmic'},
							{'traits': ['Non-Legendary', 'City'],     'label':'City'},
							{'traits': ['Non-Horseman', 'Legendary'], 'label':'Legendary<br>Non-Horseman'},
							{'traits': ['Legendary', 'Apocalypse'],   'label':'Legendary<br>+ Apoc'},
							] ]
					}

# Meta Heroes for use in Teams
tables['teams'] = { 'name': 'Teams',
					'sort_by': 'stp',
					'span': True,
					'lanes':[ [  
							# Said 'no' to AxMen, BA, F4, Inhumans, Rebirth, Shadowland, Uncanny, X-Factor, X-Force     Removed Rebirth, Bifrost, Pegasus, and Invader as redundant.
							{'traits': ['AForce']},
							{'traits': ['BlackOrder','Thanos']},
							{'traits': ['Darkhold']},
							{'traits': ['DarkHunter']},
							{'traits': ['Deathseed']},
							{'traits': ['Eternal','Undying']},
							{'traits': ['Gamma']},
							{'traits': ['HeroesForHire']},
							{'traits': ['Infestation']},
							{'traits': ['InfinityWatch']},
							{'traits': ['Knowhere']},
							{'traits': ['MastersOfEvil']},
							{'traits': ['NewAvenger']},
							{'traits': ['NewWarrior']},
							{'traits': ['Rebirth'], 'meta': ['Captain America', 'Captain Carter', 'Agent Venom', 'Winter Soldier', 'U.S. Agent']},
							{'traits': ['SecretDefender']},
							{'traits': ['SuperiorSix']},
							{'traits': ['Under-<br>world'], 'meta': ['Kingpin', 'Mister Negative', 'Nobu', 'Taskmaster', 'Green Goblin']},
							{'traits': ['Unlimited']},
							{'traits': ['WarDog']},
							{'traits': ['WeaponX']},
							{'traits': ['XTreme']},
							{'traits': ['Young<br>Avengers'], 'meta': ['America Chavez', 'Echo', 'Kate Bishop', 'Ms. Marvel', 'Squirrel Girl']},	
							{'traits': ['Horseman', 'Mythic', 'Black Cat', 'Quicksilver', 'Green Goblin (Classic)', 'Spider-Man (Big Time)', 'Juggernaut (Zombie)', 'Iron Man (Zombie)'], 'label':'DPC Chars'},	
							] ]
					}

# Meta Heroes for use in All Characters
tables['all_chars'] = { 'name': 'All Characters',
					'max_others': 0,
					'sort_by': 'tcp',
					'inc_keys': ['power','tier','iso'],
					'inc_class': True,
					}

