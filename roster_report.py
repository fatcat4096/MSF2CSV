"""roster_report.py
Code to generate roster reports inside Discord.
"""

import discord
from discord.ext.commands import Context

from msf_shared import *
from lookup_alliance import lookup_alliance
from roster_refresh  import get_roster_refresh

import datetime



# Ask all the pertinent questions to fill out table_format and then generate the actual report.
@timed
async def get_roster_report(
	self, context: Context, table_format, NEED_DEFER=True
) -> None:

	#
	# REWRITE get_avail_alliances(context) TO INCLUDE DEFAULT AUTHS ON USER/CHANEL IN AVAILABLE ALLIANCES LIST
	# REWRITE THIS LOGIC TO INCLUDE FLAG FOR SPECIFIC ALLIANCE REQUESTED BY OWNER
	#

	# Figure out whether we are immediately prompting for information.
	NEED_ALLI = len(await self.bot.database.get_avail_alliances(context)) != 1			
	NEED_HIST = table_format.get('inc_hist') or table_format.get('inline_hist')
	HAVE_HIST = table_format.get('use_oldest')
	NEED_MEMB = table_format.get('select_members')
	NEED_KEYS = table_format.get('custom_keys')

	PROMPTING = NEED_ALLI or (NEED_HIST and not HAVE_HIST) or NEED_MEMB or NEED_KEYS
	DEFERRED  = not PROMPTING and context.interaction and NEED_DEFER

	# If not asking clarifying questions immediately,
	# show "MSFRosterBot is Thinking" to buy me some time.
	if DEFERRED:
		await context.interaction.response.defer(ephemeral=False)

	#
	# SPECIFIC ALLIANCE REQUESTED BY OWNER PASSED IN VIA TABLE_FORMAT, PROVIDE THAT HINT IN THIS CALL
	#

	# Determine which, if any, alliance is valid for this combination of user, roles, and channel.
	alliance_name = table_format.get('use_alliance_info') or await lookup_alliance(self, context)

	# If no valid alliance, have to bail.
	if not alliance_name:
		return

	# Ask user to select hist_date if requested.
	if NEED_HIST:
		await get_hist_date(self, context, alliance_name, table_format)

	if NEED_MEMB:

		# Build the options for member selection 
		member_dict = get_member_dict(alliance_name)
		options = [discord.SelectOption(label = key, description = member_dict[key]) for key in sorted(member_dict, key=str.lower)[:25]]

		# Allow selection of multiple members.
		selected_members = await get_alliance_members(self, context, options, len(options))

		# No members selected, command cancelled.
		if not selected_members:
			return

		table_format['only_members'] = selected_members
		
	# Ask user to select custom keys if requested.
	if NEED_KEYS:
		await get_custom_keys(self, context, table_format)

	output_name = table_format.get('output')

	# Take note of when we started.
	start_time = datetime.datetime.now()

	# Before we start, make sure we are not already running the same report for the same alliance. 
	if report_in_progress(alliance_name, output_name, start_time) != start_time:
		return await send_rosterbot_error(self, context, f"**/roster {output_name}** for **{msf2csv.remove_tags(alliance_name)}** already in progress.\nCommand cancelled.")

	# Just log the table_format contents. 
	self.bot.logger.info (f'{table_format=}')

	message = None
	embed   = None

	# If we didn't defer interaction, add a message so there's not a long pause
	# while we grab reports or refresh the rosters.
	if not DEFERRED:
		message = await context.send("One moment...", ephemeral=False)

	# How long has it been since Alliance Info has been updated?
	STALE_DATA = not msf2csv.fresh_enough(alliance_name)

	# If STALE_DATA, let's see if we can find a valid AUTH
	if STALE_DATA and not DISABLE_REFRESH:

		AUTH = await get_auth(self, context, alliance_name)

		# If a valid AUTH is available, get the report using stale data first.
		if AUTH:

			# If we're generating multiple images, only get the first image.
			if table_format.get('output_format') == 'image' and not table_format.get('only_section'):
				table_format['render_sections'] = True	

			report = await get_report(self, alliance_name, table_format)

			# Next, request a refresh of the roster.
			message, embed = await get_roster_refresh(self, context, AUTH, alliance_name, report, message)

	# If we're generating multiple images, render them in sections.
	if table_format.get('output_format') == 'image' and not table_format.get('only_section'):
		table_format['render_sections'] = True

	# If not STALE_DATA, this is the first time we've generated a report
	# If STALE_DATA, this is updating the original report after refresh
	report = await get_report(self, alliance_name, table_format)

	if not report:
		report_is_complete(alliance_name, output_name, start_time)
		return await send_rosterbot_error(self, context, f"**/roster {output_name}** for **{msf2csv.remove_tags(alliance_name)}** failed.\nCommand cancelled.")
	
	# If we didn't create an embed in roster refresh, make one now 
	if not embed:
		description = f"Requested info is **ABOVE**{' and continues **BELOW**' if table_format.get('render_sections') else ''}."
		
		if STALE_DATA and not DISABLE_REFRESH:
			description += f'\n```ansi\n{ansi.bold}{ansi.red}WARNING:{ansi.reset} Info is {ansi.bold}STALE{ansi.reset} ({int(msf2csv.age_of(alliance_name)/86400)}d)\nUse {ansi.bold}/roster refresh{ansi.reset} to update\n```'
		embed = await get_rosterbot_embed(self, context, description=description, color=0x3cde07, inc_icon=False, inc_footer=False)	# Green, indicates we are done.

	# If we don't have a message to edit, just make one now
	if not message:
		message = await context.send(embed=embed, file=discord.File(report[0]))
	# Edit the existing message with the provided embed and file attachments
	else:
		attachments = [discord.File(report[0])] if report else []
		await message.edit(embed=embed, content=None, attachments=attachments)

	# If more than one file was returned, send the rest, four at a time
	while table_format.get('render_sections'):
		report = await get_report(self, alliance_name, table_format)

		# Something went wrong during segmented rendering. Abort
		if not report:	break
		
		await context.send(files=[discord.File(file) for file in report])

	# Signal that we're done with this
	report_is_complete(alliance_name, output_name, start_time)

	# Log the completion time
	self.bot.logger.info (f'Report Complete. Total time is {(datetime.datetime.now()-start_time).seconds}s.')



