#!/usr/bin/env python3
# Encoding: UTF-8
"""msf_shared.py
Routines shared between /alliance and /roster and interacting with msf2csv.py.
"""

import os
import sys
import asyncio
import pickle
import traceback
import re
import glob
import json

import discord
from discord.ext.commands import Context
from discord.app_commands import Choice

from datetime   import datetime
from functools  import partial
from enum       import Enum
from subprocess import Popen, CREATE_NEW_CONSOLE



# Ensure MSF2CSV is in our path.
msf2csv_path = r'C:\Users\baker\Dev\MSF'
if msf2csv_path not in sys.path:
	sys.path.insert(0,msf2csv_path)

import msf2csv
from log_utils import timed, ansi, find_log_file



# Required for CLIENT_TOKEN for use by MSF API
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Precalculate the CLIENT_TOKEN for MSF API access
CLIENT_TOKEN = msf2csv.construct_token(os.getenv('CLIENT_ID'), os.getenv('CLIENT_SECRET'))



#888888b.  8888888888 888888b.   888     888  .d8888b.       888     888 88888888888 8888888 888      .d8888b.  
#88  "Y88b 888        888  "88b  888     888 d88P  Y88b      888     888     888       888   888     d88P  Y88b 
#88    888 888        888  .88P  888     888 888    888      888     888     888       888   888     Y88b.      
#88    888 8888888    8888888K.  888     888 888             888     888     888       888   888      "Y888b.   
#88    888 888        888  "Y88b 888     888 888  88888      888     888     888       888   888         "Y88b. 
#88    888 888        888    888 888     888 888    888      888     888     888       888   888           "888 
#88  .d88P 888        888   d88P Y88b. .d88P Y88b  d88P      Y88b. .d88P     888       888   888     Y88b  d88P 
#888888P"  8888888888 8888888P"   "Y88888P"   "Y8888P88       "Y88888P"      888     8888888 88888888 "Y8888P"  



# Abstract is_owner() so I can selectively disable my Owner status
async def is_owner(self, context):
	return not msf2csv.get_cached('disable_owner') and await self.bot.is_owner(context.author)



# Abstract the flag for DISABLE_REFRESH so I can selectively disable /roster refresh without relaunch
async def refresh_disabled(self, context):
	return msf2csv.get_cached('disable_refresh') and not await is_owner(self, context)



#888888b. 8888888 .d8888b.   .d8888b.   .d88888b.  8888888b.  8888888b.       888b    888        d8888 888b     d888 8888888888      888     888 88888888888 8888888 888      .d8888b.  
#88  "Y88b  888  d88P  Y88b d88P  Y88b d88P" "Y88b 888   Y88b 888  "Y88b      8888b   888       d88888 8888b   d8888 888             888     888     888       888   888     d88P  Y88b 
#88    888  888  Y88b.      888    888 888     888 888    888 888    888      88888b  888      d88P888 88888b.d88888 888             888     888     888       888   888     Y88b.      
#88    888  888   "Y888b.   888        888     888 888   d88P 888    888      888Y88b 888     d88P 888 888Y88888P888 8888888         888     888     888       888   888      "Y888b.   
#88    888  888      "Y88b. 888        888     888 8888888P"  888    888      888 Y88b888    d88P  888 888 Y888P 888 888             888     888     888       888   888         "Y88b. 
#88    888  888        "888 888    888 888     888 888 T88b   888    888      888  Y88888   d88P   888 888  Y8P  888 888             888     888     888       888   888           "888 
#88  .d88P  888  Y88b  d88P Y88b  d88P Y88b. .d88P 888  T88b  888  .d88P      888   Y8888  d8888888888 888   "   888 888             Y88b. .d88P     888       888   888     Y88b  d88P 
#888888P" 8888888 "Y8888P"   "Y8888P"   "Y88888P"  888   T88b 8888888P"       888    Y888 d88P     888 888       888 8888888888       "Y88888P"      888     8888888 88888888 "Y8888P" 



async def get_discord_name(self, context, discord_id):

	# Short circuit for base case
	if not discord_id:
		return

	if type(discord_id) is str:
		discord_id = int(discord_id)

	# If passed an int for discord_id, determine whether channel or user.
	if type(discord_id) is int:
		
		# Short circuit if it's in our context
		if discord_id == context.author.id:
			return context.author.name
		elif discord_id == context.channel.id:
			return get_discord_channel_name(context.channel)

		# See if we have it cached
		found_cached = self.bot.get_user(discord_id)
		if found_cached:
			return found_cached.name
		found_cached = self.bot.get_channel(discord_id)
		if found_cached: 
			return get_discord_channel_name(found_cached)

		# See if it's a user...
		try:
			found_user    = await self.bot.fetch_user(discord_id)
			# Success!
			return found_user.name
		except:
			pass

		# See if it's a channel...
		try:
			found_channel = await self.bot.fetch_channel(discord_id)	
			# Success!
			return get_discord_channel_name(found_channel)
		except:
			return

	# If a user, just return user name
	if type(discord_id) == type(context.author):
		return discord_id.name

	# If a channel, do channel things
	if type(discord_id) == type(context.channel):
		return get_discord_channel_name(discord_id)

	#print ('Could NOT find a match:',discord_id)



def get_discord_channel_name(channel):

	# In Private Channel/DM
	if 'private' == channel.type.name:
		return f'Private/DM ({channel.recipient.name})'
	# In Thread
	elif 'thread' in channel.type.name and channel.parent:
		return f'{channel.parent.name}/{channel.name}'
	# In Thread
	elif 'thread' in channel.type.name:
		return f'{channel.name} (Thread)'
	# In Group Discussion
	elif 'group' == channel.type.name:
		print (channel.recipients)
		return f'Group Discussion'
	
	# In Channel
	return channel.name



       #8888 888     888 88888888888 888    888      888     888 88888888888 8888888 888      .d8888b.  
      #88888 888     888     888     888    888      888     888     888       888   888     d88P  Y88b 
     #88P888 888     888     888     888    888      888     888     888       888   888     Y88b.      
    #88P 888 888     888     888     8888888888      888     888     888       888   888      "Y888b.   
   #88P  888 888     888     888     888    888      888     888     888       888   888         "Y88b. 
  #88P   888 888     888     888     888    888      888     888     888       888   888           "888 
 #8888888888 Y88b. .d88P     888     888    888      Y88b. .d88P     888       888   888     Y88b  d88P 
#88P     888  "Y88888P"      888     888    888       "Y88888P"      888     8888888 88888888 "Y8888P"  



def age_of(expires_at):
	if type(expires_at) == str:
		expires_at = int(expires_at)
	if type(expires_at) in (int, float):
		expires_at = datetime.fromtimestamp(expires_at)
	return datetime.now() - expires_at



def expired_cant_refresh(expires_at, refresh_token):
	return age_of(expires_at).days >= (30 if refresh_token else 0)
	


async def send_auth_link(self, context: Context) -> None:

	# Provide a link to connect account to RosterBot
	AUTH_URL = await get_auth_url(self, context)

	# Send the link per request
	await send_rosterbot_embed(self, context, 'Link to Account', f'[**CLICK HERE**]({AUTH_URL}) to log onto the MSF website and authorize MSF RosterBot to access roster data.', ephemeral=True, delete_after=30)



# Generate a URL to link account
async def get_auth_url(self, context):

	# Check to see if there's already a recent session_key
	SESSION_ID = await self.bot.database.get_session_key(context.author.id, only_recent=True)	

	# Get the Session ID and Link URL to use
	SESSION_ID, LINK_URL = msf2csv.get_session_and_link(os.getenv("CLIENT_ID"), SESSION_ID)

	# Store the shared secret as the session_id
	await self.bot.database.save_session_key(context.author.id, SESSION_ID, context.author.name)	

	# Log the generated key for reference
	self.bot.logger.info(f"Link URL requested! Generated Session ID: {ansi.bold}{SESSION_ID}{ansi.reset}")

	return LINK_URL



#
# Find a valid AUTH for this context / user and request refresh if expired.
# If alliance name has changed and is a DIFFERENT alliance, only allow owner to use
#

