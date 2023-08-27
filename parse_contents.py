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
	alliance['image']     = soup.find('div',  attrs = {'class':'trophy-icon'}).find('img').get('src')

	# Parse the alliance stats.
	alliance_stats = soup.findAll('div', attrs = {'class':'level-item'})
	
	alliance['num_mems']  = int(alliance_stats[0].text.split('/')[-1])
	alliance['stark_lvl'] = alliance_stats[1].text.split('level ')[-1]
	alliance['type']      = alliance_stats[2].text.split('Type ')[-1]
	alliance['tot_power'] = alliance_stats[3].text.split('power ')[-1]
	alliance['avg_power'] = alliance_stats[4].text.split('Power')[-1]
	
	# Parse each row of the members table, extracting stats for each member.
	members_table = soup.find('tbody').findAll('tr', attrs={'draggable':'false'})

	members  = {}
	captains = []
	order    = []

	# Iterate through each entry, building up a member dict with stats for each.
	for member_row in members_table:
		member = {}

		member_name = remove_tags(member_row.find('td', attrs={'data-label':'Name'}).text)

		# It's ME, hi, I'm the problem it's ME.
		if member_name.find('[ME]') != -1:
			member_name = member_name.replace('[ME]','')
			alliance['me'] = member_name

		member['level'] = int(member_row.find('td', attrs={'class':'avatar'}).text.strip())
		member['image'] = member_row.find('td', attrs={'class':'avatar'}).find('img').get('src')
		member['role']  = member_row.find('td', attrs={'data-label':'Role'}).text

		# Process role information.
		if member['role'] == 'Leader':
			alliance['leader'] = member_name
		elif member['role'] == 'Captain':
			captains.append(member_name)

		member['tcp'] = int(member_row.find('td', attrs={'data-label':'Collection Power'}).text.replace(',',''))
		member['stp'] = int(member_row.find('td', attrs={'data-label':'Strongest Team Power'}).text.replace(',',''))
		member['mvp'] = int(member_row.find('td', attrs={'data-label':'War MVP'}).text.replace(',',''))
		member['tcc'] = int(member_row.find('td', attrs={'data-label':'Total Characters Collected'}).text.replace(',',''))

		# Store the finished member info.
		members[member_name] = member
		order.append(member_name)

	alliance['members']  = members
	alliance['captains'] = captains
	alliance['order']    = order
	
	# Return the parsed alliance info.
	return alliance


# Parse the character file out of MHTML or the page_source directly from the website.
def parse_characters(contents, char_stats, processed_players):
	soup = BeautifulSoup(contents, 'html.parser')

	player_name = remove_tags(soup.find('div', attrs = {'class':'player-name is-italic'}).text.strip())

	print("Parsing %i bytes...found Alliance Member named: %s" % (len(contents), player_name))

	processed_chars  = {}
	
	chars  = soup.findAll('li', attrs = {'class':'character'})

	# Add up all the power of the heroes we find. Will compare this to the previously found info
	# AND to the live Total Power for their roster to determine whether the info collected is fresh or stale.
	tot_power = 0

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
			# Is this character a favorite? Using this format for the csv. 
			favorite = ['true','false'][char.find('i', attrs = {'class':'is-favorite'}) == None]

			# Decode Level and Power
			stats = toon_stats.findAll('div', attrs = {'class':''})
			level = stats[0].text.strip().split()[1]
			power = ''.join(stats[1].text.strip().split(','))

			# For total roster calculation.
			tot_power += int(power)

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

			set_min_max(char_stats,char_name,'iso',iso)
			
			processed_chars[char_name] = {'favorite':favorite, 'level':level, 'power':power, 'tier':tier, 'iso':iso, 'iso_class':iso_class, 'yelStars':yelStars, 'redStars':redStars, 'basic':basic, 'special':special, 'ult':ult, 'passive':passive}

		# Entries for Heroes not yet collected, no name on final entry for page.
		elif char_name:
			processed_chars[char_name] = {'favorite':'', 'level':'0', 'power':'0', 'tier':'0', 'iso':'0', 'iso_class':'', 'yelStars':'0', 'redStars':'0', 'basic':'0', 'special':'0', 'ult':'0', 'passive':'0'}

	# Finally, store total roster power and now as last_update.
	processed_chars['tot_power'] = tot_power
	processed_chars['last_update'] = datetime.datetime.now()
	
	# Only keep if we have no roster, or this roster's TCP is higher.
	if player_name not in processed_players or tot_power > processed_players[player_name]['tot_power']:

		# Add this parsed data to our list of processed players.
		processed_players[player_name] = processed_chars
		
	# After successfully parsing, cache the character.html file to disk for future use.
	# open('roster.%s.html' % player_name, 'wb').write(soup.prettify().encode('utf8'))


def parse_teams(contents):
	soup = BeautifulSoup(contents, 'html.parser')

	team_members = []

	members = soup.findAll('div', attrs = {'class':'alliance-user'})
	for member in members:
		member_name = member.findAll('span')[-1].text
		if member_name:
			team_members.append(member_name)

	return team_members


# Keep track of min/max for each stat for each hero
def set_min_max(char_stats,char_name,stat,value):
	value = int(value)

	# Find min/max stats for this specific toon.
	char_stats[char_name].setdefault(stat,{'min':[value-1,0][stat=='iso'],'max':value})

	if value<char_stats[char_name][stat]['min']:
		char_stats[char_name][stat]['min'] = value

	if value>char_stats[char_name][stat]['max']:
		char_stats[char_name][stat]['max'] = value


# Sanitize Alliance Names and player names of any HTML tags.
def remove_tags(text):
    return TAG_RE.sub('', text)