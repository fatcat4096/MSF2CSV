#!/usr/bin/env python3
# Encoding: UTF-8
"""parse_contents.py
Scrapes the alliance.html (Alliance display page) and characters.html file (Roster display page) from MSF.gg.  

Returns in easy to use dicts for inclusion in tables.
"""

from bs4 import BeautifulSoup
import datetime
import re

TAG_RE = re.compile(r'<[^>]+>')

# Parse the alliance information directly from the website.
def parse_alliance(contents):
	soup = BeautifulSoup(contents, 'html.parser')

	alliance = {}

	# Parse the basic alliance info
	alliance['name']      = remove_tags(soup.find('span', attrs = {'class':'alliance-name'}).text)
	alliance['desc']      = soup.find('div',  attrs = {'class':'editable-msg'}).text
	alliance['trophies']  = soup.find('div',  attrs = {'class':'war-trophies'}).text.strip()
	alliance['image']     = soup.find('div',  attrs = {'class':'trophy-icon'}).find('img').get('src').split('Portrait_')[-1]

	# Parse the alliance stats.
	alliance_stats = soup.findAll('div', attrs = {'class':'level-item'})
	
	alliance['num_mems']  = int(alliance_stats[0].text.split('/')[-1])
	alliance['stark_lvl'] = alliance_stats[1].text.split()[-1]
	alliance['type']      = alliance_stats[2].text.split()[-1]
	
	tot_power = int(re.sub(r"\D", "", alliance_stats[3].text))
	avg_power = int(re.sub(r"\D", "", alliance_stats[4].text))
	
	alliance['tot_power'] = f'{tot_power:,}'
	alliance['avg_power'] = f'{avg_power:,}'
	
	# Parse each row of the members table, extracting stats for each member.
	members_table = soup.find('tbody').findAll('tr', attrs={'draggable':'false'})

	members  = {}
	captains = []
	order    = []

	# Iterate through each entry, building up a member dict with stats for each.
	for member_row in members_table:
		member = {}

		member_name = remove_tags(member_row.find('td', attrs={'class':'player'}).text)

		# It's ME, hi, I'm the problem it's ME.
		if member_name.find('[ME]') != -1:
			member_name = member_name.replace('[ME]','')
			alliance['me'] = member_name

		member['level'] = int(member_row.find('td', attrs={'class':'avatar'}).text.strip())
		member['image'] = member_row.find('td', attrs={'class':'avatar'}).find('img').get('src').split('Portrait_')[-1]
		member_role     = member_row.find('td', attrs={'class':'role'})

		# Process role information.
		if str(member_role).find('is-leader') != -1:
			alliance['leader'] = member_name
		elif str(member_role).find('is-captain') != -1:
			captains.append(member_name)

		member['role'] = member_role.text

		member['tcp'] = int(re.sub(r"\D", "", member_row.find('td', attrs={'class':'tcp'}).text))

		# The fact that they've used 'stp' for all three of these is probably a bug 
		# on their part, and I'll probably need to change this a year down the road.
		member_stp = member_row.findAll('td', attrs={'class':'stp'})
		member['stp'] = int(re.sub(r"\D", "", member_stp[0].text))
		member['mvp'] = int(re.sub(r"\D", "", member_stp[1].text))
		member['tcc'] = int(re.sub(r"\D", "", member_stp[2].text))

		# Store the finished member info.
		members[member_name] = member
		order.append(member_name)

	alliance['members']  = members
	alliance['captains'] = captains
	alliance['order']    = order
	
	# Just grab the URLs for the js scripts on the page. Will be used by extract_traits.
	alliance['scripts']  = [script.get('src') for script in soup.findAll('script', attrs = {'charset':'utf-8'})]
	
	# Return the parsed alliance info.
	return alliance


