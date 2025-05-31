#!/usr/bin/env python3
# Encoding: UTF-8
"""msf_shared.py
Routines shared between /alliance and /roster and interacting with msf2csv.py.
"""

DISABLE_REFRESH = False


import os
import sys
import time
import datetime
import asyncio
import keyring
import pickle
import traceback
import re

import discord
from discord.ext.commands import Context
from discord.app_commands import Choice

from functools import partial
from enum import Enum

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait

# Ensure MSF2CSV is in our path.
msf2csv_path = r'C:\Users\baker\Dev\MSF'
if msf2csv_path not in sys.path:
	sys.path.insert(0,msf2csv_path)

import msf2csv
from log_utils import timed, ansi, find_log_file
from login import chromium_path



# Generate the CLIENT_TOKEN for use by MSF2CSV
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Precalculate the CLIENT_TOKEN for MSF API access
CLIENT_TOKEN = msf2csv.construct_token(os.getenv('CLIENT_ID'), os.getenv('CLIENT_SECRET'))



# Generate a URL to link account
async def get_auth_url(self, context):

	# Get the Session ID and Link URL to use
	SESSION_ID, LINK_URL = msf2csv.get_session_and_link(os.getenv("CLIENT_ID"))

	# Store the shared secret as the session_id
	await self.bot.database.save_session(context.author.id, SESSION_ID)	

	return LINK_URL
	
	
# NOT IN USE YET!
# NOT IN USE YET!
# NOT IN USE YET!
#
# Look for a stored Auth for this user. 
async def get_auth(self, context):	

	# Look for an entry in the database
	AUTH = await self.bot.database.get_auth(context.author.id)

	# If expired, try to refresh
	if AUTH and not msf2csv.auth_valid(AUTH):
		msf2csv.refresh_auth(AUTH, CLIENT_TOKEN)

		# If AUTH refreshed, store in the database.
		if AUTH.get('updated'):
			await self.bot.database.save_auth(AUTH, context.author.id)	
			
		# If unable to refresh, don't return an AUTH
		elif not msf2csv.auth_valid(AUTH):
			AUTH = None
	
	return AUTH



# NEW ROUTINE I GOTTA WORK ON.
# THIS WILL DO THE HARD WORK OF TRACKING DOWN A VALID AUTH BASED ON DEFAULTS ON CHANNEL AND USER. 
async def get_valid_auth(self, context):	

	# See if we have a default AUTH defined on ourselves or the channel.
	auth_id = await self.bot.database.get_default_auth([context.author.id, context.channel.id])

	# Found an auth_id for a default AUTH. Pull the AUTH associated with this auth_id
	#
	#
	# NOT SURE WHAT THIS CALL IS REALLY DOING. THINK I SHOULD JUST GO TO if no auth_id: AND THE STEPS BELOW.
	# 
	# Oh, I think I get it. Need alliance_name along with auth_id for the get_auth request. 
	# SO WE NEED TO MAKE SURE THAT THE UNVARNISHED RESPONSE FROM THE JSON IS STORED IN ALLIANCE NAME 
	# NEED TO CLEAR THEM ALL AND ALLOW SYSTEM TO FILL THEM IN NATURALLY WITH USE
	if auth_id:
		alliance_name = await self.bot.database.get_default_alliance(auth_id)

	# If no default, see if the person sending the message has any saved authorizations OF THEIR OWN
	else:
		alliance_name = await self.bot.database.get_avail_auths(context)
		if alliance_name:
			auth_id = context.author.id
		
	# Grab an AUTH from the auth_id we found.
	AUTH = await self.bot.database.get_auth(auth_id, alliance_name)

	# If expired, try to refresh
	if AUTH and not msf2csv.auth_valid(AUTH):
		msf2csv.refresh_auth(AUTH, CLIENT_TOKEN)

		# If AUTH refreshed, store in the database.
		if AUTH.get('updated'):
			await self.bot.database.save_auth(AUTH, context.author.id)	
			
		# If unable to refresh, don't return an AUTH
		elif not msf2csv.auth_valid(AUTH):
			AUTH = None
	
	return AUTH



