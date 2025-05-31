"""roster_maps.py
Routines to generate Raid Maps for Chaos and Spotlight raids.
"""

import os

from msf_shared import msf2csv


def get_raid_map(alliance_info, raid_name):

	html_files = {}

	file_name = f"{raid_name}_map-{alliance_info.get('name')}.html"

	html_files[file_name] = generate_raid_map(alliance_info, raid_name)

	pathname = os.path.dirname(__file__) + os.sep + 'images' + os.sep

	# Write out the files to disk.
	html_files = msf2csv.write_file(pathname, html_files, print_path=False)
	html_files = msf2csv.html_to_images(html_files)

	return html_files



def generate_raid_map(alliance_info, raid_name):

	if 'chaos' in raid_name:
		RAID_TYPE = 'chaos'
	elif 'spotlight' in raid_name:
		RAID_TYPE = 'spotlight'

	# Map Strike Team definitions
	if 'nolanes' in raid_name:
		color_map = {	0:'blue',
						1:'blue',
						2:'blue',
						3:'blue'}
	elif 'lanes' in raid_name:
		color_map = {	0:'red',
						1:'orange',
						2:'yellow',
						3:'green',
						4:'ltblue',
						5:'blue',
						6:'purple',
						7:'magenta',}
	else:
		color_map = {	0:'red',
						1:'orange',
						2:'yellow',
						3:'gray',
						4:'green',
						5:'blue',
						6:'purple',
						7:'gray'}

	strike_teams = alliance_info.get('strike_teams',{}).get(RAID_TYPE,[])

	html_file = ''

	# Gotta start somewhere.
	html_file += add_css_header(table_name=RAID_TYPE.title()+' Raid')			# background_color='343734'
	html_file += ' <table class="map" style="background:#1a1a1a">\n'

	# Top border
	html_file += f'  <tr><td><br></td></tr>\n'

	# Start the Row and Left Shoulder
	html_file += f'  <tr>\n'
	html_file += f'   <td style="min-width:50px;"></td>\n'
	
	# Start the Strike Team Column -- build it as a nested table
	html_file += f'   <td style="min-width:400px;">\n'
	html_file += f'    <table>\n'

	# Title bar
	RAID_TITLE = {'chaos':'CHAOTIC<br>STORM', 'spotlight':'SPOTLIGHT<br>RAID'}
	html_file += f'     <tr><td colspan="5"><div class="{RAID_TYPE}_map_title">{RAID_TITLE[RAID_TYPE]}</div></td></tr>\n'

	# Do the Strike Teams on the right side. 
	for team_num in range(3):

		# Map Header line
		html_file += f'     <tr class="map_header"><td colspan="5"><br>STRIKE TEAM {team_num+1}</td></tr>\n'

		for idx in range(8):
			player_name = strike_teams[team_num][idx].replace('Commander','Cmdr') if len(strike_teams)>team_num and len(strike_teams[team_num])>idx else ''

			html_file += f'     <tr>\n'
			html_file += f'      <td style="width:50px;"</td>\n'
			html_file += f'      <td style="width:50px;"><div class="numbercircle {color_map.get(idx,"red")}">{idx+1}</div></td>\n'
			html_file += f'      <td style="width:25px;"</td>\n'
			html_file += f'      <td class="map_caption">{player_name}</td>\n'
			html_file += f'      <td style="width:25px;"</td>\n'
			html_file += f'     </tr>\n'

	# Finish the Strike Team Column
	html_file += f'    </table>\n'
	html_file += f'   </td>\n'

	# Gutter
	html_file += f'   <td style="min-width:50px;"></td>\n'
	
	# Map Column
	html_file += f'   <td class="map_body"><div class="{RAID_TYPE}_map_container"><img src="./src/raid.{raid_name}.png"></div></td>\n'

	# Right Shoulder and Finish the row
	html_file += f'   <td style="min-width:50px;"></td>\n'
	html_file += '  </tr>\n'

	# Bottom border
	html_file += f'  <tr><td><br></td></tr>\n'

	# Finish it off
	html_file += ' </table>\n</body>\n</html>\n'	

	return html_file



