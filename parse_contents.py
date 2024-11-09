#!/usr/bin/env python3
# Encoding: UTF-8
"""parse_contents.py
Scrapes the alliance.html (Alliance display page) and characters.html file (Roster display page) from MSF.gg.  

Returns in easy to use dicts for inclusion in tables.
"""

from log_utils import *

import datetime
import re

from file_io import *

from bs4 import BeautifulSoup
from selenium import webdriver

# Parse the alliance information directly from the website.
@timed(level=3)
def parse_alliance(driver):

	alliance = {}

	# Used for file naming
	alliance['name'] = driver.alliance_name

	# Used for display in reports
	alliance['display_name'] = driver.alliance_html

	# Used to discriminate if multiple alliances have same base filename
	alliance['color'] = ''.join([x[6:] for x in driver.alliance_html.split('"') if x.startswith('color:')])

	# Pull Total Power, Average TCP, Trophy Count, OPENINGS?, War Zone, War League, War Rank, Raid Rank from driver.page_source
	soup = BeautifulSoup(driver.page_source, 'html.parser')

	icon_and_frame = soup.find('div',  attrs = {'class':'alliance-icon'})

	alliance['image']     = icon_and_frame.find('img', attrs = {'class':'icon' }).get('src').split('ALLIANCEICON_')[-1][:-4]
	alliance['frame']     = icon_and_frame.find('img', attrs = {'class':'frame'}).get('src').split('ALLIANCEICON_')[-1][:-4]
	
	# Parse the Alliance trophies.
	alliance_trophies    = soup.find('div', attrs = {'class':'info-wrapper'}).find('div', attrs = {'class':'trophies'}).text
	alliance['trophies'] = int(re.sub(r"\D", "", alliance_trophies))
	
	# Parse the Alliance stats.
	alliance_stats       = soup.findAll('div', attrs = {'class':'msf-tag'})
	
	for stat in alliance_stats:

		# Skip over entries which don't have data. ;)
		if not stat.find('div', attrs = {'class':'filter-title'}):
			continue
			
		title = stat.find('div', attrs = {'class':'filter-title'}).text
		value = stat.find('div', attrs = {'class':'filter-value'}).text

		if   title == 'total power':	alliance['tot_power']  = int(re.sub(r"\D", "", value))
		elif title == 'average tcp':	alliance['avg_power']  = int(re.sub(r"\D", "", value))
		elif title == 'War Time':   	alliance['war_zone']   = int(re.sub(r"\D", "", value))
		elif title == 'War League': 	alliance['war_league'] = value
		elif title == 'war rank':   	alliance['war_rank']   = int(re.sub(r"\D", "", value))
		elif title == 'raid rank':  	alliance['raid_rank']  = int(re.sub(r"\D", "", value))

	members  = {}
	captains = []

	# Pull base Member Info from the info.csv file.
	parse_info_csv(driver, alliance, captains, members)

	# If no info.csv was available, fall back to parsing HTML.
	if not members:
		parse_info_html(driver, alliance, captains, members)

	alliance['members']  = members
	alliance['captains'] = captains

	# Return the parsed alliance info.
	return alliance
	


# Parse the Member data directly from the info.csv file.
def parse_info_csv(driver, alliance, captains, members):
	
	# Can't parse if info.csv is unavailable.
	if not driver.info_csv or not os.path.exists(driver.info_csv):
		print ('WARNING: No info.csv file found. Member data will come from HTML.')
		return

	info_csv = open(driver.info_csv, 'r', encoding='utf-8').readlines()

	# Iterate through each entry, building up a member dict with stats for each.
	for idx, member_row in enumerate(info_csv[1:]):
		member = {}

		member_row = member_row.strip().split(',')

		# Remove HTML tags if present.
		member_name = remove_tags(member_row[2]).strip()

		# Process role information.
		member_role     = member_row[1]
		if member_role == 'leader':
			alliance['leader'] = member_name
		elif member_role == 'captain':
			captains.append(member_name)

		member['url']   = member_row[0]
		
		# Store URL in driver if this is the login user
		if member_name.lower() == driver.username.lower():
			driver.url = member_row[0]

		member['image'] = member_row[3].split('Portrait_')[-1][:-4]
		member['frame'] = member_row[4].split('ICON_FRAME_')[-1][:-4]
		member['level'] = int(member_row[5])  if member_row[5] else 0
		member['tcp']   = int(member_row[7])  if member_row[7] else 0
		member['stp']   = int(member_row[8])  if member_row[8] else 0
		member['mvp']   = int(member_row[9])  if member_row[9] else 0
		member['tcc']   = int(member_row[10]) if member_row[10] else 0
		member['avail'] = member_row[11]=='true'

		# Store the finished member info.
		members[member_name] = member