async def api_request_failed(self, context, response, failed_on):
	
	status_and_message = f'Status: {response.status_code} Message: {response.text}' if response else 'NO RESPONSE' 
	
	# Log the error for later review
	self.bot.logger.error(f'API request failed -- {status_and_message}')

	# Advise that the request failed.
	embed = await get_rosterbot_embed(self, context, title='API Request Failed:', description=f'Unable to get {failed_on} info.\n**API request failed.** Command cancelled.', color=build_color(0.01))

	return await send_embed(context, embed)



# Build the dict with player name and Discord Name/ID that's used for Member selection picklist.
def get_member_dict(alliance_name):

	# Load the cached data file. 
	alliance_info = find_cached_data(alliance_name)

	member_dict = {}
	member_info = alliance_info.get('members',{})

	for member in member_info:
		member_discord = member_info[member].get('discord','')
		
		if type (member_discord) is str:
			member_dict[member] = member_discord
		
		else:
			member_discord = f"@{member_discord.get('name')}, ID: {member_discord.get('id')}"
			member_dict[member] = member_discord

	# If found, return the dict of members.
	return member_dict



# Convert a list of dict into a pre-processed list of Discord Choices
# Name (which is displayed) is normal, Value (used for searching) is all lowercase.
def get_choices(LIST_OR_DICT):
	return [Choice(name=choice,value=choice.lower()) for choice in LIST_OR_DICT]



# Generic build of Autocomplete menu choices.
def get_choice_list(current, CHOICE_LIST):

	choices = []

	# Remove special characters
	current = re.sub('\W+','', current).lower()
	
	# Search for any string with these chars in this order
	current = re.compile('.*'+'.*'.join(current)+'.*')

	for choice in CHOICE_LIST:

		# If we found a match, add it to the list
		if current.match(choice.value):
			choices.append(choice)

			# Short circuit if we have the max
			if len(choices) == 25: 
				return choices

	return choices
	


# Leverage fix_auto to fix our autocomplete entries.
def auto_val(VALID_SELECTIONS, selection_or_list):

	val = fix_auto(VALID_SELECTIONS, selection_or_list)

	if type(VALID_SELECTIONS) == dict:
		return VALID_SELECTIONS.get(val, val)
	elif type(VALID_SELECTIONS) == list:
		return VALID_SELECTIONS.index(val) if val in VALID_SELECTIONS else val
	return val



# Leverage find_selection to fix our autocomplete entries.
def fix_auto(VALID_SELECTIONS, selection_or_list):
	
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

	# Compile the matching criteria
	criteria = re.compile(f".*{'.*'.join(entered_value)}.*")

	# Sloppy search using regex
	for list_option in key_list:
		if criteria.match(list_option):
			return key_list.get(list_option)

	# Unknown value. Return original, unchanged
	return selection



# Do the right thing regardless of what we're sent.
async def send_embed(context, embed=None, message=None, file=None):

	# If we already had an existing message, just edit it
	if message:
		attachments = [discord.File(file)] if file else []
		return await message.edit(embed=embed, content=None, attachments=attachments)

	# If we deferred, start with followup
	elif context.interaction:
		if file:	return await context.interaction.followup.send(embed=embed, file=discord.File(file))
		else:		return await context.interaction.followup.send(embed=embed)

	# Otherwise, return a fresh message
	if file:	return await context.send(embed=embed, file=discord.File(file))
	else:		return await context.send(embed=embed)
	

	
async def send_rosterbot_embed(
		self, context: Context, title: str = '', description: str = '', cont : bool = False, color = None, ephemeral = False,
	) -> None:

	if title:
		title = f'__{title}:__' + (' (cont)' if cont else '')

	embed = await get_rosterbot_embed(self, context, title, description, color)
	
	content =  "Here's the info you requested..." if cont else None
	
	await context.send(embed=embed, content=content, ephemeral=ephemeral)



async def send_rosterbot_error(
		self, context: Context, error_msg: str
	) -> None:

	# Log an error message in the logger.
	self.bot.logger.error(error_msg.replace('\n',' '))

	# Build and send an embed with the same message.
	embed = await get_rosterbot_embed(self, context, description=error_msg, color=build_color(0.01), inc_icon=False, inc_footer=False)
	await context.send(embed=embed)



