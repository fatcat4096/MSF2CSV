#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_local_files.py
Sources strike_teams and raids_and_lanes if they exist locally.  
Builds a new strike_teams.py if a valid file isn't present in the folder. 
Builds a new raids_and_lanes.py if a valid file isn't present in the folder.
"""

from file_io import *

# If file is invalid/deleted, generate a new one after alliance_info loaded.
try:	from strike_teams import *
except:	print ("Missing strike_teams.py...will be regenerated after alliance_members are known.")

# If raids_and_lanes is invalid, no longer auto-generate.
try:
	from raids_and_lanes import *
	add_formats_for_lanes(tables)
except:
	print ("Missing raids_and_lanes.py...need to download a new copy before continuing.")
	raise

import inspect
import importlib

# Create a new strike_teams.py if an outdated one exists.
def generate_strike_teams(alliance_info):

	global strike_teams

	new_teams = alliance_info.setdefault('strike_teams',{})

	for raid_type in ('chaos','spotlight'):

		if not new_teams.get(raid_type):

			# If not there, just put the member list in generic groups of 8.
			print (f"Valid {raid_type} strike_team definition not found. Creating default strike_team from member list.")
			
			# Get member_list and sort them.
			members = sorted(alliance_info['members'],key=str.lower)

			# Break it up into chunks and add the appropriate dividers.
			new_teams[raid_type] = [members[:8], members[8:16], members[16:]]
	
	# Create header
	new_file  = '''# This file contains the Strike Teams used for HTML file output.
#
# Move entries between strike teams and reorder players within strike teams.
#
# Also, you can add entries in strike_teams dict and use them in output in msf2csv.py.
# These teams will be saved and included in cached alliance information.
#
# DELETE THIS FILE TO AUTO-GENERATE A NEW ONE WITH CURRENT ALLIANCE MEMBERS.

strike_teams = {}
'''

	# Create each strike_team definition
	new_file += generate_strike_team('chaos',     new_teams['chaos'],    'Used for Chaos Raid output.')
	new_file += generate_strike_team('spotlight', new_teams['spotlight'], 'Used for Spotlight Raids and other output.')

	# Write it to disk.

	# If we're updating a local strike_teams.py, overwrite the existing module.
	if 'strike_temp' in globals():
		write_file(inspect.getfile(strike_temp), new_file)

		importlib.reload(strike_temp)
		strike_teams = strike_temp.strike_teams

	# Otherwise, just write it into the local path.
	else:
		write_file(get_local_path()+'strike_teams.py', new_file)
		strike_teams = new_teams



# Take the strike_team variable and create the text for the team definition in strike_teams.py
def generate_strike_team(type,strike_team,desc):

	team_def  = '\n# %s\n' % desc
	team_def += 'strike_teams["%s"] = [\n' % type
	
	for team_num in range(len(strike_team)): 
		team_def += '[### Strike team %i ###]\n' % (team_num+1)
		
		for member in strike_team[team_num]:
			team_def += '\t"%s",\n' % member
		
		team_def += ['],\n',']]\n'][team_num == len(strike_team)-1]

	return team_def