def add_css_header(table_name='Raid Maps', background_color='000000'):

	html_file = '''<!doctype html>
<html lang="en">
<head>
<title>'''+table_name+''' Info</title>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@200..700&family=Protest+Revolution&family=Protest+Strike&display=swap" rel="stylesheet">
<style>

.alt_style {
	background-color : rgba(100,100,100,0.5);
}

.map {
	background  : #1a1a1a;
	font-family : 'Oswald', sans-serif; 
	font-weight : 400;	
	color  : white;
	text-shadow : 2px 2px 2px black,
				-2px 2px 2px black,
				2px -2px 2px black,
				-2px -2px 2px black, 
				0px 2px 2px black,
				0px -2px 2px black, 
				2px 0px 2px black,
				-2px 0px 2px black;	
}

.spotlight_map_title {
	display     : inline-block;
	text-shadow : none;	
	height      : 200px; 
	font-family : 'Protest Strike', sans-serif; 
	font-size   : 100px;
	line-height : 95%;
    background-image: conic-gradient(from 0turn at 0% 0% in hsl, black, 100deg, DarkKhaki, 105deg, lightyellow, 115deg, white, 120deg, lightyellow, 125deg, darkkhaki, 135deg, black);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent; 
	-webkit-text-stroke: 2px white;
	transform   : scale(1, 1.2);
}
.chaos_map_title {
	display     : inline-block;
	height      : 200px; 
	font-family : 'Protest Revolution', sans-serif; 
	color : red;
	transform   : scale(1, 0.9);
	letter-spacing: -13px;
	line-height : 95%;
	text-shadow : 1px 1px 1px black,
				-1px 1px 1px black,
				1px -1px 1px black,
				-1px -1px 1px black, 
				0px 1px 1px black,
				0px -1px 1px black, 
				1px 0px 1px black,
				-1px 0px 1px black,
				 15px 15px 15px white,
				-15px 15px 15px white,
				15px -15px 15px white,
				-15px -15px 15px white, 
				0px 15px 15px white,
				0px -15px 15px white, 
				15px 0px 15px white,
				-15px 0px 15px white;	
	font-size   : 155px;
}
.map_body {
	width       : 1300px; 
	height      : auto; 
	background-position: center;
	background-repeat: no-repeat;
	background-size: cover;
	object-fit: cover;
}
.map_header {
	font-weight : 700;	
	%font-weight : 900;	
	font-size   : 48px;
	text-align: center;
	align-items: center;
	white-space: nowrap;
}
.map_caption {
	width       : 250px; 
	font-size   : 36px;
	font-weight   : 400;
	text-align: left;
	align-items: left;
}
.spotlight_map_container img{
	width: 1000px;
	height: auto;
	background-size: cover;
	background-repeat: no-repeat;
	background-position: center;
	margin:0;
	padding:0;
}
.chaos_map_container img{
	width: 1300px;
	height: auto;
	background-size: cover;
	background-repeat: no-repeat;
	background-position: center;
	margin:0;
	padding:0;
}
.numbercircle {
	border-radius: 50%;
	width: 36px;
	height: 36px;
	padding: 0px 8px 16px 8px;
	border: 2px solid #000;
	text-align: center;
	font-weight : 700;	
	font-size: 24pt;
	text-shadow : none;
}
.red {
	background: #f00;
}
.orange {
	background: #f90;
	color: black;
}
.yellow {
	background: #ff0;
	color: black;
}
.green {
	background: #0f0;
	color: black;
}
.ltblue {
	background: #4a86e8;
	color: black;
}
.blue {
	background: #4a86e8;
}
.ltblue {
	background: #0ff;
}
.purple {
	background: #90f;
}
.magenta {
	background: #f0f;
}
.gray {
	background: #c1c1c1;
	color: black;
}
'''

	# Finish off the Header.
	html_file += '</style>\n'
	html_file += '</head>\n'
	html_file += f'<body style="background: #{background_color}; text-align:center;">\n'

	return html_file

