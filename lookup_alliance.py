"""roster_report.py
Code to generate roster reports inside Discord.
"""

import discord
from discord.ext.commands import Context

from msf_shared import *


# Used by lookup_alliance() if more than one match found.
class SelectAllianceView(discord.ui.View):
	def __init__(self, alliance_list, set_default='', can_set_both=False, timeout=60) -> None:
		super().__init__(timeout=timeout)

		self.value = None

		# Store these values for easy reference
		self.set_default  = set_default
		self.can_set_both = can_set_both

		# Current selection: /set_default for User, Channel, or Both
		self.user_or_channel = None

		# Abstracted alliance entries with cleaned names if possible
		ENTRIES = get_entries_from_alliance_list(alliance_list)
		self.alliance_select.options=[discord.SelectOption(label=entry, value=ENTRIES[entry]) for entry in ENTRIES]

		# Remove or disable buttons based on initial args
		self.update_buttons()


	@discord.ui.select(placeholder="Please select an alliance")
	async def alliance_select(self, interaction: discord.Interaction, select: discord.ui.Select):
		alliance_name = select.values[0]

		embed = discord.Embed(color=0x57F287, description=f"Working with **{msf2csv.remove_tags(alliance_name)}**")

		try:
			await interaction.response.edit_message(embed=embed, content=None, view=None, delete_after=10)
		except Exception as e:
			print (f'{ansi.ltred}ERROR!{ansi.reset} Caught {type(e).__name__}: {e}  during edit_message(). Alliance selected was {msf2csv.remove_tags(alliance_name)}.')

		self.value = alliance_name
		self.stop()


	@discord.ui.button(label="User", style=discord.ButtonStyle.blurple)
	async def user_btn(
		self, interaction: discord.Interaction, button: discord.ui.Button
	) -> None:
		await self.button_pressed(interaction, button) 


	@discord.ui.button(label="Channel", style=discord.ButtonStyle.blurple)
	async def channel_btn(
		self, interaction: discord.Interaction, button: discord.ui.Button
	) -> None:
		await self.button_pressed(interaction, button) 


	@discord.ui.button(label="Both", style=discord.ButtonStyle.blurple)
	async def both_btn(
		self, interaction: discord.Interaction, button: discord.ui.Button
	) -> None:
		await self.button_pressed(interaction, button) 


	async def button_pressed(
		self, interaction: discord.Interaction, button: discord.ui.Button
	) -> None:

		# Toggle the button selection
		self.user_or_channel = None if self.user_or_channel == button else button

		# Update the menus and button controls
		self.update_buttons()

		# Default: display the standard set_default text
		guidance = self.set_default

		# If we have selected a button, provide specific info about that selection
		if self.user_or_channel:
			if button.label == 'User':
				guidance = '\n-# **USER DEFAULT:** Your /roster commands will use this alliance'
			elif button.label == 'Channel':
				guidance = '\n-# **CHANNEL DEFAULT:** Commands in this channel will use this alliance' 
			elif button.label == 'Both':
				guidance = '\n-# **BOTH:** Alliance is default for you anywhere and commands in this channel' 

		# Edit the original message with the updated view
		await interaction.response.edit_message(content=f'Which alliance?{guidance}', view=self)


	# Update the Select Menu, Option Menu, and button controls as necessary
	def update_buttons(self):

		# If can't set default, remove the buttons -- we're here because of a conflict 
		if not self.set_default:
			for button in (self.user_btn, self.channel_btn, self.both_btn):
				self.remove_item(button)

		# If user isn't a captain, disable CHANNEL and BOTH buttons
		if not self.can_set_both:
			for button in (self.channel_btn, self.both_btn):
				button.disabled = True
			
		# Update button coloring
		for button in (self.user_btn, self.channel_btn, self.both_btn):
			button.style = discord.ButtonStyle.green if self.user_or_channel==button else discord.ButtonStyle.grey if self.user_or_channel else discord.ButtonStyle.blurple
			

	async def on_timeout(self):
		self.stop()


