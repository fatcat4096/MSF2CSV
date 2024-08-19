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
def parse_alliance(driver):		# contents, discord_user=None, scopely_login=None):

	alliance = {}

	# ALLIANCE_NAME, USERNAME in Driver already
	alliance_name = driver.alliance_name

	"""# Parse the basic alliance info
	alliance_name = soup.find('span', attrs = {'class':'alliance-name'})
	alliance_html = ''.join([str(x) for x in alliance_name.children])

	alliance_color = ''

	# Two options for color, either explicit color= indicator
	if '<color=' in alliance_html:
		alliance_color = alliance_html[alliance_html.index('<color=')+6:]

	# or just a simple tag with a hex color in it.
	#elif '<#' in alliance_html:
	
	# ONCE COLOR IS LOADED IN ALLIANCE_INFO['COLOR'] NEEDS TO BE USED TO WRITE FILE **AND** USED WHEN STORING DEFAULT ALLIANCE IN DATABASE
	# ALSO, NEED TO FIND EVERYWHERE THAT WE USE ALLIANCE_INFO['NAME'] FOR FILE NAMING.
	
	# Define dict entry even if empty so that existing/old entry won't be copied over. 
	#alliance['color'] = alliance_color

	alliance_style = ''
	
	if '<b>' in alliance_html:
		alliance_style += 'font-weight:bold;'
	if '<i>' in alliance_html:
		alliance_style += 'font-style:italic;'
	if alliance_color:
		alliance_style += f'color:{alliance_color};'
	
	# Start by removing all formatting.
	alliance_name = remove_tags(alliance_name.text).strip()

	# Wrap the alliance_name if we found special formatting.
	if alliance_style:
		alliance_name = f'<span style="{alliance_style}">{alliance_name}</span>'"""

	alliance['name']      = alliance_name

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

	#
	# TEMPORARY FIX, PARSE MEMBER NAME FROM HTML
	#

	html_rows = soup.find('div', attrs = {'class':'alliance-member-table'}).findAll('tr')[1:]
	
	#
	# TEMPORARY FIX, PARSE MEMBER NAME FROM HTML
	#

	# Pull base Member Info from the info.csv file.
	info_csv = open(driver.info_csv, 'r', encoding='utf-8').readlines()
	
	# Iterate through each entry, building up a member dict with stats for each.
	for idx, member_row in enumerate(info_csv[1:]):
		member = {}

		#
		# TEMPORARY FIX, PARSE MEMBER NAME FROM HTML
		#

		member_name = remove_tags(html_rows[idx].findAll('td')[0].find('div', attrs={'class':'name'}).text.strip().replace(' [ME]',''))

		#
		# TEMPORARY FIX, PARSE MEMBER NAME FROM HTML
		#

		member_row = member_row.strip().split(',')

		"""# Remove HTML tags if present.
		member_name = remove_tags(member_row[2])"""

		# Process role information.
		member_role     = member_row[1]
		if member_role == 'leader':
			alliance['leader'] = member_name
		elif member_role == 'captain':
			captains.append(member_name)

		member['url']   = member_row[0]
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

	alliance['members']  = members
	alliance['captains'] = captains
	
	# Just grab the URLs for the js scripts on the page. Will be used by extract_traits.
	alliance['scripts']  = [script.get('src') for script in soup.findAll('script', attrs = {'type':'text/javascript'}) if script.get('src') and 'static' in script.get('src')]

	# Finally, fix the driver.username value with proper casing. 
	match = [member for member in members if member.lower() == driver.username.lower()]
	if match:
		driver.username = match[0]

	# Return the parsed alliance info.
	return alliance



