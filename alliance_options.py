"""alliance_options.py
Picklists and enumerations for use in the /alliance menus.
"""

from discord import Interaction
from discord.ext.commands import Context

from enum import Enum
from msf_shared import *




RAID_TYPE = Enum('RAID_TYPE', {'Chaos':'chaos', 'Spotlight':'spotlight'})
TEAM_NUM  = Enum('TEAM_NUM', [str(x+1) for x in range(3)])
LANE_NUM  = Enum('LANE_NUM', [str(x+1) for x in range(8)])

SET_DEFAULT_OPTIONS    = Enum('options', [
	'Allow Refresh and Reports',
	'Allow Reports only',
	])

REMOVE_DEFAULT_OPTIONS = Enum('options', [
	'Remove Refresh',
	'Remove Refresh and Reports',
	])



# Verify member is Captain, Leader, Admin or Bot Owner
async def captain_or_above(self, context: Context, alliance_name) -> bool:
	bot_owner     = await is_owner(self, context)
	leadership    = get_member_role(alliance_name, context.author.id) in ('captain','leader','admin')

	return bot_owner or leadership



async def find_matching_alliance(self, context, alliance_name, min=''):

	# Find a matching Alliance if entered.
	if alliance_name:
		alliance_match = auto_fix(await get_available_alliances(self, context, min), alliance_name)

		# Special Handling if nothing found in regular list
		if not alliance_match and await is_owner(self, context):
			alliance_match = auto_fix(get_alliance_names_from_files(), alliance_name)
			
		alliance_name = alliance_match

	# If nothing entered or no match, look for a single valid option
	if not alliance_name:
		alliance_name = await get_one_alliance(self, context, min)

	return alliance_name



async def get_available_alliances(self, context: Context, min: str='') -> list:
	
	# Get names from user auths.
	avail_alliances = await self.bot.database.get_auths_by_owner(context.author.id)
	
	# Get names from explicitly defined defaults.
	avail_alliances.union(await self.bot.database.get_default_alliance([context.author.id, context.channel.id]))

	# purge entries if less than min.
	if min in ('captain','leader'):
		for alliance_name in list(avail_alliances):
			if get_member_role(alliance_name, context.author.id) not in (min, 'leader','admin'):
				avail_alliances.remove(alliance_name)

	return sorted(avail_alliances)



def under_min(alliance_name, discord_id, min):
	return min in ('captain','leader') and get_member_role(alliance_name, discord_id) not in (min, 'leader','admin')



# Return ONE matching alliance
async def get_one_alliance(self, context: Context, min: str='') -> str:

	# Default on channel always takes priority
	alliance_name = await self.bot.database.get_default_alliance(context.channel.id)

	# If none found, or not high enough -- Default on user is next 
	if not alliance_name or under_min(alliance_name, context.author.id, min):
		alliance_name = await self.bot.database.get_default_alliance(context.author.id)
	
	# If none found, or not high enough -- Check auths on user last 
	if not alliance_name or under_min(alliance_name, context.author.id, min):
		for alliance_name in sorted(await self.bot.database.get_auths_by_owner(context.author.id)):
			if not under_min(alliance_name, context.author.id, min):
				break

	if alliance_name and under_min(alliance_name, context.author.id, min):
		alliance_name = ''

	return alliance_name



# Get a list of ALL available alliances.
async def alliance_avail_auto(self, interaction: Interaction, current: str, min: str=''):
	context = await self.bot.get_context(interaction)

	ALLIANCE_NAMES  = await get_available_alliances(self, context, min)
	CHOICES         = await get_choices_from_alliance_names(self, context, current, ALLIANCE_NAMES)
	return CHOICES or await get_choices_from_alliance_names(self, context, current)



