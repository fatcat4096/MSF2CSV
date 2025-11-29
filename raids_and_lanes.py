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
#		required by the level of raid you are running.
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

ACCURSED   = ['Hellverine', 'Juggernaut', 'Mordo', 'Satana', 'The Hood']
ASTRAL     = ['Ancient One', 'Doctor Strange', 'Emma Frost (X-Men)', 'Moondragon', 'Shadow King']
BRIMSTONE  = ['Daimon Hellstrom', 'Elsa Bloodstone', 'Hellcat', 'Living Mummy', 'Strange (Heartless)']
F4MCU3PACK = ['Franklin Richards', 'Invisible Woman (MCU)', 'Mister Fantastic (MCU)']
F4MCUTEAM  = ['Franklin Richards', 'Human Torch', 'Invisible Woman (MCU)', 'Mister Fantastic (MCU)', 'The Thing']
IMMORTAL   = ['Iron Fist','Iron Fist (WWII)','Lady Bullseye','Steel Serpent','Sword Master']
INSIDIOUS  = ['Hobgoblin', 'Scorpion', 'Shocker', 'Superior Spider-Man', 'Vulture']
HELLFIRE   = ['Azazel', 'Emma Frost', 'Madelyne Pryor', 'Rachel Summers', 'Sebastian Shaw']
NIGHTSTALK = ['Agatha Harkness', 'Blade', 'Man-Thing', 'Moon Knight', 'Oath']
SECRETWAR  = ['Domino', 'Negasonic', 'Phantom Rider', 'Quake', 'Yo-Yo']
TBOLTS     = ['Ghost', 'Hyperion', 'Songbird', 'Taskmaster', 'Victoria Hand']
UNCANNY    = ['Hercules','Falcon','Jean Grey','Beast','Storm']
UNDYING    = ['Hela', 'Iron Man (Zombie)', 'Juggernaut (Zombie)', 'Kestrel (Zombie)', 'Scarlet Witch (Zombie)']
VIGILANTE  = ['Daredevil (Modern)', 'Elektra', 'Hit-Monkey', 'Punisher', 'Silver Sable']

# Meta Heroes for use in Thunderstrike Raid
tables['thunderstrike'] = { 'name': 'Thunderstrike Raid',
					'max_others': 10,
					'strike_teams': 'thunderstrike',
					'sort_char_by': 'avail',
					'inc_keys': ['power','lvl','tier','iso'],
					'lanes':[ [
							{'traits': ['Harbingers']},
							{'traits': ['Conqueror']},
							{'traits': ['Stormbound']},
							] ]
					}

# Meta Heroes for use in Spotlight Raid
tables['spotlight'] = { 'name': 'Spotlight Raid',
					'min_iso': 13,
					'max_others': 5,
					'strike_teams': 'spotlight',
					'sort_char_by': 'avail',
					'inc_keys': ['power','lvl','tier','iso'],
					'lanes':[ [
							{'traits': ['AlphaFlight'],    'meta': ['Wolverine', 'Sunfire', 'Sasquatch', 'Guardian', 'Northstar']},
							{'traits': ['UncannyAvenger'], 'meta': UNCANNY},
							] ]
					}

# Meta Heroes for use in Annihilation Raid (D9)
tables['anni'] = { 'name': 'Annihilation Raid',
					'min_iso': 13,
					'max_others': 0,
					'strike_teams': 'annihilation',
					'sort_char_by': 'avail',
					'inc_keys': ['power','lvl','tier','iso'],
					'lanes':[ [
							{'traits': ['Skill'],  'meta': VIGILANTE, 'label':'Skill<br>(Vigilantes)'}, 
							{'traits': ['Global'], 'meta': UNCANNY,   'label':'Global<br>(Uncanny)'},
							{'traits': ['Mutant'], 'meta': HELLFIRE,  'label':'Mutant<br>(Hellfire)'},
							{'traits': ['Bio'],    'meta': TBOLTS,    'label':'Bio<br>(Thunder)'}, 
							{'traits': ['Tech'],   'meta': INSIDIOUS, 'label':'Tech<br>(Insidious)'}, 
							{'traits': ['Mystic'], 'meta': IMMORTAL,  'label':'Mystic<br>(Immortal)'},
							] ],
					}

