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

# Meta Heroes for use in Spotlight Raid
tables['spotlight'] = { 'name': 'Spotlight Raid',
					'min_iso': 13,
					'max_others': 5,
					'strike_teams': 'spotlight',
					'sort_char_by': 'avail',
					'inc_keys': ['power','lvl','tier','iso'],
					'lanes':[ [
							{'traits': ['AlphaFlight'],    'meta': ['Wolverine', 'Sunfire', 'Sasquatch', 'Guardian', 'Northstar']},
							{'traits': ['UncannyAvenger'], 'meta': ['Hercules','Falcon','Jean Grey','Beast','Storm']},
							] ]
					}

# Meta Heroes for use in Orchis Raid
tables['chaos'] = { 'name': 'Chaos Raid',
					'min_iso': 13,
					'max_others': 0,
					'strike_teams': 'chaos',
					'sort_char_by': 'avail',
					'inc_keys': ['power','lvl','tier','iso'],
					'lanes':[ [
							{'traits': ['Tech'], 'meta': ['Scientist Supreme', 'Lady Deathstrike', 'Sentinel', 'Nimrod', 'Omega Sentinel'], 'label':'Tech<br>(Orchis)'}, 
							#{'traits': ['Bio'], 'meta': ['Carnage', 'Super Skrull', 'Void Knight', 'Gwenom', 'Red Goblin'], 'label':'Bio<br>(Hive-Mind)'}, 
							{'traits': ['Bio'], 'meta': ['Taskmaster','Ghost','Hyperion','Victoria Hand','Songbird'], 'label':'Bio<br>(Thunderbolts)'}, 
							{'traits': ['Mystic'], 'meta': ['Oath', 'Man-Thing', 'Blade', 'Agatha Harkness', 'Moon Knight'], 'label':'Mystic<br>(Nightstalkers)'},
							#{'traits': ['Skill'], 'meta': ['Peni Parker', 'Ghost-Spider', 'Peter B. Parker', 'Spider-Man (Noir)', 'Spider-Man (Pavitr)'], 'label':'Skill<br>(Spider Society)'}, 
							{'traits': ['Skill'], 'meta': ['Daredevil (Modern)', 'Silver Sable', 'Hit-Monkey', 'Punisher', 'Elektra'], 'label':'Skill<br>(Vigilantes)'}, 
							{'traits': ['Mutant'], 'meta': ['Gambit', 'Nightcrawler', 'Forge', 'Sunspot', 'Old Man Logan'], 'label':'Mutant<br>(X-Treme)'},
							] ],
					}

# Meta Heroes for use in Annihilation Raid (D8-9)
tables['anni'] = { 'name': 'Annihilation Raid',
					'min_iso': 13,
					'max_others': 0,
					'strike_teams': 'annihilation',
					'sort_char_by': 'avail',
					'inc_keys': ['power','lvl','tier','iso'],
					'lanes':[ [
							{'traits': ['Tech'], 'meta': ['Shocker', 'Hobgoblin', 'Scorpion', 'Vulture', 'Spider-Man (Superior)'], 'label':'Tech<br>(Insidious Six)'}, 
							#{'traits': ['Bio'], 'meta': ['Carnage', 'Super Skrull', 'Void Knight', 'Gwenom', 'Red Goblin'], 'label':'Bio<br>(Hive-Mind)'}, 
							{'traits': ['Bio'], 'meta': ['Taskmaster','Ghost','Hyperion','Victoria Hand','Songbird'], 'label':'Bio<br>(Thunderbolts)'}, 
							{'traits': ['Mystic'], 'meta': ['Oath', 'Man-Thing', 'Blade', 'Agatha Harkness', 'Moon Knight'], 'label':'Mystic<br>(Nightstalkers)'},
							#{'traits': ['Skill'], 'meta': ['Peni Parker', 'Ghost-Spider', 'Peter B. Parker', 'Spider-Man (Noir)', 'Spider-Man (Pavitr)'], 'label':'Skill<br>(Spider Society)'}, 
							{'traits': ['Skill'], 'meta': ['Daredevil (Modern)', 'Silver Sable', 'Hit-Monkey', 'Punisher', 'Elektra'], 'label':'Skill<br>(Vigilantes)'}, 
							{'traits': ['Mutant'], 'meta': ['Gambit', 'Nightcrawler', 'Forge', 'Sunspot', 'Old Man Logan'], 'label':'Mutant<br>(X-Treme)'},
							] ],
					}

