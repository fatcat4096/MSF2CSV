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
tables = {'active': ['incur', 'gamma', 'war', 'all']}


# Meta Heroes for use in Incursion Raid
tables['incur'] = { 'name': 'Incursion Raid',
					'min_tier': 16,
					'min_iso': 9,
					'strike_teams': 'incur',
					'lanes':[ [
							{'traits': ['Mutant'], 'meta': ['Archangel', 'Nemesis', 'Dark Beast', 'Psylocke', 'Magneto']},
							{'traits': ['Bio'], 'meta': ['Captain America', 'Captain Carter', 'Agent Venom', 'Winter Soldier', 'U.S. Agent']},
							{'traits': ['Skill'], 'meta': ['Nick Fury', 'Captain America (WWII)', 'Iron Fist (WWII)', 'Bucky Barnes', 'Union Jack']},
							{'traits': ['Mystic'], 'meta': ['Beta Ray Bill', 'Loki', 'Loki (Teen)', 'Sylvie', 'Vahl']},
							{'traits': ['Tech'], 'meta': ['Kang the Conqueror', 'Doctor Doom', 'Hulkbuster', 'Viv Vision', 'Vision']},
							] ]
					}

# Meta Heroes for use in Gamma Raid
tables['gamma'] = { 'name': 'Gamma Raid',
					'min_tier': 16,
					'strike_teams': 'other',
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
tables['all'] = { 'name': 'All Characters',
					'keys': ['power'],
					}
