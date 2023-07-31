#!/usr/bin/env python3
# Encoding: UTF-8
"""msf2csv.py
Unpacks all MHTML files in the local directory. Searches the MHTML tree to find the character file from MSF.GG. 
Scrapes this file for Roster info (player name, character stats, etc.) and adds everything into a single CSV for the Alliance.
Use pivot tables in a Spreadsheet app to format table with the information relevant to your purpose -- power, gear tier, or ISO 
Derived from mhtifier.py code by Ilan Irad -- https://github.com/Modified/MHTifier
"""

# Standard library modules do the heavy lifting. Ours is all simple stuff.
import email, email.message
import os
import sys
import datetime
from bs4 import BeautifulSoup

# Just do it.
def main():
	"""
	History: 
		MSF.gg used to have a CSV download option which made it easy to load up full roster stats for everyone in the alliance. 
		During a recent "upgrade" this button was removed. Likely a temporary issue, but it still leaves Alliance leaders in a bad spot.
		This is a rudimentary solution to the problem. Takes more work, but it does produce a good result.
		Feel free to provide feedback, questions, comments, etc. My username is "fatcat4096" on Discord. 
	
	Requirements:
		1. Install Python
		2. Install Beautiful Soup 4 -- 'pip install beautifulsoup4

	Usage:
		1. From the MSF website Alliance view, navigate into the Roster page for each member of your alliance.
		2. On each member's Roster page, right click on the background and Save As a "Webpage, single file (*.mhtml)"
		3. Actual name of the MHTML file is not critical. Player name for the CSV file is taken from the HTML.
		4. Double click on the mht2csv.py file. 
		
	Output:
		Currently, the script creates multiple output files. Keep or delete whichever you want.
			1. One copy of the CSV in the original format which used to be downloadable from MSF.gg
			2. One version of a pivot table showing Power for each character for each of the Alliance members
			3. One version of a pivot table showing Power and Gear Tier (for planning Gamma 4.5, for example)
			4. One version of a pivot table showing Power and ISO (for planning Incursion Raids)
			5. One version with all three data points.
			
	"""
	quiet   = 0
	verbose = 1

	alliance_name = 'SIGMA_Infamously_Strange'
	processed_players = {}

	# FUTURE FEATURE: char_stats - build up a dict with all the char names and min/max for each stat as we find them in the MHTML. We will eventually use these stats for Heat Maps / Coloring in the HTML.
	# FUTURE FEATURE: char_list shouldn't change from one player to the next. So after all MHTML processed, pull the char_list from char_stats.keys and sort it to use everywhere.

	# We will look for MHTML in the same directory as this file.
	try:
		path = os.path.dirname(__file__)+os.sep
	# Sourcing locally, no __file__ object.
	except:
		path = '.'+os.sep

	for file in os.listdir(path):
		# Skip if not MHTML
		if file[-5:] != "mhtml":
			continue
		
		# Open the .mhtml file for reading. 
		mht = open(path+file, "rb")

		if not quiet:
			sys.stderr.write("Unpacking "+file+"...\n")

		# Read entire MHT archive -- it's a multipart(/related) message.
		a = email.message_from_bytes(mht.read()) 
		
		parts = a.get_payload() # Multiple parts, usually?
		if not type(parts) is list:
			parts = [a] # Single 'str' part, so convert to list.
																			
		# Look for the 'character' file among the file parts.
		for part in parts: 
			content_type = part.get_content_type() # String coerced to lower case of the form maintype/subtype, else get_default_type().			
			file_path    = part.get("content-location") or "index.html" # File path. Expecting root HTML is only part with no location.

			# Ignore the path, focus on the filename.
			decoded_file = file_path.split('/')[-1]

			# Only the characters.html file has relevant data.
			if decoded_file == 'characters':
				if verbose:
					sys.stderr.write("Parsing %s to %s, %d bytes...\n" % (content_type, file_path, len(part.get_payload())))
				soup = BeautifulSoup(part.get_payload(decode=True), 'html.parser')

				player_name = soup.find('div', attrs = {'class':'player-name is-italic'}).text.strip().capitalize()

				#Skip file if player info already processed.
				if player_name in processed_players:
					continue

				processed_chars  = {}
				
				chars  = soup.findAll('li', attrs = {'class':'character'})

				for char in chars:
					
					# If no char_name defined, last entry on page. Skip.
					char_name = char.find('h4').text.strip()
					if not char_name:
						pass

					# FUTURE FEATURE: Lookup Table to Rewrite Character Names into Common Names
					
					toon_stats = char.find('div', attrs = {'id':'toon-stats'})
					
					# Stats available only if character is recruited.
					if toon_stats:
						stats = toon_stats.findAll('div', attrs = {'class':''})
						level = stats[0].text.strip().split()[1]
						power = ''.join(stats[1].text.strip().split(','))
						
						stars = str(toon_stats.find('span'))
						redStars = str(stars.count('red'))
						yelStars = str(stars.count('red') + stars.count('orange'))
						
						abilities = toon_stats.findAll('div', attrs = {'class':'ability-level'})
						basic   = str(abilities[0]).split('-')[3][1]
						special = str(abilities[1]).split('-')[3][1]
						ult = '0'
						if len(abilities)==4:
							ult = str(abilities[-2]).split('-')[3][1]
						passive = str(abilities[-1]).split('-')[3][1]
						
						gear = char.find('div',attrs={'class':'gear-tier-ring'})
						tier = str(gear).split('"g')[2].split('"')[0]
					
						iso_info = str(char.find('div',attrs={'class','iso-wrapper'}))
						iso = 0
						if iso_info.find('-pips-') != -1:
							iso = int(iso_info.split('-pips-')[1][0])
						if iso_info.find('blue') != -1:
							iso += 5
						iso = str(iso)

						processed_chars[char_name] = {'level':level,'power':power,'tier':tier,'iso':iso, 'yelStars':yelStars, 'redStars':redStars, 'basic':basic, 'special':special, 'ult':ult, 'passive':passive}

					# Entries for Heroes not yet collected, no name on final entry for page.
					elif char_name:
						processed_chars[char_name] = {'level':'0','power':'0','tier':'0','iso':'0', 'yelStars':'0', 'redStars':'0', 'basic':'0', 'special':'0', 'ult':'0', 'passive':'0'}

					# Add these chars to our list of processed players.
					processed_players[player_name] = processed_chars

	# Write the basic output to a CSV in the local directory.
	keys = ['level','power','tier','iso','yelStars','redStars','basic','special','ult','passive']
	csv_file = ['Player,Character,']+','.join([key.capitalize() for key in keys])]
	player_list = list(processed_players.keys())
	player_list.sort()
	for player_name in player_list:
		processed_chars = processed_players[player_name]
		char_list = list(processed_chars.keys())
		char_list.sort()
		for char_name in char_list:
			csv_file.append(','.join([player_name, char_name] + [processed_chars[char_name][key] for key in keys]))

	# Original CSV format, all info included. 
	open(path+alliance_name+datetime.datetime.now().strftime("-orig-%Y%m%d-%H%M.csv"), 'w').write('\n'.join(csv_file))

	# Pivot table with Power only. 
	csv_file = create_pivot_table(processed_players)
	open(path+alliance_name+datetime.datetime.now().strftime("-pivot-power-%Y%m%d-%H%M.csv"), 'w').write('\n'.join(csv_file))

	# Incursion focused pivot table with Power and ISO. 
	csv_file = create_pivot_table(processed_players,['power','iso'])
	open(path+alliance_name+datetime.datetime.now().strftime("-pivot-incursion-%Y%m%d-%H%M.csv"), 'w').write('\n'.join(csv_file))

	# Gamma focused pivot table with Power and Gear Tier. 
	csv_file = create_pivot_table(processed_players,['power','tier'])
	open(path+alliance_name+datetime.datetime.now().strftime("-pivot-gamma-%Y%m%d-%H%M.csv"), 'w').write('\n'.join(csv_file))

	# Full pivot table with all three. 
	csv_file = create_pivot_table(processed_players,['power','tier','iso'])
	open(path+alliance_name+datetime.datetime.now().strftime("-pivot-all-%Y%m%d-%H%M.csv"), 'w').write('\n'.join(csv_file))