# Meta Heroes for use in Annihilation Raid (D6-7)
tables['anni_low'] = { 'name': 'Annihilation Raid (D6-7)',
					'min_iso': 13,
					'max_others': 0,
					'strike_teams': 'annihilation',
					'sort_char_by': 'avail',
					'inc_keys': ['power','lvl','tier','iso'],
					'lanes':[ [
							{'traits': ['Tech'], 'meta': ['Scientist Supreme', 'Lady Deathstrike', 'Sentinel', 'Nimrod', 'Omega Sentinel'], 'label':'Tech<br>(Orchis)'}, 
							#{'traits': ['Bio'], 'meta': ['Carnage', 'Super Skrull', 'Void Knight', 'Gwenom', 'Red Goblin'], 'label':'Bio<br>(Hive-Mind)'}, 
							{'traits': ['Bio'], 'meta': ['Taskmaster','Ghost','Hyperion','Victoria Hand','Songbird'], 'label':'Bio<br>(Thunderbolts)'}, 
							{'traits': ['Mystic'], 'meta': ['Oath', 'Man-Thing', 'Blade', 'Agatha Harkness', 'Moon Knight'], 'label':'Mystic<br>(Nightstalkers)'},
							#{'traits': ['Skill'], 'meta': ['Peni Parker', 'Ghost-Spider', 'Peter B. Parker', 'Spider-Man (Noir)', 'Spider-Man (Pavitr)'], 'label':'Skill<br>(Spider Society)'}, 
							{'traits': ['Skill'], 'meta': ['Daredevil (Modern)', 'Silver Sable', 'Hit-Monkey', 'Punisher', 'Elektra'], 'label':'Skill<br>(Vigilantes)'}, 
							{'traits': ['Mutant'], 'meta': ['Gambit', 'Nightcrawler', 'Forge', 'Sunspot', 'Old Man Logan'], 'label':'Mutant<br>(X-Treme)'},
							] ],
					}