# Look for a stored Auth for this user. 
async def get_valid_auth(self, context, alliance_name=None, discord_id=None, silent=False):	

	# Start search for auth on USER (want to use own AUTH if possible)
	if not discord_id:
		avail_auths = await self.bot.database.get_auths_by_owner(context.author.id)
		if alliance_name in avail_auths:
			discord_id = context.author.id
			
	# Search for match for alliance_name in CHANNEL DEFAULT -- if matching, get default auth_id for CHANNEL
	if not discord_id and alliance_name == await self.bot.database.get_default_alliance_name(context.channel.id):
		discord_id = await self.bot.database.get_default_auth_id(context.channel.id)
		
	# Search for match for allinace_name in USER DEFAULT -- if matching, get default auth_id for USER
	if not discord_id and alliance_name == await self.bot.database.get_default_alliance_name(context.author.id):
		discord_id = await self.bot.database.get_default_auth_id(context.author.id)

	# If still no matching discord_id and is_owner()
	if not discord_id and await is_owner(self, context):
		AVAIL_AUTHS = await self.bot.database.get_all_auths()
		discord_id  = AVAIL_AUTHS.get(alliance_name)

	# Look for an entry in the database
	AUTH = await self.bot.database.get_auth(discord_id, alliance_name) if discord_id else None

	# If no AUTH found or no chance of refresh, just return (AUTH = None)
	if not AUTH or expired_cant_refresh(AUTH['expires_at'], AUTH['refresh_token']):
		return

	# If we found an AUTH but is expired, try to refresh
	if not msf2csv.auth_valid(AUTH):

		response = msf2csv.refresh_auth(AUTH, CLIENT_TOKEN)

		# If unable to refresh, log the response and return AUTH = None
		if not(response.ok and AUTH.get('updated') and msf2csv.auth_valid(AUTH)):
			print (f"{ansi.ltred}AUTH REFRESH FAILED:{ansi.reset}")
			print (f"{ansi.bold}Error {response.status_code}: {ansi.ltyel}{response.reason}{ansi.reset}")
			print (f"{ansi.bold}Response:{ansi.reset}\n{json_dumps(response.json())}")
			return

		# AUTH was refreshed, store in the database.
		await self.bot.database.save_auth(AUTH)	

	# Now have AUTH and AUTH is valid

	# Let's fill the base alliance_info structure and get the current alliance_name
	response, alliance_info = msf2csv.get_alliance_api(AUTH)
	
	# If not valid alliance_info, it's an error message
	failed_on = '' if type(alliance_info) is dict else alliance_info

	# If an error occurred, report the error and return AUTH = None
	if failed_on:
		await api_request_failed(self, None if silent else context, response, failed_on)
		return

	# Otherwise, we are good to go, populate AUTH with this info 
	AUTH['alliance_info']      = alliance_info
	AUTH['alliance_name_curr'] = alliance_info.get('name')

	# Get the cached_info for the old alliance_name
	alliance_info_old = find_cached_data(AUTH['alliance_name'])

	# Note if any members have changed
	AUTH['same_members'] = alliance_info_old.get('members',{}).keys() == alliance_info.get('members',{}).keys()

	# If Alliance Name has changed, determine whether same alliance or alliance has changed
	if AUTH['alliance_name'] != AUTH['alliance_name_curr']:

		# Compare lists of members between the two, make note if same alliance
		AUTH['same_alliance'] = AUTH['same_members'] or msf2csv.similar_members(alliance_info_old.get('members',{}), alliance_info.get('members',{}))

		# If NOT same alliance and requester isn't owner, DO NOT ALLOW USE, just return (AUTH = None)
		if not AUTH['same_alliance'] and context and context.author.id != AUTH['discord_id'] and not await is_owner(self, context):
			return

	return AUTH



async def log_auth_row(self, discord_id, alliance_name, message=''):
	row = (await self.bot.database.get_table_rows('auth_id', discord_id, alliance_name)).pop(f'{discord_id}{alliance_name}')
	self.bot.logger.info(format_auth_row(row) + f' {ansi.yellow}{message}{ansi.reset}')



async def log_alliance_row(self, discord_id, message=''):
	row = (await self.bot.database.get_table_rows('default_alliance', discord_id)).pop(str(discord_id)	)
	self.bot.logger.info(format_alliance_row(*row, skip_auth=True) + f' {ansi.yellow}{message}{ansi.reset}')



# Update alliance default and report results
async def update_default_alliance_name(self, ALLIANCE_NAME_NEW, discord_id):

	# Actually make the change, updating default alliance with new Alliance Name
	await self.bot.database.update_default_alliance_name(discord_id, ALLIANCE_NAME_NEW)

	# Verify and report the changes made
	await log_alliance_row(self, discord_id, message='Changed alliance name')



# Remove revoked / expired AUTH from any alliance defaults			
async def remove_auth_id_from_defaults(self, alliance_name, discord_id, message):
			
	# Get ALL DEFAULT ENTRIES (users and channels) WHERE alliance_name == alliance of REVOKING USER, auth_id == discord_id of REVOKING USER
	remove_auth_ids = await self.bot.database.get_discord_ids_from_defaults(alliance_name, discord_id)

	# Log what we're about to do only if there are candidates that need removal
	if remove_auth_ids:
		self.bot.logger.info(message)

	# Set default for ALL THESE ENTRIES to just discord_id -- remove the auth_id from these entries
	for remove_id in remove_auth_ids:

		# Actually make the change, updating default alliance and removing Auth ID
		await self.bot.database.update_default_auth_id(remove_id, None)

		# Verify and report the changes made
		await log_alliance_row(self, remove_id, message='Removed default AUTH')



       #8888 888      888      8888888        d8888 888b    888  .d8888b.  8888888888      888     888 88888888888 8888888 888      .d8888b.  
      #88888 888      888        888         d88888 8888b   888 d88P  Y88b 888             888     888     888       888   888     d88P  Y88b 
     #88P888 888      888        888        d88P888 88888b  888 888    888 888             888     888     888       888   888     Y88b.      
    #88P 888 888      888        888       d88P 888 888Y88b 888 888        8888888         888     888     888       888   888      "Y888b.   
   #88P  888 888      888        888      d88P  888 888 Y88b888 888        888             888     888     888       888   888         "Y88b. 
  #88P   888 888      888        888     d88P   888 888  Y88888 888    888 888             888     888     888       888   888           "888 
 #8888888888 888      888        888    d8888888888 888   Y8888 Y88b  d88P 888             Y88b. .d88P     888       888   888     Y88b  d88P 
#88P     888 88888888 88888888 8888888 d88P     888 888    Y888  "Y8888P"  8888888888       "Y88888P"      888     8888888 88888888 "Y8888P"  



# Verify whether member is under the minimum level or Bot Owner
async def under_min(self, context, alliance_name, min):
	return min in ('captain','leader') and not (get_member_role(alliance_name, context.author.id) in (min, 'leader','admin') or await is_owner(self, context))



# THIS USES SPECIFIC SELECTION ORDER -> Channel / User / Owned AUTHs
# Keeps looking if found alliance is less than min role level

# Return ONE matching alliance
async def get_one_alliance(self, context: Context, min: str='') -> str:

	# Default on channel always takes priority
	alliance_name = await self.bot.database.get_default_alliance_name(context.channel.id)

	# If none found, or not high enough -- Default on user is next 
	if not alliance_name or await under_min(self, context, alliance_name, min):
		alliance_name = await self.bot.database.get_default_alliance_name(context.author.id)
	
	# If none found, or not high enough -- Check auths on user last 
	if not alliance_name or await under_min(self, context, alliance_name, min):
		for alliance_name in sorted(await self.bot.database.get_auths_by_owner(context.author.id)):
			if not await under_min(self, context, alliance_name, min):
				break

	if alliance_name and await under_min(self, context, alliance_name, min):
		alliance_name = ''

	return alliance_name



# Returns ALL AVAILABLE alliances on a user/channel combo
# Used by auto-complete routines, filters on min role and for only_auths

async def get_all_avail_alliances(self, context: Context, min: str='', only_auths=False) -> list:
	
	# Get names from user auths
	avail_alliances = await self.bot.database.get_auths_by_owner(context.author.id)
	
	# Get names from explicitly defined defaults from context author and channel
	if not only_auths:
		default_alliances = {await self.bot.database.get_default_alliance_name(discord_id) for discord_id in (context.author.id, context.channel.id)}
		avail_alliances = avail_alliances.union({x for x in default_alliances if x})

	# purge entries if less than min
	if min in ('captain','leader'):
		for alliance_name in list(avail_alliances):
			if get_member_role(alliance_name, context.author.id) not in (min, 'leader','admin'):
				avail_alliances.remove(alliance_name)

	return sorted(avail_alliances)



# Use combination of Channel/User Defaults and AUTHs owned by user to determine which Alliances should be offered.

async def get_avail_alliances(self, context: Context, discord_id=None) -> set:

	# Allow alt discord_id to be passed in. Assume context.author.id if none provided.
	if not discord_id:
		discord_id = context.author.id

	# Start with the AUTHS list from the author
	selection_set = await self.bot.database.get_auths_by_owner(discord_id)

	# First, check for a CHANNEL DEFAULT
	CHANNEL_DEFAULT = await self.bot.database.get_default_alliance_name(context.channel.id)

	# If there is a CHANNEL DEFAULT defined...
	if CHANNEL_DEFAULT:

		# If CHANNEL DEFAULT matches any AUTHS in selection set, use it
		if CHANNEL_DEFAULT in selection_set:
			return {CHANNEL_DEFAULT}

		# Otherwise, add to our selection set
		selection_set.add(CHANNEL_DEFAULT)

	# Next, check for a USER DEFAULT
	USER_DEFAULT = await self.bot.database.get_default_alliance_name(discord_id)

	# If there is a USER DEFAULT defined...
	if USER_DEFAULT:
	
		# If USER DEFAULT matches any AUTHS in our selection set, use it
		if USER_DEFAULT in selection_set and (USER_DEFAULT == CHANNEL_DEFAULT or not CHANNEL_DEFAULT):
			return {USER_DEFAULT}
		
		# Otherwise, add to our selection set
		selection_set.add(USER_DEFAULT)

	# If not, return the list of available alliances
	return selection_set



# This seems like it should be elsewhere or higher?