# Parse the character file out of MHTML or the page_source directly from the website.
def parse_roster(contents, alliance_info):
	soup = BeautifulSoup(contents, 'html.parser')

	player_name = remove_tags(soup.find('div', attrs = {'class':'player-name is-italic'}).text.strip())

	print("Parsing %i bytes...found Alliance Member named: %s" % (len(contents), player_name))

	processed_chars  = {}
	char_portraits   = {}
	
	chars  = soup.findAll('li', attrs = {'class':'character'})

	# Add up all the power of the heroes we find. Will compare this to the previously found info
	# AND to the live Total Power for their roster to determine whether the info collected is fresh or stale.
	tot_power = 0

	for char in chars:
		
		# If no char_name defined, last entry on page. Skip.
		char_name = char.find('h4').text.strip()
		if not char_name:
			pass

		# Stats available only if character is recruited.
		toon_stats = char.find('div', attrs = {'id':'toon-stats'})

		if toon_stats:

			# Keep the path to the image for each character.
			char_portrait = char.find('img',attrs={'class':'portrait is-centered'}).get('src').split('Portrait_')[-1]
			
			char_portraits[char_name] = char_portrait

			# Is this character a favorite? Using this format for the csv. 
			favorite = ['true','false'][char.find('i', attrs = {'class':'is-favorite'}) == None]

			# Decode Level and Power
			stats = toon_stats.findAll('div', attrs = {'class':''})
			level = stats[0].text.strip().split()[1]
			power = ''.join(stats[1].text.strip().split(','))

			# For total roster calculation.
			tot_power += int(power)
			
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
		
			# Decode ISO Level
			iso_info = str(char.find('div',attrs={'class','iso-wrapper'}))
			
			iso = 0
			if iso_info.find('-pips-') != -1:
				iso = int(iso_info.split('-pips-')[1].split('"')[0])
			if iso_info.find('blue') != -1:
				iso += 5
			iso = str(iso)

			iso_class = ''
			if iso_info.find('gambler') != -1:
				iso_class = 'Raider'
			elif iso_info.find('assassin') != -1:
				iso_class = 'Striker'
			elif iso_info.find('fortify') != -1:
				iso_class = 'Fortifier'
			elif iso_info.find('skirmish') != -1:
				iso_class = 'Skirmisher'
			elif iso_info.find('restoration') != -1:
				iso_class = 'Healer'

			processed_chars[char_name] = {'fav':favorite, 'lvl':level, 'power':power, 'tier':tier, 'iso':iso, 'class':iso_class, 'yel':yelStars, 'red':redStars, 'bas':basic, 'spec':special, 'ult':ult, 'pass':passive}

		# Entries for Heroes not yet collected, no name on final entry for page.
		elif char_name:
			processed_chars[char_name] = {'fav':'', 'lvl':'0', 'power':'0', 'tier':'0', 'iso':'0', 'class':'', 'yel':'0', 'red':'0', 'bas':'0', 'spec':'0', 'ult':'0', 'pass':'0'}

	# Finally, store total roster power and now as last_update.
	processed_chars['tot_power'] = tot_power
	processed_chars['last_update'] = datetime.datetime.now()
	
	# Get a little closer to our work. 
	player = alliance_info['members'][player_name]
	
	# Keep the old 'last_update' if the tot_power hasn't changed.
	if 'processed_chars' in player and tot_power == player['processed_chars']['tot_power']:
		processed_chars['last_update'] = player['processed_chars']['last_update']
	
	# Add this parsed data to our list of processed players.
	player['processed_chars'] = processed_chars

	# Update alliance_info with portrait information.
	alliance_info['portraits'] = char_portraits


# Pull strike team definitions directly from the website. 
def parse_teams(contents):
	soup = BeautifulSoup(contents, 'html.parser')

	team_members = []
	
	members = soup.findAll('div', attrs = {'class':'alliance-user'})

	# Iterate through each entry.
	for member in members:
		member_name = member.findAll('span')[-1].text

		# Don't include blank entries
		if member_name:
			team_members.append(member_name)

	return team_members


# Sanitize Alliance Names and player names of any HTML tags.
def remove_tags(text):
    return TAG_RE.sub('', text)