@timed(level=3)
def parse_player_stats(contents, member_info):
	soup = BeautifulSoup(contents, 'html.parser')
	
	stats = soup.findAll('span')

	# Parse only information unavailable in info.csv.
	member_info['max']        = int(re.sub(r"\D", "", stats[4].text))
	member_info['arena']      = int(re.sub(r"\D", "", stats[5].text))
	member_info['blitz']      = int(re.sub(r"\D", "", stats[6].text))
	member_info['blitz_wins'] = int(re.sub(r"\D", "", stats[7].text))
	member_info['stars']      = int(re.sub(r"\D", "", stats[8].text))
	member_info['red']        = int(re.sub(r"\D", "", stats[9].text))



# Parse the character file out of MHTML or the page_source directly from the website.
@timed(level=3)
def parse_roster_html(contents, alliance_info, member=''):
	soup = BeautifulSoup(contents, 'html.parser')

	player_info = {}

	processed_chars  = {}
	other_data       = {}
	char_portraits   = {}
	
	chars  = soup.findAll('li', attrs = {'class':'character'})

	# Iterate through each toon that we found.
	for char in chars:
		
		# If no char_name defined, last entry on page. Skip.
		char_name = char.find('h4').text.strip()
		if not char_name:
			continue

		# Keep the path to the image for each character.
		char_portrait = char.find('img',attrs={'class':'portrait is-centered'}).get('src').split('Portrait_')[-1][:-4]
		
		char_portraits[char_name] = char_portrait

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

	# Update alliance_info with portrait information.
	alliance_info['portraits'] = char_portraits

	# Keep the scripts in use up to date in alliance_info. Will be used by extract_traits.
	scripts = [script.get('src') for script in soup.findAll('script', attrs = {'type':'text/javascript'}) if script.get('src') and 'static' in script.get('src')]
	if scripts:
		alliance_info['scripts'] = scripts


	
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
	member_info['level'] = max(calc_lvl, alliance_info['members'].get(member,{}).get('level',0))
	member_info['tcp']   = max(calc_pwr, alliance_info['members'].get(member,{}).get('tcp',0))
	member_info['stp']   = max(calc_stp, alliance_info['members'].get(member,{}).get('stp',0))
	member_info['tcc']   = max(calc_tcc, alliance_info['members'].get(member,{}).get('tcc',0))



# Parse the Diamond data directly from the roster.csv file.
@timed(level=3)
def parse_roster_csv_data(roster_csv, char_portraits, roster_csv_data={}, member_order=[]):

	# Can't parse if roster.csv is unavailable.
	if not os.path.exists(roster_csv):
		print ('No roster.csv found. Cannot parse roster.csv')
		return

	# SHOULD NOT HAPPEN.
	if not member_order:
		print ('No member_order supplied. Cannot parse roster.csv')
		return

	# Build char name lookup from portrait listing.
	char_lookup = {}
	for name in char_portraits:
		char_lookup[char_portraits[name].rsplit('_',1)[0]] = name

	# Pull full Roster Info from the roster.csv file.
	roster_csv_file = open(roster_csv, 'r', encoding='utf-8').readlines()

	# Iterate through each entry, building up a member dict with stats for each.
	for entry_row in roster_csv_file[1:]:

		entry = entry_row.split(',')

		member_name = remove_tags(entry[0])
		
		# TEMP: PULL NAMES FROM member_order AS NECESSARY.
		if not member_name:
			member_name = member_order[0]
		
		member_info = roster_csv_data.setdefault(member_name, {'processed_chars':{}, 'other_data':{}})
		
		char_name = char_lookup.get(entry[1])
		
		# SHOULD NOT HAPPEN. If lookup failed, we're missing the translation. Can't insert this data.
		if not char_name:
			print ("missing translation for",entry[1])
			continue
		
		# TEMP: IF CHAR_NAME ALREADY EXISTS, MOVE ON TO NEXT NAME.
		if char_name in member_info['processed_chars']:
			member_order.pop(0)
			member_name = member_order[0]
			member_info = roster_csv_data.setdefault(member_name, {'processed_chars':{}, 'other_data':{}})
		
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

