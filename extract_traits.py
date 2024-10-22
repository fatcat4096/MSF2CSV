#!/usr/bin/env python3
# Encoding: UTF-8
"""extract_traits.py
Quick hack to pull live trait data from MSF.gg
"""


import urllib.request


# Download and return fresh trait information using the latest info from website.
def extract_traits_from_scripts(scripts):

	traits = {}

	for script in scripts:
		traits = extract_traits(script)

		# If this file parsed correctly, stop looking.
		if traits:
			break

	return traits



# Parse the provided js file to hopefully find trait information.
def extract_traits(file=''):

	# load the indicated script, MSF.gg will respond with a 404 page if not available anymore.
	page = urllib.request.urlopen('https://marvelstrikeforce.com'+file)
	
	buffer = str(page.read())

	extracted_traits = {}

	start_idx = 0
	
	# Loop through the file looking for hero definitions, signaled by 'Playable'
	while buffer.find('Playable:',start_idx+1) != -1:
		# Find first character
		
		start_idx = buffer.find('Playable:',start_idx+1)
		
		# Look backward to find the name.
		char_idx = buffer.rfind('Name:"',0,start_idx)+6
		char_end = buffer.find('"',char_idx)
		char     = buffer[char_idx:char_end]
		
		# Look forward to find the traits.
		traits_idx = buffer.find('traits:',start_idx)+7
		traits_end = buffer.find(']',traits_idx)+1
		traits = eval(buffer[traits_idx:traits_end])

		# Parse information into the needed structure.
		for trait in traits:
			extracted_traits.setdefault(trait,{})
			extracted_traits[trait][char]=1

	# Only add extra info if we already have found data in this file.
	if extracted_traits: 

		# Update parsed data with traits missing from JSON file.
		update_traits(extracted_traits)

		# Final edits. Certain tags are not complete
		# e.g. Avengers, Defenders, and Xmen also need related heroes merged.

		avengers = extracted_traits['Avenger']
		avengers.update(extracted_traits['BionicAvenger'])
		avengers.update(extracted_traits['SecretAvenger'])
		avengers.update(extracted_traits['Wave1Avenger'])
		avengers.update(extracted_traits['NewAvenger'])
		avengers.update(extracted_traits['YoungAvenger'])

		xmen = extracted_traits['Xmen']
		xmen.update(extracted_traits['Astonishing'])
		xmen.update(extracted_traits['Uncanny'])
		xmen.update(extracted_traits['Unlimited'])

		defender = extracted_traits['Defender']
		defender.update(extracted_traits['SecretDefender'])

	return extracted_traits