async def get_rosterbot_embed(
		self, context: Context, title: str = '', description: str = '', color = None, inc_icon = True, inc_footer = True,
	) -> discord.Embed:

	embed = discord.Embed(
		title=title,
		color=color or 0xBEBEFE,
		description=description
	)

	if inc_icon and self.bot.user.avatar is not None:
		embed.set_thumbnail(url=self.bot.user.avatar.url)		

	if inc_footer:
		embed.set_footer(
			text=f"Requested by {context.author}",
			icon_url=context.author.display_avatar
		)

	return embed
	


# 
async def get_discord_channels(self, alliance_name: str) -> set:

	results_set = set()

	discord_ids = await self.bot.database.get_discord_ids(alliance_name)

	for discord_id in discord_ids:
		try:
			results_set.add(await self.bot.fetch_channel(int(discord_id)))
		except:
			pass
			
	return results_set


# 
async def get_discord_users(self, alliance_name: str) -> set:

	results_set = set()

	discord_ids = await self.bot.database.get_discord_ids(alliance_name)

	for discord_id in discord_ids:
		try:
			results_set.add(await self.bot.fetch_user(int(discord_id)))
		except:
			pass
			
	return results_set


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
	alliance_name = alliance_info['name'].lower()

	# Initialize or load the details for this Alliance
	alliance_members = cached_members.setdefault(alliance_name, {})

	alliance_members['admin']    = alliance_info.get('admin',{})
	alliance_members['leader']   = alliance_info['leader']
	alliance_members['captains'] = alliance_info.get('captains',[])
	
	member_info = alliance_info['members']
	
	alliance_members['members'] = { member:{'discord':member_info[member].get('discord',{}), 
											'scopely':member_info[member].get('scopely',''), 
											'auth'   :member_info[member].get('auth'),
											'url'    :member_info[member].get('url'),} for member in sorted(member_info, key=str.lower)}

	return alliance_members



# Get scopely_login from cached_member info
@timed(level=3)
def get_scopely_login(alliance_name, user_id):
	global cached_members

	# Get the cached_members structure. Populate it with alliance info if not already loaded.
	alliance_members = cached_members.get(alliance_name.lower())
	if not alliance_members:
		alliance_members = load_cached_members(alliance_name)

	# Discord info for alliance members is stored in members
	member_info = alliance_members['members']

	# Look for any entry that matches our Discord ID.
	for member in member_info:
		if user_id == member_info[member]['discord'].get('id'):
			return member_info[member].get('scopely')
			
	return 



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



# If arg is a string, find alliance_info by name.
# If item passed in is alliance_info, return that.
def find_cached_data(name_or_info):
	alliance_info = {}

	if type(name_or_info) == str:
		alliance_info = msf2csv.find_cached_data(name_or_info)
	elif type(name_or_info) == dict and name_or_info.get('name'):
		alliance_info = name_or_info
	
	return alliance_info



# We do the dirty work of getting a driver.
async def get_recruit_info(self, context, alliance_name, alliance_url, recruit_info):

	# Start by getting a driver.
	loop     = asyncio.get_event_loop()
	log_file = find_log_file()

	driver = await loop.run_in_executor(None, partial(get_driver_and_login, alliance_name=alliance_name, log_file=log_file))

	# Go to the Alliance website.
	driver.get(rf'https://marvelstrikeforce.com/en/alliance/{alliance_url}/card')

	# Wait for Alliance page to fully load. 
	WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'alliance-members')))

	# Build a list of the member names and URLs.
	member_list = []
	while len(member_list)<20:
		time.sleep(0.25)
		member_list = driver.find_element(By.CLASS_NAME, 'alliance-members').find_elements(By.TAG_NAME, 'tr')[1:]

	# Extract just the names -- remove [ME] from the login name.
	member_list = [member.text.split('\n')[0].replace(' [ME]','') for member in member_list if member.text]

	# Build options 
	options = [discord.SelectOption(label = key) for key in sorted(member_list, key=str.lower)[:25]]

	# Allow selection of recruit from list of alliance members.
	selected_member = await get_alliance_members(self, context, options)

	# Only process if we received a valid recruit name...
	if selected_member:

		recruit_name = selected_member[0]

		# Update the recruit_info with roster_url based on the selected member
		roster_url = f'{alliance_url}:{member_list.index(selected_member[0])}'
		recruit_info.update({'name':recruit_name, 'leader':recruit_name, 'admin':{'name':context.author.name, 'id':context.author.id}, 'members':{recruit_name:{'url':roster_url, 'avail':True}}})

		driver.roster_csv = None

		# Populate the recruit_info with roster information from roster_url.
		await loop.run_in_executor(None, partial(msf2csv.process_rosters, recruit_info, driver, only_process=[recruit_info['name']], log_file=log_file))

		# Cache the file to disk if we found valid roster information.
		if recruit_info['members'][recruit_info['name']].get('processed_chars'):
			msf2csv.write_cached_data(recruit_info, msf2csv.get_local_path()+'cached_data', filename=alliance_name+'-RECRUIT')

		# Bail if no valid roster was found.
		else:
			await context.send(f"Failed to load **{recruit_info['name']}**. Command cancelled.", ephemeral=False)

	# Finally, release the driver for additional use.
	release_driver(driver)
	
	