@timed
async def select_alliance(self, context: Context, alliance_list):

	# Initialize a few variables
	can_set_both = False
	set_default  = ''

	USER_DEFAULT    = await self.bot.database.get_default_alliance_name(context.author.id)
	CHANNEL_DEFAULT = await self.bot.database.get_default_alliance_name(context.channel.id)

	# If there's a CHANNEL DEFAULT or USER DEFAULT then do not offer to set_default
	if not (USER_DEFAULT or CHANNEL_DEFAULT):

		# Only mention Channel Default if a captain or higher
		can_set_both    = await get_one_alliance(self, context, min='captain')
		user_or_channel = 'user/channel' if can_set_both else 'user'

		set_default = f'\n-# **OPTIONAL:** Use as {user_or_channel} default?' 
	
	# Ask which Alliance user wants to work with.
	view = SelectAllianceView(sorted(alliance_list), set_default, can_set_both)
	
	# Add one more line
	if set_default:
		set_default += '\n-# *(For info on defaults see: **/help Set Default**)*'
	
	message = await context.send(f"Which Alliance?{set_default}", view=view, ephemeral=True)

	# Wait for a response and return it.
	await view.wait()

	# If no Alliance was selected, perhaps we should default to whichever is tied to the channel. 
	if not view.value:
		await send_rosterbot_error(self, context, f"**TIMEOUT:** No Alliance selected. Command cancelled.", message=message)

	# If a target for set_default was selected, need to set defaults
	if view.value and view.user_or_channel:

		# Only channel we can be working on is the current channel
		CHANNEL_NAME = get_discord_channel_name(context.channel)

		if view.user_or_channel.label.lower() in ('both', 'user'):
			await self.bot.database.set_default_entry(context.author.id, view.value, context.author.id, context.author.name, 'user')
		if view.user_or_channel.label.lower() in ('both', 'channel'):
			await self.bot.database.set_default_entry(context.channel.id, view.value, context.author.id, CHANNEL_NAME, 'channel')

		# Confirm set_default successful with Database Query
		results  = await report_defaults(self, context, context.author)
		results += await report_defaults(self, context, context.channel)

		await context.send(results, ephemeral=True, delete_after=30)
	
	# Return the selected alliance_name
	return view.value


# Use User/Channel Defaults to determine which Alliance should be used. 
# Ask user if any ambiguity and implement access rights for the selected Alliance. 
@timed
async def lookup_alliance(self, context: Context, min_level='', silent=False, alliances_found: list=None):

	# Look for matching alliances.
	if not alliances_found:
		alliances_found = await get_avail_alliances(self, context)

	# If no matching entries, report that and abort.
	if not alliances_found:
		if not silent:
			await context.send(f"No linked alliance found. Command cancelled.")
			await send_auth_link(self, context)
		return
		
	# More than one matching Alliance found. 
	elif len(alliances_found) > 1:
	
		# If silent requested, provide all matching entries. We cannot ask which Alliance should be used.
		if silent:
			return alliances_found

		alliance_name = await select_alliance(self, context, alliances_found)
		
		if not alliance_name:
			return

	# Only one match found, use it.
	else:
		alliance_name = list(alliances_found).pop()

	# If no min level or user is bot owner, always succeed.
	if not min_level or (await is_owner(self, context)):
		return alliance_name

	# See if there's a user with this Discord ID in alliance_info and if member is captain, leader, or admin.
	member_role = get_member_role(alliance_name, context.author.id)

	# Leader and admin are really synonymous.
	if min_level == 'leader' and member_role in ['leader', 'admin']:
		return alliance_name
		
	# Captain or above.
	elif min_level == 'captain' and member_role in ['leader', 'admin', 'captain']:
		return alliance_name

	# Match found, but failed for min_level. If silent not requested, use the custom error.
	if not silent:

		# Member using command is unknown. Advise that they should use /roster refresh.
		if not member_role:
			AUTH_URL = await get_auth_url(self, context)
			error_msg = f"Discord ID not connected to in-game name. [**CLICK HERE**]({AUTH_URL}) to link your account. Command cancelled."
			await send_rosterbot_error(self, context, error_msg, delete_after=30)

		else:
			error_msg = f"**/{context.command.qualified_name}** requires '{min_level.title()}' or higher. Command cancelled."
			await send_rosterbot_error(self, context, error_msg)

