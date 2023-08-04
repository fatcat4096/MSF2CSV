#!/usr/bin/env python3
# Encoding: UTF-8
"""msf2csv.py
Unpacks all MHTML files in the local directory. Searches the MHTML tree to find the character file from MSF.GG. 
Scrapes this file for Roster info (player name, character stats, etc.) and adds everything into a single CSV for the Alliance.
Use pivot tables in a Spreadsheet app to format table with the information relevant to your purpose -- power, gear tier, or ISO 

Derived from mhtifier.py code by Ilan Irad
See: https://github.com/Modified/MHTifier
"""

# Standard library modules do the heavy lifting. Ours is all simple stuff.
import email, email.message
import os
from bs4 import BeautifulSoup


# We will look for MHTML in the same directory as this file.
try:
	path = os.path.dirname(__file__)+os.sep
# Sourcing locally, no __file__ object.
except:
	path = '.'+os.sep


def process_mhtml(path=path):

	processed_players = {}
	char_stats = {}
	traits_from_char = {}
	
	for file in os.listdir(path):
		# Skip if not MHTML
		if file[-5:] != "mhtml":
			continue
		
		# Open the .mhtml file for reading. 
		mht = open(path+file, "rb")
		print("Unpacking "+file+"...")

		# Read entire MHT archive -- it's a multipart(/related) message.
		a = email.message_from_bytes(mht.read()) 
		
		parts = a.get_payload()
		if not type(parts) is list:
			parts = [a] 		# Single 'str' part, so convert to list.
																			
		# Look for the 'character' file among the file parts.
		for part in parts: 
			content_type = part.get_content_type() # String coerced to lower case of the form maintype/subtype, else get_default_type().			
			file_path    = part.get("content-location") or "index.html" # File path. Expecting root HTML is only part with no location.

			# Ignore the path, focus on the filename.
			decoded_file = file_path.split('/')[-1]

			# Only the characters.html file has relevant data.
			if decoded_file == 'characters':
				soup = BeautifulSoup(part.get_payload(decode=True), 'html.parser')

				player_name = soup.find('div', attrs = {'class':'player-name is-italic'}).text.strip()

				#Skip file if player info already processed.
				if player_name in processed_players:
					continue

				print("Parsing %s to %s, %d bytes...found %s" % (content_type, file_path, len(part.get_payload()), player_name))

				processed_chars  = {}
				
				chars  = soup.findAll('li', attrs = {'class':'character'})

				for char in chars:
					
					# If no char_name defined, last entry on page. Skip.
					char_name = char.find('h4').text.strip()
					if not char_name:
						pass

					# Keep the path to the image for each character.
					char_portrait = char.find('img',attrs={'class':'portrait is-centered'}).get('src')

					char_stats.setdefault(char_name,{})
					char_stats[char_name].setdefault('portrait',char_portrait)
					
					# Stats available only if character is recruited.
					toon_stats = char.find('div', attrs = {'id':'toon-stats'})

					if toon_stats:
						# Decode Level and Power
						stats = toon_stats.findAll('div', attrs = {'class':''})
						level = stats[0].text.strip().split()[1]
						power = ''.join(stats[1].text.strip().split(','))

						set_min_max(char_stats,char_name,'level',level)
						set_min_max(char_stats,char_name,'power',power)
						
						# Decode Yellow and Red Stars
						stars = str(toon_stats.find('span'))
						redStars = str(stars.count('red'))
						yelStars = str(stars.count('red') + stars.count('orange'))
						
						# Decode Abilities
						abilities = toon_stats.findAll('div', attrs = {'class':'ability-level'})
						basic   = str(abilities[0]).split('-')[3][1]
						special = str(abilities[1]).split('-')[3][1]
						ult = '0'
						if len(abilities)==4:
							ult = str(abilities[-2]).split('-')[3][1]
						passive = str(abilities[-1]).split('-')[3][1]
						
						# Decode Gear Tier
						gear = char.find('div',attrs={'class':'gear-tier-ring'})
						tier = str(gear).split('"g')[2].split('"')[0]

						set_min_max(char_stats,char_name,'tier',tier)
					
						# Decode ISO Level
						iso_info = str(char.find('div',attrs={'class','iso-wrapper'}))
						iso = 0
						if iso_info.find('-pips-') != -1:
							iso = int(iso_info.split('-pips-')[1][0])
						if iso_info.find('blue') != -1:
							iso += 5
						iso = str(iso)

						set_min_max(char_stats,char_name,'iso',iso)

						processed_chars[char_name] = {'level':level,'power':power,'tier':tier,'iso':iso, 'yelStars':yelStars, 'redStars':redStars, 'basic':basic, 'special':special, 'ult':ult, 'passive':passive}

					# Entries for Heroes not yet collected, no name on final entry for page.
					elif char_name:
						processed_chars[char_name] = {'level':'0','power':'0','tier':'0','iso':'0', 'yelStars':'0', 'redStars':'0', 'basic':'0', 'special':'0', 'ult':'0', 'passive':'0'}

					# Add these chars to our list of processed players.
					processed_players[player_name] = processed_chars

	return char_stats,processed_players


# Keep track of min/max for each stat, for each hero individually and collectively, across all of the players found

def set_min_max(char_stats,char_name,stat,value):
	value = int(value)

	# Find min/max stats for this specific toon.
	char_stats[char_name].setdefault(stat,{'min':[value-1,0][stat=='iso'],'max':value})

	if value<char_stats[char_name][stat]['min']:
		char_stats[char_name][stat]['min'] = value

	if value>char_stats[char_name][stat]['max']:
		char_stats[char_name][stat]['max'] = value

	# Do the same bookkeeping across all toons.
	char_stats.setdefault('all',{})

	char_stats['all'].setdefault(stat,{'min':[value-1,0][stat=='iso'],'max':value})

	if value<char_stats['all'][stat]['min']:
		char_stats['all'][stat]['min'] = value
	if value>char_stats['all'][stat]['max']:
		char_stats['all'][stat]['max'] = value