# Returns a dict of valid AUTHs using above selection methods
# Dict is filled with key=alliance_name, value=discord_id
async def get_avail_auths(self, context: Context) -> dict:

	# Get a list of the AUTHs owned by this user
	avail_auths = {alliance_name:context.author.id for alliance_name in await self.bot.database.get_auths_by_owner(context.author.id)}

	# First, check for a CHANNEL DEFAULT
	CHANNEL_DEFAULT = await self.bot.database.get_default_alliance_name(context.channel.id)

	# If there is a CHANNEL DEFAULT defined...
	if CHANNEL_DEFAULT:

		# If CHANNEL DEFAULT matches any AUTHS in selection set, use this auth
		if CHANNEL_DEFAULT in avail_auths:
			return {CHANNEL_DEFAULT:context.author.id}

		# Otherwise, if auth is on channel, add to our avail_auths
		auth_on_channel = await self.bot.database.get_default_auth_id(context.channel.id)
		if auth_on_channel:
			avail_auths[CHANNEL_DEFAULT] = auth_on_channel

	# Next, check for a USER DEFAULT
	USER_DEFAULT = await self.bot.database.get_default_alliance_name(context.author.id)

	# If there is a USER DEFAULT defined...
	if USER_DEFAULT:
	
		# If USER DEFAULT matches any AUTHS in our selection set, use it
		if USER_DEFAULT in avail_auths and not CHANNEL_DEFAULT:
			return {USER_DEFAULT:context.author.id}

		# Otherwise, if default auth is on user, add to our avail_auths
		auth_on_user = await self.bot.database.get_default_auth_id(context.author.id)
		if auth_on_user:
			avail_auths[USER_DEFAULT] = auth_on_user

			# If the default on this user matches the default for the channel use it
			if USER_DEFAULT == CHANNEL_DEFAULT:
				return {USER_DEFAULT:auth_on_user}

	# If not, return the list of alliances with available AUTHs
	return avail_auths



  #8888b.  888    888  .d88888b. 8888888 .d8888b.  8888888888             d88P      888b     d888 8888888888 888b    888 888     888      888     888 88888888888 8888888 888      .d8888b.  
#88P  Y88b 888    888 d88P" "Y88b  888  d88P  Y88b 888                   d88P       8888b   d8888 888        8888b   888 888     888      888     888     888       888   888     d88P  Y88b 
#88    888 888    888 888     888  888  888    888 888                  d88P        88888b.d88888 888        88888b  888 888     888      888     888     888       888   888     Y88b.      
#88        8888888888 888     888  888  888        8888888             d88P         888Y88888P888 8888888    888Y88b 888 888     888      888     888     888       888   888      "Y888b.   
#88        888    888 888     888  888  888        888                d88P          888 Y888P 888 888        888 Y88b888 888     888      888     888     888       888   888         "Y88b. 
#88    888 888    888 888     888  888  888    888 888               d88P           888  Y8P  888 888        888  Y88888 888     888      888     888     888       888   888           "888 
#88b  d88P 888    888 Y88b. .d88P  888  Y88b  d88P 888              d88P            888   "   888 888        888   Y8888 Y88b. .d88P      Y88b. .d88P     888       888   888     Y88b  d88P 
  #8888P"  888    888  "Y88888P" 8888888 "Y8888P"  8888888888      d88P             888       888 8888888888 888    Y888  "Y88888P"        "Y88888P"      888     8888888 88888888 "Y8888P"  



# Convert a list of dict into a pre-processed list of Discord Choices
# Name (which is displayed) is normal, Value (used for searching) is all lowercase.
def get_choices(LIST_OR_DICT):
	return [Choice(name=choice,value=choice.lower()) for choice in LIST_OR_DICT]



# Generic build of Autocomplete menu choices.
def get_choice_list(current, CHOICE_LIST, max_return=15):

	CHOICES = []
	SECOND_LIST = []

	# Remove special characters
	current = re.sub(r'\W+','', current).lower()

	# Start by looking for exact matches
	for choice in CHOICE_LIST:
		
		# If we found a match, add it to the list
		if current in choice.value:
			CHOICES.append(choice)

			# Short circuit at 15, should be enough
			if len(CHOICES) == max_return: 
				return CHOICES
		else:
			SECOND_LIST.append(choice)

	# Follow up with a second pass for a partial match
	current = re.compile(f".*{'.*'.join(current)}.*")

	for choice in SECOND_LIST:

		# If we found a match, add it to the list
		if current.match(choice.value):
			CHOICES.append(choice)

			# Short circuit at 15, should be enough
			if len(CHOICES) == max_return: 
				return CHOICES

	return CHOICES



def get_alliance_names_from_files():
	return [msf2csv.decode_tags(os.path.basename(x)[12:-4]) for x in glob.iglob(f'{msf2csv.get_local_path()}{os.sep}cached_data{os.sep}cached_data-*.msf')]



# Redirect to allow inclusion of all auths/alliance names if no list provided
async def get_choices_from_alliance_names(self, context, current, ALLIANCE_NAMES=[], refresh_avail=[], only_auths=False):

	# If no Alliance Names provided and bot owner requesting, use entire list of alliances instead
	if not ALLIANCE_NAMES:

		# Short circuit if not Owner
		if not await is_owner(self, context):
			return []

		AUTHS_AVAIL = await self.bot.database.get_all_auths()

		# Return the list of active AUTHs in the database
		ALLIANCE_NAMES = sorted(AUTHS_AVAIL)
		
		# Also include options from all cached_data filenames
		if not only_auths:
			ALLIANCE_NAMES += get_alliance_names_from_files()
			
		# Note which Alliances have AUTHs available
		if refresh_avail:
			refresh_avail = AUTHS_AVAIL

	ENTRIES = get_entries_from_alliance_list(ALLIANCE_NAMES, current, refresh_avail)

	return [Choice(name=choice,value=ENTRIES[choice]) for choice in ENTRIES]




# Generate a Choice list from encoded Alliance Names
# Use plaintext for name if no dupes/collision, value is encoded version
def get_entries_from_alliance_list(ALLIANCE_NAMES, current='', refresh_avail=[]):

	# Initialize variables
	ENTRIES = {}
	dupes   = set()

	# If provided a string, build a regular expression to match on this string
	current = re.sub(r'\W+','', current).lower()
	current = re.compile('.*'+'.*'.join(current)+'.*')

	for choice in sorted(ALLIANCE_NAMES, key=lambda x: msf2csv.remove_tags(x)):

		cleaned = msf2csv.remove_tags(choice)

		# Differentiate if some have refresh
		if refresh_avail:
			cleaned += ' (refresh avail)' if choice in refresh_avail else ' (reports only)'
			
		# If we found a match, add it to the list
		if current.match(cleaned.lower()):

			# Check to see if we have a collision
			if cleaned in ENTRIES:
				# Note that we had a collision and must treat additional collisions similarly
				dupes.add(cleaned)
				# Use original name instead for first collision
				redone = ENTRIES[cleaned]
				ENTRIES[redone] = ENTRIES.pop(cleaned)
				# Use original name instead for new entry
				ENTRIES[choice] = choice
			# If we'd previous had a collision with this name
			elif cleaned in dupes:
				# Use original name instead for new entry
				ENTRIES[choice] = choice
			# Otherwise, use the simplified Alliance Name
			else:
				ENTRIES[cleaned] = choice

			# Short circuit if we have enough
			if len(ENTRIES) == 15: 
				break

	return ENTRIES



async def defer_if_is_private(context):
	in_private = await is_private(context)
	
	if in_private:
		try:	await context.interaction.response.defer(ephemeral=True)
		except:	pass

	return in_private


async def is_private(context):
	PREFS = await get_prefs(context)

	private_mode = PREFS.get('private_mode', False)
	safe_server  = PREFS.get('safe_server',  {})
	safe_channel = PREFS.get('safe_channel', {})

	# If we're in private mode, return False only if the guild or channel we are in is considered SAFE.
	return private_mode and not ((context.guild and context.guild.id in safe_server) or (context.channel.id in safe_channel))



async def get_prefs(context):
	# Get the cached user pref
	PREFS = msf2csv.get_cached(f'defaults-{context.author.id}').get('prefs',{})

	return PREFS



async def get_default(self, context, func_name=None, var_name=None):

	# Accommodate Discord ID passed in directly
	discord_id = context if type(context) is int else context.author.id

	# Get the cached defaults
	cached_defaults = msf2csv.get_cached(f'defaults-{discord_id}')
		
	# Return one function or the entire set of defaults?
	if not func_name:
		return cached_defaults
		
	current_settings = cached_defaults.get(func_name,{})

	# Return one var value or the entire set of vars?
	return current_settings.get(var_name) if var_name else current_settings