# Actually request the report from msf2csv.py.
async def get_report(
	self, alliance_name, table_format
):
	loop = asyncio.get_event_loop()
	
	return await loop.run_in_executor(None, partial(msf2csv.main, alliance_name, force='stale', table_format=table_format, log_file=find_log_file()))



# Allow user to select the Date to use for History.

class SelectHistoryView(discord.ui.View):
	def __init__(self, hist_list, timeout=30) -> None:
		super().__init__(timeout=timeout)
		self.add_item(SelectHistoryPicklist(hist_list))
		self.value = None
		
	async def on_timeout(self):
		print("Select History timed out. No value selected.")
		self.stop()


		
class SelectHistoryPicklist(discord.ui.Select):
	def __init__(self, hist_list) -> None:
		super().__init__(
			placeholder="Please select a date",
			min_values=1,
			max_values=1,
			options=[discord.SelectOption(label = str(date)) for date in hist_list],
		)

	async def callback(self, interaction: discord.Interaction) -> None:
		hist_date = self.values[0]

		result_embed = discord.Embed(color=0xBEBEFE)
		result_embed.description = f"Working with **{hist_date}**"
		result_embed.colour = 0x57F287

		await interaction.response.edit_message(embed=result_embed, content=None, view=None)

		self.view.value = hist_date
		self.view.stop()



