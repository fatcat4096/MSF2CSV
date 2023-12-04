#!/usr/bin/env python3
# Encoding: UTF-8
"""parse_contents.py
Scrapes the alliance.html (Alliance display page) and characters.html file (Roster display page) from MSF.gg.  

Returns in easy to use dicts for inclusion in tables.
"""

import datetime
import re

from bs4 import BeautifulSoup
from parse_cache import update_parse_cache
from file_io import remove_tags

# Parse the alliance information directly from the website.
def parse_alliance(contents):
	soup = BeautifulSoup(contents, 'html.parser')

	alliance = {}

	# Parse the basic alliance info
	alliance['name']      = str(soup.find('span', attrs = {'class':'alliance-name'}).contents[0])
	alliance['trophies']  = soup.find('div',  attrs = {'class':'war-trophies'}).text.strip()
	alliance['image']     = soup.find('div',  attrs = {'class':'trophy-icon'}).find('img').get('src').split('ALLIANCEICON_')[-1][:-4]

	# Parse the alliance stats.
	alliance_stats = soup.findAll('div', attrs = {'class':'level-item'})
	
	alliance['stark_lvl'] = alliance_stats[1].text.split()[-1]
	
	# Parse each row of the members table, extracting stats for each member.
	members_table = soup.find('tbody').findAll('tr', attrs={'draggable':'false'})

	members  = {}
	captains = []

	# Iterate through each entry, building up a member dict with stats for each.
	for member_row in members_table:
		member = {}
		# Remove '[ME]' and HTML tags if present.
		member_name = remove_tags(member_row.find('td', attrs={'class':'player'}).text.replace('[ME]',''))

		member['level'] = int(member_row.find('td', attrs={'class':'avatar'}).text.strip())
		member['image'] = member_row.find('td', attrs={'class':'avatar'}).find('img').get('src').split('Portrait_')[-1][:-4]
		member_role     = member_row.find('td', attrs={'class':'role'})

		# Process role information.
		if str(member_role).find('is-leader') != -1:
			alliance['leader'] = member_name
		elif str(member_role).find('is-captain') != -1:
			captains.append(member_name)

		member['tcp'] = int(re.sub(r"\D", "", member_row.find('td', attrs={'class':'tcp'}).text))

		# The fact that they've used 'stp' for all three of these is probably a bug 
		# on their part, and I'll probably need to change this a year down the road.
		member_stp = member_row.findAll('td', attrs={'class':'stp'})
		member['stp'] = int(re.sub(r"\D", "", member_stp[0].text))
		member['mvp'] = int(re.sub(r"\D", "", member_stp[1].text))
		member['tcc'] = int(re.sub(r"\D", "", member_stp[2].text))

		# Store the finished member info.
		members[member_name] = member

	alliance['members']  = members
	alliance['captains'] = captains
	
	# Just grab the URLs for the js scripts on the page. Will be used by extract_traits.
	alliance['scripts']  = [script.get('src') for script in soup.findAll('script', attrs = {'charset':'utf-8'})]
	
	# Return the parsed alliance info.
	return alliance


