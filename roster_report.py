"""roster_report.py
Code to generate roster reports inside Discord.
"""

import discord
from discord.ext.commands import Context

from datetime import datetime, timezone, timedelta
from msf_shared import *
from lookup_alliance import lookup_alliance
from roster_refresh  import get_roster_refresh




  #8888b.  8888888888 88888888888      8888888b.   .d88888b.   .d8888b. 88888888888 8888888888 8888888b.       8888888b.  8888888888 8888888b.   .d88888b.  8888888b. 88888888888 
#88P  Y88b 888            888          888   Y88b d88P" "Y88b d88P  Y88b    888     888        888   Y88b      888   Y88b 888        888   Y88b d88P" "Y88b 888   Y88b    888     
#88    888 888            888          888    888 888     888 Y88b.         888     888        888    888      888    888 888        888    888 888     888 888    888    888     
#88        8888888        888          888   d88P 888     888  "Y888b.      888     8888888    888   d88P      888   d88P 8888888    888   d88P 888     888 888   d88P    888     
#88  88888 888            888          8888888P"  888     888     "Y88b.    888     888        8888888P"       8888888P"  888        8888888P"  888     888 8888888P"     888     
#88    888 888            888          888 T88b   888     888       "888    888     888        888 T88b        888 T88b   888        888        888     888 888 T88b      888     
#88b  d88P 888            888          888  T88b  Y88b. .d88P Y88b  d88P    888     888        888  T88b       888  T88b  888        888        Y88b. .d88P 888  T88b     888     
  #8888P88 8888888888     888          888   T88b  "Y88888P"   "Y8888P"     888     8888888888 888   T88b      888   T88b 8888888888 888         "Y88888P"  888   T88b    888     