def parse_alliance_api(alliance_data, alliance_members):

	alliance = {}

	# Used for file naming
	alliance['name'] = remove_tags(alliance_data['name']).strip()

	# Used for display in reports
	alliance['display_name'] = alliance_data['name'] # Needs additional processing to add <span> and color=tags.

	# Used to discriminate if multiple alliances have same base filename					# Need a complete rewrite, possibly along with the above.
	#alliance['color'] = ''.join([x[6:] for x in driver.alliance_html.split('"') if x.startswith('color:')])

	# Parse the Alliance image and frame
	alliance['image']      = alliance_data['icon'].split('ALLIANCEICON_')[-1][:-4]
	alliance['frame']      = alliance_data['frame'].split('ALLIANCEICON_')[-1][:-4]
	
	# Parse the Alliance stats
	alliance['trophies']   = alliance_data['warTrophies']
	alliance['tot_power']  = alliance_data['tcp']
	alliance['avg_power']  = alliance_data['avgTcp']
	alliance['war_zone']   = alliance_data['warZone']
	alliance['war_league'] = alliance_data['warLeague']
	alliance['war_rank']   = alliance_data['warRank']
	alliance['raid_rank']  = alliance_data['raidRank']

	members  = {}
	captains = []

	# Pull base Member Info from the info.csv file.
	parse_info_api(alliance_members, alliance, captains, members)

	alliance['members']  = members
	alliance['captains'] = captains

	# Return the parsed alliance info.
	return alliance



# Parse the Member data directly from the info.csv file.
def parse_info_api(alliance_members, alliance, captains, members):

	# Iterate through each entry, building up a member dict with stats for each.
	for alliance_member in alliance_members:
		member = {}

		# Get a little bit closer to our work
		member_card = alliance_member['card']

		# Remove HTML tags if present
		member_name = remove_tags(member_card['name']).strip()

		# Process role information
		member_role     = alliance_member['rank']
		if member_role == 'leader':
			alliance['leader'] = member_name
		elif member_role == 'captain':
			captains.append(member_name)

		member['url']   = alliance_member['id']
		
		# Process other info from the Member Card
		member['image'] = member_card['icon'].split('Portrait_')[-1][:-4]
		member['frame'] = member_card['frame'].split('ICON_FRAME_')[-1][:-4]
		member['level'] = member_card.get('level',{}).get('completedTier',0)
		member['tcp']   = member_card.get('tcp')
		member['stp']   = member_card.get('stp')
		member['mvp']   = member_card.get('warMvp',0)
		member['tcc']   = member_card.get('charactersCollected')
		member['avail'] = member_card.get('rosterShare')

		# Store the finished member info.
		members[member_name] = member
		


# Parse the member list out of HTML directly from the website.
def parse_info_html(driver, alliance, captains, members):

	soup = BeautifulSoup(driver.page_source, 'html.parser')

	# Parse each row of the members table, extracting stats for each member.
	members_table = soup.find('tbody').findAll('tr', attrs={'draggable':'false'})
	
	for member_row in members_table:

		member = {}
	
		# Remove HTML tags if present.
		member_name = remove_tags(member_row.find('div', attrs={'class':'name'}).text.replace('[ME]',''))	
		
		member['level'] = int(member_row.find('div', attrs={'class':'player-level'}).text.strip())
		member['image'] = member_row.find('div', attrs={'class':'user-card'}).findAll('img')[0].get('src').split('Portrait_')[-1][:-4]
		member['frame'] = member_row.find('div', attrs={'class':'user-card'}).findAll('img')[1].get('src').split('ICON_FRAME_')[-1][:-4]

		# Process role information.
		member_role     = member_row.find('div', attrs={'class':'member-card-info'}).text.split()[-1]
		if member_role == 'Leader':
			alliance['leader'] = member_name
		elif member_role == 'Captain':			
			captains.append(member_name)

		member['tcp'] = int(re.sub(r"\D", "", member_row.find('td', attrs={'data-label':'Collection Power'}).text))
		member['stp'] = int(re.sub(r"\D", "", member_row.find('td', attrs={'data-label':'Strongest Team Power'}).text))
		member['mvp'] = int(re.sub(r"\D", "", member_row.find('td', attrs={'data-label':'War MVP'}).text))
		member['tcc'] = int(re.sub(r"\D", "", member_row.find('td', attrs={'data-label':'Total Characters Collected'}).text))

		member['url'] = member_row.find('td', attrs={'class':'has-text-right'}).find('a').get('href').split('/')[-2]
		
		# Store URL in driver if this is the login user
		if member_name.lower() == driver.username.lower():
			driver.url = member['url']

		# Assume they're all available. Just have to try.
		member['avail'] = True

		# Store the finished member info.
		members[member_name] = member



