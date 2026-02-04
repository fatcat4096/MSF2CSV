"""roster_report.py
Code to generate roster reports inside Discord.
"""

import discord
from discord.ext.commands import Context

from datetime import datetime, timezone, timedelta, date
from msf_shared import *
from lookup_alliance import lookup_alliance
from roster_refresh  import get_roster_refresh
from control_frame   import ControlFrame



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

	# See if we've already determined an alliance_name
	alliance_name = table_format.get('alliance_name')
	
	# Determine what alliances are available to choose from
	avail_alliances = [alliance_name] if alliance_name else await get_avail_alliances(self, context)
	
	# Figure out whether we are immediately prompting for information
	NEED_ALLI = len(avail_alliances) != 1			
	NEED_HIST = table_format.get('inc_hist') or table_format.get('inline_hist')
	HAVE_HIST = table_format.get('use_oldest')
	NEED_MEMB = table_format.get('select_members')
	NEED_KEYS = table_format.get('custom_keys')

	PROMPTING = NEED_ALLI or (NEED_HIST and not HAVE_HIST) or NEED_MEMB or NEED_KEYS
	REFRESH_ENABLED = not await refresh_disabled(self, context)

	# Make note of whether we are sending this in_private
	in_private = table_format.get('in_private')

	# Defer ASAP, just make sure we select Ephemeral correctly.
	try:	await context.interaction.response.defer(ephemeral=PROMPTING or in_private)
	except:	pass

	# If PROMPTING and we deferred early, need to consume the deferral before prompting
	if PROMPTING and table_format.pop('deferred', None):
		await context.send(content='_ _', delete_after=0)

	# Determine which, if any, alliance is valid for this combination of user, roles, and channel.
	alliance_name = alliance_name or await lookup_alliance(self, context, alliances_found=avail_alliances)

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

		# If we deferred early, need to consume the deferral before output
		if table_format.pop('deferred', None):
			await context.send(content='_ _', delete_after=0)

		return await send_rosterbot_error(self, context, f"**/roster {output_name}** for **{msf2csv.remove_tags(alliance_name)}** already in progress.\nCommand cancelled.")

	message = table_format.pop('message', None)
	view    = table_format.pop('view', None)
	embed   = None
	refresh = None

	# Just log the table_format contents. 
	table_logged = {key:val for key,val in table_format.items() if key not in ('profile','output_format')}
	self.bot.logger.info (f'{"rerun" if view else "table"}_format: {ansi.bold}{table_logged}{ansi.reset}')

	# If we Prompted for information and didn't defer interaction, add a message so there's not a long pause
	# while we grab reports or refresh the rosters.
	if PROMPTING:
		message = await context.send("One moment...", ephemeral=in_private)

	# How long has it been since Alliance Info has been updated?
	STALE_DATA = not msf2csv.fresh_enough(alliance_name)
	
	# Are we within the 24 hours after Sunday Reset / End of Season?
	SEASON_END = not (datetime.now(timezone.utc) + timedelta(hours=3)).weekday()

	# If a Roster Refresh is taking place, show image then refresh after complete
	REFRESH_IN_PROGRESS = await refresh_in_progress(alliance_name)

	# If STALE_DATA or within 24 hours after Sunday Reset, look for AUTH
	if STALE_DATA or SEASON_END or REFRESH_IN_PROGRESS:
	
		# Only look for AUTH if refresh is NOT disabled
		AUTH = REFRESH_ENABLED and await get_valid_auth(self, context, alliance_name, silent=True)

		# Has member list changed at all?
		DIFF_MEMBERS = AUTH and not AUTH['same_members']

		# If a valid AUTH is available and alliance info is out of date
		# (STALE DATA or diff members), generate a report and then refresh
		if AUTH and (STALE_DATA or DIFF_MEMBERS or REFRESH_IN_PROGRESS):

			# If stale data, starting a refresh
			if STALE_DATA: 
				self.bot.logger.info (f"{ansi.yellow}  STALE DATA:{ansi.reset} Past 24 hours; will force Refresh.")
			# Otherwise, it's SEASON_END and the members have changed.
			elif DIFF_MEMBERS:
				self.bot.logger.info (f"{ansi.yellow}  SEASON END:{ansi.reset} Found 'different members' in AUTH; will force Refresh.")

			REFRESH_FIRST = (await get_prefs(context)).get('refresh_first', False) and not REFRESH_IN_PROGRESS

			# If we're generating multiple images, only get the first image.
			if table_format.get('output_format') == 'image' and not table_format.get('only_section') and not REFRESH_FIRST:
				table_format['render_sections'] = True	

			# Generate the report
			report = [] if REFRESH_FIRST else await get_report(self, alliance_name, table_format)

			# If we deferred early, need to consume the deferral immediately before output
			if table_format.pop('deferred', None):
				await context.send(content='_ _', delete_after=0)

			# For automatic roster refresh, always just provide summary only
			AUTH['show_old'] = 2
			
			# If we don't have a report, but we should have generated one, report the issue? 
			if not report and not REFRESH_FIRST:
				error_msg = 'Problem with cached data. Refreshing roster info.'
				message   = await send_rosterbot_error(self, context, error_msg, message=message, ephemeral=in_private, delete_after=None)
				table_format.pop('render_sections', None)
			else:
				# Prepare our arguments
				content     = None if report else message.content if message else 'One moment...'
				attachments = report if report else []

				# Keep a reference to the original message
				message = await send_message(context, message, content=content, attachments=attachments, ephemeral=in_private)

			# Pass in appropriate values
			REFRESH_ONLY  = False
			MORE_SECTIONS = table_format.get('render_sections')

			# Next, request a refresh of the roster.
			refresh, embed = await get_roster_refresh(self, context, AUTH, in_private, REFRESH_ONLY, MORE_SECTIONS)

			# Update alliance_name with new name if changed during refresh
			alliance_name = AUTH['alliance_name']
			
			# Verify the refresh was succesful
			STALE_DATA = not msf2csv.fresh_enough(alliance_name)

	# If we're generating multiple images, render them in sections.
	if table_format.get('output_format') == 'image' and not table_format.get('only_section'):
		table_format['render_sections'] = True

		# Make sure indexes are reset
		table_format.pop('lane_idx', None)
		table_format.pop('section_idx', None)
		
		# Also, if num_per_image, re-do if generated image from stale data
		if table_format.get('num_per_image'):
			table_format['only_members'] += table_format.get('redo_if_stale',[])

	# If not STALE_DATA, this is the first time we've generated a report
	# If STALE_DATA, this is updating the original report after refresh
	report = await get_report(self, alliance_name, table_format)

	# If we deferred early, need to consume the deferral immediately before output
	if table_format.pop('deferred', None):
		await context.send(content='_ _', delete_after=0)

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

	# IF we refreshed, delete the refresh message, we will refresh the original message
	if refresh:
		await refresh.delete()

	# Only allow control frame for entries with only a single image
	if not table_format.get('render_sections'):
		
		# Find the Required Parameters, these will be the basis for our control frame
		req_params = [param for param in context.command.clean_params if context.command.clean_params[param].required]

		# If we have required params and they're all filled with OptionStrs, let's add a control frame
		if (req_params and all([type(context.kwargs[param]) == OptionStr for param in req_params])) or context.command.name in ('analysis'):

			# Is this a re-render request?
			if view:
				view.table_format = table_format
				view.initialize_menus()
			# Or do we need to create a new Control Frame?
			else:
				view = ControlFrame(context, table_format)

			# Remove the embed. Don't include the links section
			embed = None
			
	# Send the message with newly generated (or refreshed) reports
	message = await send_message(context, message=message, embed=embed, attachments=report if report else [], ephemeral=in_private, view=view)

	# Add the message to the view to allow timeout
	if view:
		view.message = message

	# If more than one file was returned, request and send the rest, four at a time
	while table_format.get('render_sections'):
		report = await get_report(self, alliance_name, table_format)

		# Something went wrong during segmented rendering. Abort
		if not report:	break

		await send_message(context, attachments=report, ephemeral=in_private)

	# Signal that we're done with this
	await report_is_complete(alliance_name, output_name, start_time)

	# Log the completion time
	self.bot.logger.info (f'Report Complete. Total time is {ansi.bold}>> {(datetime.now()-start_time).seconds}s <<{ansi.reset}')

	# If stale data and couldn't refresh, prompt to link allinace.
	if STALE_DATA and REFRESH_ENABLED:
		AUTH_URL = await get_auth_url(self, context)
		await context.send(f"Data is stale. No linked account.\n[**CLICK HERE**]({AUTH_URL}) to link and allow auto-refresh.", ephemeral=True, delete_after=30)



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
	
	report = await loop.run_in_executor(None, msf2csv.main, alliance_info, table_format, find_log_file())

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
			options=[discord.SelectOption(label = str(date)) for date in self.pare_dates(hist_list)],
		)


	# Reduce full list to something manageable by the Discord UI
	def pare_dates(self,hist_list):
		
		# Keep every day for a week, keep every other day after a week, keep one per week after two weeks, keep one per month after two months
		prev_month = None
		prev_week  = None
		prev_day   = None

		for key in sorted(hist_list):
			date_diff = (date.today()-key).days

			key_month = int(date_diff/30)
			key_week  = key.isocalendar().week
			key_day   = int(key.timetuple().tm_yday/2)
			
			if (date_diff > 60 and key_month == prev_month) or (date_diff > 14 and key_week == prev_week) or (date_diff > 7 and key_day == prev_day):
				hist_list.remove(key)

			prev_month = key_month
			prev_week  = key_week
			prev_day   = key_day
			
		# Return at most 25 entries
		return hist_list[:25]


	async def callback(self, interaction: discord.Interaction) -> None:
		hist_date = self.values[0]

		result_embed = discord.Embed(color=0x57F287)
		result_embed.description = f"Working with **{hist_date}**"

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

	# See if we've been passed a valid date
	selected_date = table_format.get('inc_hist') or table_format.get('inline_hist')

	# If no other dates, history cannot be used.
	if not hist_list:
		selected_date = None
	# Use a valid date if we found one
	elif type(selected_date) == date:
		pass
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

	# Include the list of dates in case we need it
	table_format.setdefault('profile',{})['hist_list'] = hist_list



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
		self.options	= [discord.SelectOption(label={'op':'OP','iso':'ISO'}.get(key,key.title()), description=poss_keys[key], value=key, default=key in def_keys) for key in poss_keys]

	async def callback(self, interaction: discord.Interaction) -> None:
		selected_keys = self.values

		formatted_keys = [{'op':'OP','iso':'ISO'}.get(x,x.title()) for x in selected_keys]

		result_embed = discord.Embed(color=0x57F287)
		result_embed.description = f"You selected keys: **{formatted_keys}**"

		try:
			await interaction.response.edit_message(embed=result_embed, content=None, view=None, delete_after=10)
		except Exception as e:
			print (f'{ansi.ltred}ERROR!{ansi.reset} Caught {type(e).__name__}: {e}  during edit_message(). Keys selected were {formatted_keys}.')

		self.view.value = selected_keys
		self.view.stop()