# Ask all the pertinent questions to fill out table_format and then generate the actual report.
@timed
async def get_roster_report(
	self, context: Context, table_format
) -> None:

	# Figure out whether we are immediately prompting for information
	NEED_ALLI = len(await get_avail_alliances(self, context)) != 1			
	NEED_HIST = table_format.get('inc_hist') or table_format.get('inline_hist')
	HAVE_HIST = table_format.get('use_oldest')
	NEED_MEMB = table_format.get('select_members')
	NEED_KEYS = table_format.get('custom_keys')

	PROMPTING = NEED_ALLI or (NEED_HIST and not HAVE_HIST) or NEED_MEMB or NEED_KEYS
	DEFERRED  = not PROMPTING and context.interaction
	REFRESH_ENABLED = not await refresh_disabled(self, context)

	# If not asking clarifying questions immediately,
	# show "MSFRosterBot is Thinking" to buy me some time.
	if DEFERRED:
		try:	await context.interaction.response.defer(ephemeral=False)
		except:	pass

	# Determine which, if any, alliance is valid for this combination of user, roles, and channel.
	alliance_name = table_format.get('alliance_name') or await lookup_alliance(self, context)

	# If no valid alliance, have to bail.
	if not alliance_name:
		return

	# Ask user to select hist_date if requested.
	if NEED_HIST:
		await get_hist_date(self, context, alliance_name, table_format)

	if NEED_MEMB:

		# Load the cached data file
		alliance_info = find_cached_data(alliance_name)

		# Get a little closer to our work
		member_info   = alliance_info.get('members',{})

		# Build menu options list
		options = []
		
		for member in sorted(member_info, key=str.lower):
			member_discord = member_info[member].get('discord')
			options.append(discord.SelectOption(label=member, description='' if not member_discord else f"@{member_discord.get('name')}, ID: {member_discord.get('id')}"))

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
	start_time = datetime.now()

	# Before we start, make sure we are not already running the same report for the same alliance. 
	if await report_in_progress(alliance_name, output_name, start_time) != start_time:
		return await send_rosterbot_error(self, context, f"**/roster {output_name}** for **{msf2csv.remove_tags(alliance_name)}** already in progress.\nCommand cancelled.")

	# Just log the table_format contents. 
	self.bot.logger.info (f'table_format: {ansi.bold}{table_format}{ansi.reset}')

	message = None
	embed   = None

	# If we didn't defer interaction, add a message so there's not a long pause
	# while we grab reports or refresh the rosters.
	if not DEFERRED:
		message = await context.send("One moment...", ephemeral=False)

	# How long has it been since Alliance Info has been updated?
	STALE_DATA = not msf2csv.fresh_enough(alliance_name)
	
	# Are we within the 24 hours after Sunday Reset / End of Season?
	SEASON_END = not (datetime.now(timezone.utc) + timedelta(hours=3)).weekday()
	if SEASON_END:
		self.bot.logger.info (f"{ansi.yellow}  SEASON END:{ansi.reset} Checking for 'different members' condition.")

	# If STALE_DATA or within 24 hours after Sunday Reset, look for AUTH
	if STALE_DATA or SEASON_END:
	
		# Only look for AUTH if refresh is NOT disabled
		AUTH = REFRESH_ENABLED and await get_valid_auth(self, context, alliance_name, silent=True)

		# Has member list changed at all?
		DIFF_MEMBERS = AUTH and not AUTH['same_members']

		# If stale data, starting a refresh
		if STALE_DATA: 
			self.bot.logger.info (f"{ansi.yellow}  STALE DATA:{ansi.reset} Past 24 hours; will force Refresh.")
		# Otherwise, it's SEASON_END and the members have changed.
		elif DIFF_MEMBERS:
			self.bot.logger.info (f"{ansi.yellow}  SEASON END:{ansi.reset} Found 'different members' in AUTH; will force Refresh.")

		# If a valid AUTH is available and alliance info is out of date
		# (STALE DATA or diff members), generate a report and then refresh
		if AUTH and (STALE_DATA or DIFF_MEMBERS):

			# If we're generating multiple images, only get the first image.
			if table_format.get('output_format') == 'image' and not table_format.get('only_section'):
				table_format['render_sections'] = True	

			report = await get_report(self, alliance_name, table_format)

			# Were we unable to generate a report? 
			if not report:
				error_msg = 'Problem with cached data. Refreshing roster info.'
				if message:	await send_message(context, message, content=error_msg)
				message   = await send_rosterbot_error(self, context, error_msg)

			# For automatic roster refresh, always just provide summary only
			AUTH['show_old'] = 2

			# Next, request a refresh of the roster.
			message, embed = await get_roster_refresh(self, context, AUTH, message, report if report else [])

			# Update alliance_name with new name if changed during refresh
			alliance_name = AUTH['alliance_name']

	# If we're generating multiple images, render them in sections.
	if table_format.get('output_format') == 'image' and not table_format.get('only_section'):
		table_format['render_sections'] = True

		# Make sure indexes are reset
		table_format.pop('lane_idx', None)
		table_format.pop('section_idx', None)
		
		# Also, if one_per_member, re-do if generated image from stale data
		if table_format.get('one_per_member'):
			table_format['only_members'] += table_format.get('redo_if_stale',[])

	# If not STALE_DATA, this is the first time we've generated a report
	# If STALE_DATA, this is updating the original report after refresh
	report = await get_report(self, alliance_name, table_format)

	# If we weren't able to generate an image, report the issue then bail
	if not report:
		await report_is_complete(alliance_name, output_name, start_time)
		await send_rosterbot_error(self, context, f"**/roster {output_name}** for **{msf2csv.remove_tags(alliance_name)}** failed.\nCommand cancelled.")
		
		# If no alliance linked yet, suggest linking might help?
		if not await self.bot.database.get_auths_by_owner(context.author.id):
			AUTH_URL = await get_auth_url(self, context)
			await context.send(f"No linked alliance found. [**CLICK HERE**]({AUTH_URL}) to link your account.", ephemeral=True, delete_after=30)

		return

	# If we didn't create an embed in roster refresh, make one now 
	if not embed:
		description = f"Requested info is **ABOVE**"

		# Note if more sections will follow
		if table_format.get('render_sections'):
			description += "\nOther sections will be **BELOW**"

		# Add footer
		if '\n' not in description:
			description += add_footer(self)
		
		# Add STALE notification
		if STALE_DATA and REFRESH_ENABLED:
			how_old = int(msf2csv.age_of_cached_data(alliance_name)/86400)
			description += f'\n```ansi\n{ansi.ltred}WARNING:{ansi.reset} Info is {ansi.bold}STALE{ansi.reset} ({how_old}d)\nUse {ansi.bold}/roster refresh{ansi.reset} to update```'

		# Finally, build the embed
		embed = await get_rosterbot_embed(self, context, description=description, color=0x3cde07, inc_icon=False, inc_footer=False)	# Green, indicates we are done.

	# Send the message with the generated (or updated) reports
	message = await send_message(context, message=message, embed=embed, attachments=report if report else [])

	# If more than one file was returned, request and send the rest, four at a time
	while table_format.get('render_sections'):
		report = await get_report(self, alliance_name, table_format)

		# Something went wrong during segmented rendering. Abort
		if not report:	break

		await send_message(context, attachments=report)

	# Signal that we're done with this
	await report_is_complete(alliance_name, output_name, start_time)

	# Log the completion time
	self.bot.logger.info (f'Report Complete. Total time is {ansi.bold}>> {(datetime.now()-start_time).seconds}s <<{ansi.reset}')



  #8888b.  8888888888 88888888888      8888888b.  8888888888 8888888b.   .d88888b.  8888888b. 88888888888 
