#!/usr/bin/env python3
# Encoding: UTF-8
"""extract_traits.py
Quick hack to pull live trait data from MSF.gg
"""

import urllib.request


# Update the Character Trait information using the latest info from website.
def get_extracted_traits(alliance_info):

	# If the old trait file isn't being used, extracted_traits needs to be updated.
	if 'trait_file' not in alliance_info or alliance_info['trait_file'] not in alliance_info['scripts']:

		for script in alliance_info['scripts']:
			extracted_traits = extract_traits(script)

			# If this file was correctly parsed, store this new trait file.
			if extracted_traits:
				print ("Found extracted traits in",script)

				# Remember which script was the valid trait file
				alliance_info['trait_file'] = script
				alliance_info['extracted_traits'] = extracted_traits
				break


# Parse the provided js file to hopefully find trait information.
def extract_traits(file=''):

	# load the indicated script, MSF.gg will respond with a 404 page if not available anymore.
	page = urllib.request.urlopen('https://marvelstrikeforce.com'+file)
	buffer = str(page.read())

	extracted_traits = {}

	try:
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
			traits     = eval(buffer[traits_idx:traits_end])

			# Parse information into the needed structure.
			for trait in traits:
				extracted_traits.setdefault(trait,{})
				extracted_traits[trait][char]=1

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

	# Problem parsing file indicates filename has likely changed. 
	except:
		pass
		
	return extracted_traits