# Meta Heroes for use in Annihilation Raid (D8)
tables['annid89'] = { 'name': 'Annihilation Raid (8/9)',
					'min_iso': 13,
					'max_others': 0,
					'strike_teams': 'annihilation',
					'sort_char_by': 'avail',
					'inc_keys': ['power','lvl','tier','iso'],
					'lanes':[ [
							{'traits': ['Skill'],  'meta': VIGILANTE, 'label':'Skill<br>(Vigilantes)'}, 
							{'traits': ['Global'], 'meta': UNCANNY,   'label':'Global<br>(Uncanny)'},
							{'traits': ['Mutant'], 'meta': HELLFIRE,  'label':'Mutant<br>(Hellfire)'},
							{'traits': ['Bio'],    'meta': TBOLTS,    'label':'Bio<br>(Thunder)'}, 
							{'traits': ['Tech'],   'meta': INSIDIOUS, 'label':'Tech<br>(Insidious)'}, 
							{'traits': ['Mystic'], 'meta': NIGHTSTALK + IMMORTAL, 'label':'Mystic<br>(N. Stalkers<br>Imm. Weaps)'},
							] ],
					}

# Meta Heroes for use in Prof X Saga
tables['blue'] = { 'name': 'Blue Marvel',
					'max_others': 10,
					'min_others': True,
					'sort_by': 'avail',
					'sort_char_by': 'avail',
					'inc_avail': True,
					'traits_req': 'all',
					'summary_keys': ['stp','avail'],
					'summary_comp': 'Blue Marvel',
					'lanes':[ [
							{'min_iso': 14, 'traits': ['Hero','Villain'],         'label':'Any Char<br>(ISO 3-4)', 'traits_req':'any'},
							{'min_iso': 14, 'traits': ['Conqueror'],              'label':'Conquerors<br>(ISO 3-4)'},
							{'min_iso': 15, 'traits': ['Conqueror'],              'label':'Conquerors<br>(ISO 3-5)'},
							{'min_iso': 14, 'traits': ['Cosmic','Non-Mythic'],    'label':'Cosmic<br>Non-Mythic<br>(ISO 3-4)'},
							{'min_iso': 15, 'traits': ['Cosmic','Non-Mythic'],    'label':'Cosmic<br>Non-Mythic<br>(ISO 3-5)'},
							{'min_iso': 14, 'traits': ['City',  'Non-Mythic'],    'label':'City<br>Non-Mythic<br>(ISO 3-4)'},
							{'min_iso': 15, 'traits': ['City',  'Non-Mythic'],    'label':'City<br>Non-Mythic<br>(ISO 3-5)'},
							{'min_iso': 14, 'traits': ['Global','Non-Mythic'],    'label':'Global<br>Non-Mythic<br>(ISO 3-4)'},
							{'min_iso': 15, 'traits': ['Global','Non-Mythic'],    'label':'Global<br>Non-Mythic<br>(ISO 3-5)'},
							] ]
					}

# Meta Heroes for use in Prof X Saga
tables['profx'] = { 'name': 'Prof X Saga',
					'max_others': 10,
					'min_others': True,
					'sort_by': 'avail',
					'sort_char_by': 'avail',
					'inc_avail': True,
					'traits_req': 'all',
					'summary_keys': ['stp','avail'],
					'summary_comp': 'Professor Xavier',
					'lanes':[ [
							{'min_tier':20, 'traits': ['City'],             'label':'Gladiator:<br>Heroic &<br>X-Treme<br>(T20 City)'},
							{'min_tier':20, 'traits': ['Global','Villain'], 'label':'Shadow King:<br>Heroic<br>(T20 Global Villain)'},
							{'min_tier':20, 'traits': ['Global','Hero'],    'label':'Shadow King:<br>X-Treme<br>(T20 Global Hero)'},
							{'min_tier':20, 'traits': ['Cosmic','Villain'], 'label':'Dark Xavier:<br>Heroic<br>(T20 Cosmic Villain)'},
							{'min_tier':20, 'traits': ['Cosmic','Hero'],    'label':'Dark Xavier:<br>X-Treme<br>(T20 Cosmic Hero)'},
							] ]
					}