driver_pool = {}

# Ensure that only one request from a given Alliance is actively working on cached_data at any one time
# Also, if multiple roster refresh requests come in at the same time, only honor the first/active one.
@timed(level=3, init=True)
def get_driver_and_login(alliance_name=None, fresh=False, roster_refresh=False, scopely_login='', alliance_info={}, log_file=None, headless=True):
	global driver_pool

	active_pool = driver_pool.setdefault('active',{})
	avail_pool  = driver_pool.setdefault('avail',{})
	pool_queue  = driver_pool.setdefault('queues',{}).setdefault(alliance_name,[])

	driver = None

	# If we provided a scopely_login, need to take a slightly different workflow.
	if scopely_login:

		# If session is defined, will use new mechanism.
		session = None

		# Start by logging in using the Scopely login. 
		driver = msf2csv.login(headless=headless, scopely_login=scopely_login, session=session)
	
		# If no saved credential and user failed to click on the link, login process times out after 5 minutes and returns None.
		if not driver:

			# We return driver = None to indicate that refresh isn't necessary.
			# Calling routine needs to recognize -1 as a complete failure to login.
			return -1
	
		# Assume we got a valid driver back. Start by parsing alliance_info from the Alliance Info page.
		try:
			website_alliance_info = msf2csv.parse_alliance(driver)

		# Failed to get to a valid Alliance Info page. Return -2 for failure to login.
		except Exception as exception:

			# Log the error in logfile.
			print(f"EXCEPTION DURING PARSE ALLIANCE():")
			print(f"{type(exception).__name__}: {exception}")
			print (''.join(traceback.format_exception(exception)))

			# Make sure we close the driver before returning.
			try:
				driver.close()
			except:
				pass

			return -2 

		# Update the alliance_info passed in with fresh Alliance Info data.
		alliance_info.update(website_alliance_info)

		# Now we know what Alliance we are working with.
		if alliance_name != 'recruit':
			alliance_name = driver.alliance_name

	# If there's a stale request from our alliance in the active pool (>5 min), assume failure and remove from pool.
	if alliance_name in active_pool and (datetime.datetime.now() - active_pool[alliance_name]['start_time']).seconds > 300:
		del active_pool[alliance_name]

	# If a valid request from our alliance is in the active pool, add ourselves to the end of the pool queue.
	elif alliance_name in active_pool:
	
		# Short circuit if user is explicitly requesting /roster refresh while an existing refresh is taking place.
		if roster_refresh:

			# Clean up before we leave if we did get a driver opened.
			if driver:
				driver.close()

			return None
	
		# Note whether the current entry is a Roster Refresh (if 'fresh' is True) or not.
		active_is_fresh = active_pool[alliance_name]['fresh']
	
		# Create a unique entry and add it to the end of the queue.
		queue_entry = datetime.datetime.now()
		pool_queue.append(queue_entry)
		
		# Wait until our request is ready to go and there is no active request for our alliance
		while alliance_name in active_pool or pool_queue[0] != queue_entry:
			time.sleep(0.25)
		
		# It's our turn. If the active query was for a roster refresh and 
		# we're asking for the same thing, our request is redundant. Return NONE instead.
		if active_is_fresh and fresh:
			pool_queue.pop(0)
			
			# Clean up before we leave if we did get a driver opened.
			if driver:
				driver.close()
			
			return None
			
		# Otherwise our request still needs a driver.
		# Put name in the active_pool and remove our entry from the queue.
		active_pool[alliance_name] = pool_queue.pop(0)

	#
	# WHO ELSE REQUESTS DRIVERS? JUST RECRUIT?
	#

	# If there's a generic driver already available and Alliance did not request FRESH or a specific SCOPELY_LOGIN, provide the existing driver.
	if avail_pool and not (fresh or scopely_login):
	
		# Add the alliance name to the active pool and preserve the driver's creation date there.
		active_pool[alliance_name], driver = {'fresh':fresh, 'creation_date':list(avail_pool)[0], 'start_time':datetime.datetime.now()}, avail_pool.pop(list(avail_pool)[0])
	
	# Otherwise, an alliance is requesting fresh for a roster refresh. We need to create a fresh driver.
	else:
		active_pool[alliance_name] = {'fresh':fresh, 'creation_date':datetime.datetime.now(), 'start_time':datetime.datetime.now()}

		# If we haven't already created a driver, generate one now.
		if not driver:
			driver = msf2csv.login(headless=headless, scopely_login=scopely_login)
		
	return driver


