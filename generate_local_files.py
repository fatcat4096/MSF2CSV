#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_local_files.py
Sources strike_teams and raids_and_lanes if they exist locally.  
Builds a new strike_teams.py if a valid file isn't present in the folder. 
Copies the existing raids_and_lanes.py into the local dir if not present.
"""

import os
import sys


# If frozen, allow local strike_teams.py to override packaged versions.
if getattr(sys, 'frozen', False):
	sys.path.insert(0,os.path.dirname(sys.executable))


# If file is invalid/deleted, generate a new one after alliance_info loaded.
try:
	from strike_teams import *
except:
	print ("Missing strike_teams.py...will be regenerated after alliance_members are known.")


# Create a local raids_and_lanes.py that users can edit if we are Frozen and one doesn't exist. 
from raids_and_lanes import *
if not os.path.exists('raids_and_lanes.py'):
	generate_raids_and_lanes()


# Create a new strike_teams.py if an outdated one exists.
def generate_strike_teams(strike_teams={}):
	
	# Create header
	new_file  = '''# This file contains the Strike Teams used for HTML file output.
#
# Move entries between strike teams and reorder players within strike teams.
# Include lane dividers, i.e. "----" to indicate which players are in which lanes/clusters.
#
# Also, you can add entries in strike_teams dict and use them in output in msf2csv.py.
# These teams will be saved and included in cached alliance information.
#
# DELETE THIS FILE TO AUTO-GENERATE A NEW ONE WITH CURRENT ALLIANCE MEMBERS.

strike_teams = {}
'''

	# Create each strike_team definition.
	new_file += generate_strike_team('incur',strike_teams['incur'],'Used for Incursion Raid output.')
	new_file += generate_strike_team('other',strike_teams['other'],'Used for Gamma Raids and other output.')

	# Write it to disk.
	open("strike_teams.py", 'w').write(new_file)


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


# Use the default lanes defined to generate another local copy of the file.
def generate_raids_and_lanes():

	# Create header
	new_file  = '''# This file contains the list of active formats to be used for output
# and the definitions of what to include (or filter out) of those files.
#
# Add or remove entries from tables['active'] to control which files are created.
#
# For each table format, you can specify the following arguments:
#
#	* NAME -- This is the label used in the tabs at the top.
#
#	* MIN_TIER and MIN_ISO -- These are filters use to filter out background noise.
#
#		The table output will only include Characters that have been built to at least 
#		this level by at least ONE of the alliance members. Set these for the minimum
#		required by the level of Incursion, Doom, or Gamma raid you are running.
#
#		Note: Character specfied in Meta will ALWAYS be included. Never filtered out.
#
#	* STRIKE_TEAMS -- If not specified, entire alliance member list will be used.
#
#	* KEYS -- Controls which columns are displayed for each member's characters.
#
#		Default is ['power','tier','iso'] if not specified.
#
#   * LANES -- This is a list of Lanes, each lane has a list of sections.
#
#		Each section can include a list of traits and list of meta characters.
#		Traits are ADDITIVE, so ['Xmen','Kree'] includes anyone that has EITHER trait.
#		Meta characters aren't subject to filters. And if Meta characters are specified
#		and the trait indicated doesn't exist, trait will simply be used as a label


# Active tables are the files which will be generated.
'''

	new_file += "tables = {'active': " + repr(tables['active']) + "}\n\n\n"

	# Iterate through each of the included tables.
	for raid_type in tables: 
		if raid_type == 'active':
			continue
		
		if raid_type == 'all':
			new_file += "# All Characters\n"
		else:
			new_file += "# Meta Heroes for use in %s\n" % tables[raid_type]['name']

		new_file += "tables['%s'] = { 'name': '%s',\n" % (raid_type, tables[raid_type]['name'])

		# Generic keys, if specified.
		for key in ['min_tier','min_iso','strike_teams','keys']:
			if key in tables[raid_type]:
				new_file += "\t\t\t\t\t'%s': %s,\n" % (key, repr(tables[raid_type][key]))

		# Finally, add the Lanes 
		if 'lanes' in tables[raid_type]:
			new_file += "\t\t\t\t\t'lanes':[ [\n"

			for lane in tables[raid_type]['lanes']:
				for section in lane:
					meta = ''
					if section.get('meta'):
						meta = ", 'meta': %s" % repr(section['meta'])
					new_file += "\t\t\t\t\t\t\t{'traits': %s%s},\n" % (repr(section['traits']), meta)
					
				if lane == tables[raid_type]['lanes'][-1]:
					new_file += "\t\t\t\t\t\t\t] ]\n"
				else:
					new_file += "\t\t\t\t\t\t\t],[ ### Lane %i ###\n" % (tables[raid_type]['lanes'].index(lane)+2)

		# After everything else, close up the raid.  
		new_file += "\t\t\t\t\t}\n\n"

	# Write it to disk.
	open("tables.py", 'w').write(new_file)
	






