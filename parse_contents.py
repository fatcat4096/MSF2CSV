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
from parse_cache import update_parse_cache

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

	# Wrap the alliance_name if we found speical formatting.
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
	info_csv = open(driver.info_csv, 'r', encoding='utf-8').readlines()
	
	# Iterate through each entry, building up a member dict with stats for each.
	for member_row in info_csv[1:]:
		member = {}

		member_row = member_row.strip().split(',')

		# Remove HTML tags if present.
		member_name = remove_tags(member_row[2])

		# Process role information.
		member_role     = member_row[1]
		if member_role == 'leader':
			alliance['leader'] = member_name
		elif member_role == 'captain':
			captains.append(member_name)

		member['url']   = member_row[0]
		member['image'] = member_row[3].split('Portrait_')[-1][:-4]
		member['frame'] = member_row[4].split('ICON_FRAME_')[-1][:-4]
		member['level'] = int(member_row[5])
		member['tcp']   = int(member_row[7])
		member['stp']   = int(member_row[8])
		member['mvp']   = int(member_row[9])
		member['tcc']   = int(member_row[10])
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
def parse_roster(contents, alliance_info, parse_cache, member='', roster_csv='', roster_csv_data={}):
	soup = BeautifulSoup(contents, 'html.parser')

	# Sanitize the Player Name (remove html tags) and report which panel we're working on.
	#player_name = remove_tags(player_name.text)

	# Have no choice but to accept the inbound Member Name
	# Name on the HTML is for the login user.
	player_name = member

	player_info = {}

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

			# For total roster calculation.
			tot_power += int(power)
			
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
				iso_class = alliance_info.get('members',{}).get(player_name,{}).get('other_data',{}).get(char_name,0)%6

			processed_chars[char_name] = {'power':int(power), 'lvl':int(level), 'tier':int(tier), 'iso':int(iso), 'yel':yelStars, 'red':redStars, 'dmd':0, 'abil':int(bas+spc+ult+pas)}
			other_data[char_name]      = favorite+iso_class

		# Entries for Heroes not yet collected, no name on final entry for page.
		elif char_name:
			processed_chars[char_name] = {'power':0, 'lvl':0, 'tier':0, 'iso':0, 'yel':0, 'red':0, 'dmd':0, 'abil':0}
			other_data[char_name]      = 0

	# Finally, after we've processed everything else traditionally.
	# Fill the roster_csv_data structure if not yet populated.
	if roster_csv and not roster_csv_data:
		roster_csv_data = parse_roster_csv_data(roster_csv, char_portraits)

	# Should NOT happen.
	if player_name not in roster_csv_data:
		print ("Look into this. Why isn't",player_name,"in the roster_csv_data structure?")

	# Final stages -- fix any data that needs supplemental information from roster.csv and then optimize the alliance_info data structure
	for char_name in processed_chars:
		
		if char_name in roster_csv_data.get(player_name,{}):
			# Set Diamond data appropriately.
			processed_chars[char_name]['dmd'] = roster_csv_data[player_name][char_name].get('dmd',0)

			# If still no ISO Class data, look for it in the roster_csv_data.
			if not other_data[char_name]%6:
				other_data[char_name] += roster_csv_data[player_name][char_name].get('cls',0)

		# Should not be happening.
		elif processed_chars.get(char_name,{}).get('power'):
			print (f'* {player_name} -- {char_name} not found in roster.csv')
		
		# Look for a duplicate entry in our cache and point both to the same entry if possible.
		update_parse_cache(processed_chars,char_name,parse_cache)

	# Calculate level based on character leveling.

	# Use Alliance Info information if it's available.

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
	player['display_name']    = member

	# Temporary fix. Calculate values if possible.
	calc_lvl             = max([processed_chars[char_name].get('lvl',0) for char_name in processed_chars]) if processed_chars else 0
	calc_stp             = sum(sorted([processed_chars[member]['power'] for member in processed_chars], reverse=True)[:5])
	calc_tcc             = len([char for char in processed_chars if processed_chars[char]['power']])
	player_info['max']   = len([char for char in processed_chars if processed_chars[char]['yel']==7])
	player_info['stars'] = sum([processed_chars[char]['yel'] for char in processed_chars])
	player_info['red']   = sum([processed_chars[char]['red'] for char in processed_chars])

	# Only use calculated TCP, STP, and TCC if higher than the recorded values in Alliance Info.
	player_info['level'] = max(calc_lvl,  alliance_info['members'].get(member,{}).get('level',0))
	player_info['tcp']   = max(tot_power, alliance_info['members'].get(member,{}).get('tcp',0))
	player_info['stp']   = max(calc_stp,  alliance_info['members'].get(member,{}).get('stp',0))
	player_info['tcc']   = max(calc_tcc,  alliance_info['members'].get(member,{}).get('tcc',0))

	# And update the player info with current stats from the side panel.
	player.update(player_info)
	
	# Update alliance_info with portrait information.
	alliance_info['portraits'] = char_portraits

	# Keep the scripts in use up to date in alliance_info. Will be used by extract_traits.
	scripts = [script.get('src') for script in soup.findAll('script', attrs = {'type':'text/javascript'}) if script.get('src') and 'static' in script.get('src')]
	if scripts:
		alliance_info['scripts'] = scripts

	return player_name