async def get_hist_date(
	self, context: Context, alliance_name, table_format
) -> None:

	# Get the list of historical entries from the cached data file.
	hist_list = sorted(msf2csv.find_cached_data(alliance_name).get('hist',{}), reverse=True)

	# Today's date is not an option for History
	hist_list = hist_list[1:]

	# If no other dates, history cannot be used.
	if not hist_list:
		selected_date = None
	# If only one historical entry, automatically use that.
	elif len(hist_list) == 1:
		selected_date = hist_list[0]
	# If we've specified to use oldest, no need to prompt.
	elif table_format.get('use_oldest'):
		selected_date = min(hist_list)
	# If more than one, need to ask the user which one they want.
	else:
		view = SelectHistoryView(hist_list)
		message = await context.send("Which date should be used for History?", view=view, ephemeral=True)
		await view.wait()

		# Do a reverse lookup to find the matching entry for the String returned.
		if view.value:
			selected_date = {str(date):date for date in hist_list}[view.value]
		else:
			await message.edit(content=f"No value for History selected. Oldest available date will be used.", view=None)
			selected_date = min(hist_list)

	# Fill the appropriate field
	if table_format.get('inc_hist'):
		table_format['inc_hist'] = selected_date
	if table_format.get('inline_hist'):
		table_format['inline_hist'] = selected_date



# Allow user to select the Info to include in report.

class SelectKeysView(discord.ui.View):
	def __init__(self, poss_keys, def_keys, timeout=30) -> None:
		super().__init__(timeout=timeout)
		self.add_item(SelectKeysPicklist(poss_keys, def_keys))
		self.value = []

	async def on_timeout(self):
		print("Select Keys timed out. No value selected.")
		self.stop()



class SelectKeysPicklist(discord.ui.Select):
	def __init__(self, poss_keys, def_keys) -> None:
		super().__init__(
			placeholder="Which keys should be included?",
			min_values=1,
		)
		self.max_values = len(poss_keys)
		self.options	= [discord.SelectOption(label = key, description = poss_keys[key], value = key.lower(), default = key.lower() in def_keys) for key in poss_keys]

	async def callback(self, interaction: discord.Interaction) -> None:
		selected_keys = self.values

		result_embed = discord.Embed(color=0xBEBEFE)
		result_embed.description = f"You selected keys: **{selected_keys}**"
		result_embed.colour = 0x57F287

		await interaction.response.edit_message(embed=result_embed, content=None, view=None)

		self.view.value = selected_keys
		self.view.stop()



async def get_custom_keys(
	self, context: Context, table_format
) -> None:

	poss_keys = {	'Power' : 'Character Power',
					'ISO'   : 'ISO Level',
					'Lvl'   : 'Character Level',
					'Tier'  : 'Gear Tier',
					'OP'    : 'Overpower Level',
					'Yel'   : 'Yellow Stars',
					'Red'   : 'Red Stars',
					'Abil'  : 'Ability Levels',
					'Cls'   : 'ISO Class'	}

	# Get the default keys for this output.
	table    = msf2csv.tables.get(table_format.get('output'),{})
	def_keys = msf2csv.get_table_value(table_format, table, {}, key='inc_keys', default=['power','tier','iso'])
	
	# Special handling for ISO Class.
	if msf2csv.get_table_value(table_format, table, {}, key='inc_class', default=False):
		def_keys.append('cls')

	view = SelectKeysView(poss_keys, def_keys)
	message = await context.send("Which info should be included?", view=view, ephemeral=True)
	await view.wait()

	selected_keys = view.value
	
	if not selected_keys:
		await message.edit(content=f"Custom Info not selected. Will use default Info instead.", view=None)
	else:	
		# Special processing for ISO Class
		if 'cls' in selected_keys:
			table_format['inc_class'] = True
			selected_keys.remove('cls')

		# Include the selected keys in the table_format
		table_format['inc_keys'] = selected_keys



# Super basic dict to keep track of in-flight Report requests.
already_in_progress = {}



# Check to see if we're already processing this request.
def report_in_progress(alliance_name, output_name, start_time):
	global already_in_progress

	report = f'{alliance_name} {output_name}'

	# If we're been working on this report more than 90 seconds, it crashed...time to move on.
	if report in already_in_progress and (datetime.datetime.now() - already_in_progress[report]).seconds > 90:
		del already_in_progress[report]

	return already_in_progress.setdefault(report, start_time)



# Clear up the table after we're done.
def report_is_complete(alliance_name, output_name, start_time):
	global already_in_progress

	report = f'{alliance_name} {output_name}'

	# Delete the entry if it hasn't been changed.
	if report in already_in_progress and already_in_progress[report] == start_time:
		del already_in_progress[report]