async def get_set_defaults(locals):

	# Should always be present
	self     = locals.get('self')
	context  = locals.get('context')
	defaults = locals.get('defaults')

	# Use context to get the discord_id, func_name, and command signature
	discord_id = context.author.id
	func_name  = context.command.qualified_name
	params     = context.command.params
	
	# Get the cached defaults.
	cached_defaults = msf2csv.get_cached(f'defaults-{discord_id}')

	# RESET DEFAULTS -- Clear cached_defaults and don't load new settings back in
	if defaults and 'reset' in defaults:
		cached_defaults[func_name] = {}
		current_settings           = {}
	# LOAD DEFAULTS or SAVE DEFAULTS -- Start with the current cached_defaults
	else:
		current_settings = cached_defaults.setdefault(func_name,{})

	# Pull optional values from function call to override pre-defined defaults
	for param in params:
		if locals.get(param) is not None and not params[param].required and param != 'defaults':
			current_settings[param] = locals[param]

	# Remove any Enums or Discord Choices. Just deal with ints.
	for param in current_settings:
		if isinstance(current_settings[param], Enum) or isinstance(current_settings[param], Choice):
			current_settings[param] = current_settings[param].value

	# If SAVE DEFAULTS or RESET DEFAULTS, update this player's cached_defaults
	if defaults and ('save' in defaults or 'reset' in defaults):
		msf2csv.set_cached(f'defaults-{discord_id}', cached_defaults)

	# Get a little closer to our work
	PREFS = cached_defaults.get('prefs',{})

	# Special Handling for owner
	if defaults and await is_owner(self, context) and not auto_fix(['Save Defaults','Reset Defaults'], defaults):

		# Search active Authorizations first
		alliance_name = auto_fix(await self.bot.database.get_all_auths(), defaults)

		# If not found, perhaps it's a filename
		if not alliance_name:
			alliance_name = auto_fix(get_alliance_names_from_files(), defaults)

		# Store this to be picked up in the slash command
		current_settings['alliance_name'] = alliance_name

		# If requesting for another alliance, mark as private so will be sent Ephemeral
		current_settings['in_private'] = True

	# Defer as ephemeral if is_private()
	elif PREFS.get('private_mode', False):
		safe_server  = PREFS.get('safe_server', {})
		safe_channel = PREFS.get('safe_channel', {})

		# If we are in private_mode and this is NOT a safe space, mark as private
		if not ((context.guild and context.guild.id in safe_server) or (context.channel.id in safe_channel)):
			current_settings['in_private'] = True

	# If is_private, go ahead and request deferral as Ephemeral
	if current_settings.get('in_private'):
		try:	await context.interaction.response.defer(ephemeral=True)
		except:	pass

	return current_settings



# Leverage auto_fix to fix our autocomplete entries.
def auto_val(VALID_SELECTIONS, selection_or_list):

	val = auto_fix(VALID_SELECTIONS, selection_or_list)

	if type(VALID_SELECTIONS) == dict:
		return VALID_SELECTIONS.get(val, val)
	elif type(VALID_SELECTIONS) == list:
		return VALID_SELECTIONS.index(val) if val in VALID_SELECTIONS else val
	return val



# Leverage find_selection to fix our autocomplete entries.
def auto_fix(VALID_SELECTIONS, selection_or_list):

	arg_list = [selection_or_list] if type(selection_or_list) is str else selection_or_list

	# Bail if we have no args to iterate.
	if arg_list is None:
		return None

	arg_list = [find_selection(VALID_SELECTIONS, arg) for arg in arg_list]
	arg_list = [arg for arg in arg_list if arg in VALID_SELECTIONS]

	if type(selection_or_list) is str:
		return arg_list[0] if arg_list else ''

	return arg_list



# Do a sloppy search through autocomplete lists if exact entry isn't included.
def find_selection(item_list, selection):

	# Base case, nothing to process.
	if not selection:
		return

	# Exact match!
	if type(item_list) is dict and selection in item_list:
		return selection

	# Force both entries to lowercase.
	entered_value = selection.lower()
	key_list = {key.lower():key for key in item_list}

	# Exact match!
	if entered_value in key_list:
		return key_list.get(entered_value)

	# Sloppy search using substring
	for list_option in key_list:
		if entered_value in list_option:
			return key_list.get(list_option)

	# Strip symbols
	entered_value = re.sub(r'\W+','', entered_value)

	# Compile the matching criteria
	criteria = re.compile(f".*{'.*'.join(entered_value)}.*")

	# Sloppy search using regex
	for list_option in key_list:
		if criteria.match(list_option):
			return key_list.get(list_option)

	# Unknown value. Return original, unchanged
	return selection



#88      .d88888b.   .d8888b.   .d8888b.  8888888 888b    888  .d8888b.       888     888 88888888888 8888888 888      .d8888b.  
#88     d88P" "Y88b d88P  Y88b d88P  Y88b   888   8888b   888 d88P  Y88b      888     888     888       888   888     d88P  Y88b 
#88     888     888 888    888 888    888   888   88888b  888 888    888      888     888     888       888   888     Y88b.      
#88     888     888 888        888          888   888Y88b 888 888             888     888     888       888   888      "Y888b.   
#88     888     888 888  88888 888  88888   888   888 Y88b888 888  88888      888     888     888       888   888         "Y88b. 
#88     888     888 888    888 888    888   888   888  Y88888 888    888      888     888     888       888   888           "888 
#88     Y88b. .d88P Y88b  d88P Y88b  d88P   888   888   Y8888 Y88b  d88P      Y88b. .d88P     888       888   888     Y88b  d88P 
#8888888 "Y88888P"   "Y8888P88  "Y8888P88 8888888 888    Y888  "Y8888P88       "Y88888P"      888     8888888 88888888 "Y8888P"  



# Remove emojis from Channel Names
def strip_emojis(string):
	return string.encode("latin-1", "ignore").decode("latin-1")



# Dump a json structure in pretty fashion
def json_dumps(item):
	return json.dumps(item, indent=2, sort_keys=True, skipkeys=True)



def format_auth_row(row):

	# Parse the provided row
	discord_id    = row[1]
	alliance_name = row[2]
	ACCESS_TOKEN  = row[4]
	REFRESH_TOKEN = row[5]
	expires_at    = datetime.fromtimestamp(int(row[7]))
	discord_name  = row[8]

	# Start building pieces of the output
	DISPLAY_NAME   = f'{ansi.ltcyan}{strip_emojis(discord_name)[:25]:25}{ansi.reset}' if discord_name else f'{ansi.ltred}{"MISSING":25}{ansi.reset}'
	ALLIANCE_INFO  = f'{ansi.bold}{alliance_name[:30]:30}{ansi.reset}' if alliance_name else f'{"<LINK REQUEST>":^30}'

	FORMATTED_DATE = expires_at.strftime("%m/%d/%Y, %H:%M") + ansi.reset

	# Valid, recently refreshed
	if expires_at > datetime.now() and ACCESS_TOKEN:
		EXPIRES_AT = ansi.green
		ACCESSIBLE = f'{ansi.ltgrn}ONE MONTH' if REFRESH_TOKEN else f'{ansi.yellow}1HR LIMIT'

	# Valid Session Key, start of linking process
	elif not ACCESS_TOKEN and age_of(expires_at).total_seconds() < 270:
		EXPIRES_AT = ansi.blue
		ACCESSIBLE = f'{ansi.ltblu}*PENDING*'

	# Expired Session Key, stale link request
	elif not ACCESS_TOKEN:
		EXPIRES_AT = ansi.dkgray
		ACCESSIBLE = f'{ansi.reset}**STALE**'

	# Expired, but can refresh
	elif age_of(expires_at).days < 30 and REFRESH_TOKEN:
		EXPIRES_AT = ansi.yellow
		ACCESSIBLE = f'{ansi.ltyel}ONE MONTH'

	# Expired, cannot refresh
	else:
		EXPIRES_AT = ansi.red
		ACCESSIBLE = f'{ansi.ltred}*EXPIRED*' if REFRESH_TOKEN else f'{ansi.red}*1HR EXP*'

	return f'{discord_id[:19]:>19} {DISPLAY_NAME} {ALLIANCE_INFO} {ACCESSIBLE}{ansi.reset} {EXPIRES_AT}{FORMATTED_DATE}'



def format_alliance_row(discord_id, alliance_name: str='', auth_id: int=None, discord_name: str='', user_or_channel: str='', auth_name: str='', *, skip_auth=False):

	DISPLAY_INFO = f'{ansi.yellow}{"user":>7}{ansi.reset}' if user_or_channel=='user' else f'{ansi.ltyel}channel{ansi.reset}'
	DISPLAY_NAME = f'{ansi.ltcyan}{strip_emojis(discord_name)[:30]:30}{ansi.reset}' if discord_name else f'{ansi.ltred}{"MISSING":^30}{ansi.reset}'
	
	# Format Authentication information if present
	AUTH_INFO = f'{auth_id:19} {ansi.ltcyan}{auth_name[:20]:20}{ansi.reset}' if auth_id and not skip_auth else ''

	# Output the result
	return f'{discord_id:>19} {DISPLAY_INFO} {DISPLAY_NAME} {ansi.bold}{alliance_name[:30]:30}{ansi.reset} {AUTH_INFO}'



async def report_defaults(self, context, user_or_channel):
	
	# Find the name of the Default Alliance
	alliance_name  = await self.bot.database.get_default_alliance_name(user_or_channel.id)

	# Note whether an authentication is available
	auth_available = '*(refresh avail)*' if await self.bot.database.get_default_auth_id(user_or_channel.id) else '*(reports only)*' if alliance_name else ''

	# Report the Default Alliance for the specified User or Channel
	return f"> * Default for **{await get_discord_name(self, context, user_or_channel)}** (ID: {user_or_channel.id}) is {bold_no_tags(alliance_name or 'NOT SET')} {auth_available}.\n"
		
		

