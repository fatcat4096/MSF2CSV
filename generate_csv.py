#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_csv.py
Takes the processed alliance / roster data and generates original format .csv files.  
"""

from alliance_info import get_player_list, get_char_list

from copy import deepcopy


# Including this here for expedience.
def generate_csv(alliance_info):
	# Create a duplicate structure to 
	member_info = deepcopy(alliance_info.get('members',{}))
	for member in member_info:
		for char in member_info[member].get('processed_chars',{}):
			member_info[member]['processed_chars'][char]['red+dmd'] = member_info[member]['processed_chars'][char]['red'] + member_info[member]['processed_chars'][char]['dmd'] 
	
	# Write the basic output to a CSV in the local directory.
	keys1 = ['lvl','power','yel','red+dmd','tier']
	keys2 = ['iso','iso','iso','iso','iso','iso']
	
	csv_file = ['Name,AllianceName,CharacterId,Favorite,Level,Power,Stars,RedStar,GearLevel,Basic,Special,Ultimate,Passive,ISO Class,ISO Level,ISO Armor,ISO Damage,ISO Focus,ISO Health,ISO Resist']
	
	player_list = get_player_list(alliance_info)
	char_list   = get_char_list (alliance_info)
		
	alliance_name = alliance_info['name']
			
	for player_name in player_list:
		processed_chars = member_info[player_name].get('processed_chars',{})
		other_data      = member_info[player_name].get('other_data',{})

		# Only include entries for recruited characters.
		for char_name in char_list:
			if processed_chars.get(char_name,{}).get('lvl'):
				iso_class = ['','Fortifier','Healer','Skirmisher','Raider','Striker'][other_data.get(char_name,0)%6]
				favorite  = ['false','true'][int(other_data.get(char_name,0)/6)]
				
				bas,abil = divmod(processed_chars[char_name]['abil'],1000)
				spc,abil = divmod(abil,100)
				ult,pas  = divmod(abil,10)
				abil_stats = [str(abil) for abil in [bas, spc, ult, pas]]

				csv_file.append(','.join([player_name, alliance_name, char_name, favorite] + [str(processed_chars[char_name][key]) for key in keys1] + abil_stats + [iso_class] + [str(processed_chars[char_name][key]) for key in keys2]))

	return '\n'.join(csv_file)

