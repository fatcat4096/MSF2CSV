
import os
import sys

# If frozen, allow local strike_teams.py to override packaged versions.
if getattr(sys, 'frozen', False):
	sys.path.insert(0,os.path.dirname(sys.executable))
	
# If file has been deleted, generate a default format instead.
try:
	from strike_teams import *
except:
	print ("Missing strike_teams.py...will be regenerated after alliance_members are known.")


def generate_strike_teams(strike_teams={}):
	
	new_file  = '# This file contains the Strike Teams used for HTML file output.\n'
	new_file += '#\n'
	new_file += '# Move entries between strike teams and reorder players within strike teams. \n'
	new_file += '# Include lane dividers, i.e. "----" to indicate which players are in which lanes/clusters.\n'
	new_file += '#\n'
	new_file += '# Also, you can add entries in strike_teams dict and use them in output in msf2csv.py.\n'
	new_file += '# These teams will be saved and included in cached alliance information.\n'
	new_file += '#\n'
	new_file += '# DELETE THIS FILE TO AUTO-GENERATE A NEW ONE WITH CURRENT ALLIANCE MEMBERS.\n'
	new_file += '\nstrike_teams = {}\n'

	new_file += generate_strike_team('incur',strike_teams['incur'],'Used for Incursion Raid output.')
	new_file += generate_strike_team('other',strike_teams['other'],'Used for Gamma Raids and other output.')

	open("strike_teams.py", 'w').write(new_file)
	
	return strike_teams


def generate_strike_team(type,strike_team,desc):
	team_def  = '\n# %s\n' % desc
	team_def += 'strike_teams["%s"] = [\n' % type
	
	for team_num in range(len(strike_team)): 
		team_def += '[### Strike team %i ###]\n' % (team_num+1)
		
		for member in strike_team[team_num]:
			team_def += '\t"%s",\n' % member
		
		team_def += ['],\n',']]\n'][team_num == len(strike_team)-1]

	return team_def


def valid_strike_team(strike_team, alliance_info):
	return len(set(sum(strike_team,[])).intersection(alliance_info['members'])) > len(alliance_info['members'])/2