def create_pivot_table(processed_players, keys=['power']):

	# FUTURE FEATURE: Convert this output to HTML with clean formating and colspan for char_names across the top of multiple columns if multiple keys provided.
	# FUTURE FEATURE: Allow filters to be passed in and character inclusion to be based upon whether a character has any of those tags. 
	# FUTURE FEATURE: Define Lanes and Sections that can be processed individually, using the filters. So requesting a type='gamma' raid would generate four lanes with filters for each section. Incursion would generate one lane, with filters for each origin matching each section.
	# FUTURE FEATURE: After one each run through the files provided, output a text file named alliance_members.txt which has a list of all the members and definitions for Strike Teams 1-3. If edited to place those members in specific Strike Teams, those Strike teams should be used to group output rows.

	# Write an Power-only pivot-table presentation to a CSV in the local directory.	
	player_list = list(processed_players.keys())
	player_list.sort()

	# Same char_list should be present in every entry. 
	processed_chars = processed_players[player_list[0]]

	char_list = list(processed_chars.keys())
	char_list.sort()
	
	# Write the top lines - char list and then value descriptors
	csv_file  = [','.join([''] + [ x+','*(len(keys)-1) for x in char_list])]

	# Add a line with value descriptors only if more than one item requested.
	if len(keys)>1:
		csv_file += [','.join([''] + [key.capitalize() for key in keys]*len(char_list))]

	# write each of the lines, one player per line.
	for player_name in player_list:
		processed_chars = processed_players[player_name]
		csv_file.append(','.join([player_name]+ [processed_chars[char_name][key] for char_name in char_list for key in keys] ))

	return csv_file


if __name__ == "__main__":
	main() # Just run myself