# Meta Heroes for use in Prof X Saga
tables['profx'] = { 'name': 'Prof X Saga',
					'max_others': 10,
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

# Meta Heroes for use in Prof X Saga (for sections with T17-19
tables['profx_low'] = { 'name': 'Prof X Saga (T17-19)',
					'max_others': 10,
					'sort_by': 'avail',
					'sort_char_by': 'avail',
					'traits_req': 'all',
					'summary_keys': ['stp','avail'],
					#'summary_comp': 'Professor Xavier',
					'lanes':[ [
							{'min_tier':17, 'traits': ['All'],              'label':'Nimrod:<br>Hard<br>(All T17)'},
							{'min_tier':18, 'traits': ['All'],              'label':'Nimrod:<br>Heroic<br>(All T18)'},
							{'min_tier':19, 'traits': ['All'],              'label':'Nimrod:<br>X-Treme<br>(All T19)'},
							{'min_tier':19, 'traits': ['City'],             'label':'Gladiator:<br>Hard<br>(T19 City)'},
							{'min_tier':19, 'traits': ['Global'],           'label':'Shadow King:<br>Hard<br>(T19 Global)'},
							{'min_tier':19, 'traits': ['Cosmic'],           'label':'Dark Xavier:<br>Hard<br>(T19 Cosmic)'},
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

# Meta Heroes for use in Teams
tables['teams'] = { 'name': 'Teams',
					'sort_by': 'stp',
					'span': True,
					'lanes':[ [  
							{'traits': ['AbsoluteAForce'], 'meta': ['Wasp', 'Ironheart', 'Kahhori', 'Medusa', 'Ms. Marvel (Classic)']},
							{'traits': ['Accursed'], 'meta': ['Satana', 'Hellverine', 'The Hood', 'Juggernaut', 'Mordo']},
							{'traits': ['AForce'], 'meta': ['Captain Marvel', 'Jessica Jones', 'Nico Minoru', 'Photon', 'Spider-Woman']},
							{'traits': ['AlphaFlight'], 'meta': ['Wolverine', 'Sunfire', 'Sasquatch', 'Guardian', 'Northstar']},
							{'traits': ['Annihilator'], 'meta': ['Ultimus', 'Silver Surfer', 'Gladiator', 'Gorr', 'Thanos (Endgame)']},
#							{'traits': ['Astonishing']},
							{'traits': ['Astral'], 'meta': ['Doctor Strange', 'Moondragon', 'Ancient One', 'Shadow King', 'Emma Frost (X-Men)']},
							{'traits': ['Bifrost']},
#							{'traits': ['BionicAvenger']},
							{'traits': ['BlackOrder','Thanos']},
							{'traits': ['Cabal']},
							{'traits': ['Darkhold']},
#							{'traits': ['DarkHunter']},
							{'traits': ['Deathseed']},
#							{'traits': ['Eternal']},
							{'traits': ['FantasticFourMCU'], 'meta': ['Franklin Richards', 'Invisible Woman (MCU)', 'Mister Fantastic (MCU)', 'The Thing', 'Human Torch']},
							{'traits': ['Gamma'], 'meta': ['Red Hulk', 'Hulk', 'She-Hulk', 'Abomination', 'Brawn']},
							{'traits': ['HellfireClub'], 'meta': ['Sebastian Shaw', 'Rachel Summers', 'Azazel', 'Madelyne Pryor', 'Emma Frost']},
							{'traits': ['HeroesForHire']},
							{'traits': ['HiveMind']},
							{'traits': ['Illuminati'], 'meta': ['Iron Man', 'Black Bolt', 'Mister Fantastic', 'Black Panther (Shuri)', 'Captain Britain', 'Hank Pym']},
							{'traits': ['ImmortalXMen'], 'meta': ['Jean Grey','Beast','Storm','Polaris','Cable']},
							{'traits': ['Infestation']},
							{'traits': ['InfinityWatch']},
							{'traits': ['InsidiousSix'], 'meta': ['Shocker', 'Hobgoblin', 'Scorpion', 'Vulture', 'Spider-Man (Superior)']},
							{'traits': ['Invader']},
							{'traits': ['Knowhere']},
							{'traits': ['Liberty'], 'meta': ['Captain America (Sam)','War Machine','Falcon (Joaquin)','Patriot','Peggy Carter']},
#							{'traits': ['MastersOfEvil']},
							{'traits': ['MercsForMoney']},
							{'traits': ['MightyAvenger'], 'meta': ['Hercules','Scarlet Witch','Invisible Woman','Vision','Falcon']},
							{'traits': ['NewAvenger']},
							{'traits': ['NewWarrior']},
							{'traits': ['Nightstalkers'], 'meta': ['Oath', 'Man-Thing', 'Blade', 'Agatha Harkness', 'Moon Knight']},
							{'traits': ['Orchis'], 'meta': ['Scientist Supreme', 'Lady Deathstrike', 'Sentinel', 'Omega Sentinel', 'Nimrod']},
							{'traits': ['OutOfTime']},
							{'traits': ['Pegasus']},
							{'traits': ['PhoenixForce'], 'meta': ['Phoenix', 'Omega Red (Phoenix Force)']},
#							{'traits': ['PymTech']},
							{'traits': ['Rebirth']},
#							{'traits': ['SecretDefender']},
#							{'traits': ['Shadowland']},
							{'traits': ['SpiderSociety']},
							{'traits': ['SuperiorSix']},
							{'traits': ['Starjammer'], 'meta': ['Groot','Rocket Raccoon','Havok','Lilandra','Howard The Duck']},
							{'traits': ['Thunderbolts'], 'meta': ['Taskmaster','Ghost','Hyperion','Victoria Hand','Songbird']},
#							{'traits': ['Uncanny']},
							{'traits': ['UncannyAvenger'], 'meta': ['Hercules','Falcon','Jean Grey','Beast','Storm']},
							{'traits': ['Under-<br>world'], 'meta': ['Kingpin', 'Mister Negative', 'Nobu', 'Taskmaster', 'Green Goblin']},
							{'traits': ['Undying']},
							{'traits': ['Unlimited']},
							{'traits': ['Vigilantes'], 'meta': ['Daredevil (Modern)', 'Silver Sable', 'Hit-Monkey', 'Punisher', 'Elektra']}, 
							{'traits': ['WarDog']},
							{'traits': ['WeaponX']},
							{'traits': ['XTreme']},
#							{'traits': ['Young<br>Avengers'], 'meta': ['America Chavez', 'Echo', 'Kate Bishop', 'Ms. Marvel', 'Squirrel Girl']},	
#							{'traits': ['Horseman', 'Mythic', 'Black Cat', 'Quicksilver', 'Green Goblin (Classic)', 'Spider-Man (Big Time)', 'Juggernaut (Zombie)', 'Iron Man (Zombie)'], 'label':'DPC Chars', 'inc_keys':['power', 'red'], 'max_others':0},
							] ]
					}

# Meta Heroes for use in All Characters
tables['all_chars'] = { 'name': 'All Characters',
					'max_others': 0,
					'sort_by': 'tcp',
					'inc_keys': ['power','tier','iso'],
					'inc_class': True,
					}

