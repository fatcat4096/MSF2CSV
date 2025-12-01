"""roster_refresh.py
Code to refresh roster and alliance information from MSF.gg.
"""

import re

from datetime   import datetime
from msf_shared import *


# Do the actual work to refresh rosters if explicitly requested or if cached_data was stale.
@timed
async def get_roster_refresh(
	self, context, AUTH, in_private, REFRESH_ONLY=True, MORE_SECTIONS=False
):
	# Pick up logging where we left off
	log_file = find_log_file()

	# Call for deferral ASAP. Still have API work to do before I can respond one way or another.
	try:	await context.interaction.response.defer(ephemeral=in_private)
	except:	pass

	#
	# DOWNLOAD ALLIANCE INFO USING AUTH
	#
	
	# Get current information
	username = msf2csv.get_username_api(AUTH)

	# If no username return, error message 
	if not username:
		failed_on = 'player'
	else:
		# Check to see if we've already filled alliance_info
		alliance_info = AUTH.pop('alliance_info', None)
	
		# If not yet filled, get base alliance info using API (no roster data yet)
		if not alliance_info:
			response, alliance_info = msf2csv.get_alliance_api(AUTH)

		# If not valid alliance_info, it's an error message
		failed_on = '' if type(alliance_info) is dict else alliance_info

	if failed_on:
		return await api_request_failed(self, context, response, failed_on)

	# We have an alliance_info, make a note of the alliance name
	alliance_name = alliance_info.get('name')

	#
	# CREATE AN EMBED FOR THE PROGRESS REPORT
	#
	
	progress = []
	message  = None
	
	status = msf2csv.remove_tags(alliance_name) + ('' if REFRESH_ONLY else ' is stale') + '\nRoster refresh **IN PROGRESS**...\n'
	embed  = await get_rosterbot_embed(self, context, description=status, color=build_color(0), inc_icon=False, inc_footer=False)
	
	# Make note of when we begin
	start_time = datetime.now()

	# Display this embed in case we're holding for an in-progress refresh
	if not REFRESH_ONLY:
		message = await send_message(context, embed=embed, ephemeral=in_private)

	# Make sure we are not already running a refresh for the same alliance
	REFRESH_REQUESTED   = ('refresh','refresh_only')[REFRESH_ONLY]
	REFRESH_IN_PROGRESS = await report_in_progress(alliance_name, REFRESH_REQUESTED, start_time)

	# If a refresh was already in progres...
	if REFRESH_IN_PROGRESS != start_time:
		
		# This is a duplicate request, bail.
		if REFRESH_ONLY:
			return await send_rosterbot_error(self, context, f'**/roster refresh** for **{msf2csv.remove_tags(alliance_name)}** already in progress.\nCommand cancelled.')

		# Update the embed to indicate refresh is complete -- get_roster_report() will update with new image.
		description  = f'The info **ABOVE** has been refreshed.\n'
		description += f'Other sections will be **BELOW**\n' if MORE_SECTIONS else ''
		description += f'{msf2csv.remove_tags(alliance_name)} updated\n'

		embed.description = description
		embed.color       = build_color(1)			# Green, data is fresh and command is complete.

		return message, embed
		
	#
	# ACTUALLY DO THE ROSTER REFRESH USING AUTH
	#

	# Find existing cached_data and merge it with our fresh alliance_info
	msf2csv.find_cached_and_merge(alliance_info, AUTH.get('same_alliance') and AUTH['alliance_name'])
	
	# Sort the members by TCP from highest to lowest.
	members_list = sorted(alliance_info['members'], key = lambda x: alliance_info['members'][x].get('tcp',0), reverse=True)

	# Just make note of which alliance we're refreshing:
	self.bot.logger.info (f'{ansi.under}{ansi.cyan}Refreshing: {ansi.bold}{alliance_name}{ansi.reset}')

	# Then update the messages as we iterate through it.
	step = 1
	for idx in range(0, len(members_list), step):

		# Process requests one at a time
		progress += await asyncio.get_event_loop().run_in_executor(None, partial(msf2csv.process_rosters, alliance_info, only_process=members_list[idx:idx+step], AUTH=AUTH, log_file=log_file, logger=self.bot.logger.info))

		embed.description = build_desc (status, progress) 
		embed.color       = build_color(idx/len(members_list))

		message = await send_message(context, message, embed, ephemeral=in_private)

	#
	# UPDATE HISTORY AND STRIKE TEAMS IF ANYTHING WAS UPDATED
	#

	status = ''.join([line[15:] for line in progress])
	if 'UPD' in status or 'NEW' in status:
	
		# Keep a copy of critical stats from today's run for historical analysis.
		msf2csv.update_history(alliance_info)

	# Remove and replace invalid entries or duplicates, give priority to the new entry.
	for strike_team in alliance_info.get('strike_teams',{}):
		msf2csv.fix_strike_teams(alliance_info['strike_teams'][strike_team], alliance_info)

	#
	# AFTER REFRESH, UPDATE DISCORD_ID AND ADMIN INFO IF NECESSARY
	#

	# Get a little closer to our work
	member_info = alliance_info['members'].setdefault(username,{})

	# If this is first time for this user, we're going to do some additional processing.
	FIRST_TIME = 'auth' not in member_info
	
	# Update with discord_id and login/AUTH credentials.
	if FIRST_TIME:
		discord_id   = AUTH.get('discord_id')
		discord_name = context.author.name if discord_id == context.author.id else (await self.bot.fetch_user(discord_id)).name

		member_info['discord'] = {'name':discord_name, 'id':discord_id}
		member_info['auth']    = True

		# If no 'admin' has been defined, set admin to this account. 
		# If first time leader has used /roster refresh, set 'admin' to leader.
		if 'admin' not in alliance_info or username == alliance_info['leader']:
			alliance_info['admin'] = {'name':discord_name, 'id':discord_id}
			self.bot.logger.info (f"Setting this user as admin: {ansi.ltblu}{discord_name} ({discord_id}{ansi.reset})")

	# Refresh the cached information in cached_members global.
	load_cached_members(alliance_info)

	# Fix/Update Strike Teams and is_stale data
	msf2csv.update_strike_teams(alliance_info)
	msf2csv.update_is_stale(alliance_info)

	# Write the updated (or new) cached_data file to disk
	msf2csv.write_cached_data(alliance_info, msf2csv.get_local_path()+'cached_data')

	# Check to see if Alliance Name has changed, and update database entries if it has
	await name_change_processing(self, context, AUTH, alliance_info)

	#
	# REFRESH COMPLETED, SEND FINAL STATUS
	#

	# Get a summary of the results 
	summary = msf2csv.roster_results(alliance_info, start_time, progress, self.bot.logger.info)

	# Prepare the final status message.
	if 'NO UPDATE' in summary[0]:
		status  = f'{msf2csv.remove_tags(alliance_name)}\n'
	else:
		status  = ('' if REFRESH_ONLY else 'The info **ABOVE** has been refreshed.\n') + ('Other sections will be **BELOW**\n' if MORE_SECTIONS else '')
		status += f'{msf2csv.remove_tags(alliance_name)} updated\n'
		if AUTH.get('show_old') != 2:
			status += f'Refresh results are **BELOW**:\n'

	# Update the embed
	embed.description = build_desc(status, [x for x in progress if ':' in x], summary, show_old=AUTH.get('show_old'))
	embed.color       = build_color(1)	# Green, data is fresh and command is complete.

	# Signal that refresh is complete
	await report_is_complete(alliance_name, 'refresh', start_time)

	# If only requesting /roster refresh, just send the final status indicating refresh is complete.
	if REFRESH_ONLY:
		return await send_message(context, message=message, embed=embed, ephemeral=in_private)

	# If roster refresh initiated by a stale report, just return the message and embed
	# get_roster_report() will rerun the report and update with new image.
	return message, embed