# Check driver in at the end of processing. Remove us from the active pool.
# Keep only one driver on hand. Close the oldest, keep the newest.
def release_driver(driver):
	global driver_pool

	# If no driver was issued, nothing to do.
	if not driver:
		return

	active_pool = driver_pool.setdefault('active',{})
	avail_pool  = driver_pool.setdefault('avail',{})

	alliance_name = driver.alliance_name

	# Determine creation date of the driver we are checking in.
	creation_date = active_pool[alliance_name]['creation_date']
	
	# If there's no driver available in the avail_pool, just check this one in.
	if not avail_pool:
		avail_pool[creation_date] = driver
	# Otherwise, there's already a driver in the available pool. 
	# Let's compare creation dates and keep the newer one. 
	else:
		avail_creation = list(avail_pool)[0]

		# If the driver we're checking in is NEWER
		if creation_date > avail_creation:
			avail_pool[creation_date], old_driver = driver, avail_pool.pop(avail_creation)
		
			# Close the old driver to release memory.
			old_driver.close()
			
		# Otherwise our driver is older.
		else:
			# Just close it to release memory.
			driver.close()
			
	# Finally, remove ourselves from the active_pool.
	active_pool.pop(alliance_name)
			
	return



# Calculate the color for our Discord Embed
def build_color(percent):

	# Ensure percent is 0-100% 
	percent = max(0,percent)
	percent = min(1,percent)
	
	# Calculate the color value using our standard gradient.
	color = percent * (len(msf2csv.color_scale)-1)
	
	# Convert it from hex to int and return.
	return int('0x'+msf2csv.color_scale[int(color)][1:], 16)



def get_set_defaults(locals):

	# Should always be present
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

	return current_settings



# Allow user to select the Members to include in report.

class SelectMemberView(discord.ui.View):
	def __init__(self, options=[], max_values=1, timeout=30) -> None:
		super().__init__(timeout=timeout)
		self.add_item(SelectMemberPicklist(options, max_values))
		self.value = None

	async def on_timeout(self):
		print("Timed out. No value selected.")
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

		result_embed = discord.Embed(color=0xBEBEFE)
		result_embed.description = f"You selected: **{member_name}**"
		result_embed.colour = 0x57F287

		await interaction.response.edit_message(embed=result_embed, content=None, view=None)

		self.view.value = member_name
		self.view.stop()


async def get_alliance_members(self, context, options, max_values=1):

	members = 'members' if max_values>1 else 'member' 

	# Prompt user to select members to include in report.
	view = SelectMemberView(options, max_values=max_values, timeout=120)
	message = await context.send(f'Which {members} would you like?', view=view, ephemeral=True)
	await view.wait()
	
	selected_members = view.value
	
	# If no members selected, we can't go forward.
	if not selected_members:
		await message.edit(content=f"No {members} selected. Command cancelled.", view=None)
		return

	return selected_members