# Parse the character file out of MHTML or the page_source directly from the website.
def parse_roster(contents, alliance_info, parse_cache, member=''):
	soup = BeautifulSoup(contents, 'html.parser')

	# Start by parsing Player Info from the right panel. We will use this to update alliance_info if not working_from_web.
	player = soup.find('div', attrs = {'class':'fixed-wrapper panel-wrapper'})

	# Sanitize the Player Name (remove html tags) and report which panel we're working on.
	player_name = member or remove_tags(player.find('div', attrs = {'class':'player-name'}).text)

	player_info = {}

	player_info['image'] = player.find('img').get('src').split('Portrait_')[-1][:-4]
	player_info['level'] = int(player.find('span').text)

	player_stats = player.find('div', attrs = {'class':'player-stats'}).findAll('span')

	mvp_missing = player.text.find('MVP') == -1

	player_info['tcp']   =  int(re.sub(r"\D", "", player_stats[0].text))
	player_info['stp']   =  int(re.sub(r"\D", "", player_stats[1].text))
	player_info['mvp']   = [int(re.sub(r"\D", "", player_stats[2].text)),0][mvp_missing]
	player_info['tcc']   =  int(re.sub(r"\D", "", player_stats[3-mvp_missing].text))
	player_info['max']   =  int(re.sub(r"\D", "", player_stats[4-mvp_missing].text))
	player_info['arena'] =  int(re.sub(r"\D", "", player_stats[5-mvp_missing].text))
	
	player_info['blitz'] =  int(re.sub(r"\D", "", player_stats[-3].text))
	player_info['stars'] =  int(re.sub(r"\D", "", player_stats[-2].text))
	player_info['red']   =  int(re.sub(r"\D", "", player_stats[-1].text))

	processed_chars  = {}
	other_data       = {}
	char_portraits   = {}
	
	chars  = soup.findAll('li', attrs = {'class':'character'})

	# Add up all the power of the heroes we find. Will compare this to the previously found info
	# AND to the live Total Power for their roster to determine whether the info collected is fresh or stale.
	tot_power = 0

	for char in chars:
		
		# If no char_name defined, last entry on page. Skip.
		char_name = char.find('h4').text.strip()
		if not char_name:
			continue

		# Keep the path to the image for each character.
		char_portrait = char.find('img',attrs={'class':'portrait is-centered'}).get('src').split('Portrait_')[-1][:-4]
		
		char_portraits[char_name] = char_portrait

		# Stats available only if character is recruited.
		toon_stats = char.find('div', attrs = {'id':'toon-stats'})

		if toon_stats:

			# Is this character a favorite? Using this format for the csv. 
			favorite = [6,0][char.find('i', attrs = {'class':'is-favorite'}) == None]

			# Decode Level and Power
			level = 0
			power = 0

			stats = toon_stats.findAll('div', attrs = {'class':''})

			for stat in stats:
				if '/' in stat.text or 'MAX' in stat.text:
					continue
				elif 'LVL' in stat.text:
					level = int(re.sub(r"\D", "", stat.text))
				else:
					power = int(re.sub(r"\D", "", stat.text))

			# For total roster calculation.
			tot_power += int(power)
			
			# Decode Yellow Stars, Red Stars, and Diamonds
			stars = str(toon_stats.find('span'))
			if not stars:
				redStars = 7
				yelStars = 7
				diamonds = str(toon_stats.find('div',attrs={'class':'diamonds-container'})).count('diamond-filled')
				if not diamonds:
					print ("Should never happen.",char_name)
			else:
				redStars = str(stars.count('star-red'))
				yelStars = str(stars.count('fas fa-star star-red') + stars.count('star-orange'))

				# These are 'unrealized' diamonds -- diamonds earned but not usable because char isn't 7R.
				diamonds = toon_stats.find('div',attrs={'class':'diamond-container'})
				if not diamonds:
					diamonds = 0
				elif not diamonds.text:
					diamonds = 1
				else:
					diamonds = int(diamonds.text)
			
			# Decode Abilities
			abilities = toon_stats.findAll('div', attrs = {'class':'ability-level'})
			
			bas = '0'
			spc = '0'
			ult = '0'
			pas = '0'

			if '-level-' in str(abilities[0]):
				bas = str(abilities[0]).split('-')[3][1]
			
			if '-level-' in str(abilities[1]):
				spc = str(abilities[1]).split('-')[3][1]
			
			if '-level-' in str(abilities[-2]) and len(abilities)==4:
				ult = str(abilities[-2]).split('-')[3][1]
			
			if '-level-' in str(abilities[-1]):
				pas = str(abilities[-1]).split('-')[3][1]
			
			# Decode Gear Tier
			tier = '0'
			gear = char.find('div',attrs={'class':'gear-tier-ring'})
			if str(gear) != 'None':
				tier = str(gear).split('"g')[2].split('"')[0]

			# Decode ISO Level
			iso_info = str(char.find('div',attrs={'class','iso-wrapper'}))
			
			iso = 0
			
			if iso_info.find('-pips-') != -1:
				iso = int(iso_info.split('-pips-')[1].split('"')[0])
			
			if iso_info.find('blue') != -1:
				iso += 5
			
			iso = str(iso)

			iso_class = 0
			if iso_info.find('fortify') != -1:
				iso_class = 1
			elif iso_info.find('restoration') != -1:
				iso_class = 2
			elif iso_info.find('skirmish') != -1:
				iso_class = 3
			elif iso_info.find('gambler') != -1:
				iso_class = 4
			elif iso_info.find('assassin') != -1:
				iso_class = 5

			processed_chars[char_name] = {'power':int(power), 'lvl':int(level), 'tier':int(tier), 'iso':int(iso), 'yel':int(yelStars), 'red':int(redStars), 'abil':int(bas+spc+ult+pas)}
			other_data[char_name]      = favorite+iso_class

		# Entries for Heroes not yet collected, no name on final entry for page.
		elif char_name:
			processed_chars[char_name] = {'power':0, 'lvl':0, 'tier':0, 'iso':0, 'yel':0, 'red':0, 'abil':0}
			other_data[char_name]      = 0

		# Look for a duplicate entry in our cache and point both to the same entry if possible.
		update_parse_cache(processed_chars,char_name,parse_cache)

	print(f"Parsing {len(contents)} bytes...found: {player_name:17}", end='')

	# Get a little closer to our work. 
	player = alliance_info['members'].setdefault(player_name,{})
	
	# Temporary code to fix previous location of tot_power and last_updated -- DELETE THIS IN A COUPLE WEEKS
	if 'processed_chars' in player and 'tot_power' in player['processed_chars']:
		player['tot_power']   = player['processed_chars']['tot_power']
		player['last_update'] = player['processed_chars']['last_update']
	
	# Keep the old 'last_update' if the calculated tot_power hasn't changed.
	if player.get('tot_power') == tot_power:
		print ('(skipping -- unchanged)')
	else:
		print ('(Updated!)')
		player['tot_power']   = tot_power
		player['last_update'] = datetime.datetime.now()
		
	# Add the 'clean' parsed data to our list of processed players.
	player['processed_chars'] = processed_chars
	player['other_data']      = other_data

	# And update the player info with current stats from the side panel.
	player.update(player_info)
	
	# Update alliance_info with portrait information.
	alliance_info['portraits'] = char_portraits

	# If 'scripts' isn't already defined, just grab the URLs for the js scripts on the page. Will be used by extract_traits.
	if 'scripts' not in alliance_info:
		alliance_info['scripts']  = [script.get('src') for script in soup.findAll('script', attrs = {'charset':'utf-8'})]

	# Cleanup for a weird naming bug. 
	# If member name is unparsable on Alliance Info screen but visible on Roster page, remnant gets left behind.
	if member != player_name and alliance_info.get(member):
		del alliance_info[member]

	return player_name