#88P  Y88b 888            888          888   Y88b 888        888   Y88b d88P" "Y88b 888   Y88b    888     
#88    888 888            888          888    888 888        888    888 888     888 888    888    888     
#88        8888888        888          888   d88P 8888888    888   d88P 888     888 888   d88P    888     
#88  88888 888            888          8888888P"  888        8888888P"  888     888 8888888P"     888     
#88    888 888            888          888 T88b   888        888        888     888 888 T88b      888     
#88b  d88P 888            888          888  T88b  888        888        Y88b. .d88P 888  T88b     888     
  #8888P88 8888888888     888          888   T88b 8888888888 888         "Y88888P"  888   T88b    888     



# Actually request the report from msf2csv.py.
async def get_report(
	self, alliance_name, table_format
):
	loop = asyncio.get_event_loop()

	# Pre-fetch alliance_info and log which file was used for output.
	alliance_info = msf2csv.find_cached_data(alliance_name)
	self.bot.logger.info (f" {ansi.yellow}cached data: {ansi.bold}{os.path.basename(alliance_info.get('file_path',f'{ansi.red}FILE NOT FOUND'))}{ansi.reset}")

	# If no alliance_info found, bail
	if not alliance_info:
		return
	
	report = await loop.run_in_executor(None, partial(msf2csv.main, alliance_info, table_format=table_format, log_file=find_log_file()))

	for file in report:
		self.bot.logger.info (f" {ansi.cyan}result file: {ansi.ltcyan}{os.path.basename(file)}{ansi.reset}")

	return report


  #8888b.  8888888888 88888888888      888    888 8888888 .d8888b. 88888888888      8888888b.        d8888 88888888888 8888888888 
#88P  Y88b 888            888          888    888   888  d88P  Y88b    888          888  "Y88b      d88888     888     888        
#88    888 888            888          888    888   888  Y88b.         888          888    888     d88P888     888     888        
#88        8888888        888          8888888888   888   "Y888b.      888          888    888    d88P 888     888     8888888    
#88  88888 888            888          888    888   888      "Y88b.    888          888    888   d88P  888     888     888        
#88    888 888            888          888    888   888        "888    888          888    888  d88P   888     888     888        
#88b  d88P 888            888          888    888   888  Y88b  d88P    888          888  .d88P d8888888888     888     888        
  #8888P88 8888888888     888          888    888 8888888 "Y8888P"     888          8888888P" d88P     888     888     8888888888 



