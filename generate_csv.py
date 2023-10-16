#!/usr/bin/env python3
# Encoding: UTF-8
"""generate_csv.py
Takes the processed alliance / roster data and generates original format .csv files.  
"""


from alliance_info import get_player_list, get_char_list


# Including this here for expedience.
def generate_csv(alliance_info):
	# Write the basic output to a CSV in the local directory.
	keys1 = ['lvl','power','yel','red','tier']
	keys2 = ['iso','iso','iso','iso','iso','iso']
	
	csv_file = ['Name,AllianceName,CharacterId,Favorite,Level,Power,Stars,RedStar,GearLevel,Basic,Special,Ultimate,Passive,ISO Class,ISO Level,ISO Armor,ISO Damage,ISO Focus,ISO Health,ISO Resist']
	
	player_list = get_player_list(alliance_info)
	char_list   = get_char_list (alliance_info)
		
	alliance_name = alliance_info['name']
			
	for player_name in player_list:
		processed_chars = alliance_info['members'][player_name]['processed_chars']

		# Only include entries for recruited characters.
		for char_name in char_list:
			if processed_chars[char_name]['lvl'] != '0':
				iso_class = {'S':'Striker','K':'Skirmisher','H':'Healer','F':'Fortifier','R':'Raider'}[alliance_info['members'][player_name]['other_data']['cls']]
				favorite  = ['false','true'][alliance_info['members'][player_name]['other_data']['fav']]
				
				bas,abil = divmod(alliance_info['members'][player_name]['abil'],1000)
				spc,abil = divmod(abil,100)
				ult,pas  = divmod(abil,10)
				abil_stats = [str(abil) for abil in [bas, spc, ult, pas]]

				csv_file.append(','.join([player_name, alliance_name, char_name, favorite] + [str(processed_chars[char_name][key]) for key in keys1] + abil_stats + [iso_class] + [str(processed_chars[char_name][key]) for key in keys2]))

	return '\n'.join(csv_file)