#88888b.    .d88888b. 88888888888      8888888 .d8888b.       8888888b.  888     888 888b    888 888b    888 8888888 888b    888  .d8888b.  
#88  "88b  d88P" "Y88b    888            888  d88P  Y88b      888   Y88b 888     888 8888b   888 8888b   888   888   8888b   888 d88P  Y88b 
#88  .88P  888     888    888            888  Y88b.           888    888 888     888 88888b  888 88888b  888   888   88888b  888 888    888 
#888888K.  888     888    888            888   "Y888b.        888   d88P 888     888 888Y88b 888 888Y88b 888   888   888Y88b 888 888        
#88  "Y88b 888     888    888            888      "Y88b.      8888888P"  888     888 888 Y88b888 888 Y88b888   888   888 Y88b888 888  88888 
#88    888 888     888    888            888        "888      888 T88b   888     888 888  Y88888 888  Y88888   888   888  Y88888 888    888 
#88   d88P Y88b. .d88P    888            888  Y88b  d88P      888  T88b  Y88b. .d88P 888   Y8888 888   Y8888   888   888   Y8888 Y88b  d88P 
#888888P"   "Y88888P"     888          8888888 "Y8888P"       888   T88b  "Y88888P"  888    Y888 888    Y888 8888888 888    Y888  "Y8888P88  



def is_file_locked(filePath):
	"""
	Checks to see if a file is locked. Performs three checks
		1. Checks if the file even exists
		2. Attempts to open the file for reading. This will determine if the file has a write lock.
			Write locks occur when the file is being edited or copied to, e.g. a file copy destination
		3. Attempts to rename the file. If this fails the file is open by some other process for reading. The 
			file can be read, but not written to or deleted.
	"""
	if not (os.path.exists(filePath)):
		return False
	try:
		f = open(filePath, 'r')
		f.close()
	except IOError:
		return True

	lockFile = filePath + ".lckchk"
	if (os.path.exists(lockFile)):
		os.remove(lockFile)
	try:
		os.rename(filePath, lockFile)
		os.rename(lockFile, filePath)
		return False
	except WindowsError:
		return True



# Look for any locked logfiles. If nothing active, bot is not running.
def bot_is_running(bot_name):

	# Cache file open status to prevent excessive OS calls
	logfile_status = msf2csv.get_cached(f'logfile_status')
	updated = False
	
	BASE_PATH = r'c:\users\baker\dev'
	
	locked_files = logfile_status.setdefault(bot_name,{}).setdefault('locked',{})
	closed_files = logfile_status.setdefault(bot_name,{}).setdefault('closed',{})

	file_path = f'{BASE_PATH}{os.sep}{bot_name}{os.sep}trace{os.sep}'
	file_list = set(glob.iglob(file_path + 'discord*.log'))

	# Purge deleted files from closed_files to start:
	for file in list(closed_files):
		# Closed file has been deleted
		if file not in file_list:
			closed_files.pop(file, None)
			updated = True
		# Don't look at this file again
		else:
			file_list.remove(file)

	# Check locked_files -- purge deleted entries, update closed_files with entries if no longer open
	for file in list(locked_files):
		# Purge deleted entries
		if file not in file_list:
			locked_files.pop(file, None)
			updated = True
			continue
		# Check existing entries -- closed yet?
		if not is_file_locked(file):
			locked_files.pop(file, None)
			updated = closed_files[file] = True
		# Don't look at this file again
		file_list.remove(file)
	
	# Remaining entries are new files, locked status?
	for file in file_list:
		if is_file_locked(file):
			updated = locked_files[file] = True
		else:
			updated = closed_files[file] = True

	# Update the cached value if anything changed
	if updated:
		msf2csv.set_cached('logfile_status', logfile_status)

	# And return True if logfiles are in use
	if locked_files:
		return True

	# Otherwise, relaunch the bot!
	Popen(f'cmd /S /K "cd {BASE_PATH}{os.sep}{bot_name} && title {bot_name.upper()} && py bot.py', creationflags=CREATE_NEW_CONSOLE)



#888888888 888b     d888 888888b.   8888888888 8888888b.       888     888 88888888888 8888888 888      .d8888b.  
#88        8888b   d8888 888  "88b  888        888  "Y88b      888     888     888       888   888     d88P  Y88b 
#88        88888b.d88888 888  .88P  888        888    888      888     888     888       888   888     Y88b.      
#888888    888Y88888P888 8888888K.  8888888    888    888      888     888     888       888   888      "Y888b.   
#88        888 Y888P 888 888  "Y88b 888        888    888      888     888     888       888   888         "Y88b. 
#88        888  Y8P  888 888    888 888        888    888      888     888     888       888   888           "888 
#88        888   "   888 888   d88P 888        888  .d88P      Y88b. .d88P     888       888   888     Y88b  d88P 
#888888888 888       888 8888888P"  8888888888 8888888P"        "Y88888P"      888     8888888 88888888 "Y8888P"  



def has_tags(alliance_name):
	return msf2csv.remove_tags(alliance_name) != alliance_name



def bold_no_tags(alliance_name):

	# Normalize input to a sorted list
	if type(alliance_name) is str:
		alliance_list = [alliance_name]
	else:
		alliance_list = sorted(alliance_name)

	return ', '.join([f'**{msf2csv.remove_tags(x)}**' for x in alliance_list])



def bold_with_tags(alliance_name):

	# Normalize input to a sorted list
	if type(alliance_name) is str:
		alliance_list = [alliance_name]
	else:
		alliance_list = sorted(alliance_name)

	with_tags = []
	
	for alliance_name in alliance_list:
		without_tags = msf2csv.remove_tags(alliance_name)
		if alliance_name == without_tags:
			with_tags.append(f'**{without_tags}**')
		else:
			with_tags.append(f'**{without_tags}** *({alliance_name})*')

	return ', '.join(with_tags)



def format_discord_info(member_info):

	# Go one level deeper if necessary
	discord_info = member_info.get('discord', member_info)
	
	return f" - {discord_info.get('name')} *(ID: {discord_info.get('id')})*" if discord_info else ""



def format_default_info(DEFAULTS, desc, auth_id, embed): 

	chan_shared = {}
	user_shared = {}

	for row in DEFAULTS:
		discord_id   = DEFAULTS[row][0]
		discord_name = DEFAULTS[row][3]
		discord_type = DEFAULTS[row][4]
		discord_auth = DEFAULTS[row][2]
		
		# Filter the list of Defaults to just the ones that include a shared auth from this user
		if   discord_auth == auth_id and discord_type == 'user' and discord_id != auth_id:
			user_shared[discord_name] = discord_id
		elif discord_auth == auth_id:
			chan_shared[discord_name] = discord_id

	auth_info = f''
	prefix = ''

	refresh_avail = 'Refresh avail' if auth_id else 'Reports only'

	if user_shared:
		auth_info += f'{prefix}**Users:** *({refresh_avail})*\n'
		for user in sorted(user_shared):
			auth_info += f'{prefix}* {user} *(ID: {user_shared[user]})*\n'
	if chan_shared:
		auth_info += f'{prefix}**Channels:** *({refresh_avail})*\n'
		for chan in sorted(chan_shared):
			auth_info += f'{prefix}* {chan} *(ID: {chan_shared[chan]})*\n'

	if not (user_shared or chan_shared):
		auth_info += f'{prefix}*(not shared with any users or channels)*\n'

	if auth_info:
		embed.add_field(
			name=f"__{desc}:__",
			value=auth_info, 
			inline=False,
		)



# Do the right thing regardless of what we're sent.
async def send_message(context, message=None, embed=None, content=None, attachments=[], ephemeral=False, delete_after=None, view=None):

	# If no context, nowhere to send
	if not context:
		return

	BOT_ON_SERVER = context.guild and context.guild.name

	# If we already had an existing message, just edit it
	if message:
		try:
			message = await message.edit(embed=embed, content=content, attachments=[discord.File(file) for file in attachments], view=view)
		# If issues, set message to None to force retry in new message
		except Exception as e:
			message = print (f'{ansi.ltred}ERROR!{ansi.reset} Caught {ansi.ltyel}{type(e).__name__}: {ansi.yellow}{e}{ansi.reset} during {ansi.bold}message.edit(){ansi.reset}. Sending new message instead...')

	# Otherwise, return a fresh message in the context
	if not message:
		try:
			message = await context.send(embed=embed, content=content, ephemeral=ephemeral, files=[discord.File(file) for file in attachments], view=view, delete_after=delete_after)
		# If issues, try sending directly to the channel
		except Exception as e:
			print (f'{ansi.ltred}ERROR!{ansi.reset} Caught {ansi.ltyel}{type(e).__name__}: {ansi.yellow}{e}{ansi.reset} during {ansi.bold}context.send(){ansi.reset}. Context missing. ' + ('Sending to channel...' if BOT_ON_SERVER else 'Failed to send message.'))

	# Otherwise, return a fresh message in the channel
	if not message and BOT_ON_SERVER:
		try:
			message = await context.channel.send(embed=embed, content=content, files=[discord.File(file) for file in attachments], view=view)
		# If issues, we've failed to send the message
		except Exception as e:
			print (f'{ansi.ltred}ERROR!{ansi.reset} Caught {ansi.ltyel}{type(e).__name__}: {ansi.yellow}{e}{ansi.reset} during {ansi.bold}context.channel.send(){ansi.reset}. Failed to send message.')

	return message


	