# Parse the Diamond data directly from the roster.csv file.
@timed(level=3)
def parse_roster_csv_data(roster_csv, char_portraits):

	roster_csv_data = {}

	# Can't parse if diamond data is unavailable.
	if not os.path.exists(roster_csv):
		return roster_csv_data

	# Pull full Roster Info from the roster.csv file.
	roster_csv = open(roster_csv, 'r', encoding='utf-8').readlines()

	# Build char name lookup from portrait listing.
	char_lookup = {}
	for name in char_portraits:
		char_lookup[char_portraits[name].rsplit('_',1)[0]] = name
		
	# Build up an index of the fields.
	index_line = roster_csv[0].strip().split(',')
	index_dict = {}
	for idx, item in enumerate(index_line):
		if item.count('.')<2:
			continue
		item = item.split('.',2)
		entry = index_dict.setdefault(item[1],{})
		entry[item[-1]] = idx

	# Iterate through each entry, building up a member dict with stats for each.
	for member_row in roster_csv[1:]:

		member = {}

		member_row  = member_row.split(',')
		member_name = remove_tags(member_row[1])
		
		for item in index_dict:
			char_id_idx  = index_dict[item].get('id')
			char_red_idx = index_dict[item].get('activeRed')
			char_cls_idx = index_dict[item].get('iso8.active')

			# Should not happen.
			if not char_id_idx:
				continue

			# Abort if no char defined -- member hasn't recruited all heroes yet.
			char_id = member_row[char_id_idx]
			if not char_id:
				continue
				
			# Translate from internal ID to human readable name.
			char_name = char_lookup.get(char_id)

			# Should not happen.
			if not char_name:
				print ('ERROR: Could not find translation for:',char_id)
				continue

			# Create the entry to hold data.
			char_entry = roster_csv_data.setdefault(member_name,{}).setdefault(char_name, {})

			# Translate from Active Red to Diamond count.
			if char_red_idx:
				char_red = member_row[char_red_idx]
				char_dmd = max(0,int(char_red)-7) if char_red else 0
				char_entry['dmd'] = char_dmd

			# Translate from ISO Class literal to internal representation.
			if char_cls_idx:
				char_cls = member_row[char_cls_idx]
				char_cls = {
					'fortifier': 1,
					'healer': 2,
					'skirmisher': 3,
					'raider': 4,
					'striker': 5,
				}.get(char_cls,0)

				# Add this entry to the roster_csv_data.
				char_entry['cls'] = char_cls

	return roster_csv_data
