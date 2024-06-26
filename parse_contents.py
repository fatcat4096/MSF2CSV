#!/usr/bin/env python3
# Encoding: UTF-8
"""parse_contents.py
Scrapes the alliance.html (Alliance display page) and characters.html file (Roster display page) from MSF.gg.  

Returns in easy to use dicts for inclusion in tables.
"""

from log_utils import *

import datetime
import re

from bs4 import BeautifulSoup
from parse_cache import update_parse_cache
from file_io import *

from alliance_info import is_valid_user_id

# Parse the alliance information directly from the website.
@timed(level=3)
def parse_alliance(contents, discord_user=None, scopely_login=None):

	soup = BeautifulSoup(contents, 'html.parser')

	alliance = {}

	# Parse the basic alliance info
	alliance['name']      = remove_tags(soup.find('span', attrs = {'class':'alliance-name'}).text).strip()
	alliance['image']     = soup.find('div',  attrs = {'class':'trophy-icon'}).find('img').get('src').split('ALLIANCEICON_')[-1][:-4]

	# Parse the alliance stats.
	alliance_stats = soup.findAll('div', attrs = {'class':'level-item'})
	
	# Parse each row of the members table, extracting stats for each member.
	members_table = soup.find('tbody').findAll('tr', attrs={'draggable':'false'})

	members  = {}
	captains = []

	# Iterate through each entry, building up a member dict with stats for each.
	for member_row in members_table:
		member = {}

		# Remove HTML tags if present.
		member_name = remove_tags(member_row.find('td', attrs={'class':'player'}).text)

		# If '[ME]' is in name, THIS is where we store Discord User and Scopely Login info.
		if '[ME]' in member_name:
			# Get rid of the '[ME]' in member name.
			member_name = member_name.replace('[ME]','')

			# Store extra information if provided.
			if discord_user:	member['discord'] = discord_user
			if scopely_login:	member['scopely'] = scopely_login

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
@timed(level=3)
def parse_roster(contents, alliance_info, parse_cache, member=''):
	soup = BeautifulSoup(contents, 'html.parser')

	# Start by parsing Player Info from the right panel. We will use this to update alliance_info if not working_from_web.
	player = soup.find('div', attrs = {'class':'fixed-wrapper panel-wrapper'})
	
	# Not sure what causes this.
	if not player:
		print ('Could not find player info when parsing. Writing HTML to disk as',member+'.html')
		write_file(get_local_path()+member+'.html', soup.prettify())
		return

	# Did we actually arrive at a valid Roster Page?
	player_name = player.find('div', attrs = {'class':'player-name'})
	if not player_name:
		return
		
	# Sanitize the Player Name (remove html tags) and report which panel we're working on.
	player_name = remove_tags(player_name.text)

	player_info = {}

	player_info['image'] = player.find('img').get('src').split('Portrait_')[-1][:-4]

	player_stats = player.find('div', attrs = {'class':'player-stats'}).findAll('span')

	mvp_missing = player.text.find('MVP') == -1
	red_missing = player.text.find('Total Red') == -1

	# SIDE PANEL IS CURRENTLY INVALID, KEEP DATA FROM ALLIANCE_INFO PAGE.
	#player_info['tcp']   =  int(re.sub(r"\D", "", player_stats[0].text))
	#player_info['stp']   =  int(re.sub(r"\D", "", player_stats[1].text))
	#player_info['mvp']   = [int(re.sub(r"\D", "", player_stats[2].text)),0][mvp_missing]
	#player_info['tcc']   =  int(re.sub(r"\D", "", player_stats[3-mvp_missing].text))
	#player_info['max']   =  int(re.sub(r"\D", "", player_stats[4-mvp_missing].text))
	#player_info['arena'] =  int(re.sub(r"\D", "", player_stats[5-mvp_missing].text))
	
	#player_info['blitz'] =  int(re.sub(r"\D", "", player_stats[-3+red_missing*2].text))
	#player_info['stars'] = [int(re.sub(r"\D", "", player_stats[-2].text)),0][red_missing]
	#player_info['red']   = [int(re.sub(r"\D", "", player_stats[-1].text)),0][red_missing]

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
				elif stat.text:
					power = int(re.sub(r"\D", "", stat.text))

			# For total roster calculation.
			tot_power += int(power)
			
			# Decode Yellow Stars, Red Stars, and Diamonds
			stars = str(toon_stats.find('span'))
			if stars == 'None':
				redStars = 7
				yelStars = 7
				diamonds = str(toon_stats.find('div',attrs={'class':'diamonds-container'})).count('diamond-filled')
				if not diamonds:
					print ("Should never happen.",char_name)
			else:
				yelStars = stars.count('fas fa-star star-red') + stars.count('star-orange')
				redStars = min(stars.count('star-red'),yelStars)

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

			processed_chars[char_name] = {'power':int(power), 'lvl':int(level), 'tier':int(tier), 'iso':int(iso), 'yel':yelStars, 'red':redStars, 'dmd':0*diamonds, 'abil':int(bas+spc+ult+pas)}
			other_data[char_name]      = favorite+iso_class

		# Entries for Heroes not yet collected, no name on final entry for page.
		elif char_name:
			processed_chars[char_name] = {'power':0, 'lvl':0, 'tier':0, 'iso':0, 'yel':0, 'red':0, 'dmd':0, 'abil':0}
			other_data[char_name]      = 0

		# Look for a duplicate entry in our cache and point both to the same entry if possible.
		update_parse_cache(processed_chars,char_name,parse_cache)

	# Calculate level based on character leveling.
	player_info['level'] = max([processed_chars[char_name].get('lvl',0) for char_name in processed_chars]) if processed_chars else 0

	# Use Alliance Info information if it's available.
	player_info['level'] = max(player_info['level'], alliance_info['members'].get(member,{}).get('level',0))

	# Get a little closer to our work. 
	player = alliance_info['members'].setdefault(player_name,{})
	
	# Update 'last_update' if the calculated tot_power has changed.
	if player.get('tot_power') != tot_power:
		player['tot_power']   = tot_power
		player['last_update'] = datetime.datetime.now()

	# Add the 'clean' parsed data to our list of processed players.
	player['processed_chars'] = processed_chars
	player['other_data']      = other_data
	
	# Keep the top level name, but only if valid.
	if not is_valid_user_id(member):
		player['display_name']    = member

	# Only use calculated total power for TCP if higher than the recorded TCP in Alliance Info.
	if tot_power > alliance_info['members'].get(member,{}).get('tcp',0):
		player_info['tcp'] = tot_power
		
	# Temporary fix. Calculate values if possible.
	player_info['stp']   = sum(sorted([processed_chars[member]['power'] for member in processed_chars], reverse=True)[:5])
	player_info['tcc']   = len([char for char in processed_chars if processed_chars[char]['power']])
	player_info['max']   = len([char for char in processed_chars if processed_chars[char]['yel']==7])
	player_info['stars'] = sum([processed_chars[char]['yel'] for char in processed_chars])
	player_info['red']   = sum([processed_chars[char]['red'] for char in processed_chars])

	# And update the player info with current stats from the side panel.
	player.update(player_info)
	
	# Update alliance_info with portrait information.
	alliance_info['portraits'] = char_portraits

	# Keep the scripts in use up to date in alliance_info. Will be used by extract_traits.
	scripts = [script.get('src') for script in soup.findAll('script', attrs = {'charset':'utf-8'})]
	if scripts:
		alliance_info['scripts'] = scripts

	# If a new member name has been found during Roster parse, 
	if member != player_name:

		# Copy any existing information from the old 'members' entry to the new one.
		if alliance_info['members'].get(member):
			for key in alliance_info['members'][member]:
				if key not in alliance_info['members'][player_name]:
					alliance_info['members'][player_name][key] = alliance_info['members'][member][key]

			# Finish by deleting the outdated entry.
			del alliance_info['members'][member]

		# Also update any matching definitions in 'Leaders' and 'Captains'
		if alliance_info.get('leader') == member:
			alliance_info['leader'] = player_name
		
		if member in alliance_info.get('captains',[]):
			member_idx = alliance_info['captains'].index(member)
			alliance_info['captains'][member_idx] = player_name

	return player_name