async def send_rosterbot_error(
		self, context: Context, error_msg: str, title: str='', message=None, ephemeral=True, delete_after=10, warning=False,
	) -> None:

	# Change from Discord formatting to ANSI colors
	replace_with = [f'{ansi.reset}' if i%2 else f'{ansi.bold}' for i in range(error_msg.count('**'))]
	logged_msg = error_msg.replace('\n',' ').replace('**','{}').format(*replace_with)

	# Log an error message in the logger
	if warning:	self.bot.logger.warning(logged_msg)
	else:		self.bot.logger.error(logged_msg)

	# Set embed color to yellow or red, as necessary
	color = build_color(0.50) if warning else build_color(0.01)

	# Build and send an embed with the same message
	return await send_rosterbot_embed(self, context, title, description=error_msg, message=message, color=color, inc_icon=False, inc_footer=False, ephemeral=ephemeral, delete_after=delete_after)



async def send_rosterbot_embed(
		self, context: Context, title='', description='', message=None, color=None, inc_icon=True, inc_footer=True, ephemeral=False, delete_after=None,
	) -> None:

	# If no context, nowhere to send
	if not context:
		return

	# Don't indicate who requested if only user can see it
	inc_footer = False if ephemeral else inc_footer

	embed = await get_rosterbot_embed(self, context, title, description, color, inc_icon, inc_footer)
	
	return await send_message(context, message=message, embed=embed, ephemeral=ephemeral, delete_after=delete_after)



async def get_rosterbot_embed(
		self, context: Context, title: str='', description: str='', color=None, inc_icon=True, inc_footer=True,
	) -> discord.Embed:

	embed = discord.Embed(
		title=title,
		color=color or 0xBEBEFE,
		description=description
	)

	if inc_icon and self.bot.user.avatar is not None:
		embed.set_thumbnail(url=self.bot.user.avatar.url)		

	if inc_footer and context:
		embed.set_footer(
			text=f"Requested by {context.author}",
			icon_url=context.author.display_avatar
		)

	return embed



# Calculate the color for our Discord Embed
def build_color(percent):

	# Ensure percent is 0-100% 
	percent = max(0,percent)
	percent = min(1,percent)
	
	# Calculate the color value using our standard gradient.
	color = percent * (len(msf2csv.color_scale)-1)
	
	# Convert it from hex to int and return.
	return int('0x'+msf2csv.color_scale[int(color)][1:], 16)



def wiki_link(self, link_name):
	link_url = self.bot.config.get(link_name)
	link_name = link_name.partition('||')[0]
	return f'**{link_name}**' if link_url is None else f'[**{link_name}**]({self.bot.config.get("wiki_link")}/{link_url})'



def add_footer(self):
	return f"\n-# [**ADD BOT**]({self.bot.config['invite_link']}) ║ [**WIKI**]({self.bot.config['wiki_link']}) ║ [**DONATE**]({self.bot.config['donate_link']})"



#
async def api_request_failed(self, context, response, failed_on):

	# Handle recognized API call issues differently
	if failed_on == 'alliance' and response.status_code == 404:
		error_msg = "Player NOT in Alliance"

	# If unknown, log the error for later review
	else:
		error_msg = "API Request Failed" 
		status_and_message = 'NO RESPONSE' if response is None else f'Status: {response.status_code} Message: {response.text}'
		self.bot.logger.error(f'{error_msg} -- {status_and_message}')

	# Advise that the request failed.
	return await send_rosterbot_error(self, context, f"Unable to get {failed_on} info.\n" + ("Command cancelled." if context else ""), title=f'{error_msg}:')



# 
async def report_exception(self, context: Context, exception: Exception) -> None:

	# Log the error in logfile.
	self.bot.logger.error(f"{type(exception).__name__}: {ansi.bold}{exception}{ansi.reset}")
	
	# Get the Owner's Discord User.
	owner = await self.bot.fetch_user(self.bot.owner_id)

	embed_description = f'**{type(exception).__name__}:** {exception}'
	
	for idx in range(0,len(embed_description),980):

		# Build the error messages.
		embed = discord.Embed(
			title =f'EXCEPTION RAISED:',
			description=embed_description[idx:idx+980],
			color=0xff0000,
		)
		# Attempt to send alert to bot Owner
		try:
			await owner.send(embed=embed)
		# Failing that, just send it in the local channel.
		except discord.Forbidden:
			await context.send(embed=embed)

	exception_content = ''.join(traceback.format_exception(exception))

	for idx in range(0,len(exception_content),980):
		content = f"```haskell\n{exception_content[idx:idx+980]}```"

		# Attempt to send alert to bot Owner
		try:
			await owner.send(content=content)
		# Failing that, just send it in the local channel.
		except discord.Forbidden:
			await context.send(content=content)



  #8888b.        d8888  .d8888b.  888    888 8888888888 8888888b.       888b     d888 8888888888 888b     d888 888888b.   8888888888 8888888b.       888     888 88888888888 8888888 888      .d8888b.  
#88P  Y88b      d88888 d88P  Y88b 888    888 888        888  "Y88b      8888b   d8888 888        8888b   d8888 888  "88b  888        888   Y88b      888     888     888       888   888     d88P  Y88b 
#88    888     d88P888 888    888 888    888 888        888    888      88888b.d88888 888        88888b.d88888 888  .88P  888        888    888      888     888     888       888   888     Y88b.      
#88           d88P 888 888        8888888888 8888888    888    888      888Y88888P888 8888888    888Y88888P888 8888888K.  8888888    888   d88P      888     888     888       888   888      "Y888b.   
#88          d88P  888 888        888    888 888        888    888      888 Y888P 888 888        888 Y888P 888 888  "Y88b 888        8888888P"       888     888     888       888   888         "Y88b. 
#88    888  d88P   888 888    888 888    888 888        888    888      888  Y8P  888 888        888  Y8P  888 888    888 888        888 T88b        888     888     888       888   888           "888 
#88b  d88P d8888888888 Y88b  d88P 888    888 888        888  .d88P      888   "   888 888        888   "   888 888   d88P 888        888  T88b       Y88b. .d88P     888       888   888     Y88b  d88P 
  #8888P" d88P     888  "Y8888P"  888    888 8888888888 8888888P"       888       888 8888888888 888       888 8888888P"  8888888888 888   T88b       "Y88888P"      888     8888888 88888888 "Y8888P"  



# Cache for member names / discord info for every cached_data file we open. 

# cached_members is a dict, with a dict for each Alliance. 
'''cached_members = {'alliance_name': {	'admin':{'name':discord_user.name, 'id':discord_user.id},	
										'leader':    'FatCat',
										'captains':  [ 'Unclad', 'Zen Master', 'JoeyB' ], 
										'members': {'member_name': {'url': 'scopely_user_id', 'discord': {'name':discord_user.name, 'id':discord_user.id}}, 
													'member_name': {'url': 'scopely_user_id', 'discord': {'name':discord_user.name, 'id':discord_user.id}}, 
													'member_name': {'url': 'scopely_user_id', 'discord': {'name':discord_user.name, 'id':discord_user.id}}, 
													'member_name': {'url': 'scopely_user_id', 'discord': {}}, 
													'member_name': {'url': 'scopely_user_id', 'discord': {}} }
'''

cached_members = {}

# Refresh alliance_info within the cached_members structure.
def load_cached_members(alliance_name):
	global cached_members

	alliance_info = find_cached_data(alliance_name)
	alliance_name = alliance_info.get('name','').lower()

	# Initialize or load the details for this Alliance
	alliance_members = cached_members.setdefault(alliance_name, {})

	alliance_members['admin']        = alliance_info.get('admin',{})
	alliance_members['leader']       = alliance_info.get('leader','')
	alliance_members['captains']     = alliance_info.get('captains',[])
	alliance_members['custom_teams'] = alliance_info.get('custom_teams',{})
	
	member_info = alliance_info.get('members',{})
	
	alliance_members['members'] = { member:{'discord':member_info[member].get('discord',{}), 
											'auth'   :member_info[member].get('auth'),
											'url'    :member_info[member].get('url'),} for member in sorted(member_info, key=str.lower)}

	return alliance_members



# Get member status from cached_member info
def get_member_role(alliance_name, user_id):
	global cached_members
	
	if not alliance_name:
		return ''
	
	# Get the cached_members structure. Populate it with alliance info if not already loaded.
	alliance_members = cached_members.get(alliance_name.lower())
	if not alliance_members:
		alliance_members = load_cached_members(alliance_name)

	#if not alliance_members:	return

	# Discord info for alliance members is stored in members
	member_info = alliance_members.get('members',{})

	leader = alliance_members.get('leader')
	if user_id == member_info.get(leader,{}).get('discord',{}).get('id'):
		return 'leader'
		
	admin = alliance_members.get('admin',{})
	if user_id == admin.get('id'):
		return 'admin'

	captains = alliance_members.get('captains',[])
	if user_id in [member_info.get(captain,{}).get('discord',{}).get('id') for captain in captains]:
		return 'captain'
	
	if user_id in [member_info.get(member,{}).get('discord',{}).get('id') for member in member_info]:
		return 'member'
		
	# Returns None if none of these are true. ;) 



