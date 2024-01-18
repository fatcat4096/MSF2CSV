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
tables = {'active': ['incur', 'old_incur', 'gamma', 'dd6', 'teams', 'all_chars']}

# Meta Heroes for use in Incursion 2 Raid
tables['incur'] = { 'name': 'Incursion 2 Raid',
					'min_iso': 9,
					'max_others': 10,
					'strike_teams': 'incur2',
					'sort_char_by': 'avail',
					'keys': ['power','lvl','tier','iso'],
					'lanes':[ [
							{'traits': ['Mystic'], 'meta': ['Beta Ray Bill', 'Loki', 'Loki (Teen)', 'Sylvie', 'Vahl']},
							{'traits': ['Tech'], 'meta': ['Kestrel', 'Rescue', 'Iron Man (Infinity War)', 'Darkhawk', 'Ironheart (MKII)']},
							{'traits': ['Mutant'], 'meta': ['Cyclops', 'Gambit', 'Nightcrawler', 'Forge', 'Sunspot']},
							{'traits': ['Bio'], 'meta': ['Captain America', 'Captain Carter', 'Super Skrull', 'Winter Soldier', 'U.S. Agent']},
							{'traits': ['Skill'], 'meta': ['Nick Fury', 'Captain America (WWII)', 'Iron Fist (WWII)', 'Bucky Barnes', 'Union Jack']},
							] ]
					}

# Meta Heroes for use in Incursion 1.x Raid
tables['old_incur'] = { 'name': 'Incursion 1.x Raid',
					'min_iso': 9,
					'max_others': 10,
					'strike_teams': 'incur',
					'sort_char_by': 'avail',
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
							{'traits': ['Avenger', 'GotG'], 'meta': ['Viv Vision', 'Vision', 'Deathlok', 'Hulkbuster', 'Iron Man']},
							{'traits': ['PymTech', 'Infestation', 'Kree'], 'meta': ['Black Widow', 'Spider-Man (Big Time)', 'Minn-Erva', 'Captain Marvel', 'Phyla-Vell']},
							{'traits': ['Brotherhood', 'Mercenary', 'Xmen'], 'meta': ['Dazzler', 'Fantomex', 'Gambit', 'Rogue', 'Sunfire']},
							{'traits': ['Kree', 'SpiderVerse', 'GotG'], 'meta': ['Ghost-Spider', 'Spider-Man (Miles)', 'Spider-Weaver', 'Spider-Man', 'Scarlet Spider']},
							],[ ### Lane 2 ###
							{'traits': ['Avenger', 'SpiderVerse'], 'meta': ['Viv Vision', 'Vision', 'Deathlok', 'Hulkbuster', 'Iron Man']},
							{'traits': ['PymTech', 'Infestation', 'Wakanda'], 'meta': ['Black Panther', 'Black Panther (1MM)', 'Nakia', 'Okoye', 'Shuri']},
							{'traits': ['Brotherhood', 'Mercenary', 'Xmen'], 'meta': ['Dazzler', 'Fantomex', 'Gambit', 'Rogue', 'Sunfire']},
							{'traits': ['Kree', 'SpiderVerse', 'GotG'], 'meta': ['Ghost-Spider', 'Spider-Man (Miles)', 'Spider-Weaver', 'Spider-Man', 'Scarlet Spider']},
							],[ ### Lane 3 ###
							{'traits': ['Shield', 'Brotherhood'], 'meta': ['Black Widow', 'Captain America', 'Nick Fury', 'Maria Hill', 'Magneto']},
							{'traits': ['Defender', 'Mercenary', 'HeroesForHire'], 'meta': ['Black Cat', 'Ghost Rider (Robbie)', 'Ms. Marvel (Hard Light)', 'Photon', 'Doctor Strange']},
							{'traits': ['GotG', 'Xmen', 'Mercenary'], 'meta': ['Dazzler', 'Fantomex', 'Gambit', 'Rogue', 'Sunfire']},
							{'traits': ['Brotherhood', 'Mercenary', 'Xmen'], 'meta': ['Dazzler', 'Fantomex', 'Gambit', 'Rogue', 'Sunfire']},
							{'traits': ['Kree', 'SpiderVerse', 'GotG'], 'meta': ['Ghost-Spider', 'Spider-Man (Miles)', 'Spider-Weaver', 'Spider-Man', 'Scarlet Spider']},
							],[ ### Lane 4 ###
							{'traits': ['Shield', 'Aim'], 'meta': ['Black Widow', 'Captain America', 'Nick Fury', 'Maria Hill', 'Hawkeye']},
							{'traits': ['Defender', 'Hydra', 'HeroesForHire'], 'meta': ['Black Cat', 'Ghost Rider (Robbie)', 'Ms. Marvel (Hard Light)', 'Photon', 'Doctor Strange']},
							{'traits': ['Shield', 'Wakanda', 'Defender', 'HeroesForHire'], 'meta': ['Black Panther', 'Black Panther (1MM)', 'Nakia', 'Okoye', 'Shuri']},
							{'traits': ['Kree', 'SpiderVerse', 'GotG'], 'meta': ['Ghost-Spider', 'Spider-Man (Miles)', 'Spider-Weaver', 'Spider-Man', 'Scarlet Spider']},
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
							{'traits': ['Non-Horseman', 'Legendary'], 'label':'Legendary Non-Horseman'},
							{'traits': ['Legendary', 'Apocalypse'],   'label':'Legendary + Apoc'},
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
							{'traits': ['Hive Mind'], 'meta': ['Carnage', 'Venom', 'Void Knight', 'Gwenom', 'Super Skrull']},
							{'traits': ['Infestation']},
							{'traits': ['InfinityWatch']},
							{'traits': ['Knowhere']},
							{'traits': ['MastersOfEvil']},
							{'traits': ['NewAvenger']},
							{'traits': ['NewWarrior']},
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
					'keys': ['power','tier','iso'],
					'sort_by': 'tcp',
					'inc_class': True,
					}

