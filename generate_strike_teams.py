# If file has been deleted, generate a default format instead.
try:
	from strike_teams import *
except:
	print ("Missing strike_teams.py...will be regenerated after alliance_members are known.")
	pass
	
	
def generate_strike_teams(alliance_members):

	strike_teams = {}
	
	incur_strike_teams = []
	other_strike_teams = []

	for num_entry in range(len(alliance_members)):

		# Starting a new Strike Team definition.
		if not (num_entry%8):
			incur_group = []
			other_group = []
		# Incursion has dividers added.
		elif ((num_entry%8)%3)==2:
			incur_group.append("----")

		# Add the member into each.
		incur_group.append(alliance_members[num_entry])
		other_group.append(alliance_members[num_entry])
		
		# Finished with the group.
		if (num_entry%8)==7 or num_entry==(len(alliance_members)-1):
			incur_strike_teams.append(incur_group)
			other_strike_teams.append(other_group)

	# All done, add these to the strike_teams dict to return.
	strike_teams['incur'] = incur_strike_teams
	strike_teams['other'] = other_strike_teams
	
	new_file  = '# This file contains the Strike Teams used for HTML file output.\n'
	new_file += '#\n'
	new_file += '# Move entries between strike teams and reorder players within strike teams. \n'
	new_file += '# Include lane dividers, i.e. "----" to indicate which players are in which lanes/clusters.\n'
	new_file += '#\n'
	new_file += '# Also, you can add entries in strike_teams dict and use them in output in msf2csv.py.\n'
	new_file += '# These teams will be saved and included in cached alliance information.\n'
	new_file += '#\n'
	new_file += '# DELETE THIS FILE TO AUTO-GENERATE A NEW ONE WITH CURRENT ALLIANCE MEMBERS.\n'
	new_file += '\nstrike_teams = {}\n\n'

	new_file += generate_strike_team('incur',incur_strike_teams,'Used for Incursion Raid output.')
	new_file += generate_strike_team('other',other_strike_teams,'Used for Gamma Raids and other output.')

	open("strike_teams.py", 'w').write(new_file)
	
	return strike_teams


def generate_strike_team(type,strike_team,desc):
	team_def  = '\n\n# %s\n' % desc
	team_def += 'strike_teams[%s] = [\n' % type
	
	for team_num in range(len(strike_team)): 
		team_def += '[### Strike team %i ###]\n' % (team_num+1)
		
		for member in strike_team[team_num]:
			team_def += '\t"%s",\n' % member
		
		team_def += ['],\n',']]\n'][team_num == len(strike_team)-1]

	return team_def