# Parse the character file out of HTML directly from the website.
@timed(level=3)
def parse_roster_html(contents, alliance_info, member=''):
	soup = BeautifulSoup(contents, 'html.parser')

	player_info = {}

	processed_chars  = {}
	other_data       = {}
	
	chars  = soup.findAll('li', attrs = {'class':'character'})

	# Iterate through each toon that we found.
	for char in chars:
		
		# If no char_name defined, last entry on page. Skip.
		char_name = char.find('h4').text.strip()
		if not char_name:
			continue

		# Stats available only if character is recruited.
		char_stats = char.find('div', attrs = {'id':'toon-stats'})

		if char_stats:

			# Is this character a favorite? Using this format for the csv. 
			favorite = [6,0][char.find('i', attrs = {'class':'is-favorite'}) == None]

			# Decode Level and Power
			level = 0
			power = 0

			stats = char_stats.findAll('div', attrs = {'class':''})

			for stat in stats:
				if '/' in stat.text or 'MAX' in stat.text:
					continue
				elif 'LVL' in stat.text:
					level = int(re.sub(r"\D", "", stat.text))
				elif stat.text:
					power = int(re.sub(r"\D", "", stat.text))

			# Decode Yellow Stars, Red Stars, and Diamonds
			stars = str(char_stats.find('span'))
			if stars == 'None':
				redStars = 7
				yelStars = 7
				diamonds = str(char_stats.find('div',attrs={'class':'diamonds-container'})).count('diamond-filled')
				if not diamonds:
					print ("Should never happen.",char_name)
			else:
				yelStars = stars.count('fas fa-star star-red') + stars.count('star-orange')
				redStars = min(stars.count('star-red'),yelStars)

				# These are 'unrealized' diamonds -- diamonds earned but not usable because char isn't 7R.
				diamonds = char_stats.find('div',attrs={'class':'diamond-container'})
				if not diamonds:
					diamonds = 0
				elif not diamonds.text:
					diamonds = 1
				else:
					diamonds = int(diamonds.text)
			
			# Decode Abilities
			abilities = char_stats.findAll('div', attrs = {'class':'ability-level'})
			
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
			elif iso_info.find('purple') != -1:
				iso += 10
			
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

			# TEMP FIX FOR BROKEN WEBSITE
			if level >= 85 and not iso:

				# ISO level is easy. It's 10.
				iso = 10

				# ISO class is harder. Gotta copy from current entry.
				iso_class = alliance_info.get('members',{}).get(member,{}).get('other_data',{}).get(char_name,0)%6

			processed_chars[char_name] = {'power':int(power), 'lvl':int(level), 'tier':int(tier), 'iso':int(iso), 'yel':yelStars, 'red':redStars, 'dmd':0, 'abil':int(bas+spc+ult+pas)}
			other_data[char_name]      = favorite+iso_class

		# Entries for Heroes not yet collected, no name on final entry for page.
		elif char_name:
			processed_chars[char_name] = {'power':0, 'lvl':0, 'tier':0, 'iso':0, 'yel':0, 'red':0, 'dmd':0, 'abil':0}
			other_data[char_name]      = 0

	# Finally, merge the processed roster into our Alliance Info
	merge_roster(alliance_info, member, processed_chars, other_data)



