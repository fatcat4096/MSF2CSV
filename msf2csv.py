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
			2. HTML for a table showing Power for each character for each of the Alliance members
			3. HTML for a table showing Power and Gear Tier (for planning Gamma 4.5, for example)
			4. HTML for a table showing Power and ISO (for planning Incursion Raids)
			5. HTML for a version with all three data points.
			
	"""
	quiet   = 0
	verbose = 1

	alliance_name = 'SIGMA_Infamously_Strange'
	processed_players = {}
	char_stats = {}
	
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

				player_name = soup.find('div', attrs = {'class':'player-name is-italic'}).text.strip().title()

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

	# Pull char_list from char_stats.
	char_list = list(char_stats.keys())
	char_list.sort()	

	filename = path+alliance_name+datetime.datetime.now().strftime("-%Y%m%d-%H%M-")

	# Write the basic output to a CSV in the local directory.
	keys = ['level','power','tier','iso','yelStars','redStars','basic','special','ult','passive']
	csv_file = ['Player,Character,'+','.join([key.title() for key in keys])]
	player_list = list(processed_players.keys())
	player_list.sort()
	for player_name in player_list:
		processed_chars = processed_players[player_name]
		for char_name in char_list:
			csv_file.append(','.join([player_name, char_name] + [processed_chars[char_name][key] for key in keys]))

	# Original CSV format, all info included. 
	open(filename+"orig.csv"), 'w').write('\n'.join(csv_file))

	# Pivot table with Power only. 
	html_file = create_pivot_table(processed_players,char_stats)
	open(filename+"pivot-power.html"), 'w').write(html_file)

	# Incursion focused pivot table with Power and ISO. 
	html_file = create_pivot_table(processed_players,char_stats,['power','iso'])
	open(filename+"pivot-incursion.html"), 'w').write(html_file)

	# Gamma focused pivot table with Power and Gear Tier. 
	html_file = create_pivot_table(processed_players,char_stats,['power','tier'])
	open(filename+"pivot-gamma.html"), 'w').write(html_file)

	# Full pivot table with all three. 
	html_file = create_pivot_table(processed_players,char_stats,['power','tier','iso'])
	open(filename+"pivot-all.html"), 'w').write(html_file)


def set_min_max(char_stats,char_name,stat,value):
	value = int(value)
	char_stats.setdefault(char_name,{})
	char_stats[char_name].setdefault(stat,{'min':[value-1,0][stat=='iso'],'max':value})
	if value<char_stats[char_name][stat]['min']:
		char_stats[char_name][stat]['min'] = value
	if value>char_stats[char_name][stat]['max']:
		char_stats[char_name][stat]['max'] = value


def get_value_color(char_stats,char_name,stat,value):
	value = int(value)
	char_stats.setdefault(char_name,{})
	char_stats[char_name].setdefault(stat,{'min':value-1,'max':value})

	if not value:
		return 'White'

	# Linear gradient from red, to yellow, to green.
	color_scale = ['#ff2d00', '#fe3100', '#fe3500', '#fe3900', '#fe3e00', '#fe4200', '#fe4600', '#fd4b00', '#fd4f00', '#fd5300', '#fd5700', '#fd5c00', '#fd6000', '#fc6400', '#fc6900', '#fc6d00', '#fc7100', '#fc7500', '#fc7a00', '#fb7e00', '#fb8200', '#fb8700', '#fb8b00', '#fb8f00', '#fb9300', '#fa9800', '#fa9c00', '#faa000', '#faa500', '#faa900', '#faad00', '#f9b100', '#f9b600', '#f9ba00', '#f9be00', '#f9c300', '#f9c700', '#f8cb00', '#f8cf00', '#f8d400', '#f8d800', '#f8dc00', '#f8e100', '#f7e500', '#f7e900', '#f7ed00', '#f7f200', '#f7f600', '#f7fa00', '#f7ff00', '#f7ff00', '#f2fe00', '#eefd00', '#eafc01', '#e5fb01', '#e1fa01', '#ddfa02', '#d9f902', '#d4f803', '#d0f703', '#ccf603', '#c8f604', '#c3f504', '#bff405', '#bbf305', '#b7f205', '#b2f106', '#aef106', '#aaf006', '#a5ef07', '#a1ee07', '#9ded08', '#99ed08', '#94ec08', '#90eb09', '#8cea09', '#88e90a', '#83e80a', '#7fe80a', '#7be70b', '#77e60b', '#72e50c', '#6ee40c', '#6ae40c', '#65e30d', '#61e20d', '#5de10d', '#59e00e', '#54df0e', '#50df0f', '#4cde0f', '#48dd0f', '#43dc10', '#3fdb10', '#3bdb11', '#37da11', '#32d911', '#2ed812', '#2ad712', '#26d713', '#26d713']

	min = char_stats[char_name][stat]['min']
	max = char_stats[char_name][stat]['max']

	color_percent = int((value-min)/(max-min)*100)
	#print (char_name, char_stats[char_name], max, min, value, color_percent)
	return color_scale[color_percent]
	

def create_pivot_table(processed_players, char_stats, keys=['power']):

	# FUTURE: Allow filters to be passed in and character inclusion to be based upon whether a character has any of those tags. 
	# FUTURE: Define Lanes and Sections that can be processed individually, using the filters. So requesting a type='gamma' raid would generate four lanes with filters for each section. Incursion would generate one lane, with filters for each origin matching each section.
	# FUTURE: After one each run through the files provided, output a text file named alliance_members.txt which has a list of all the members and definitions for Strike Teams 1-3. If edited to place those members in specific Strike Teams, those Strike teams should be used to group output rows.

	# Pull char_list from char_stats
	char_list = list(char_stats.keys())
	char_list.sort()	

	# Get the list of Alliance Members we will iterate through as rows.	
	player_list = list(processed_players.keys())
	player_list.sort()

	# Write the top lines - char list and then value descriptors
	html_file  = '<table border="1" class="dataframe" style="font-family:verdana">\n'
	html_file += '  <thead>\n'
	html_file += '    <tr style="text-align: center;">\n'
	html_file += '      <th style="background-color:LightBlue;">'+['Alliance member',''][len(keys)>1]+'</th>\n'

	for char in char_list:
		html_file += '      <th style="background-color:LightBlue;" colspan="'+str(len(keys))+'">'+char+'</th>\n'
	
	html_file += '    </tr>\n'

	# Add a line with value descriptors only if more than one item requested.
	if len(keys)>1:
		html_file += '    <tr style="text-align: center;">\n'
		html_file += '      <th style="background-color:MidnightBlue;color:White;">Alliance member</th>\n'
		for char in char_list:
			for key in keys:
				html_file += '      <th style="background-color:MidnightBlue;color:white;">'+key.title()+'</th>\n'
	
		html_file += '    </tr>\n'

	html_file += '  </thead>\n'
	html_file += '  <tbody>\n'

	# Finally, write the data for each row. Player name then relevant stats for each character.
	for player_name in player_list:
		processed_chars = processed_players[player_name]
		html_file += '    <tr style="text-align: center;">\n'
		html_file += '     <th style="text-align: left; background-color:LightBlue;">'+player_name+'</th>\n'

		for char_name in char_list:
			for key in keys:
				html_file += '     <td style="background-color:'+get_value_color(char_stats,char_name,key,processed_chars[char_name][key])+';">'+processed_chars[char_name][key]+'</td>\n'
	
		html_file += '     </th>\n'
		html_file += '    </tr>\n'
	
	# Close the HTML table at the end of the doc.
	html_file += '  </tbody>\n'
	html_file += '</table >\n'
		
	return html_file


if __name__ == "__main__":
	main() # Just run myself
