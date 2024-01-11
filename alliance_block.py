#!/usr/bin/env python3
# Encoding: UTF-8
"""alliance_block.py
Routines used to encode and decode the alliance info to/from a text block for easy transmission to the Discord Bot.

Re-uses routines from the standard process as much as possible.
"""


import string

from login           import login
from parse_cache     import build_parse_cache
from parse_contents  import remove_tags
from process_website import process_roster, add_strike_team_dividers
from extract_traits  import add_extracted_traits
from alliance_info   import update_history
from file_io         import *


# Use as many printable characters as possible. None of these cause problems in Discord or DOS.
ENCODING = string.digits + string.ascii_lowercase + string.ascii_uppercase + '!#$%+-./:;=?@[]{}~'


# Encode key info from alliance_info into something that fits in a DM.
def encode_block(alliance_info):
	block = []

	# Include basic info about the alliance.
	block.append(alliance_info['name'].replace(' ','_').replace('>','gt;').replace('<','lt;'))
	block.append(alliance_info['image'])
	block.append(alliance_info['stark_lvl'])
	block.append(alliance_info['trophies'])

	# Only members with a defined URL can be sent this way.
	encodable_members = [member for member in alliance_info['members'] if 'url' in alliance_info['members'][member]]

	encodable_leader   = [member for member in [alliance_info['leader']] if member in encodable_members]
	encodable_captains = [member for member in alliance_info['captains'] if member in encodable_members]

	captain_list  = encodable_leader + encodable_captains

	# Include the count of leader + captains.
	block.append(str(len(captain_list)))

	# Encode each member's URL.
	member_list = captain_list + [member for member in encodable_members if member not in captain_list]
	member_urls = [encode_url(alliance_info['members'][member]['url']) for member in member_list]
	block += member_urls

	# Encode the strike teams
	for team in ['incur','incur2','gamma']:
		encoded_team = ''
		for member in sum(alliance_info['strike_teams'][team],[]):
			if member in member_list:
				encoded_team += ENCODING[member_list.index(member)]
		block.append(encoded_team)
	
	# Smash it all together and hand it off.
	return ','.join(block)


# Decode the encoded block and populate alliance_info with stats and rosters from MSF.gg. 
def decode_block(block):
	
	alliance_info = {'members':{}}
	
	parts = block.strip().split(',')

	alliance_info['name']  = parts[0].replace('_',' ').replace('gt;','>').replace('lt;','<')
	alliance_info['image'] = parts[1]
	
	alliance_info['stark_lvl'] = parts[2]
	alliance_info['trophies']  = parts[3]

	leader_count = int(parts[4])
	
	# These are the encoded URL fragments
	member_urls = [decode_url(part) for part in parts[5:-2]]
	
	# These are the encoded Strike Teams
	encoded_strike_teams = {}
	encoded_strike_teams['incur'] = parts[-3]
	encoded_strike_teams['incur2'] = parts[-2]
	encoded_strike_teams['gamma'] = parts[-1]
	
	# Once we've parsed all the parts of the block, let's see if there's "cached_data-" + alliance_name + ".msf" file locally. 
	cached_alliance_info = load_cached_data(alliance_info['name'])
	
	# Then copy any members from the previous cached_data if they are still in the alliance. 
	# These will all be updated during roster refresh.
	for member in cached_alliance_info.setdefault('members',{}):
		if 'url' in cached_alliance_info['members'][member] and cached_alliance_info['members'][member]['url'] in member_urls:
			alliance_info.setdefault('members',{})[member] = cached_alliance_info['members'][member]

	# Copy over the old definitions to start. Will also be updated during or after roster refresh.
	for key in cached_alliance_info:
		if key not in alliance_info:
			alliance_info[key] = cached_alliance_info[key]

	# Use this cache to optimize our cached_data output.
	parse_cache = {}

	# Populate the parse_cache if we have existing history.  
	if 'hist' in alliance_info:
		build_parse_cache(alliance_info, parse_cache)
	
	# Start by logging in. 
	driver = login(headless=True)

	# Download and parse each roster, updating each entry
	member_list = []
	rosters_output = []
	for member_url in member_urls:
		driver.get('https://marvelstrikeforce.com/en/player/%s/characters' % member_url)

		# Note when we began processing
		start_time = datetime.datetime.now()

		member_name = process_roster(driver, alliance_info, parse_cache)
		member_list.append(member_name)

		# Did we find an updated roster? 
		last_update = alliance_info['members'][member_name].get('last_update')
		not_updated = last_update and last_update < start_time

		rosters_output.append(f'WEB - {member_name:17}'+['NEW',f'{(datetime.datetime.now() - last_update).days:>2}d'][not_updated])
		print (rosters_output[-1])

	# Close the Selenium session.
	driver.close()

	# Update our new alliance_info with the info from the block.
	alliance_info['leader']   = member_list[0]
	alliance_info['captains'] = member_list[1:leader_count]

	# Translate the Strike Teams from the encoded format.
	strike_teams = alliance_info.setdefault('strike_teams',{})
	
	for raid_type in ['incur','incur2','gamma']:
		strike_team = []
		for encoded_member in encoded_strike_teams[raid_type]:
			strike_team.append(member_list[ENCODING.index(encoded_member)])

		# Break it up into chunks and add the appropriate dividers.
		strike_teams[raid_type] = add_strike_team_dividers(strike_team, raid_type)

	# Populate extracted_traits if not present.
	add_extracted_traits(alliance_info)

	# Keep a copy of critical stats from today's run for historical analysis.
	update_history(alliance_info)
	
	# Write the collected roster info to disk in a subdirectory.
	write_cached_data(alliance_info, get_local_path()+'cached_data')

	return '\n'.join(rosters_output)


# Convert to Base 92 for shorter encoding.
def encode_url(decoded):

	# Start by removing any dashes and converting to base 10 int
	pid = int(decoded.replace('-',''),16)

	# Convert from base 10 to base 92.
	encoded = []
	while pid != 0:
		pid, mod = divmod(pid, len(ENCODING))
		encoded.append(ENCODING[mod])

	return ''.join(reversed(encoded))


# Decode from base 92 and insert hyphens as needed.
def decode_url(encoded):
	pid = 0
	
	for idx in range(len(encoded)-1,-1,-1):
		pid += ENCODING.index(encoded[idx]) * len(ENCODING)**(len(encoded)-1-idx)
	decoded = hex(pid)[2:].zfill(13)
	
	# If short format, we're done.
	if len(decoded)==13:
		return decoded

	# Long format includes dashes.
	decoded = decoded.zfill(32)
	return decoded[:8]+'-'+decoded[8:12]+'-'+decoded[12:16]+'-'+decoded[16:20]+'-'+decoded[20:]
	