# Get a list of members from cached_member info 
def get_member_list(alliance_name, discord_user = False, remove_leader=False):
	global cached_members
	
	if not alliance_name:
		return []
	
	# Get the cached_members structure. Populate it with alliance info if not already loaded.
	alliance_members = cached_members.get(alliance_name.lower())
	if not alliance_members:
		alliance_members = load_cached_members(alliance_name)

	member_list = list(alliance_members['members'])
	
	if remove_leader:
		member_list.remove(alliance_members['leader'])

	if not discord_user:
		return member_list
	else:
		member_info = alliance_members['members']
		return [member + (' / ' + (member_info[member]['discord'].get('name','')) if member_info[member]['discord'] else '') for member in member_list]



# Get member status from cached_member info
def get_member_by_name(alliance_name, member_name):
	global cached_members
	
	if not alliance_name:
		return ''
	
	# Get the cached_members structure. Populate it with alliance info if not already loaded.
	alliance_members = cached_members.get(alliance_name.lower())
	if not alliance_members:
		alliance_members = load_cached_members(alliance_name)

	# Discord info for alliance members is stored in members
	member_info = alliance_members.get('members',{})

	return member_info.get(member_name)
	# Returns None if none of these are true. ;) 



# Get a specific member name by Discord ID from cached_member info 
def get_member_by_id(alliance_name, user_id):
	global cached_members
	
	if not alliance_name:
		return ''

	# Get the cached_members structure. Populate it with alliance info if not already loaded.
	alliance_members = cached_members.get(alliance_name.lower())
	if not alliance_members:
		alliance_members = load_cached_members(alliance_name)

	# Discord info for alliance members is stored in members
	member_info = alliance_members.get('members',{})

	for member in member_info:
		if member_info.get(member,{}).get('discord',{}).get('id') == user_id:
			return member
	
	return ''
	


# Get a specific member name by Discord ID from cached_member info 
def get_custom_teams(alliance_name):
	global cached_members
	
	if not alliance_name:
		return {}

	# Get the cached_members structure. Populate it with alliance info if not already loaded.
	alliance_members = cached_members.get(alliance_name.lower())
	if not alliance_members:
		alliance_members = load_cached_members(alliance_name)

	# Return custom_team info if there is any
	return alliance_members.get('custom_teams',{})
	


# If arg is a string, find alliance_info by name.
# If item passed in is alliance_info, return that.
def find_cached_data(name_or_info):
	alliance_info = {}

	if not name_or_info:
		return {}
	if type(name_or_info) == str:
		alliance_info = msf2csv.find_cached_data(name_or_info)
	elif type(name_or_info) == dict and name_or_info.get('name'):
		alliance_info = name_or_info
	
	return alliance_info



  #8888b.  8888888888 888      8888888888 .d8888b. 88888888888      888b     d888 8888888888 888b     d888 888888b.   8888888888 8888888b.       888     888 8888888 8888888888 888       888 
#88P  Y88b 888        888      888       d88P  Y88b    888          8888b   d8888 888        8888b   d8888 888  "88b  888        888   Y88b      888     888   888   888        888   o   888 
#88b.      888        888      888       888    888    888          88888b.d88888 888        88888b.d88888 888  .88P  888        888    888      888     888   888   888        888  d8b  888 
  #888b.   8888888    888      8888888   888           888          888Y88888P888 8888888    888Y88888P888 8888888K.  8888888    888   d88P      Y88b   d88P   888   8888888    888 d888b 888 
     #88b. 888        888      888       888           888          888 Y888P 888 888        888 Y888P 888 888  "Y88b 888        8888888P"        Y88b d88P    888   888        888d88888b888 
       #88 888        888      888       888    888    888          888  Y8P  888 888        888  Y8P  888 888    888 888        888 T88b          Y88o88P     888   888        88888P Y88888 
#88b  d88P 888        888      888       Y88b  d88P    888          888   "   888 888        888   "   888 888   d88P 888        888  T88b          Y888P      888   888        8888P   Y8888 
  #8888P"  8888888888 88888888 8888888888 "Y8888P"     888          888       888 8888888888 888       888 8888888P"  8888888888 888   T88b          Y8P     8888888 8888888888 888P     Y888 



# Allow user to select the Members to include in report.

class SelectMemberView(discord.ui.View):
	def __init__(self, options=[], max_values=1, timeout=30) -> None:
		super().__init__(timeout=timeout)
		self.add_item(SelectMemberPicklist(options, max_values))
		self.value = None

	async def on_timeout(self):
		self.stop()


class SelectMemberPicklist(discord.ui.Select):
	def __init__(self, options, max_values=1) -> None:
		super().__init__(
			placeholder='Please select ' + ('a member.','the members')[max_values>1],
			min_values=1,
		)

		self.options = options
		self.max_values = min(max_values,len(self.options))
		
	async def callback(self, interaction: discord.Interaction) -> None:
		member_name = sorted(self.values, key=str.lower)

		result_embed = discord.Embed(color=0x57F287)
		result_embed.description = f"You selected: **{member_name}**"

		try:
			await interaction.response.edit_message(embed=result_embed, content=None, view=None, delete_after=10)
		except Exception as e:
			print (f'{ansi.ltred}ERROR!{ansi.reset} Caught {type(e).__name__}: {e}  during edit_message(). Member selected was {member_name}.')

		self.view.value = member_name
		self.view.stop()


async def get_alliance_members(self, context, options, max_values=1):

	members = 'members' if max_values>1 else 'member' 

	# Prompt user to select members to include in report.
	view = SelectMemberView(options, max_values=max_values, timeout=120)
	message = await context.send(f'Which {members} would you like?', view=view, ephemeral=True)
	await view.wait()
	
	# If no members selected, we can't go forward.
	if not view.value:
		return await send_rosterbot_error(self, context, f"**TIMEOUT:** No {members} selected. Command cancelled.", message=message)

	return view.value




 #d8888b.  8888888888 88888888888      8888888b.  8888888888 8888888888     d8888 888     888 888    88888888888       .d88888b.  8888888b. 88888888888 8888888 .d88888b.  888b    888  .d8888b.  
#88P  Y88b 888            888          888  "Y88b 888        888           d88888 888     888 888        888          d88P" "Y88b 888   Y88b    888       888  d88P" "Y88b 8888b   888 d88P  Y88b 
#88    888 888            888          888    888 888        888          d88P888 888     888 888        888          888     888 888    888    888       888  888     888 88888b  888 Y88b.      
#88        8888888        888          888    888 8888888    8888888     d88P 888 888     888 888        888          888     888 888   d88P    888       888  888     888 888Y88b 888  "Y888b.   
#88  88888 888            888          888    888 888        888        d88P  888 888     888 888        888          888     888 8888888P"     888       888  888     888 888 Y88b888     "Y88b. 
#88    888 888            888          888    888 888        888       d88P   888 888     888 888        888          888     888 888           888       888  888     888 888  Y88888       "888 
#88b  d88P 888            888          888  .d88P 888        888      d8888888888 Y88b. .d88P 888        888          Y88b. .d88P 888           888       888  Y88b. .d88P 888   Y8888 Y88b  d88P 
 #Y8888P88 8888888888     888          8888888P"  8888888888 888     d88P     888  "Y88888P"  88888888   888           "Y88888P"  888           888     8888888 "Y88888P"  888    Y888  "Y8888P"  



# Allow user to select whether defaults should be added/remove from themselves, the channel, or both.
class UserChannelBoth(discord.ui.View):
	def __init__(self, timeout=15) -> None:
		super().__init__(timeout=timeout)
		self.value = None

	@discord.ui.button(label="User", style=discord.ButtonStyle.blurple)
	async def user(
		self, interaction: discord.Interaction, button: discord.ui.Button
	) -> None:
		self.value = "user"
		self.stop()

	@discord.ui.button(label="Channel", style=discord.ButtonStyle.blurple)
	async def channel(
		self, interaction: discord.Interaction, button: discord.ui.Button
	) -> None:
		self.value = "channel"
		self.stop()

	@discord.ui.button(label="Both", style=discord.ButtonStyle.blurple)
	async def both(
		self, interaction: discord.Interaction, button: discord.ui.Button
	) -> None:
		self.value = "both"
		self.stop()

	async def on_timeout(self):
		self.stop()



async def get_default_options(self, context, SETTING_DEFAULT=''):

	action = 'this default be applied to' if SETTING_DEFAULT else 'defaults be removed from'

	USER_DEFAULT    = await self.bot.database.get_default_alliance_name(context.author.id)
	CHANNEL_DEFAULT = await self.bot.database.get_default_alliance_name(context.channel.id)

	CAPTAIN_OR_HIGHER = await get_all_avail_alliances(self, context, min='captain')

	view = UserChannelBoth(timeout=20)

	description  = f'What should {action}?\n'
	description += f'> User Default: **{USER_DEFAULT or 'NOT SET'}**\n' 
	description += f'> Chan Default: **{CHANNEL_DEFAULT or 'NOT SET'}**\n'
	
	# Disable buttons if removing and no user default set
	if not (SETTING_DEFAULT or USER_DEFAULT):
		view.both.disabled = view.user.disabled    = True

	# Disable buttons if removing and no channel default set
	if not (SETTING_DEFAULT or CHANNEL_DEFAULT):
		view.both.disabled = view.channel.disabled = True
	
	# Protest if user is not a captain
	if not CAPTAIN_OR_HIGHER:
		description += f'**Note:** *Only **Captains** and **Leaders** can change channel defaults*'
		view.both.disabled = view.channel.disabled = True

	message = await context.send(description, view=view, ephemeral=True, delete_after=30)
	
	await view.wait()
	
	# If no members selected, we can't go forward.
	if not view.value:
		return await send_rosterbot_error(self, context, f"**TIMEOUT:** No target selected. Command cancelled.", message=message)

	embed = discord.Embed(color=0x57F287)
	embed.description = f"You selected: **{'SET DEFAULT** on' if SETTING_DEFAULT else 'REMOVE DEFAULT** from'} **{view.value.upper()}**"

	await send_message(context, message, embed=embed)

	return view.value