# Break this out as a separate routine so can be used to merge roster.csv data.
def merge_roster(alliance_info, member, processed_chars, other_data):

	# Get a little closer to our work. 
	member_info = alliance_info['members'].setdefault(member,{})
	
	# Update 'last_update' if the calculated tot_power has changed.
	calc_pwr = sum([processed_chars[char]['power'] for char in processed_chars])
	if  member_info.get('tot_power') != calc_pwr:
		member_info['tot_power']      = calc_pwr
		member_info['last_update']    = datetime.datetime.now()

	# Add the 'clean' parsed data to our list of processed players.
	member_info['processed_chars'] = processed_chars
	member_info['other_data']      = other_data
	
	# Do I really USE the display_name?
	member_info['display_name']    = member

	# Temporary fix. Calculate values if possible.
	calc_lvl             = max([processed_chars[char_name].get('lvl',0) for char_name in processed_chars]) if processed_chars else 0
	calc_stp             = sum(sorted([processed_chars[member]['power'] for member in processed_chars], reverse=True)[:5])
	calc_tcc             = len([char for char in processed_chars if processed_chars[char]['power']])
	member_info['max']   = len([char for char in processed_chars if processed_chars[char]['yel']==7])
	member_info['stars'] = sum([processed_chars[char]['yel'] for char in processed_chars])
	member_info['red']   = sum([processed_chars[char]['red'] for char in processed_chars])

	# Only use calculated TCP, STP, and TCC if higher than the recorded values in Alliance Info.
	member_info['level'] = max(calc_lvl, member_info.get('level',0))
	member_info['tcp']   = max(calc_pwr, member_info.get('tcp',0))
	member_info['stp']   = max(calc_stp, member_info.get('stp',0))
	member_info['tcc']   = max(calc_tcc, member_info.get('tcc',0))


	
# Parse the Roster data directly from the roster.csv file.
@timed(level=3)
def parse_roster_csv(roster_csv, char_lookup, roster_csv_data={}, member_order=[]):

	# Can't parse if roster.csv is unavailable.
	if not roster_csv or not os.path.exists(roster_csv):
		print ('WARNING: No roster.csv file found. Roster data will come from HTML.')
		return

	# Pull full Roster Info from the roster.csv file.
	roster_csv_file = open(roster_csv, 'r', encoding='utf-8').readlines()

	# Iterate through each entry, building up a member dict with stats for each.
	for entry_row in roster_csv_file[1:]:

		entry = entry_row.split(',')

		member_name = remove_tags(entry[0]).strip()
		
		member_info = roster_csv_data.setdefault(member_name, {'processed_chars':{}, 'other_data':{}})
		
		char_name = char_lookup.get(entry[1])
		
		# SHOULD NOT HAPPEN. If lookup failed, we're missing the translation. Can't insert this data.
		if not char_name:
			print ("missing translation for",entry[1])
			continue
		
		char_info = member_info['processed_chars'].setdefault(char_name,{})
		
		char_info['lvl']   = int(entry[2]) if entry[2] else 0
		char_info['power'] = int(entry[3]) if entry[3] else 0
		char_info['yel']   = int(entry[4]) if entry[4] else 0
		
		active_red = int(entry[5]) if entry[5] else 0
		char_info['red']   = active_red   if active_red < 7 else 7 
		char_info['dmd']   = active_red-7 if active_red > 7 else 0
		
		char_info['tier']  = int(entry[6]) if entry[6] else 0

		bas = entry[7]  if entry[7]  else '0' 
		spc = entry[8]  if entry[8]  else '0'
		ult = entry[9]  if entry[9]  else '0'
		pas = entry[10] if entry[10] else '0'

		char_info['abil'] = int(bas+spc+ult+pas)
		
		iso_class = entry[11] if entry[11] else 0

		if iso_class == 'fortifier':
			member_info['other_data'][char_name] = 1
			char_info['iso'] = int(entry[14]) if entry[14] else 0
		elif iso_class == 'healer':
			member_info['other_data'][char_name] = 2
			char_info['iso'] = int(entry[15]) if entry[15] else 0
		elif iso_class == 'skirmisher':
			member_info['other_data'][char_name] = 3
			char_info['iso'] = int(entry[17]) if entry[17] else 0
		elif iso_class == 'raider':
			member_info['other_data'][char_name] = 4
			char_info['iso'] = int(entry[16]) if entry[16] else 0
		elif iso_class == 'striker':
			member_info['other_data'][char_name] = 5
			char_info['iso'] = int(entry[13]) if entry[13] else 0
		elif not iso_class:
			member_info['other_data'][char_name] = 0
			char_info['iso'] = 0
	
	# Fill out entries for toons not yet collected.
	for member in roster_csv_data:
		for char_name in [char for char in char_lookup if char not in roster_csv_data[member]['processed_chars']]:
			roster_csv_data[member]['processed_chars'][char_name] = {'power':0, 'lvl':0, 'tier':0, 'iso':0, 'yel':0, 'red':0, 'dmd':0, 'abil':0}
			roster_csv_data[member]['other_data'][char_name]      = 0