async def get_custom_keys(
	self, context: Context, table_format
) -> None:

	# Get the default keys for this output.
	output   = table_format.get('output')
	table    = msf2csv.tables.get(output,{})
	
	# Special handling for Roster Analysis
	if output == 'roster_analysis':
		poss_keys = {	'yel'   : 'Yellow Stars',
						'red'   : 'Red Stars / Diamonds',
						'lvl'   : 'Character Level',
						'iso'   : 'ISO Level',
						'tier'  : 'Gear Tier',
						'abil'  : 'Ability Levels',
						'op'    : 'Overpower Level'}
		default = ['yel', 'red', 'lvl', 'iso', 'tier', 'abil', 'op'] 
	else:
		poss_keys = {	'power' : 'Character Power',
						'iso'   : 'ISO Level',
						'lvl'   : 'Character Level',
						'tier'  : 'Gear Tier',
						'op'    : 'Overpower Level',
						'yel'   : 'Yellow Stars',
						'red'   : 'Red Stars / Diamonds',
						'abil'  : 'Ability Levels',
						'class' : 'ISO Class',
						'avail' : 'Include # Available',
						'rank'  : 'Include Rank'}
		default = ['power','tier','iso']

	def_keys = msf2csv.get_table_value(table_format, table, {}, key='inc_keys', default=default)[:]
	
	# Special handling for ISO Class, Rank, and Avail
	for key in ('class', 'avail', 'rank'):
		if key in poss_keys and msf2csv.get_table_value(table_format, table, {}, key=f'inc_{key}', default=False):
			def_keys.append(key)

	view = SelectKeysView(poss_keys, def_keys)
	message = await context.send("Which info should be included?", view=view, ephemeral=True)
	await view.wait()

	selected_keys = view.value
	
	if not selected_keys:
		await send_rosterbot_error(self, context, f"**TIMEOUT:** Custom Info not selected. Will use default Info instead.", message=message, warning=True)
	else:	
		# Special processing for ISO Class, Rank, and Avail
		table_format['inc_class'] = 'class' in selected_keys
		table_format['inc_avail'] = 'avail' in selected_keys
		table_format['inc_rank']  = 'rank'  in selected_keys

		# Include the selected keys in the table_format
		table_format['inc_keys'] = [x for x in selected_keys if x not in ('class','avail','rank')]


