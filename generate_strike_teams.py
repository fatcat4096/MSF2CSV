
def generate_strike_teams(path, alliance_members):

	incur_strike_teams = []
	other_strike_teams = []

	new_file  = '# This file contains the Strike Teams used for HTML file output.\n'
	new_file += '# Move entries between strike teams and reorder players within strike teams.\n'
	new_file += '# Include lane dividers, i.e. "----" to indicate which players are in which lanes/clusters.\n'
	new_file += '#\n'
	new_file += '# DELETE THIS FILE TO AUTO-GENERATE A NEW ONE WITH CURRENT ALLIANCE MEMBERS\n'
	new_file += '\n'

	incur_def  = '# Used for Incursion Raid output.\n'
	incur_def += 'incur_strike_teams = [\n'

	other_def  = '\n\n# Used for Gamma Raids and other output.\n'
	other_def += 'other_strike_teams = [\n'

	print("Alliance members:",alliance_members)

	for num_entry in range(len(alliance_members)):

		# Starting a new Strike Team definition.
		if not (num_entry%8):
			incur_group = []
			other_group = []

			incur_def += '[### Strike Team %i ###]\n' % ((num_entry/8)+1)
			other_def += '[### Strike Team %i ###]\n' % ((num_entry/8)+1)

		# Incursion has dividers added.
		elif ((num_entry%8)%3)==2:
			incur_def += '\t"----",\n'
			incur_group.append("----")

		# Add the member into each.
		incur_def += '\t"%s",\n' % alliance_members[num_entry]
		other_def += '\t"%s",\n' % alliance_members[num_entry]
		
		incur_group.append(alliance_members[num_entry])
		other_group.append(alliance_members[num_entry])
		
		# Finished with the group.
		if (num_entry%8)==7 or num_entry==(len(alliance_members)-1):
			if num_entry==(len(alliance_members)-1):
				incur_def += ']]\n'
				other_def += ']]\n'
			else:
				incur_def += '],\n'
				other_def += '],\n'
			
			incur_strike_teams.append(incur_group)
			other_strike_teams.append(other_group)
	
	open(path+"strike_teams.py", 'w').write(new_file+incur_def+other_def)
	
	return  incur_strike_teams,other_strike_teams


	
