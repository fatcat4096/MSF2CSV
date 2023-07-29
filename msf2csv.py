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
	"""
	quiet   = 0
	verbose = 1

	alliance_name = 'SIGMA_Infamously_Strange'
	extracted_chars = ['Player,Character,Level,Power,Gear,ISO']

	# We will look for MHTML in the same directory as this file.
	try:
		path = os.path.dirname(__file__)+os.sep
	except:
		path = '.'+os.sep

	for file in os.listdir(path):
		# Skip if not MHTML
		if file[-5:] != "mhtml":
			continue
		
		# File name or stdin/stdout?
		mht = open(path+file, "rb")

		if not quiet:
			sys.stderr.write("Unpacking "+file+"...\n")

		# Read entire MHT archive -- it's a multipart(/related) message.
		a = email.message_from_bytes(mht.read()) 
		
		parts = a.get_payload() # Multiple parts, usually?
		if not type(parts) is list:
			parts = [a] # Single 'str' part, so convert to list.
																			
		# Look for the 'character' file among the file parts.
		for p in parts: # walk() for a tree, but I'm guessing MHT is never nested?
			ct = p.get_content_type() # String coerced to lower case of the form maintype/subtype, else get_default_type().			
			fp = p.get("content-location") or "index.html" # File path. Expecting root HTML is only part with no location.

			# Ignore the path, focus on the filename.
			decoded_file = fp.split('/')[-1]

			# Only the characters.html file has relevant data.
			if decoded_file == 'characters':
				if verbose:
					sys.stderr.write("Parsing %s to %s, %d bytes...\n" % (ct, fp, len(p.get_payload())))
				soup = BeautifulSoup(p.get_payload(decode=True), 'html.parser')

				player = soup.find('div', attrs = {'class':'player-name is-italic'}).text.strip()
				chars  = soup.findAll('li', attrs = {'class':'character'})

				for char in chars:
					toon_name = char.find('h4').text.strip()
					if not toon_name:
						pass
					
					toon = char.find('div', attrs = {'id':'toon-stats'})
					
					# Stats available only if character is recruited.
					if toon:
						stats = toon.findAll('div', attrs = {'class':''})
						level = stats[0].text.strip().split()[1]
						power = ''.join(stats[1].text.strip().split(','))
						
						# Available, but not useful for Raid Planning
						"""
						stars = str(toon.find('span'))
						redStars = str(stars.count('red'))
						yelStars = str(stars.count('red') + stars.count('orange'))
						
						abilities = toon.findAll('div', attrs = {'class':'ability-level'})
						basic   = str(abilities[0]).split('-')[3][1]
						special = str(abilities[1]).split('-')[3][1]
						ult = '0'
						if len(abilities)==4:
							ult = str(abilities[-2]).split('-')[3][1]
						passive = str(abilities[-1]).split('-')[3][1]
						"""
						
						gear = char.find('div',attrs={'class':'gear-tier-ring'})
						tier = str(gear).split('"g')[2].split('"')[0]
					
						iso = str(char.find('div',attrs={'class','iso-wrapper'}))
						pips = 0
						if iso.find('-pips-') != -1:
							pips = int(iso.split('-pips-')[1][0])
						if iso.find('blue') != -1:
							pips += 5
						pips = str(pips)

						extracted_chars.append(','.join([player,toon_name,level,power,tier,pips]))

					# Entries for Heroes not yet collected, no name on final entry for page.
					elif toon_name:
						extracted_chars.append(','.join([player,toon_name,'','','','']))

	# Write the output to a CSV in the local directory.	
	open(path+alliance_name+datetime.datetime.now().strftime("-%Y%m%d-%H%M")+'.csv', 'w').write('\n'.join(extracted_chars))


if __name__ == "__main__":
	main() # Just run myself