def parse_roster_api(response, char_lookup, processed_chars, other_data):

	# Iterate through each in roster, building up a member dict with stats for each.
	for entry in response.json()['data']:

		char_name = char_lookup.get(entry['id'])
		
		# SHOULD NOT HAPPEN. If lookup failed, we're missing the translation. Can't insert this data.
		if not char_name:
			print ("missing translation for",entry[1])
			continue
		
		char_info = processed_chars.setdefault(char_name,{})
		
		char_info['lvl']   = entry.get('level',0)
		char_info['power'] = entry.get('power',0)
		char_info['yel']   = entry.get('activeYellow',0)
		
		active_red = entry.get('activeRed',0)
		char_info['red']   = active_red   if active_red < 7 else 7 
		char_info['dmd']   = active_red-7 if active_red > 7 else 0
		
		char_info['tier']  = entry.get('gearTier',0)

		bas = str(entry.get('basic',0))
		spc = str(entry.get('special',0))
		ult = str(entry.get('ultimate',0))
		pas = str(entry.get('passive',0))

		char_info['abil'] = int(bas+spc+ult+pas)
		
		iso_class = entry.get('iso8',{}).get('active')

		iso_classes =  {'fortifier':1,
						'healer':2,
						'skirmisher':3,
						'raider':4,
						'striker':5}

		other_data[char_name] = iso_classes.get(iso_class,0)

		char_info['iso'] = entry.get('iso8',{}).get(iso_class,0)



# Parse character names, traits, portraits all out of API character call
def parse_char_dict(char_dict, char_lookup, portraits, traits):

	for char in char_dict['data']:

		# Short circuit if this isn't a valid entry
		if not char.get('portrait') or not char.get('name'):
			continue

		char_id   = char['id']    # Internal naming
		char_name = char['name']  # Human readable
		
		# Build char_lookup
		char_lookup[char_id] = char_name
		
		# Build portrait lookup
		portraits[char_name] = char['portrait'].split('Portrait_')[-1][:-4]
		
		for trait in char.get('traits',[]):
			traits.setdefault(trait['id'],{})[char_name] = 1
		
		for trait in char.get('invisibleTraits',[]):
			if not trait.get('alwaysInvisible'):
				traits.setdefault(trait['id'],{})[char_name] = 1
			
	# Add missing trait
	traits['MsfOriginal'] = {'Deathpool': 1, 'Kestrel': 1, 'Spider-Weaver': 1, 'Vahl': 1}

	# Remove excess trait
	if 'Ultron' in traits:
		del traits['Ultron']



# Parse the character file out of MHTML or the page_source directly from the website.
@timed(level=3)
def parse_portraits(contents):
	soup = BeautifulSoup(contents, 'html.parser')

	portraits   = {}
	
	chars  = soup.findAll('li', attrs = {'class':'character'})

	# Iterate through each toon that we found.
	for char in chars:
		
		# If no char_name defined, last entry on page. Skip.
		char_name = char.find('h4').text.strip()
		if not char_name:
			continue

		# Keep the path to the image for each character.
		portrait = char.find('img',attrs={'class':'portrait is-centered'}).get('src').split('Portrait_')[-1][:-4]
		
		portraits[char_name] = portrait

	# Update alliance_info with portrait information.
	return portraits



# Parse the character file out of MHTML or the page_source directly from the website.
@timed(level=3)
def parse_scripts(contents):
	soup = BeautifulSoup(contents, 'html.parser')

	# Keep the scripts in use up to date in alliance_info. Will be used by extract_traits.
	return [script.get('src') for script in soup.findAll('script', attrs = {'type':'text/javascript'}) if script.get('src') and 'static' in script.get('src')]



