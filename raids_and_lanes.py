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
							] ]
					}

# Meta Heroes for use in Orchis Raid
tables['orchis'] = { 'name': 'Orchis Raid',
					'min_iso': 10,
					'max_others': 0,
					'strike_teams': 'orchis',
					'sort_char_by': 'avail',
					'inc_keys': ['power','lvl','tier','iso'],
					'lanes':[ [
							{'traits': ['Mutant'], 'meta': ['Gambit', 'Nightcrawler', 'Forge', 'Sunspot', 'Old Man Logan'], 'label':'Mutant<br>(X-Treme)'},
							{'traits': ['Mystic'], 'meta': ['Oath', 'Man-Thing', 'Blade', 'Agatha Harkness', 'Moon Knight'], 'label':'Mystic<br>(Nightstalkers)'},
							{'traits': ['Skill'], 'meta': ['Peni Parker', 'Ghost-Spider', 'Peter B. Parker', 'Spider-Man (Noir)', 'Spider-Man (Pavitr)'], 'label':'Skill<br>(Spider Society)'}, 
							{'traits': ['Tech'], 'meta': ['Scientist Supreme', 'Lady Deathstrike', 'Sentinel', 'Nimrod', 'Omega Sentinel'], 'label':'Tech<br>(Orchis)'}, 
							{'traits': ['Bio'], 'meta': ['Carnage', 'Super Skrull', 'Void Knight', 'Gwenom', 'Red Goblin'], 'label':'Bio<br>(Hive-Mind)'}, 
							] ],
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


# Meta Heroes for use in Dark Dimension 8
tables['dd8'] = { 'name': 'Dark Dimension 8',
					'min_iso': 13,
					'max_others': 10,
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
					'sort_by': 'avail',
					'sort_char_by': 'avail',
					'inc_avail': True,
					'traits_req': 'all', 
					'summary_keys': ['stp','avail'],
					'summary_comp': 'Super Skrull',
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
					'summary_keys': ['stp','avail'],
					'summary_comp': 'Dormammu',
					'lanes':[ [
							{'traits': ['Non-Legendary', 'Global'],   'label':'Global'},
							{'traits': ['Non-Legendary', 'Cosmic'],   'label':'Cosmic'},
							{'traits': ['Non-Legendary', 'City'],     'label':'City'},
							{'traits': ['Legendary']},
							] ]
					}

# Meta Heroes for use in Battleworld
unused =  { 'name': 'Battleworld',
					'sort_by': 'stp',
					'span': True,
					'lanes':[ [  
							{'traits': ['SuperiorSix']},
							{'traits': ['Annihilator'], 'meta': ['Ultimus', 'Silver Surfer', 'Gladiator', 'Gorr', 'Thanos (Endgame)']},
							{'traits': ['SpiderSociety']},
							{'traits': ['Bifrost']},
							{'traits': ['Astral'], 'meta': ['Moondragon', 'Doctor Strange']},
							],[
							{'traits': ['MercsForMoney']},
							{'traits': ['Cabal']},
							{'traits': ['Undying']},
							{'traits': ['AlphaFlight'], 'meta': ['Wolverine', 'Sunfire', 'Sasquatch', 'Guardian', 'Northstar']},
							{'traits': ['Astral'], 'meta': ['Moondragon', 'Doctor Strange']},
							],[
							{'traits': ['Annihilator'], 'meta': ['Ultimus', 'Silver Surfer', 'Gladiator', 'Gorr', 'Thanos (Endgame)']},
							{'traits': ['Illuminati'], 'meta': ['Black Bolt', 'Mister Fantastic', 'Black Panther (Shuri)', 'Captain Britain', 'Hank Pym']},
							{'traits': ['OutOfTime']},
							{'traits': ['SuperiorSix']},
							{'traits': ['Astral'], 'meta': ['Moondragon', 'Doctor Strange']},
							],[
							{'traits': ['AlphaFlight'], 'meta': ['Wolverine', 'Sunfire', 'Sasquatch', 'Guardian', 'Northstar']},
							{'traits': ['XTreme']},
							{'traits': ['MercsForMoney']},
							{'traits': ['MsfOriginal'], 'meta': ['Kestrel', 'Deathpool', 'Spider-Weaver', 'Vahl']},
							{'traits': ['Astral'], 'meta': ['Moondragon', 'Doctor Strange']},
							],[
							{'traits': ['HiveMind']},
							{'traits': ['Illuminati'], 'meta': ['Black Bolt', 'Mister Fantastic', 'Black Panther (Shuri)', 'Captain Britain', 'Hank Pym']},
							{'traits': ['Orchis'], 'meta': ['Scientist Supreme', 'Lady Deathstrike', 'Sentinel', 'Omega Sentinel', 'Nimrod']},
							{'traits': ['Nightstalkers'], 'meta': ['Oath', 'Man-Thing', 'Blade', 'Agatha Harkness', 'Moon Knight']},
							{'traits': ['Astral'], 'meta': ['Moondragon', 'Doctor Strange']},
							] ],
					'lane_name':'Zone',
					}

# Meta Heroes for use in Spec Ops
tables['spec_ops'] = { 'name': 'Spec Ops',
					'sort_by': 'stp',
					'span': True,
					'lanes':[ [ 
							{'traits': ['Mission 1'], 'min_yel' : 3, 'meta': ["Old Man Logan", "Hank Pym", "Sasquatch", "Guardian", "Daken", "Iron Patriot"] },
							{'traits': ['Mission 2'], 'min_yel' : 5, 'meta': ["Black Bolt", "Black Panther (Shuri)", "Northstar", "Pandapool", "The Leader", "Sunfire"] },
							{'traits': ['Mission 3'], 'min_yel' : 7, 'meta': ["Iron Man", "Deathpool", "Namor", "Mister Fantastic", "Deadpool", "Wolverine"] },
							{'traits': ['Mission 4'], 'min_tier':15, 'meta': ["Cosmic Ghost Rider", "Spider-Slayer", "Spider-Man (Noir)", "Silver Surfer", "Moon Knight", "Venom"] },
							{'traits': ['Mission 5'], 'min_tier':17, 'meta': ["Super Skrull", "Black Cat", "Peter B. Parker", "Red Goblin", "Kraven the Hunter", "Ultimus"] },
							{'traits': ['Mission 6'], 'min_red' : 6, 'meta': ["Nova", "Doctor Octopus", "Gorr", "Spider-Man (Pavitr)", "Mysterio", "Carnage"] },
							{'traits': ['Mission 7'], 'min_tier':19, 'meta': ["Green Goblin (Classic)", "Thanos (Endgame)", "Peni Parker", "Void Knight", "Spider-Man (Big Time)", "Vahl"] },
							{'traits': ['Mission 8'], 'min_red' : 8, 'meta': ["Gladiator", "Gwenom", "Lizard", "Kang the Conqueror", "Ghost-Spider", "Vulture"] },
							],[
							{'traits': ['Mission 1'], 'min_yel' : 3, 'meta': ["Captain Britain", "Thanos (Endgame)", "Gorr", "Black Panther (Shuri)", "Peni Parker", "Peter B. Parker"] },
							{'traits': ['Mission 2'], 'min_yel' : 5, 'meta': ["Gladiator", "Hank Pym", "Spider-Man (Pavitr)", "Starbrand", "Mister Fantastic", "Ultimus"] },
							{'traits': ['Mission 3'], 'min_yel' : 7, 'meta': ["Black Bolt", "Cosmic Ghost Rider", "Black Knight", "Spider-Man (Noir)", "Silver Surfer", "Ghost-Spider"] },
							{'traits': ['Mission 4'], 'min_tier':15, 'meta': ["Doctor Doom", "Juggernaut (Zombie)", "Omega Sentinel", "Northstar", "Daken", "Sunspot"] },
							{'traits': ['Mission 5'], 'min_tier':17, 'meta': ["Rogue", "Sentinel", "Ares", "Forge", "Sunfire", "Deathpool"] },
							{'traits': ['Mission 6'], 'min_red' : 6, 'meta': ["Iron Man (Zombie)", "Pandapool", "Iron Patriot", "Cyclops", "Scientist Supreme", "Wolverine"] },
							{'traits': ['Mission 7'], 'min_tier':19, 'meta': ["Apocalypse", "Old Man Logan", "Nimrod", "Sasquatch", "The Leader", "Gambit"] },
							{'traits': ['Mission 8'], 'min_red' : 8, 'meta': ["Guardian", "Nightcrawler", "Agatha Harkness", "Lady Deathstrike", "Namor", "Deadpool"] },
							],[
							{'traits': ['Mission 1'], 'min_yel' : 3, 'meta': ["Omega Sentinel", "Nimrod", "Northstar", "Pandapool", "Gwenom", "Deadpool"] },
							{'traits': ['Mission 2'], 'min_yel' : 5, 'meta': ["Old Man Logan", "Sentinel", "Sasquatch", "Red Goblin", "Deathpool", "Wolverine"] },
							{'traits': ['Mission 3'], 'min_yel' : 7, 'meta': ["Guardian", "Daken", "Void Knight", "Sunfire", "Lady Deathstrike", "Scientist Supreme"] },
							{'traits': ['Mission 4'], 'min_tier':15, 'meta': ["Black Cat", "Iron Man", "Peter B. Parker", "Starbrand", "Quicksilver", "Ultimus"] },
							{'traits': ['Mission 5'], 'min_tier':17, 'meta': ["Green Goblin (Classic)", "Captain Britain", "Gorr", "Spider-Man (Pavitr)", "Spider-Man (Big Time)", "Captain Carter"] },
							{'traits': ['Mission 6'], 'min_red' : 6, 'meta': ["Super Skrull", "Black Bolt", "Ares", "Cosmic Ghost Rider", "Sunspot", "Silver Surfer"] },
							{'traits': ['Mission 7'], 'min_tier':19, 'meta': ["Mephisto", "Nova", "Gladiator", "Black Panther (Shuri)", "Black Knight", "Nightcrawler"] },
							{'traits': ['Mission 8'], 'min_red' : 8, 'meta': ["Apocalypse", "Thanos (Endgame)", "Hank Pym", "Peni Parker", "Forge", "Captain America"] },
							],[
							{'traits': ['Mission 1'], 'min_yel' : 3, 'meta': ["Man-Thing", "Oath", "Blade", "Sentinel", "Agatha Harkness", "Ultimus"] },
							{'traits': ['Mission 2'], 'min_yel' : 5, 'meta': ["Doctor Doom", "Captain Britain", "Omega Sentinel", "Nimrod", "Thanos (Endgame)", "Guardian"] },
							{'traits': ['Mission 3'], 'min_yel' : 7, 'meta': ["Dormammu", "Hank Pym", "Black Panther (Shuri)", "Northstar", "Peni Parker", "Moon Knight"] },
							{'traits': ['Mission 4'], 'min_tier':15, 'meta': ["Archangel", "Phoenix", "Scarlet Witch (Zombie)", "Spider-Man (Pavitr)", "Spider-Weaver", "Cyclops"] },
							{'traits': ['Mission 5'], 'min_tier':17, 'meta': ["Rogue", "Morgan Le Fay", "Juggernaut (Zombie)", "Gladiator", "Sunspot", "X-23"] },
							{'traits': ['Mission 6'], 'min_red' : 6, 'meta': ["Odin", "Old Man Logan", "Red Hulk", "Peter B. Parker", "Red Goblin", "Nightcrawler"] },
							{'traits': ['Mission 7'], 'min_tier':19, 'meta': ["Super Skrull", "Gorr", "Gwenom", "Forge", "Deathpool", "Wolverine"] },
							{'traits': ['Mission 8'], 'min_red' : 8, 'meta': ["Iron Man (Zombie)", "Sasquatch", "Void Knight", "Vahl", "Sunfire", "Gambit"] },
							],[
							{'traits': ['Mission 1'], 'min_yel' : 3, 'meta': ["Scarlet Witch (Zombie)", "Gladiator", "Guardian", "Sunfire", "Silver Surfer", "Wolverine"] },
							{'traits': ['Mission 2'], 'min_yel' : 5, 'meta': ["Iron Man (Zombie)", "Gorr", "Ares", "Northstar", "Daken", "Deadpool"] },
							{'traits': ['Mission 3'], 'min_yel' : 7, 'meta': ["Old Man Logan", "Juggernaut (Zombie)", "Thanos (Endgame)", "Sasquatch", "Pandapool", "Ultimus"] },
							{'traits': ['Mission 4'], 'min_tier':15, 'meta': ["Man-Thing", "Peni Parker", "Void Knight", "Ghost Rider (Robbie)", "Lady Deathstrike", "Mysterio"] },
							{'traits': ['Mission 5'], 'min_tier':17, 'meta': ["Apocalypse", "Oath", "Gwenom", "Spider-Slayer", "Quicksilver", "Scientist Supreme"] },
							{'traits': ['Mission 6'], 'min_red' : 6, 'meta': ["Green Goblin (Classic)", "Captain Britain", "Sentinel", "Hank Pym", "Black Panther (Shuri)", "Venom"] },
							{'traits': ['Mission 7'], 'min_tier':19, 'meta': ["Blade", "Omega Sentinel", "Peter B. Parker", "Cosmic Ghost Rider", "Red Goblin", "Vulture"] },
							{'traits': ['Mission 8'], 'min_red' : 8, 'meta': ["Doctor Octopus", "Nimrod", "Spider-Man (Pavitr)", "Deathpool", "Moon Knight", "Carnage"] }
							] ],
					'inc_keys':['power','tier','yel','red','iso'], 
					'lane_name':'Zone',
					'show_reqs': True, 
					'spec_ops':True,
					}

# Meta Heroes for use in Teams
tables['teams'] = { 'name': 'Teams',
					'sort_by': 'stp',
					'span': True,
					'lanes':[ [  
							{'traits': ['AbsoluteAForce'], 'meta': ['Wasp', 'Ironheart', 'Kahhori', 'Medusa', 'Ms. Marvel (Classic)']},
							{'traits': ['AForce']},
							{'traits': ['AlphaFlight'], 'meta': ['Wolverine', 'Sunfire', 'Sasquatch', 'Guardian', 'Northstar']},
							{'traits': ['Annihilator'], 'meta': ['Ultimus', 'Silver Surfer', 'Gladiator', 'Gorr', 'Thanos (Endgame)']},
							{'traits': ['Astonishing']},
							{'traits': ['Astral'], 'meta': ['Doctor Strange', 'Moondragon', 'Ancient One', 'Shadow King', 'Emma Frost (X-Men)']},
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
							{'traits': ['Nightstalkers'], 'meta': ['Oath', 'Man-Thing', 'Blade', 'Agatha Harkness', 'Moon Knight']},
							{'traits': ['Orchis'], 'meta': ['Scientist Supreme', 'Lady Deathstrike', 'Sentinel', 'Omega Sentinel', 'Nimrod']},
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


zones =	{1:{'bonus':['SuperiorSix','Annihilator','SpiderSociety','Bifrost','Astral'],
			'specops':{	1:{'req': {'yel' :3},	'chars': ["Old Man Logan", "Hank Pym", "Sasquatch", "Guardian", "Daken", "Iron Patriot"] },
						2:{'req': {'yel' :5},	'chars': ["Black Bolt", "Black Panther (Shuri)", "Northstar", "Pandapool", "The Leader", "Sunfire"] },
						3:{'req': {'yel' :7},	'chars': ["Iron Man", "Deathpool", "Namor", "Mister Fantastic", "Deadpool", "Wolverine"] },
						4:{'req': {'tier':15},	'chars': ["Cosmic Ghost Rider", "Spider-Slayer", "Spider-Man (Noir)", "Silver Surfer", "Moon Knight", "Venom"] },
						5:{'req': {'tier':17},	'chars': ["Super Skrull", "Black Cat", "Peter B. Parker", "Red Goblin", "Kraven the Hunter", "Ultimus"] },
						6:{'req': {'red' :6},	'chars': ["Nova", "Doctor Octopus", "Gorr", "Spider-Man (Pavitr)", "Mysterio", "Carnage"] },
						7:{'req': {'tier':19},	'chars': ["Green Goblin (Classic)", "Thanos (Endgame)", "Peni Parker", "Void Knight", "Spider-Man (Big Time)", "Vahl"] },
						8:{'req': {'red' :8},	'chars': ["Gladiator", "Gwenom", "Lizard", "Kang the Conqueror", "Ghost-Spider", "Vulture"] } } },
		2:{'bonus':['MercsForMoney','Cabal','Undying','AlphaFlight','Astral'],
			'specops':{	1:{'req': {'yel' :3},	'chars': ["Captain Britain", "Thanos (Endgame)", "Gorr", "Black Panther (Shuri)", "Peni Parker", "Peter B. Parker"] },
						2:{'req': {'yel' :5},	'chars': ["Gladiator", "Hank Pym", "Spider-Man (Pavitr)", "Starbrand", "Mister Fantastic", "Ultimus"] },
						3:{'req': {'yel' :7},	'chars': ["Black Bolt", "Cosmic Ghost Rider", "Black Knight", "Spider-Man (Noir)", "Silver Surfer", "Ghost-Spider"] },
						4:{'req': {'tier':15},	'chars': ["Doctor Doom", "Juggernaut (Zombie)", "Omega Sentinel", "Northstar", "Daken", "Sunspot"] },
						5:{'req': {'tier':17},	'chars': ["Rogue", "Sentinel", "Ares", "Forge", "Sunfire", "Deathpool"] },
						6:{'req': {'red' :6},	'chars': ["Iron Man (Zombie)", "Pandapool", "Iron Patriot", "Cyclops", "Scientist Supreme", "Wolverine"] },
						7:{'req': {'tier':19},	'chars': ["Apocalypse", "Old Man Logan", "Nimrod", "Sasquatch", "The Leader", "Gambit"] },
						8:{'req': {'red' :8},	'chars': ["Guardian", "Nightcrawler", "Agatha Harkness", "Lady Deathstrike", "Namor", "Deadpool"] } } },
		3:{'bonus':['Annihilator','Illuminati','OutOfTime','SuperiorSix','Astral'],
			'specops':{	1:{'req': {'yel' :3},	'chars': ["Omega Sentinel", "Nimrod", "Northstar", "Pandapool", "Gwenom", "Deadpool"] },
						2:{'req': {'yel' :5},	'chars': ["Old Man Logan", "Sentinel", "Sasquatch", "Red Goblin", "Deathpool", "Wolverine"] },
						3:{'req': {'yel' :7},	'chars': ["Guardian", "Daken", "Void Knight", "Sunfire", "Lady Deathstrike", "Scientist Supreme"] },
						4:{'req': {'tier':15},	'chars': ["Black Cat", "Iron Man", "Peter B. Parker", "Starbrand", "Quicksilver", "Ultimus"] },
						5:{'req': {'tier':17},	'chars': ["Green Goblin (Classic)", "Captain Britain", "Gorr", "Spider-Man (Pavitr)", "Spider-Man (Big Time)", "Captain Carter"] },
						6:{'req': {'red' :6},	'chars': ["Super Skrull", "Black Bolt", "Ares", "Cosmic Ghost Rider", "Sunspot", "Silver Surfer"] },
						7:{'req': {'tier':19},	'chars': ["Mephisto", "Nova", "Gladiator", "Black Panther (Shuri)", "Black Knight", "Nightcrawler"] },
						8:{'req': {'red' :8},	'chars': ["Apocalypse", "Thanos (Endgame)", "Hank Pym", "Peni Parker", "Forge", "Captain America"] } } },
		4:{'bonus':['AlphaFlight','XTreme','MercsForMoney','MsfOriginal','Astral'],
			'specops':{	1:{'req': {'yel' :3},	'chars': ["Man-Thing", "Oath", "Blade", "Sentinel", "Agatha Harkness", "Ultimus"] },
						2:{'req': {'yel' :5},	'chars': ["Doctor Doom", "Captain Britain", "Omega Sentinel", "Nimrod", "Thanos (Endgame)", "Guardian"] },
						3:{'req': {'yel' :7},	'chars': ["Dormammu", "Hank Pym", "Black Panther (Shuri)", "Northstar", "Peni Parker", "Moon Knight"] },
						4:{'req': {'tier':15},	'chars': ["Archangel", "Phoenix", "Scarlet Witch (Zombie)", "Spider-Man (Pavitr)", "Spider-Weaver", "Cyclops"] },
						5:{'req': {'tier':17},	'chars': ["Rogue", "Morgan Le Fay", "Juggernaut (Zombie)", "Gladiator", "Sunspot", "X-23"] },
						6:{'req': {'red' :6},	'chars': ["Odin", "Old Man Logan", "Red Hulk", "Peter B. Parker", "Red Goblin", "Nightcrawler"] },
						7:{'req': {'tier':19},	'chars': ["Super Skrull", "Gorr", "Gwenom", "Forge", "Deathpool", "Wolverine"] },
						8:{'req': {'red' :8},	'chars': ["Iron Man (Zombie)", "Sasquatch", "Void Knight", "Vahl", "Sunfire", "Gambit"] } } },
		5:{'bonus':['HiveMind','Illuminati','Orchis','Nightstalkers','Astral'],
			'specops':{	1:{'req': {'yel' :3},	'chars': ["Scarlet Witch (Zombie)", "Gladiator", "Guardian", "Sunfire", "Silver Surfer", "Wolverine"] },
						2:{'req': {'yel' :5},	'chars': ["Iron Man (Zombie)", "Gorr", "Ares", "Northstar", "Daken", "Deadpool"] },
						3:{'req': {'yel' :7},	'chars': ["Old Man Logan", "Juggernaut (Zombie)", "Thanos (Endgame)", "Sasquatch", "Pandapool", "Ultimus"] },
						4:{'req': {'tier':15},	'chars': ["Man-Thing", "Peni Parker", "Void Knight", "Ghost Rider (Robbie)", "Lady Deathstrike", "Mysterio"] },
						5:{'req': {'tier':17},	'chars': ["Apocalypse", "Oath", "Gwenom", "Spider-Slayer", "Quicksilver", "Scientist Supreme"] },
						6:{'req': {'red' :6},	'chars': ["Green Goblin (Classic)", "Captain Britain", "Sentinel", "Hank Pym", "Black Panther (Shuri)", "Venom"] },
						7:{'req': {'tier':19},	'chars': ["Blade", "Omega Sentinel", "Peter B. Parker", "Cosmic Ghost Rider", "Red Goblin", "Vulture"] },
						8:{'req': {'red' :8},	'chars': ["Doctor Octopus", "Nimrod", "Spider-Man (Pavitr)", "Deathpool", "Moon Knight", "Carnage"] } } } }