# Allow user to select the Date to use for History.

class SelectHistoryView(discord.ui.View):
	def __init__(self, hist_list, timeout=30) -> None:
		super().__init__(timeout=timeout)
		self.add_item(SelectHistoryPicklist(hist_list))
		self.value = None
		
	async def on_timeout(self):
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

		try:
			await interaction.response.edit_message(embed=result_embed, content=None, view=None, delete_after=10)
		except Exception as e:
			print (f'{ansi.ltred}ERROR!{ansi.reset} Caught {type(e).__name__}: {e}  during edit_message(). Date selected was {hist_date}.')

		self.view.value = hist_date
		self.view.stop()



async def get_hist_date(
	self, context: Context, alliance_name, table_format
) -> None:

	# Get the list of historical entries from the cached data file
	hist_list = sorted(msf2csv.find_cached_data(alliance_name).get('hist',{}), reverse=True)

	# Today's date is not an option for History
	hist_list = hist_list[1:26]

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
			await send_rosterbot_error(self, context, f"**TIMEOUT:** No value for History selected. Oldest available date will be used", message=message, warning=True)
			selected_date = min(hist_list)

	# Fill the appropriate field
	if table_format.get('inc_hist'):
		table_format['inc_hist'] = selected_date
	if table_format.get('inline_hist'):
		table_format['inline_hist'] = selected_date



  #8888b.  8888888888 88888888888       .d8888b.  888     888  .d8888b. 88888888888 .d88888b.  888b     d888      888    d8P  8888888888 Y88b   d88P  .d8888b.  
#88P  Y88b 888            888          d88P  Y88b 888     888 d88P  Y88b    888    d88P" "Y88b 8888b   d8888      888   d8P   888         Y88b d88P  d88P  Y88b 
#88    888 888            888          888    888 888     888 Y88b.         888    888     888 88888b.d88888      888  d8P    888          Y88o88P   Y88b.      
#88        8888888        888          888        888     888  "Y888b.      888    888     888 888Y88888P888      888d88K     8888888       Y888P     "Y888b.   
#88  88888 888            888          888        888     888     "Y88b.    888    888     888 888 Y888P 888      8888888b    888            888         "Y88b. 
#88    888 888            888          888    888 888     888       "888    888    888     888 888  Y8P  888      888  Y88b   888            888           "888 
#88b  d88P 888            888          Y88b  d88P Y88b. .d88P Y88b  d88P    888    Y88b. .d88P 888   "   888      888   Y88b  888            888     Y88b  d88P 
  #8888P88 8888888888     888           "Y8888P"   "Y88888P"   "Y8888P"     888     "Y88888P"  888       888      888    Y88b 8888888888     888      "Y8888P"  



# Allow user to select the Info to include in report.

class SelectKeysView(discord.ui.View):
	def __init__(self, poss_keys, def_keys, timeout=30) -> None:
		super().__init__(timeout=timeout)
		self.add_item(SelectKeysPicklist(poss_keys, def_keys))
		self.value = []

	async def on_timeout(self):
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

		try:
			await interaction.response.edit_message(embed=result_embed, content=None, view=None, delete_after=10)
		except Exception as e:
			print (f'{ansi.ltred}ERROR!{ansi.reset} Caught {type(e).__name__}: {e}  during edit_message(). Keys selected were {selected_keys}.')

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
		await send_rosterbot_error(self, context, f"**TIMEOUT:** Custom Info not selected. Will use default Info instead.", message=message, warning=True)
	else:	
		# Special processing for ISO Class
		if 'cls' in selected_keys:
			table_format['inc_class'] = True
			selected_keys.remove('cls')
		else:
			table_format['inc_class'] = False

		# Include the selected keys in the table_format
		table_format['inc_keys'] = selected_keys


