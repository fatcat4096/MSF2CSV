#!/usr/bin/env python3
# Encoding: UTF-8
"""extract_traits.py
Quick hack to pull live trait data from MSF.gg
"""


import urllib.request


# Update the Character Trait information in alliance_info using the latest info from website.
def add_extracted_traits(alliance_info):

	updated = False

	# Temporary, rename 'extracted_traits' as 'traits'.
	if 'extracted_traits' in alliance_info:
		alliance_info['traits'] = alliance_info.pop('extracted_traits')
		updated = True

	# Update with traits missing from JSON file.
	traits  = alliance_info.setdefault('traits',{})
	updated = update_traits(traits) or updated
		
	# If the old trait file isn't being used, traits needs to be updated.
	if not traits or alliance_info.get('trait_file') not in alliance_info.setdefault('scripts',[]):

		for script in alliance_info.get('scripts'):
			traits = extract_traits(script)

			# If this file was correctly parsed, store this new trait file.
			if not traits:
				continue
				
			print ("Found traits info in",script)

			# Remember which script was the valid trait file
			alliance_info['trait_file'] = script
			alliance_info['traits']     = traits
			updated = True
			break

	return updated


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

	# Currently includes: Alpha Flight, Cabal, Hive-Mind, MercsForMoney, OutOfTime, and SpiderSociety
	if 'AlphaFlight' not in extracted_traits:

		manual_traits =	{
						# Alpha Flight
						'Sunfire'            :['AlphaFlight'],
						'Wolverine'          :['AlphaFlight'],
						'Guardian'           :['AlphaFlight','Hero','Global','Tech','Brawler'],
						'Northstar'          :['AlphaFlight','Hero','Global','Mutant','Controller'],
						'Sasquatch'          :['AlphaFlight','Hero','Global','Bio','Protector'],
						# Cabal
						'Namor'              :['Cabal'],
						'Iron Patriot'       :['Cabal','Global','Villain','Tech','Blaster'],
						'The Leader'         :['Cabal','Global','Villain','Bio','Support','Gamma'],
						# Hive-Mind
						'Carnage'            :['HiveMind'],
						'Venom'              :['HiveMind'],
						'Void Knight'        :['HiveMind','Bio','SpiderVerse','Symbiote','Hero','Cosmic','Support'],
						'Gwenom'             :['HiveMind','Bio','SpiderVerse','Symbiote','Hero','City','Brawler'],
						'Red Goblin'         :['HiveMind','Bio','SpiderVerse','Symbiote','Villain','City','Protector'],
						# Mercs For Money
						'Deadpool'           :['MercsForMoney'],
						'Deathpool'          :['MercsForMoney'], 
						'Daken'              :['MercsForMoney','Mutant','Mercenary','Global','Villain','Controller'],
						'Old Man Logan'      :['MercsForMoney','Mutant','Mercenary','Global','Hero','Controller','Xmen','Legendary'],
						'Pandapool'          :['MercsForMoney','Mutant','Mercenary','Global','Hero','Protector'],
						# Out of Time
						'Captain America'    :['OutOfTime'],
						'Captain Carter'     :['OutOfTime'],
						'Black Knight'       :['OutOfTime','Hero','Global','Skill','Protector'],
						'Starbrand'          :['OutOfTime','Hero','Global','Mystic','Brawler'],
						'Cosmic Ghost Rider' :['OutOfTime','Hero','Cosmic','Mystic','Controller',],
						# Spider Society
						'Ghost-Spider'       :['SpiderSociety','Skill'],
						'Spider-Man (Noir)'  :['SpiderSociety','Skill'],
						'Peni Parker'        :['SpiderSociety','SpiderVerse','Hero','City','Skill','Tech','Protector',],
						'Peter B. Parker'    :['SpiderSociety','SpiderVerse','Hero','City','Skill','Bio','Support'],
						'Spider-Man (Pavitr)':['SpiderSociety','SpiderVerse','Hero','City','Skill','Bio','Brawler'],
						# Mephisto
						'Mephisto'           :['Mythic','Villain','Cosmic','Mystic','Protector'],
						# Spider-Verse
						'Spider-Woman'       :['SpiderVerse'],
						# Weapon X
						'X23'                :['WeaponX'],
						}

		# Parse information into the needed structure.
		for char in manual_traits:
			for trait in manual_traits[char]:
				extracted_traits.setdefault(trait,{})[char]=1
				extracted_traits[trait]
	
		if 'AlphaStar' in extracted_traits:
			del extracted_traits['AlphaStar']
	
		# Indicate extracted_traits has been Updated.
		return True