# Build up the description to include in Roster Refresh status.
def build_desc(desc, progress, summary=[], show_old=True):

	# Sort the progress into a cleaner order.

	NEW = [line for line in progress if 'NEW' in line[15:]]
	NEW = sorted(NEW, key=lambda x: x[25] + x[19:] + str(10**10-ord(x[0].lower())), reverse=True)

	UPD = [line for line in progress if 'UPD' in line[15:]]
	UPD = sorted(UPD, key=lambda x: str(int(10**10-{' ':1,'K':1000,'M':10**6}[x[25]]*float(x[19:25]))).zfill(11) + x[0].lower())

	OLD = [line for line in progress if 'OLD' in line[15:]]
	OLD = sorted(OLD, key=lambda x: chr(255-ord(x[25])) + x[19:] + str(10**10-ord(x[0].lower())), reverse=True)

	ERR = [line for line in progress if ':' not in line]

	# NEW Colors
	discord_green     = '\u001b[0;32m'
	discord_ltgrn     = '\u001b[1;32m'
	discord_reset     = '\u001b[0;0m'

	# UPD Colors
	discord_ltblu     = '\u001b[1;34m'
	discord_cyan      = '\u001b[0;36m'
	discord_red       = '\u001b[0;31m'

	# OLD Colors
	discord_yellow    = '\u001b[0;33m'
	discord_ltyel     = '\u001b[1;33m'

	# Final display? Let's add some color
	if summary and show_old != 2:
		NEW = [f'{line[:14]}{discord_ltgrn}{line[14:19]}{discord_green}{line[19:]}{discord_reset}' for line in NEW]
		UPD = [f'{line[:14]}{discord_ltblu}{line[14:19]}{discord_cyan if "+" in line[19:] else discord_red}{line[19:]}{discord_reset}' for line in UPD]
		if show_old:
			OLD = [f'{line[:14]}{discord_ltyel}{line[14:19]}{discord_yellow}{line[19:]}{discord_reset}' for line in OLD]
	
	# Combine all information, omitting OLD entries on the final summary
	progress = NEW + UPD + (OLD if show_old else []) + ERR

	# Then build the final description

	if progress and not (summary and show_old == 2):
		use_ansi = 'ansi\n' if summary else ''
		desc += f'```{use_ansi}' + '\n'.join(progress)+ '```'

	if summary:
		desc += '\n'.join(summary)
	
	return desc