#888888b.  8888888888 8888888b.   .d88888b.  8888888b. 88888888888      8888888 888b    888      8888888b.  8888888b.   .d88888b.   .d8888b.  8888888b.  8888888888 .d8888b.   .d8888b.  
#88   Y88b 888        888   Y88b d88P" "Y88b 888   Y88b    888            888   8888b   888      888   Y88b 888   Y88b d88P" "Y88b d88P  Y88b 888   Y88b 888       d88P  Y88b d88P  Y88b 
#88    888 888        888    888 888     888 888    888    888            888   88888b  888      888    888 888    888 888     888 888    888 888    888 888       Y88b.      Y88b.      
#88   d88P 8888888    888   d88P 888     888 888   d88P    888            888   888Y88b 888      888   d88P 888   d88P 888     888 888        888   d88P 8888888    "Y888b.    "Y888b.   
#888888P"  888        8888888P"  888     888 8888888P"     888            888   888 Y88b888      8888888P"  8888888P"  888     888 888  88888 8888888P"  888           "Y88b.     "Y88b. 
#88 T88b   888        888        888     888 888 T88b      888            888   888  Y88888      888        888 T88b   888     888 888    888 888 T88b   888             "888       "888 
#88  T88b  888        888        Y88b. .d88P 888  T88b     888            888   888   Y8888      888        888  T88b  Y88b. .d88P Y88b  d88P 888  T88b  888       Y88b  d88P Y88b  d88P 
#88   T88b 8888888888 888         "Y88888P"  888   T88b    888          8888888 888    Y888      888        888   T88b  "Y88888P"   "Y8888P88 888   T88b 8888888888 "Y8888P"   "Y8888P"  



# Super basic dict to keep track of in-flight Report requests.
already_in_progress = {}



# Check to see if we're already processing this request.
async def report_in_progress(alliance_name, output_name, start_time):
	global already_in_progress
	
	# Special processing if REFRESH ONLY is requested
	REFRESH_ONLY = output_name == 'refresh_only'
	if REFRESH_ONLY:
		output_name = 'refresh'

	REPORT_NAME = f'{alliance_name} {output_name}'

	# If we're been working on this report more than 45 seconds, it crashed...time to move on.
	if REPORT_NAME in already_in_progress and (datetime.now() - already_in_progress[REPORT_NAME]).seconds > 45:
		del already_in_progress[REPORT_NAME]
		
	START_TIME = already_in_progress.setdefault(REPORT_NAME, start_time)

	# If there's no reason to wait, go ahead and return the result.
	if output_name != 'refresh' or REFRESH_ONLY or START_TIME == start_time:
		return START_TIME

	# This a refresh requested while generating a report, but there's
	# already another refresh in progress. Wait until refresh completes.

	# Wait for a max of 90 seconds, return once refresh is complete
	for x in range(360):
		await asyncio.sleep(0.25)
		if REPORT_NAME not in already_in_progress:
			break



# Clear up the table after we're done.
async def report_is_complete(alliance_name, output_name, start_time):
	global already_in_progress

	report = f'{alliance_name} {output_name}'

	# Delete the entry if it hasn't been changed.
	if report in already_in_progress and already_in_progress[report] == start_time:
		del already_in_progress[report]



 #d8888b.  888     888 8888888b.  8888888b.   .d88888b.  8888888b. 88888888888      8888888b.   .d88888b.  888     888 88888888888 8888888 888b    888 8888888888 .d8888b.  
#88P  Y88b 888     888 888   Y88b 888   Y88b d88P" "Y88b 888   Y88b    888          888   Y88b d88P" "Y88b 888     888     888       888   8888b   888 888       d88P  Y88b 
#88b.      888     888 888    888 888    888 888     888 888    888    888          888    888 888     888 888     888     888       888   88888b  888 888       Y88b.      
 #Y888b.   888     888 888   d88P 888   d88P 888     888 888   d88P    888          888   d88P 888     888 888     888     888       888   888Y88b 888 8888888    "Y888b.   
    #Y88b. 888     888 8888888P"  8888888P"  888     888 8888888P"     888          8888888P"  888     888 888     888     888       888   888 Y88b888 888           "Y88b. 
      #888 888     888 888        888        888     888 888 T88b      888          888 T88b   888     888 888     888     888       888   888  Y88888 888             "888 
#88b  d88P Y88b. .d88P 888        888        Y88b. .d88P 888  T88b     888          888  T88b  Y88b. .d88P Y88b. .d88P     888       888   888   Y8888 888       Y88b  d88P 
 #Y8888P"   "Y88888P"  888        888         "Y88888P"  888   T88b    888          888   T88b  "Y88888P"   "Y88888P"      888     8888888 888    Y888 8888888888 "Y8888P"  



# List the commands available in each of the Cogs
async def list_commands(self, context):
	embed = discord.Embed(
		title="Help", description="List of available commands:", color=0xBEBEFE
	)

	# Iterate through each of the Loaded cogs, building up a help_text paragraph for each.
	for i in self.bot.cogs:

		# Skip the owner cog if the person requesting help is NOT the bot owner.
		if i in ("owner") and not await is_owner(self, context):
			continue

		cog = self.bot.get_cog(i.lower())

		commands = cog.get_commands() + cog.get_app_commands()

		list_of_commands = list(cog.walk_commands())+list(cog.walk_app_commands())

		data = []
		for command in commands or sorted(set([c.qualified_name.partition(' ')[0] for c in list_of_commands])):
			if type(command) is str:
				command_name = command
				command_desc = f'The /{command} command group'
			else:
				command_name = command.name
				command_desc = command.description.partition("\n")[0]

			subcommands =  [c for c in list_of_commands if f'{command} ' in c.qualified_name]

			subdata = []
			for subcommand in subcommands:
				desc = subcommand.description.partition('\n')[0]
				subdata.append(f"  * `{subcommand.name}`- {desc}")

			subdata = [f"* `/{command_name}`- {command_desc}"] + sorted(subdata, key=str.lower)

			data.append("\n".join(subdata))

		data = sorted(data, key=str.lower)
		help_text = "\n".join(data)

		embed.add_field(
			name=f'__{i.upper()}__:', value=f"{help_text}", inline=False
		)

	embed.set_footer(
		text=f"Requested by {context.author}",
		icon_url=context.author.display_avatar
	)

	await context.send(embed=embed)



async def show_prefs_section(self, context: Context, embed=None, PREFS=None):
	
	# Create a new embed if none provided
	if not embed:
		embed = await get_rosterbot_embed(self, context, inc_footer=False)
	
	# Get the cached PREFS if not provided
	if not PREFS:
		cached_defaults = msf2csv.get_cached(f'defaults-{context.author.id}')		
		PREFS = cached_defaults.pop('prefs',{})

	refresh_first = PREFS.get('refresh_first', False)
	refresh_value = {
		True:	'> *If data is stale when you request a report, RosterBot will automatically call **/roster refresh** and then render the requsted image*',
		False:	'> *If data is stale when you request a report, RosterBot will render the image, call **/roster refresh**, then update the image new data*'
	}[refresh_first]
	embed.add_field(
		name="User Preferences",
		value=f"refresh_first: **{repr(refresh_first).upper()}**\n{refresh_value}", 
		inline=False,
	)
	
	private_mode  = PREFS.get('private_mode', False)
	private_value = {
		True:	'> *Requested reports will only be visible by you. Use **safe_channel** or **safe_server** to indicate where public responses should be allowed.*',
		False:	'> *Requested reports will be visible by anyone in the channel (if the server allows slash commands).*'
	}[private_mode]
	embed.add_field(
		name="",
		value=f"private_mode: **{repr(private_mode).upper()}**\n{private_value}",
		inline=False,
	)
	
	chan_list  = PREFS.get('safe_channel', {})
	chan_value = '\n'.join([f'> * **{chan_list[key]}** *(ID: {key})*' for key in chan_list])
	embed.add_field(
		name="",
		value="safe_channels:\n" + (chan_value or '> * *No safe channels defined!*'),
		inline=False,
	)

	serv_list  = PREFS.get('safe_server', {})
	serv_value = '\n'.join([f'> * **{serv_list[key]}** *(ID: {key})*' for key in serv_list])
	embed.add_field(
		name="",
		value="safe_servers:\n" + (serv_value or '> * *No safe servers defined!*'),
		inline=False,
	)

	await context.send(embed=embed, ephemeral=True)