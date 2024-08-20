"""roster_report.py
Code to generate roster reports inside Discord.
"""

import discord
from discord.ext.commands import Context

from msf_shared import *


# Used by lookup_alliance() if more than one match found.
class SelectAllianceView(discord.ui.View):
	def __init__(self, alliance_list, timeout=30) -> None:
		super().__init__(timeout=timeout)
		self.add_item(SelectAlliancePicklist(alliance_list))
		self.value = None

	async def on_timeout(self):
		print("Select Alliance timed out. No value selected.")
		self.stop()
		
class SelectAlliancePicklist(discord.ui.Select):
	def __init__(self, alliance_list) -> None:
		super().__init__(
			placeholder="Please select an alliance",
			min_values=1,
			max_values=1,
			options=[discord.SelectOption(label = alliance) for alliance in alliance_list],
		)

	async def callback(self, interaction: discord.Interaction) -> None:
		alliance_name = self.values[0]

		result_embed = discord.Embed(color=0xBEBEFE)
		result_embed.description = f"Working with **{alliance_name}**"
		result_embed.colour = 0x57F287

		await interaction.response.edit_message(embed=result_embed, content=None, view=None)

		self.view.value = alliance_name
		self.view.stop()



# Use User/Channel Defaults to determine which Alliance should be used. 
# Ask user if any ambiguity and implement access rights for the selected Alliance. 
async def lookup_alliance(self, context: Context, min_level='', silent=False, match_type='all', alliances_found=[]):

	if not silent:
		log_command(self,context)

	# Look for matching alliances.
	if not alliances_found:
		alliances_found = await self.bot.database.get_alliances(context, match_type)

	# If no matching entries, report that and abort.
	if not alliances_found:
		if not silent:
			await context.send("No valid alliance found. Are you in the right channel?", ephemeral=True)
		return
		
	# More than one matching Alliance found. 
	elif len(alliances_found) > 1:
	
		# If silent requested, provide all matching entries. We cannot ask which Alliance should be used.
		if silent:
			return alliances_found

		# Ask which Alliance user wants to work with.
		view = SelectAllianceView(sorted(alliances_found))
		message = await context.send("Which Alliance?", view=view, ephemeral=True)
		
		# Wait for a response and return it.
		await view.wait()

		# If no Alliance was selected, perhaps we should default to whichever is tied to the channel. 
		if not view.value:
			await message.edit(content=f"No Alliance selected. Command cancelled.", view=None)
			return
			
		# Get the selected alliance_name
		alliance_name = view.value	

	# Only one match found, use it.
	else:
		alliance_name = alliances_found.pop()

	# If no min level or user is bot owner, always succeed.
	if not min_level: #or (await self.bot.is_owner(context.author)):
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
			error_msg = f"\nDiscord ID not connected to player in **{alliance_name}**.\nUse **/roster refresh** to connect your Discord ID to use this command."
		else:
			error_msg = f"**/{context.command.qualified_name}** requires '{min_level.title()}' or higher. Command cancelled."

		embed = await get_rosterbot_embed(self, context, description=error_msg, color=build_color(0.01), inc_icon=False)
		await context.send(embed=embed)