#
# HERE'S WHERE ALL THE FINAL PROCESSING TAKES PLACE WHEN ALLIANCE NAME HAS CHANGED
#

async def name_change_processing(self, context, AUTH, alliance_info):
	
	# Pull out information about the Alliance Name
	ALLIANCE_NAME_OLD = AUTH['alliance_name']
	ALLIANCE_NAME_NEW = AUTH['alliance_name_curr']

	# Final AUTH processing. Needed if the Alliance Name needs to be updated
	if ALLIANCE_NAME_OLD != ALLIANCE_NAME_NEW:

		# Make a note of when we started...
		START_TIME = datetime.now()
	
		# Report what the explicit name change was
		self.bot.logger.info (f"{ansi.bold}Alliance changed from {ansi.ltcyan}{ALLIANCE_NAME_OLD}{ansi.white} to {ansi.ltcyan}{ALLIANCE_NAME_NEW}{ansi.reset}!")

		# If AUTH['same_alliance'], then alliance has simply changed name -- got a BUNCH of updates to make
		if AUTH['same_alliance']:

			# DEBUG FOR NOW, TAKE IT OUT LATER
			self.bot.logger.info (f"{ansi.bold}In the {ansi.cyan}SAME ALLIANCE{ansi.white} logic!{ansi.reset}")

			# Find all valid Discord IDs in the CURRENT alliance_info
			IDS_IN_ALLIANCE = {alliance_info['members'][x].get('discord',{}).get('id',0) for x in alliance_info['members']}

			# Find all Default Alliance entries that are using the OLD alliance_name
			ENTRIES_TO_UPDATE = sorted(await self.bot.database.get_discord_ids_from_defaults(ALLIANCE_NAME_OLD))
			if ENTRIES_TO_UPDATE:
				self.bot.logger.info (f'{ansi.bold}Changing Default Alliance from {ansi.ltcyan}{ALLIANCE_NAME_OLD}{ansi.white} to {ansi.ltcyan}{ALLIANCE_NAME_NEW}{ansi.reset}')

				# Let's update Default Alliance entries for channels/users referencing the old name
				for discord_id in ENTRIES_TO_UPDATE:

					# Is there a Auth ID saved for this user/channel?
					auth_id = await self.bot.database.get_default_auth_id(discord_id)

					# If this Auth ID is a Discord ID still in the Alliance, update
					if auth_id in IDS_IN_ALLIANCE:

						# Update alliance default and report results
						await update_default_alliance_name(self, ALLIANCE_NAME_NEW, discord_id)

			# Remove ourself and the undefined AUTH ID
			IDS_IN_ALLIANCE = IDS_IN_ALLIANCE.difference({0, context.author.id})
			if IDS_IN_ALLIANCE:
				self.bot.logger.info (f'Updating alliance name for other players with AUTHs:')

			# Need to update AUTHs for other Discord IDs still in the Alliance
			for discord_id in IDS_IN_ALLIANCE:

				# Pull the AUTH from the Database and if found, update with the new Alliance Name
				self.bot.logger.info (f'Looking for AUTH for Discord ID: {ansi.ltblu}{discord_id}{ansi.reset}')
				AUTH_TO_UPDATE = await self.bot.database.get_auth(discord_id, ALLIANCE_NAME_OLD)

				# Not found? Keep looking
				if not AUTH_TO_UPDATE:
					continue

				# Make the changes and report the results
				await self.bot.database.save_auth(AUTH_TO_UPDATE, ALLIANCE_NAME_NEW)
				await log_auth_row(self, discord_id, ALLIANCE_NAME_NEW, message='Alliance name updated')

			# Finally, rename the OLD cached_data-alliance_name.msf file to OLD_DATA-alliance_name.msf (verify isn't same file with diff caps)
			if ALLIANCE_NAME_NEW.lower() != ALLIANCE_NAME_OLD.lower():
				msf2csv.retire_cached_data(ALLIANCE_NAME_OLD)

		# If NOT AUTH['same_alliance'], the member has changed into ANOTHER Alliance
		else:
			# DEBUG FOR NOW, TAKE IT OUT LATER
			self.bot.logger.info (f"{ansi.bold}In the {ansi.cyan}DIFFERENT ALLIANCE{ansi.white} logic!{ansi.reset}")

			# If our own Default points at the OLD alliance name, update it to point to the NEW alliance instead
			if ALLIANCE_NAME_OLD == await self.bot.database.get_default_alliance_name(AUTH.get('discord_id')):

				# Update alliance default and report results
				self.bot.logger.info (f'{ansi.bold}Changing Default Alliance from {ansi.ltcyan}{ALLIANCE_NAME_OLD}{ansi.white} to {ansi.ltcyan}{ALLIANCE_NAME_NEW}{ansi.reset}')
				await update_default_alliance_name(self, ALLIANCE_NAME_NEW, AUTH.get('discord_id'))

			# Remove this AUTH from any users or channels it may have been shared with			
			message = f'{ansi.bold}AUTH changed alliances.{ansi.reset} Removing AUTH from Alliance Defaults on channels and users:'
			await remove_auth_id_from_defaults(self, ALLIANCE_NAME_OLD, AUTH.get('discord_id'), message)

		# Update our OWN final AUTH with the new Alliance Name
		await self.bot.database.save_auth(AUTH, ALLIANCE_NAME_NEW)

		# DEBUG FOR NOW, TAKE IT OUT LATER
		self.bot.logger.info (f"{ansi.bold}ALLIANCE NAME CHANGE -- COMPLETE! -- ELAPSED TIME: {ansi.yellow}>> {(datetime.now()-START_TIME).total_seconds()} seconds <<{ansi.reset}")