# Meta Heroes for use in Dark Dimension 8
tables['dd8'] = { 'name': 'Dark Dimension 8',
					'min_iso': 13,
					'max_others': 10,
					'min_others': True,
					'sort_by': 'avail',
					'sort_char_by': 'avail',
					'inc_avail': True,
					'traits_req': 'all',
					'summary_keys': ['stp','avail'],
					'summary_comp': 'Odin',
					'lanes':[ [
							{'traits': ['Non-Legendary', 'City', 'Hero'],      'label':'City Hero'},
							{'traits': ['Non-Legendary', 'City', 'Villain'],   'label':'City Villain'},
							{'traits': ['Non-Legendary', 'Global', 'Hero'],    'label':'Global Hero'},
							{'traits': ['Non-Legendary', 'Global', 'Villain'], 'label':'Global Villain'},
							{'traits_req':'any', 'traits': ['Cosmic', 'Legendary'],   'label':'Cosmic or<br>Legendary'},
							] ]
					}

# Meta Heroes for use in Dark Dimension 7
tables['dd7'] = { 'name': 'Dark Dimension 7',
					'min_tier': 19,
					'max_others': 10,
					'min_others': True,
					'sort_by': 'avail',
					'sort_char_by': 'avail',
					'inc_avail': True,
					'traits_req': 'all', 
					'summary_keys': ['stp','avail'],
					'summary_comp': 'Mephisto',
					'lanes':[ [
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
					'min_others': True,
					'sort_by': 'avail',
					'sort_char_by': 'avail',
					'inc_avail': True,
					'traits_req': 'all', 
					'summary_keys': ['stp','avail'],
					'summary_comp': 'Super Skrull',
					'lanes':[ [
							{'traits': ['Global','Non-Legendary'],    'label':'Global'},
							{'traits': ['Cosmic','Non-Legendary'],    'label':'Cosmic'},
							{'traits': ['City',  'Non-Legendary'],    'label':'City'},
							{'traits': ['Legendary', 'Non-Horseman'], 'label':'Legendary<br>Non-Horseman'},
							{'traits': ['Legendary', 'Apocalypse'],   'label':'Legendary<br>+ Apoc', 'traits_req':'any'},
							] ]
					}

# Meta Heroes for use in Dark Dimension 5
tables['dd5'] = { 'name': 'Dark Dimension 5',
					'min_tier': 16,
					'max_others': 10,
					'min_others': True,
					'sort_by': 'avail',
					'sort_char_by': 'avail',
					'inc_avail': True,
					'traits_req': 'all', 
					'summary_keys': ['stp','avail'],
					'summary_comp': 'Dormammu',
					'lanes':[ [
							{'traits': ['Global','Non-Legendary'],   'label':'Global'},
							{'traits': ['Cosmic','Non-Legendary'],   'label':'Cosmic'},
							{'traits': ['City',  'Non-Legendary'],   'label':'City'},
							{'traits': ['Legendary']},
							] ]
					}

# Meta Heroes for use in Teams
tables['teams'] = { 'name': 'Teams',
					'sort_by': 'stp',
					'span': True,
					'max_others': 10,
					'min_others': True,
					'lanes':[ [  
							{'traits': ['AbsoluteAForce'], 'meta': ['Wasp', 'Ironheart', 'Kahhori', 'Medusa', 'Ms. Marvel (Classic)']},
							{'traits': ['Accursed'], 'meta': ACCURSED},
							{'traits': ['AForce'], 'meta': ['Captain Marvel', 'Jessica Jones', 'Nico Minoru', 'Photon', 'Spider-Woman'], 'min_others':False},
							{'traits': ['AlphaFlight'], 'meta': ['Wolverine', 'Sunfire', 'Sasquatch', 'Guardian', 'Northstar']},
							{'traits': ['Annihilator'], 'meta': ['Ultimus', 'Silver Surfer', 'Gladiator', 'Gorr', 'Thanos (Endgame)']},
#							{'traits': ['Astonishing']},
							{'traits': ['Astral'], 'meta': ASTRAL},
							{'traits': ['Bifrost']},
#							{'traits': ['BionicAvenger']},
							{'traits': ['BlackOrder'], 'meta': ['Corvus Glaive', 'Cull Obsidian', 'Ebony Maw', 'Proxima Midnight', 'Thanos']},
							{'traits': ['Brimstone'], 'meta': BRIMSTONE},
							{'traits': ['Cabal']},
							{'traits': ['Darkhold']},
#							{'traits': ['DarkHunter']},
							{'traits': ['Deathseed']},
#							{'traits': ['Eternal']},
							{'traits': ['FantasticFourMCU'], 'meta': F4MCUTEAM},
							{'traits': ['Gamma'], 'meta': ['Red Hulk', 'Hulk', 'She-Hulk', 'Abomination', 'Brawn']},
							{'traits': ['HellfireClub'], 'meta': HELLFIRE},
							{'traits': ['HeroesForHire']},
							{'traits': ['HiveMind']},
							{'traits': ['Illuminati'], 'meta': ['Black Bolt', 'Mister Fantastic', 'Black Panther (Shuri)', 'Captain Britain', 'Hank Pym']},
							{'traits': ['ImmortalWeapon'], 'meta': IMMORTAL},
							{'traits': ['ImmortalXMen'], 'meta': ['Jean Grey','Beast','Storm','Polaris','Cable']},
							{'traits': ['Infestation'], 'meta': ['Ant-Man', 'Black Widow', 'Spider-Man (Big Time)', 'Swarm', 'Yellowjacket']},
							{'traits': ['InfinityWatch']},
							{'traits': ['InsidiousSix'], 'meta': INSIDIOUS},
							{'traits': ['Invader']},
							{'traits': ['Knowhere']},
							{'traits': ['Liberty'], 'meta': ['Captain America (Sam)','War Machine','Falcon (Joaquin)','Patriot','Peggy Carter']},
#							{'traits': ['MastersOfEvil']},
							{'traits': ['MercsForMoney']},
							{'traits': ['MightyAvenger'], 'meta': ['Hercules','Scarlet Witch','Invisible Woman','Vision','Falcon']},
							{'traits': ['NewAvenger']},
							{'traits': ['NewMutant'], 'meta': ['Magik', 'Sunspot', 'Cannonball', 'Warlock', 'Wolfsbane']},
							{'traits': ['NewWarrior']},
							{'traits': ['Nightstalkers'], 'meta': NIGHTSTALK},
							{'traits': ['Orchis'], 'meta': ['Scientist Supreme', 'Lady Deathstrike', 'Sentinel', 'Omega Sentinel', 'Nimrod']},
							{'traits': ['OutOfTime']},
							{'traits': ['Pegasus']},
							{'traits': ['PhoenixForce'], 'meta': ['Phoenix', 'Omega Red (Phoenix Force)']},
#							{'traits': ['PymTech']},
							{'traits': ['Rebirth']},
#							{'traits': ['SecretDefender']},
							{'traits': ['SecretWarrior'], 'meta': SECRETWAR},
#							{'traits': ['Shadowland']},
							{'traits': ['SpiderSociety']},
							{'traits': ['SuperiorSix'], 'meta': ['Green Goblin (Classic)', 'Doctor Octopus', 'Lizard', 'Kraven the Hunter', 'Spider-Slayer']},
							{'traits': ['Starjammer'], 'meta': ['Groot','Rocket Raccoon','Havok','Lilandra','Howard The Duck']},
							{'traits': ['Thunderbolts'], 'meta': TBOLTS},
#							{'traits': ['Uncanny']},
							{'traits': ['UncannyAvenger'], 'meta': UNCANNY},
							{'traits': ['Under-<br>world'], 'meta': ['Kingpin', 'Mister Negative', 'Nobu', 'Taskmaster', 'Green Goblin']},
							{'traits': ['Undying'], 'meta': UNDYING},
							{'traits': ['Unlimited']},
							{'traits': ['Vigilante'], 'meta': VIGILANTE}, 
							{'traits': ['WarDog']},
							{'traits': ['WeaponX'], 'meta': ['Omega Red', 'Sabretooth', 'Silver Samurai', 'Wolverine', 'X-23']},
							{'traits': ['XTreme']},
#							{'traits': ['Young<br>Avengers'], 'meta': ['America Chavez', 'Echo', 'Kate Bishop', 'Ms. Marvel', 'Squirrel Girl']},	
							] ]
					}



tables['battleworld'] = { 'name': 'Battleworld',
					'max_others': 10,
					'sort_char_by': 'avail',
					'lane_name': 'zone',
					'lanes':[ [ ### Zone 1 ###
							{'header':'Mission 1', 'traits': ['Mystic',  'Non-Mythic'], 'meta': ACCURSED, 'max_others':5},
							{'header':'Mission 2', 'traits': ['Mutant',  'Non-Mythic'], 'meta': HELLFIRE, 'max_others':5}, 
							{'header':'Mission 3', 'traits': ['Villain', 'Non-Mythic']}, 
							{'header':'Mission 4', 'meta': ['Quasar', 'Blastaar'], 'label':'Quasar and<br>Blastaar'},
							{'header':'Mission 5', 'meta': F4MCUTEAM + BRIMSTONE, 'label':'F4 MCU or<br>Brimstone'},
							{'header':'Mission 6', 'traits': ['ChaosTeam'], 'meta': ['Quasar', 'Blastaar','Songbird','Hercules','Falcon'], 'max_others':5},
							],[ ### Zone 2 ###
							{'header':'Mission 1', 'traits': ['Tech', 'Non-Mythic'], 'meta': INSIDIOUS, 'max_others':5},
							{'header':'Mission 2', 'traits': ['Bio',  'Non-Mythic'], 'meta': TBOLTS,    'max_others':5},
							{'header':'Mission 3', 'traits': ['Hero', 'Non-Mythic'], 'meta': ['Franklin Richards', 'Invisible Woman (MCU)', 'Mister Fantastic (MCU)', 'Quasar', 'Blade'], 'max_others':5},
							{'header':'Mission 4', 'meta': ACCURSED  + HELLFIRE,  'label':'Accursed or<br>Hellfire Club'},
							{'header':'Mission 5', 'meta': SECRETWAR + BRIMSTONE, 'label':'Secret Warrior<br>or Brimstone'},
							{'header':'Mission 6', 'traits': ['ChaosTeam'], 'max_others':5},
							],[ ### Zone 3 ###
							{'header':'Mission 1', 'traits': ['Skill',  'Non-Mythic'], 'meta': VIGILANTE, 'max_others':5},
							{'header':'Mission 2', 'traits': ['Global', 'Non-Mythic'], 'meta': ['Old Man Logan', 'Emma Frost', 'Madelyne Pryor', 'Rachel Summers', 'Sebastian Shaw'],  'max_others':5},
							{'header':'Mission 3', 'traits': ['Cosmic', 'Non-Mythic'], 'meta': F4MCU3PACK + ['Quasar', 'Knull'], 'max_others':5},
							{'header':'Mission 4', 'traits': ['City'], 'meta': INSIDIOUS, 'max_others':5},
							{'header':'Mission 5', 'traits': ['Blue Marvel', 'Phantom Rider', 'PhoenixForce'], 'traits_req':'any', 'label':'Blue Marvel<br>Phant. Rider<br>or P. Force'},
							{'header':'Mission 6', 'meta': UNDYING + BRIMSTONE, 'label':'Undying or<br>Brimstone'},
							],[ ### Zone 4 ###
							{'header':'Sentry', 'label':'Option 1', 'meta': F4MCU3PACK + ['Odin','Mephisto']},
							{'header':'Sentry', 'label':'Option 2', 'meta': BRIMSTONE},
							{'header':'Sentry', 'label':'Option 3', 'meta': ASTRAL},
							{'header':'Sentry', 'label':'Option 4', 'meta': VIGILANTE},
							{'header':'Sentry', 'label':'Option 5', 'meta': ['Professor Xavier', 'Apocalypse','Knull', 'Old Man Logan', 'Havok', ]},
							{'header':'Sentry', 'label':'Option 6', 'meta': ['Professor Xavier', 'Quasar', 'Phoenix', 'Emma Frost', 'Omega Red (Phoenix Force)']},
							] ]
					}



# Meta Heroes for use in All Characters
tables['all_chars'] = { 'name': 'All Characters',
					'max_others': 0,
					'sort_by': 'tcp',
					'inc_keys': ['power','tier','iso'],
					'inc_class': True,
					'lanes':[ [
							{'traits': ['All'], 'label':'All Chars'},
							{'traits': ['Bio'], },
							{'traits': ['Mutant'], },
							{'traits': ['Mystic'], },
							{'traits': ['Skill'], },
							{'traits': ['Tech'], },
							{'traits': ['Cosmic'], },
							{'traits': ['City'], },
							{'traits': ['Global'], },
							] ]
					}