# Manually add entries for NEW or UPDATED heroes which aren't yet included in JSON file.
def update_traits(extracted_traits):

	if extracted_traits and 'MsfOriginal' not in extracted_traits:

		manual_traits =	{
						# Ares
						'Ares'                  :['Villain','Global','Mystic','Protector'],
						# Alpha Flight
						'Sunfire'               :['AlphaFlight'],
						'Wolverine'             :['AlphaFlight'],
						'Guardian'              :['AlphaFlight','Hero','Global','Tech','Brawler'],
						'Northstar'             :['AlphaFlight','Hero','Global','Mutant','Controller'],
						'Sasquatch'             :['AlphaFlight','Hero','Global','Bio','Protector'],
						# Annihilator
						'Ultimus'               :['Annihilator'],
						'Silver Surfer'         :['Annihilator'],
						'Gladiator'             :['Annihilator','Villain','Cosmic','Bio','Protector'],
						'Gorr'                  :['Annihilator','Villain','Cosmic','Bio','Controller'],
						'Thanos (Endgame)'      :['Annihilator','Villain','Cosmic','Skill','Brawler'],
						# Cabal
						'Namor'                 :['Cabal'],
						'Iron Patriot'          :['Cabal','Global','Villain','Tech','Blaster'],
						'The Leader'            :['Cabal','Global','Villain','Bio','Support','Gamma'],
						# Epic
						'Iron Man (Zombie)'     :['Epic'],
						'Juggernaut (Zombie)'   :['Epic'],
						'Scarlet Witch (Zombie)':['Epic','Villain','Global','Bio','Mystic','Support','Undying'],
						# Hive-Mind
						'Carnage'               :['HiveMind'],
						'Venom'                 :['HiveMind'],
						'Void Knight'           :['HiveMind','Bio','SpiderVerse','Symbiote','Hero','Cosmic','Support'],
						'Gwenom'                :['HiveMind','Bio','SpiderVerse','Symbiote','Hero','City','Brawler'],
						'Red Goblin'            :['HiveMind','Bio','SpiderVerse','Symbiote','Villain','City','Protector'],
						# Illuminati
						'Iron Man'              :['Illuminati'],
						'Black Bolt'            :['Illuminati'],
						'Mister Fantastic'      :['Illuminati'],
						'Black Panther (Shuri)' :['Illuminati','Hero','Global','Mystic','Controller','Wakandan'], 
						'Captain Britain'       :['Illuminati','Hero','Global','Mystic','Protector','Epic'],
						'Hank Pym'              :['Illuminati','Hero','Global','Tech','Support','PymTech','Avenger'],
						# Mercs For Money
						'Deadpool'              :['MercsForMoney'],
						'Deathpool'             :['MercsForMoney','MsfOriginal'], 
						'Daken'                 :['MercsForMoney','Mutant','Mercenary','Global','Villain','Controller'],
						'Old Man Logan'         :['MercsForMoney','Mutant','Mercenary','Global','Hero','Controller','Xmen','Legendary'],
						'Pandapool'             :['MercsForMoney','Mutant','Mercenary','Global','Hero','Protector'],
						# Morbius
						'Morbius'               :['Vampire'],
						# MSF Original
						'Kestrel'               :['MsfOriginal'],
						'Spider-Weaver'         :['MsfOriginal'],
						'Vahl'                  :['MsfOriginal'],
						# Nightstalkers
						'Agatha Harkness'       :['Nightstalker'],
						'Moon Knight'           :['Nightstalker'],
						'Blade'                 :['Nightstalker','Mystic','Hero','Vampire','City','Brawler'],
						'Man-Thing'             :['Nightstalker','Mystic','Hero','Global','Protector'],
						'Oath'                  :['Nightstalker','Mystic','Hero','Vampire','City','Controller'],
						# Odin
						'Odin'                  :['Hero','Cosmic','Mystic','Blaster','Asgard','Mythic'],
						# Orchis
						'Lady Deathstrike'      :['Orchis'],
						'Scientist Supreme'     :['Orchis'],
						'Nimrod'                :['Orchis','Villain','Tech','Global','Blaster'],
						'Sentinel'              :['Orchis','Villain','Tech','Global','Protector'],
						'Omega Sentinel'        :['Orchis','Villain','Tech','Global','Support'],
						# Out of Time
						'Captain America'       :['OutOfTime'],
						'Captain Carter'        :['OutOfTime'],
						'Black Knight'          :['OutOfTime','Hero','Global','Skill','Protector'],
						'Starbrand'             :['OutOfTime','Hero','Global','Mystic','Brawler'],
						'Cosmic Ghost Rider'    :['OutOfTime','Hero','Cosmic','Mystic','Controller',],
						# Spider Society
						'Ghost-Spider'          :['SpiderSociety','Skill'],
						'Spider-Man (Noir)'     :['SpiderSociety','Skill'],
						'Peni Parker'           :['SpiderSociety','SpiderVerse','Hero','City','Skill','Tech','Protector',],
						'Peter B. Parker'       :['SpiderSociety','SpiderVerse','Hero','City','Skill','Bio','Support'],
						'Spider-Man (Pavitr)'   :['SpiderSociety','SpiderVerse','Hero','City','Skill','Bio','Brawler'],
						# Mephisto
						'Mephisto'              :['Mythic','Villain','Cosmic','Mystic','Protector'],
						# Spider-Verse
						'Spider-Woman'          :['SpiderVerse'],
						# Weapon X
						'X-23'                  :['WeaponX'],
						}

		# Parse information into the needed structure.
		for char in manual_traits:
			for trait in manual_traits[char]:
				# Report if we can remove some of these manual definitions.
				if extracted_traits.setdefault(trait,{}).get(char):
					print (f"No longer need def for extracted_traits['{char}']['{trait}']")
				else:
					extracted_traits[trait][char]=1
