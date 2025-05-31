"""sigma_utils.py
Routines to generate posters and Openings info for the SIGMA cluster.
"""

import os
import re
import pickle 
import random

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from datetime import datetime
from msf_shared import msf2csv

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# The ID and range of a sample spreadsheet.
SHEET_ID = "10yr_ZHAK3vr-iGk0Wy-WlY1VNY1aZyqYJkxEj_5R52o"
DATA_RANGE = "MSF ASS Raw Data!A3:P42"


def main():
	html_files = {}
	
	html_files['./images/sigma_poster.html']   = generate_sigma_poster()
	html_files['./images/sigma_openings.html']   = generate_sigma_openings()

	output = 'html'		# or 'image'

	pathname = os.path.dirname(__file__) + os.sep

	# Write out the files to disk.
	html_files = msf2csv.write_file(pathname, html_files, print_path=(output=='html'))

	# If 'image' was requested, we need to convert the HTML files to PNG images.
	if output=='image':
		html_files = msf2csv.html_to_images(html_files)
	
	return html_files



def get_sigma_poster(alliance_name=''):

	pathname = os.path.dirname(__file__) + os.sep + 'images' + os.sep
	filename = f"poster{'-'+alliance_name if alliance_name else ''}"

	try:
		# Generate the HTMl.
		html_files = {filename+'.html':generate_sigma_poster(alliance_name)}
		html_files = msf2csv.write_file(pathname, html_files, print_path=False)

		# Convert the HTML to PNG.
		html_files = msf2csv.html_to_images(html_files)

	# Issue getting an image back? Just send the most recently generated.
	except Exception as exc:
		print(f"EXCEPTION RAISED. Sending cached {filename}.png.")
		html_files = [pathname + filename + '.png', exc]

	return html_files



def generate_sigma_poster(alliance_name=''):

	alliances = get_sheet_data()

	# Gotta start somewhere.
	html_file  = add_css_header(table_name='SIGMA Poster', background_color='000000')

	# Add a gradient
	html_file += '<table style="background-image: linear-gradient(#1a2666, #000000);">\n'

	# If a single alliance is specified, output only that Alliance.
	if alliance_name:
		# Sigma Branding.
		html_file += ' <tr>\n  <td style="width:400px;height:112px;" class="poster_header"></td>\n </tr>\n'

		# Include a locally defined poster if available.
		poster_path = r'./images/src/'
		
		poster_options = [x for x in os.listdir(poster_path) if x.lower().startswith(f'poster.{alliance_name.lower()}') and x.lower().endswith('.png')]
		
		if poster_options:
			poster_img = random.choice(poster_options).replace(' ','%20')
			html_file += f' <tr>\n  <td><div class="alliance_poster"><img src=src/{poster_img}></div></td>\n </tr>\n'

		# Add the alliance name. Ideally, we figure out how to get this to width of 1200px. 
		html_file += sigma_poster_alliances(alliances, [alliance_name]) 

	# Standard behavior. Produce entire poster.
	else:
		# Sigma Branding.
		html_file += ' <tr>\n  <td style="width:1600px;height:447px" class="poster_header" colspan="4"></td>\n </tr>\n'

		# Sort in order of Raid Difficulty / Completion, top to bottom.
		alliance_list = sorted(alliances, key=lambda x: alliances[x]['chaos_raid'].lower().replace('u','a')+f"{alliances[x]['chaos_comp'].zfill(4)}"+alliances[x]['spot_raid'].lower()+f"{alliances[x]['spot_comp'].zfill(4)}"+f"{10**10-int(alliances[x]['raid_season'] or 0)}", reverse=True)

		# Add the alliance names.
		html_file += sigma_poster_alliances(alliances, alliance_list)

	# Finish it off.
	html_file += '</table>\n</body>\n</html>\n'	
	
	return html_file



def sigma_poster_alliances(alliances, alliance_list):

	# Start the first row.
	html_file = ' <tr>\n'

	for idx, alliance_name in enumerate(alliance_list):

		RAID   = alliances[alliance_name]['chaos_raid']
		COMP   = alliances[alliance_name]['chaos_comp'].replace('%','')
		GAMMA  = alliances[alliance_name]['gamma'].replace('%','').replace(' ','-')
		LEAGUE = alliances[alliance_name]['league']
		ZONE   = alliances[alliance_name]['zone']
		BWDIFF = alliances[alliance_name]['bwdiff']

		alliance_logo = get_alliance_logo(alliance_name)

		html_file += f' <td style="height:140px;">\n'
		html_file += f' <table>\n'
		html_file += f'  <tr>\n'
		html_file += f'   <td class="left_side">{alliance_logo}</td>\n'
		html_file += f'   <td class="right_side">{RAID}-{COMP}<br>{GAMMA}<br>Z{ZONE} {LEAGUE}<br>BW Diff {BWDIFF}</td>\n'
		html_file += f'  </tr>\n'
		html_file += f' </table>\n'
		html_file += f' </td>\n'

		# Every three entries, end the row and start a new one. Except if this is the last entry.
		if idx % 4 == 3 and alliance_name != alliance_list[-1]:
			html_file += ' </tr>\n'
			html_file += ' <tr>\n'

	# And end the last one.
	html_file += ' </tr>\n'

	return html_file



def get_sigma_openings(only_needs=False, only_raid=''):

	pathname = os.path.dirname(__file__) + os.sep + 'images' + os.sep

	try:
		# Generate the HTMl.
		html_files = {'openings.html':generate_sigma_openings(only_needs, only_raid)}
		html_files = msf2csv.write_file(pathname, html_files, print_path=False)

		# Convert the HTML to PNG.
		html_files = msf2csv.html_to_images(html_files)

	# Issue getting an image back? Just send the most recently generated.
	except Exception as exc:
		print("EXCEPTION RAISED. Sending cached Openings.png.")
		html_files = [pathname + 'openings.png', exc]

	return html_files



def generate_sigma_openings(only_needs=False, only_raid=''):

	html_file = ''

	alliances = get_sheet_data()

	# Gotta start somewhere.
	html_file += add_css_header(table_name='SIGMA Openings')			# background_color='343734'
	html_file += '<table class="openings_background">\n'
	
	# Title bar.
	html_file += ' <tr>\n  <td class="openings_header" colspan=11></td>\n </tr>\n'

	# Column Headers
	html_file += ' <tr class="column_headers">\n'
	html_file += ' <td>Alliance</td>\n'
	html_file += ' <td>Need</td>\n'
	html_file += ' <td>Upgr</td>\n'
	html_file += ' <td>Main<br>Raid</td>\n'
	html_file += ' <td>Spot /<br>Greek</td>\n'
	html_file += ' <td>Raid<br>Season</td>\n'
	html_file += ' <td>War<br>League</td>\n'
	html_file += ' <td>War<br>Zone</td>\n'
	html_file += ' <td>War<br>Season</td>\n'
	html_file += ' <td>BW<br>Diff</td>\n'
	html_file += ' <td>Min<br>TCP</td>\n'
	html_file += ' </tr>\n'

	# Only include Alliances with at least one opening or upgrade.
	alliance_list = []
	for alliance,values in alliances.items():
		# Remove alliances explicitly marked inactive.
		if values.get('inactive'):
			continue
		# Filter out if ASS hasn't been updated in the last two weeks.
		elif (datetime.today()-datetime.strptime(values.get('last_update','1/1/1900'),'%m/%d/%Y')).days>14:
			continue
		# Filter on a specific raid
		elif only_raid not in f"{values.get('chaos_raid')} {values.get('chaos_comp')}%":
			continue
		# Bail if only_needs and no openings.
		elif only_needs and '0' == values.get('open'):
			continue
		# Only include entries with an opening or an upgrade.
		elif values.get('open') != '0' or values.get('upgr') != '0':
			alliance_list.append(alliance)

	if alliance_list:
		alliance_list = sorted(alliance_list, key=lambda x:	alliances[x]['chaos_raid'].lower().replace('u','a') + f"{alliances[x]['chaos_comp'].zfill(4)}" + 
															alliances[x]['open'] + alliances[x]['upgr'] + 
															f"{10**10-int(alliances[x]['raid_season'] or 0)}", reverse=True)

		alt_style = ''

		for alliance_name in alliance_list:

			# Just minor preprocessing for a few fields.
			alliance_logo = get_alliance_logo(alliance_name)

			# Put Raid and War Season targets into the right format if filled.
			raid_season = alliances[alliance_name]["raid_season"]
			war_season  = alliances[alliance_name]["war_season"]

			if raid_season:	raid_season = f'Top<br><span class="table_larger">{raid_season}</span>'
			if war_season: 	war_season  = f'Top<br><span class="table_larger">{war_season}</span>'

			# Inject a little color in for Percentage Completion.
			chaos_comp = alliances[alliance_name]['chaos_comp']
			chaos_color = msf2csv.get_scaled_value(0, 40, 100, int(chaos_comp))

			spot_comp = alliances[alliance_name]['spot_comp']
			spot_color = msf2csv.get_scaled_value(0, 40, 100, int(spot_comp))

			chaos_raid = f'{alliances[alliance_name]["chaos_raid"]}<br><span style="color:{chaos_color}">{chaos_comp}%</span>'
			spot_raid  = f'{alliances[alliance_name]["spot_raid"]}<br><span style="color:{spot_color}">{spot_comp}%</span>'

			war_league = alliances[alliance_name]["league"]
			if len(war_league.split())>1:
				war_league  = f'{war_league.split()[0]}<br><span class="table_larger">{war_league.split()[1]}</span>'

			# Start the row.
			html_file += f' <tr class="table_text {alt_style}">\n'
			html_file += f'  <td class="left_side">{alliance_logo}</td>'
			html_file += f'  <td class="table_larger">{alliances[alliance_name]["open"]}</td>'
			html_file += f'  <td class="table_larger">{alliances[alliance_name]["upgr"]}</td>'
			html_file += f'  <td>{chaos_raid}'
			html_file += f'  <td>{spot_raid}'
			html_file += f'  <td class="table_smaller">{raid_season}</td>'

			html_file += f'  <td class="table_smaller">{war_league}</td>'
			html_file += f'  <td class="table_larger">{alliances[alliance_name]["zone"]}</td>'
			html_file += f'  <td class="table_smaller">{war_season}</td>'
			html_file += f'  <td class="table_larger">{alliances[alliance_name]["bwdiff"]}</td>'
			html_file += f'  <td class="table_larger">{alliances[alliance_name]["min_tcp"]}</td>'
			html_file += f' </tr>'

			alt_style = ['','alt_style'][not alt_style]

	# Finish it off.
	html_file += '</table>\n</body>\n</html>\n'	

	return html_file



def get_alliance_list():
	alliance_list=[]

	file_path = './tokens/cached_alliances'

	if os.path.exists(file_path):
		alliance_list =  pickle.load(open(file_path,'rb'))

	return alliance_list
	
	

def get_sheet_data(alliances={}):

	values   = []
	alliances = {}

	creds = None
	# The file token.json stores the user's access and refresh tokens, and is
	# created automatically when the authorization flow completes for the first
	# time.
	pathname = os.path.dirname(__file__)+'/tokens'

	if os.path.exists(f'{pathname}/google_token.json'):
		creds = Credentials.from_authorized_user_file(f'{pathname}/google_token.json', SCOPES)
	# If there are no (valid) credentials available, let the user log in.

	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(
					f'{pathname}/google_credentials.json', SCOPES
			)
			creds = flow.run_local_server(port=0)
		# Save the credentials for the next run
		with open(f'{pathname}/google_token.json', 'w') as token:
			token.write(creds.to_json())

	try:
		service = build("sheets", "v4", credentials=creds)

		# Call the Sheets API
		sheet = service.spreadsheets()
		result = (
				sheet.values()
				.get(spreadsheetId=SHEET_ID, range=DATA_RANGE)
				.execute()
		)
		values = result.get("values", [])
		
		# Cache current read for future use if token expires or table unreadable.
		pickle.dump(values,open('./tokens/cached_values', 'wb'))

	except Exception as exc:
		print(f"{type(exc).__name__}: {exc}")

		# Just use cached values if token expires or table unreadable.
		values = pickle.load(open('./tokens/cached_values','rb'))
	
	# Load cached Spreadsheet information from last successful request.
	if not values:
		print("No data found.")
		return

	#print ('values:',values)
			
	for row in values:
		alliance_name = row[0].replace('SIGMA ','').upper()

		if len(row) < 12:
			#print ("Row is missing fields:", row)
			continue
	
		openings = 0
		current = row[1]
		if current:
			openings = str(int(current))
	
		# Do a little pre-processing on the raid info columns.
		chaos_raid, chaos_comp = row[3].rsplit(' ', 1)
		spot_raid,  spot_comp  = row[4].rsplit(' ', 1)

		min_tcp = row[8].lower().replace('m','')
		if min_tcp:
			min_tcp = f'{round(float(min_tcp))}M'

		# Take only the first number offered.
		chaos_comp = chaos_comp.replace('%',' ').replace('+',' ').replace('-',' ').split()
		spot_comp  = spot_comp .replace('%',' ').replace('+',' ').replace('-',' ').split()
		
		chaos_comp = chaos_comp[0] if chaos_comp else ''
		spot_comp  = spot_comp [0] if spot_comp  else ''
	
		# Preprocess the Raid and War season targets and take only the first number offered.
		raid_season = row[10].lower().replace('top ','').replace('+',' ').replace('-',' ').split()
		war_season  = row[11].lower().replace('top ','').replace('+',' ').replace('-',' ').split()
	
		raid_season = raid_season[0] if raid_season else ''
		war_season  = war_season [0] if war_season  else ''
	
		war_zone   = '' 
		war_league = ''

		inactive = len(row)>15 and row[15]
		
		# Double check for expected formatting.
		if row[6].count(' ') == 2:
			war_zone   = re.sub(r"\D", "", row[6].split(' ',1)[0])
			war_league = row[6].split(' ',1)[1]
	
		alliances[alliance_name] = {'open'       :openings, 
									'upgr'       :row[2], 
									'chaos_raid' :chaos_raid, 
									'chaos_comp' :chaos_comp, 
									'spot_raid'  :spot_raid, 
									'spot_comp'  :spot_comp, 
									'gamma'      :row[4], 
									'zone'       :war_zone, 
									'bwdiff'     :row[5], 
									'league'     :war_league,
									'last_update':row[7],
									'min_tcp'    :min_tcp,
									'raid_season':raid_season,
									'war_season' :war_season,
									'inactive'   :inactive}

	# Caching traits and char lists for Discord autocomplete.
	pickle.dump(sorted(alliances, key=str.lower), open('./tokens/cached_alliances', 'wb'))

	# Cache available Raid options.
	raid_dict = {}
	for value in alliances.values():
		if value.get('open') != '0' or value.get('upgr') != '0':
			raid_entry = raid_dict.setdefault(value.get('chaos_raid'),set())
			raid_entry.add(value.get('chaos_comp'))

	# After building the dict, use it to build a list.
	raid_list = []
	for raid_diff in sorted(raid_dict, key=lambda x: x.lower().replace('u','a'), reverse=True):
		raid_list.append(raid_diff)
		
		if len(raid_dict[raid_diff]) == 1:
			continue
		
		for raid_comp in sorted(raid_dict[raid_diff], key = lambda x: f"{x:>4}", reverse=True):
			raid_list.append(f'{raid_diff} {raid_comp}%')

	pickle.dump(raid_list, open('./tokens/cached_raid_list', 'wb'))
	
	return alliances



def get_raid_list():
	RAID_LIST = [] 

	if os.path.exists('./tokens/cached_raid_list'):
		RAID_LIST = pickle.load(open('./tokens/cached_raid_list','rb'))
	
	return RAID_LIST



def get_alliance_logo(alliance_name):

	translated = {	'AETHERIALS':'Aetherials',
					'BATTALION':'<span style="color:red">BAT</span>TAL<span style="color:blue">ION</span>',
					'BOO BOO KAI':'BBK',
					'CHILLED OUT RAIDERS':'Chilled Out Raiders',
					'CLAWS OF WOLVERINE':'CLAWS OF<br>WOLVERINE',
					'EVOKER':'Evoker',
					'GOLD':'SIGMA',
					'XI':'Xi',
					'HUNKA-HULKA BURNING FUDGE':'HHBF',
					'JUNIOR AVENGERS':'Junior<br>Avengers',
					'LEVIATHAN KNIGHTS':'LEVIATHAN KNIGHTS',
					'MISFITS FROM VALHALLA':'MISFITS',
					'MONARCHS':'MOnArchS',
					'THE WATCHERS':'The<br>Watchers',
				}.get(alliance_name,alliance_name)

	styles = {  'aetherials':['AETHERIALS'],
				'battalion':['BATTALION'],
				'bbk':['BBK'],
				'blueteam':['BLUE TEAM'],
				'bo616r':['BO616R'],
				'brotherhood':['BROTHERHOOD'],
				'chilled':['CHILLED OUT RAIDERS'],
				'claws':['CLAWS OF WOLVERINE'],
				'dbc':['DOTHRAKI BATTLE CATS'],					
				'dailybugle':['DAILY BUGLE DAMAGE CONTROL'],					
				'envy':['ENVY'],
				'elite':['ELITE'],
				'empire':['RAVAGER EMPIRE'],
				'evoker':['EVOKER'],
				'exiles':['EXILES'],
				'firstclass':['FIRST CLASS'],
				'forestorm':['FORESTORM'],
				'gatorstorm':['GATORSTORM'],
				'gold':['GOLD'],
				'legacy':['GOLD LEGACY'],
				'junior':['JUNIOR AVENGERS'],
				'kok':['KNIGHTS OF KNULL'],
				'homeys':['HOMEYS'],
				'hhbf':['HUNKA-HULKA BURNING FUDGE'],
				'illumi-naughty':['ILLUMI-NAUGHTY'],
				'immortal':['IMMORTAL BROTHERHOOD'],
				'infamous':['INFAMOUSLY STRANGE'],
				'infantry': ['107TH INFANTRY'],
				'lethal':['LETHAL ILLUMINATI'],
				'leviathan':['LEVIATHAN KNIGHTS'],
				'logan':["LOGAN'S HEROES"],
				'mayhem':['MAYHEM'],
				'misfits':['MISFITS'],
				'monarchs':['MONARCHS'],
				'quantum':['QUANTUM'],
				'ravengers':['RAVENGERS'],
				f'righthand{random.randint(1,2)}':['RED RIGHT HAND'],
				'symbiotes':['SYMBIOTES'],
				'syndicate':['SYNDICATE OF SUM PEOPLE'],
				f'tahiti{random.randint(1,2)}':['T.A.H.I.T.I.'],
				'uprising':['UPRISING'],
				'warheads':['WARHEADS'],
				'watchers':['THE WATCHERS'],
				'xi':['XI'],					
				'youth':['SCHOOL FOR GIFTED YOUTH'],					
				}
				
	add_style = []
	for style in styles:
		if translated in styles[style] or alliance_name in styles[style]:
			add_style.append(style)
	add_style = ' '.join(add_style)

	if 'aetherials' in add_style:
		translated = '<div class="container"><img src="./src/aetherials.png"></div>'

	if 'bbk' in add_style:
		translated = '<div class="container"><img src="./src/bbk.png"></div>'

	if 'bo616r' in add_style:
		translated = '<div class="container"><img src="./src/bo616r.png"></div>'

	if 'brotherhood' in add_style:
		translated = '<div class="container"><img src="./src/brotherhood.png"></div>'

	if 'chilled' in add_style:
		translated = '<div class="container"><img src="./src/chilled.png"></div>'

	if 'dbc' in add_style:
		translated = '<div class="container"><img src="./src/dbc.png"></div>'

	if 'dailybugle' in add_style:
		translated = '<div class="container"><img src="./src/daily.bugle.png"></div>'

	if 'empire' in add_style:
		translated = '<div class="container"><img src="./src/empire.png"></div>'

	if 'envy' in add_style:
		translated = '<div class="container"><img src="./src/envy.png"></div>'

	if 'evoker' in add_style:
		translated = '<div class="container"><img src="./src/evoker.png"></div>'

	if 'exiles' in add_style:
		translated = '<div class="container"><img src="./src/exiles.png"></div>'

	if 'forestorm' in add_style:
		translated = '<div class="container"><img src="./src/forestorm.png"></div>'

#	if 'firstclass' in add_style:
#		translated = '<div class="container"><img src="./src/firstclass.png"></div>'

	if 'gatorstorm' in add_style:
		translated = '<div class="container"><img src="./src/gatorstorm.png"></div>'

	if 'gold' in add_style:
		translated = '<div class="container"><img src="./src/gold.png"></div>'

	if 'hhbf' in add_style:
		translated = '<div class="container"><img src="./src/hhbf.png"></div>'

	if 'infamous' in add_style:
		translated = '<span class="infamous_1">INFAMOUSLY<br></span>STRANGE'

	if 'immortal' in add_style:
		translated = '<div class="immortal_1">IMMORTAL</div><div class="immortal_2">Brotherhood</div>'
		
	if 'infantry' in add_style:
		translated = '<div class="container"><img src="./src/infantry.png"></div>'

	if 'junior' in add_style:
		translated = '<div class="container"><img src="./src/junior.png"></div>'

	if 'kok' in add_style:
		translated = '<div class="container"><img src="./src/kok.png"></div>'

	if 'legacy' in add_style:
		translated = '<div class="container"><img src="./src/legacy.png"></div>'

	if 'lethal' in add_style:
		translated = '<div class="container"><img src="./src/lethal.png"></div>'
		
	if 'leviathan' in add_style:
		translated = '<div class="leviathan_1">LEVIATHAN</div><div class="leviathan_2">Knights</div>'
		
	if 'logan' in add_style:
		translated = '<div class="container"><img src="./src/logan.png"></div>'

	if 'quantum' in add_style:
		translated = '<div class="container"><img src="./src/Quantum.png"></div>'

	if 'ravengers' in add_style:
		translated = '<div class="container"><img src="./src/ravengers.png"></div>'

	if 'righthand1' in add_style:
		translated = '<div class="container"><img src="./src/righthand1.png"></div>'

	if 'righthand2' in add_style:
		translated = '<div class="container"><img src="./src/righthand2.png"></div>'

	if 'symbiotes' in add_style:
		translated = '<div class="container"><img src="./src/Symbiotes.png"></div>'

	if 'syndicate' in add_style:
		translated = '<div class="syndicate_1">SYNDICATE</div><br><div class="syndicate_2">of</div><br><div class="syndicate_3">SUM PEOPLE</div>'

	if 'tahiti1' in add_style:
		translated = '<div class="container"><img src="./src/tahiti1.png"></div>'

	if 'tahiti2' in add_style:
		translated = '<div class="container"><img src="./src/tahiti2.png"></div>'

	if 'warheads' in add_style:
		translated = '<div class="container"><img src="./src/warheads.png"></div>'

	if 'watchers' in add_style:
		translated = '<div class="container"><img src="./src/watchers.png"></div>'

	if 'youth' in add_style:
		translated = '<div class="container"><img src="./src/sgy.png"></div>'

	return f'<span class="{add_style}">{translated}</span>'



def add_css_header(table_name='SIGMA', background_color='000000'):

	html_file = '''<!doctype html>
<html lang="en">
<head>
<title>'''+table_name+''' Info</title>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Medula+One&family=Akronim&family=Audiowide&family=Black+Han+Sans&family=Protest+Revolution&family=Black+Han+Sans&family=Niconne&family=Oswald:wght@200..700&family=Ruslan+Display&family=Pirata+One&family=Lobster&family=Vollkorn:ital,wght@1,900&family=Sonsie+One&family=Denk+One&family=UnifrakturMaguntia&family=Romanesco&family=Racing+Sans+One&family=Protest+Guerrilla&family=Amarante&family=Sigmar+One&family=Voltaire&family=Mouse+Memoirs&family=Karantina:wght@300;400;700&family=Permanent+Marker&family=Protest+Strike&family=Ropa+Sans:ital@0;1&family=Poller+One&display&family=Fira+Sans+Condensed:wght@400;700;900&family=Trade+Winds&family=Rye&family=Fredericka+the+Great&family=Kaushan+Script&family=Cinzel+Decorative:wght@400;700;900&family=Fondamento:ital@0;1&family=Kolker+Brush&family=Anton+SC&family=Goldman:wght@400;700&family=Federant&family=Days+One&family=Gajraj+One&family=Beau+Rivage&family=Jockey+One&family=Outfit:wght@100..900&family=Palanquin+Dark:wght@400;500;600;700&family=Passion+One:wght@400;700;900&family=Nosifer&family=Splash&family=Imbue:opsz,wght@10..100,100..900&display=swap" rel="stylesheet">
<style>

.poster_header {
	background-image: url("./src/poster_header.png");
	height      : 700px; 
	width       : 1450px; 
	background-position: center;
	background-size: cover;
	object-fit: cover;
}

.openings_background {
	background-image: linear-gradient(#1a2666, #000000);
	%background-image: url("./src/openings_background.png");
	width       : 1600px; 
	background-position: center;
	background-size: cover;
}

.openings_header {
	background-image: url("./src/openings_header.png");
	height      : 307px; 
	width       : 1600px; 
	background-position: center;
	background-size: cover;
	object-fit: cover;
}

.column_headers {
	font-size   : 30pt;
	font-weight : 400;
	background  : #336FA0;
	color       : white;
	white-space : nowrap;
	text-shadow : 2px 2px 2px black,
				-2px 2px 2px black,
				2px -2px 2px black,
				-2px -2px 2px black, 
				0px 2px 2px black,
				0px -2px 2px black;
}

.table_text {
	font-family : "Fira Sans Condensed", sans-serif;
	font-weight : 700;
	font-style : normal;
	
	font-size   : 36pt;
	font-style  : normal;
	color       : white;
	text-shadow : 2px 2px 2px black,
                -2px 2px 2px black,
                2px -2px 2px black,
                -2px -2px 2px black, 
                0px 2px 2px black,
                0px -2px 2px black; 
}

.table_larger {
	font-size   : 48pt;
	line-height: 80%;
}

.table_smaller {
	font-size   : 24pt;
}

.alt_style {
	background-color : rgba(100,100,100,0.5);
}

.left_side {
	font-size   : 41pt;
	font-style  : normal;
	color       : Indigo;
	text-shadow : 3px 3px 3px white,
				-3px 3px 3px white,
				3px -3px 3px white,
				-3px -3px 3px white, 
				0px 3px 3px white,
				0px -3px 3px white, 
				3px 0px 3px white,
				-3px 0px 3px white;
	min-width   : 290px;
	max-width   : 290px;
	line-height : 100%;
}
.right_side {
	font-family : "Ropa Sans", sans-serif;
	font-size   : 22pt;
	font-style  : normal;
	color       : white;
	text-shadow : 2px 2px 2px black,
				-2px 2px 2px black,
				2px -2px 2px black,
				-2px -2px 2px black, 
				0px 2px 2px black,
				0px -2px 2px black, 
				2px 0px 2px black,
				-2px 0px 2px black;
	min-width   : 135px;
	%max-width   : 135px;
}
.container img{
	width: 260px;
	height: auto;
	background-size: cover;
	background-repeat: no-repeat;
	background-position: center;
	margin:0;
	padding:0;
}

.alliance_poster img{
	width: 400px;
	height: auto;
	background-size: cover;
	background-repeat: no-repeat;
	background-position: center;
	margin:0;
	padding:0;
}
.aetherials {
	font-family : "Romanesco", cursive;
	color : Khaki;
	font-size   : 75pt;
	display     : inline-block;
	vertical-align: bottom;
	text-shadow: 2px 2px 2px black,
				-2px 2px 2px black,
				2px -2px 2px black,
				-2px -2px 2px black, 
				0px 2px 2px black,
				0px -2px 2px black, 
				2px 0px 2px black,
				-2px 0px 2px black,
				7px 7px 7px white,
				-7px 7px 0.2em darkgray,
				7px -7px 0.2em darkgray,
				-7px -7px 0.2em darkgray, 
				0px 7px 0.2em darkgray,
				0px -7px 0.2em darkgray, 
				7px 0px 0.2em darkgray,
				-7px 0px 0.2em darkgray;  
	line-height : 100%;
}
.claws {
	color       : #fad400;
	font-size   : 44pt;
	font-family : "Protest Revolution", sans-serif;
	% font-weight: 700;  
	% -webkit-text-stroke: 2px black;
	display     : inline-block;
	% transform   : scale(1, 1.2);
	text-shadow: 2px 2px 2px black,
				-2px 2px 2px black,
				2px -2px 2px black,
				-2px -2px 2px black, 
				0px 2px 2px black,
				0px -2px 2px black, 
				2px 0px 2px black,
				-2px 0px 2px black,
				7px 7px 7px darkgray,
				-7px 7px 0.2em darkgray,
				7px -7px 0.2em darkgray,
				-7px -7px 0.2em darkgray, 
				0px 7px 0.2em darkgray,
				0px -7px 0.2em darkgray, 
				7px 0px 0.2em darkgray,
				-7px 0px 0.2em darkgray; 
}
.bbk {
	font-family : "Akronim", system-ui;
	font-size   : 85pt;
	color       : greenyellow;
	display     : inline-block;
	transform   : scale(1, 1);
	vertical-align: bottom;
	text-shadow : 2px 2px 2px black,
				-2px 2px 2px black,
				2px -2px 2px black,
				-2px -2px 2px black, 
				0px 2px 2px black,
				0px -2px 2px black, 
				2px 0px 2px black,
				-2px 0px 2px black,
				5px 5px 5px lightblue,
				-5px 5px 5px lightblue,
				5px -5px 5px lightblue,
				-5px -5px 5px lightblue, 
				0px 5px 5px lightblue,
				0px -5px 5px lightblue, 
				5px 0px 5px lightblue,
				-5px 0px 5px lightblue,
				8px 8px 8px white,
				-8px 8px 8px white,
				8px -8px 8px white,
				-8px -8px 8px white, 
				0px 8px 8px white,
				0px -8px 8px white, 
				8px 0px 8px white,
				-8px 0px 8px white;					
}
.blueteam {
	% font-family : "Audiowide", sans-serif;
	% font-family : "Gajraj One", sans-serif;
	% font-family : "Outfit", sans-serif;
	% font-family : "Palanquin Dark", sans-serif;
	font-family : "Passion One", sans-serif;
	font-weight: 700;

	font-optical-sizing: auto;
	% font-weight: 900;
	font-style: normal;
  
	font-size   : 68pt;
	color       : MediumBlue;
	display     : inline-block;
	transform   : scale(1, 0.9);
	% font-style: italic;
	line-height: 85%;
	% letter-spacing: -1px;
	% vertical-align: bottom;
	text-shadow : 3px 3px 3px LightCyan,
				-3px 3px 3px LightCyan,
				3px -3px 3px LightCyan,
				-3px -3px 3px LightCyan, 
				0px 3px 3px LightCyan,
				0px -3px 3px LightCyan, 
				3px 0px 3px LightCyan,
				-3px 0px 3px LightCyan;
}
.bo616r {
	font-family : "Audiowide", sans-serif;
	color : purple;
	font-size   : 50pt;
	display     : inline-block;
	vertical-align: bottom;
	text-shadow: 2px 2px 2px black,
				-2px 2px 2px black,
				2px -2px 2px black,
				-2px -2px 2px black, 
				0px 2px 2px black,
				0px -2px 2px black, 
				2px 0px 2px black,
				-2px 0px 2px black,
				7px 7px 7px white,
				-7px 7px 7px white,
				7px -7px 7px white,
				-7px -7px 7px white, 
				0px 7px 7px white,
				0px -7px 7px white, 
				7px 0px 7px white,
				-7px 0px 7px white;  
	line-height : 100%;
}
.brotherhood {
	font-family : "Mouse Memoirs", sans-serif;
	font-size   : 56pt;
	display     : inline-block;
	% transform   : scale(1, 1.2);
	color : #b81d11;
	-webkit-text-stroke: 2px #5F0700;
}
.chilled { 
	font-family : "Sonsie One", system-ui;
	font-size   : 33pt;
	color : #195E98;
	display     : inline-block;
	vertical-align: bottom;
	letter-spacing: -2px;
	line-height : 100%;
}
.dbc {
	color       : orangered;
	font-size   : 45pt;
	font-family : "Voltaire", sans-serif;
	font-weight: 700;
	display     : inline-block;
    line-height : 100%;
	text-shadow: 2px 2px 2px black,
				-2px 2px 2px black,
				2px -2px 2px black,
				-2px -2px 2px black, 
				0px 2px 2px black,
				0px -2px 2px black, 
				2px 0px 2px black,
				-2px 0px 2px black,
				5px 5px 5px white,
				-5px 5px 5px white,
				5px -5px 5px white,
				-5px -5px 5px white, 
				0px 5px 5px white,
				0px -5px 5px white, 
				5px 0px 5px white,
				-5px 0px 5px white,
				5px 5px 5px white,
				-5px 5px 5px white,
				5px -5px 5px white,
				-5px -5px 5px white, 
				0px 5px 5px white,
				0px -5px 5px white, 
				5px 0px 5px white,
				-5px 0px 5px white;  
}
.empire {
	color : royalblue;
	font-family: "Black Han Sans", sans-serif;
	font-size   : 50pt;
	display     : inline-block;
	vertical-align: bottom;
	line-height : 100%;
	letter-spacing: 4px;
	% -webkit-text-stroke: 4px #004200;
	text-shadow : 3px 3px 3px black,
				-3px 3px 3px black,
				3px -3px 3px black,
				-3px -3px 3px black, 
				0px 3px 3px black,
				0px -3px 3px black, 
				3px 0px 3px black,
				-3px 0px 3px black,

				8px 8px 8px white,
				-8px 8px 8px white,
				8px -8px 8px white,
				-8px -8px 8px white, 
				0px 8px 8px white,
				0px -8px 8px white, 
				8px 0px 8px white,
				-8px 0px 8px white;	
}
.empire_2 {
	color : lightskyblue;
	font-family: "Protest Revolution", sans-serif;
	font-size   : 55pt;
	display     : inline-block;
	vertical-align: bottom;
	line-height : 65%;
	letter-spacing: 0px;
	z-index: 5;
	position: relative;
	text-shadow : 2px 2px 2px black,
				-2px 2px 2px black,
				2px -2px 2px black,
				-2px -2px 2px black, 
				0px 2px 2px black,
				0px -2px 2px black, 
				2px 0px 2px black,
				-2px 0px 2px black,
				5px 5px 5px Thistle,
				-5px 5px 5px Thistle,
				5px -5px 5px Thistle,
				-5px -5px 5px Thistle, 
				0px 5px 5px Thistle,
				0px -5px 5px Thistle, 
				5px 0px 5px Thistle,
				-5px 0px 5px Thistle;	
}
.envy {
	color : darkgreen;
	font-family : "Protest Strike", sans-serif;
	font-size   : 75pt;
	display     : inline-block;
	vertical-align: bottom;
	-webkit-text-stroke: 4px #004200;
	text-shadow: 7px 7px 7px #BEFFBE,
				-7px 7px 7px #BEFFBE,
				7px -7px 7px #BEFFBE,
				-7px -7px 7px #BEFFBE, 
				0px 7px 7px #BEFFBE,
				0px -7px 7px #BEFFBE, 
				7px 0px 7px #BEFFBE,
				-7px 0px 7px #BEFFBE;  
}
.evoker { 
	font-family : "Kaushan Script", cursive;
	color       : #4B006E;
	font-size   : 65pt;
	display     : inline-block;
	transform   : scale(1, 1);
	vertical-align: bottom;	
	text-shadow : 3px 3px 3px black,
				-3px 3px 3px lightblue,
				3px -3px 3px orchid,
				-3px -3px 3px lightblue, 
				0px 3px 3px blue,
				0px -3px 3px blue, 
				3px 0px 3px black,
				-3px 0px 3px black,
				7px 7px 7px gold,
				-7px 7px 7px gold,
				7px -7px 7px gold,
				-7px -7px 7px gold, 
				0px 7px 7px gold,
				0px -7px 7px gold, 
				7px 0px 7px gold,
				-7px 0px 7px gold;
}
.firstclass { 
	font-family : "Goldman", serif;
	color       : palegoldenrod;
	font-size   : 40pt;
	display     : inline-block;
	transform   : scale(1, 1);
	vertical-align: bottom;	
	text-shadow : 3px 3px 3px black,
				-3px 3px 3px black,
				3px -3px 3px black,
				-3px -3px 3px black, 
				0px 3px 3px black,
				0px -3px 3px black, 
				3px 0px 3px black,
				-3px 0px 3px black,
				7px 7px 7px PaleTurquoise,
				-7px 7px 7px PaleTurquoise,
				7px -7px 7px PaleTurquoise,
				-7px -7px 7px PaleTurquoise, 
				0px 7px 7px PaleTurquoise,
				0px -7px 7px PaleTurquoise, 
				7px 0px 7px PaleTurquoise,
				-7px 0px 7px PaleTurquoise;
}
.forestorm {
	font-family : "Medula One", system-ui;
	font-size   : 66pt;
	background-color: #f3ec78;
	background-image: linear-gradient(
		10deg,
		hsl(118deg 100% 40%) 22%,
		hsl(114deg 54% 51%) 27%,
		hsl(109deg 44% 54%) 34%,
		hsl(102deg 34% 56%) 39%,
		hsl(89deg 23% 57%) 45%,
		hsl(54deg 14% 59%) 50%,
		hsl(6deg 18% 64%) 55%,
		hsl(338deg 31% 66%) 60%,
		hsl(328deg 46% 66%) 65%,
		hsl(322deg 61% 66%) 71%,
		hsl(319deg 75% 66%) 76%,
		hsl(316deg 88% 64%) 83%,
		hsl(314deg 100% 62%) 90%
	);
	-webkit-background-clip: text;
	-webkit-text-fill-color: transparent; 
	text-shadow : none;	
	-webkit-text-stroke: 1.5px white;
}
.gold {
	color       : gold;
	font-family : "Protest Strike", sans-serif;
	font-size   : 75pt;
	-webkit-text-stroke: 3px gray;
	display     : inline-block;
	vertical-align: bottom;
	text-shadow : 4px 4px 2px black,
				-4px 4px 2px black,
				4px -4px 2px black,
				-4px -4px 2px black, 
				0px 4px 2px black,
				0px -4px 2px black, 
				4px 0px 2px black,
				-4px 0px 2px black,
				9px 7px 9px white,
				-9px 7px 9px white,
				9px -7px 9px white,
				-9px -7px 9px white, 
				0px 9px 9px white,
				0px -9px 9px white, 
				9px 0px 9px white,
				-9px 0px 9px white;		
}
.hhbf_2 {
    color       : green;
	text-shadow : 3px 3px 3px lightgreen,
				-3px 3px 3px lightgreen,
				3px -3px 3px lightgreen,
				-3px -3px 3px lightgreen, 
				0px 3px 3px lightgreen,
				0px -3px 3px lightgreen, 
				3px 0px 3px lightgreen,
				-3px 0px 3px lightgreen; 
}
.hhbf {
	color       : Purple;
	font-family : "Sigmar One", sans-serif;
	font-size   : 24pt;
    line-height : 100%;
	letter-spacing: -4px;
	-webkit-text-stroke: 1px white;
	display     : inline-block;
	% transform   : scale(1, 1.8);
	text-shadow : 3px 3px 3px thistle,
				-3px 3px 3px thistle,
				3px -3px 3px thistle,
				-3px -3px 3px thistle, 
				0px 3px 3px thistle,
				0px -3px 3px thistle, 
				3px 0px 3px thistle,
				-3px 0px 3px thistle; 	
}
.homeys {
	font-size   : 55pt;
	letter-spacing: -2px;
    background-color: #f3ec78;
    background-image: linear-gradient(45deg, red, orange, yellow);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent; 
	text-shadow : none;	
	-webkit-text-stroke: 2px white;
	display     : inline-block;
	% transform   : scale(1, 1.2);	
}

.immortal_1 {
	position: relative;
	font-family : "Protest Revolution", serif;
	font-size   : 46pt;
	transform   : scale(1, 0.8);
	color: orange;
	-webkit-text-stroke: 1px red;

	z-index:15;
	text-shadow: 4px 4px 4px black;
	display     : inline-block;
	vertical-align: bottom;	
}

.immortal_2 {
	font-family : "Anton SC", serif;
	font-size   : 40pt;
    line-height : 60%;

    color       : Indigo;
	text-shadow: 2px 2px 2px MediumSlateBlue,
				-2px 2px 2px MediumSlateBlue,
				2px -2px 2px MediumSlateBlue,
				-2px -2px 2px MediumSlateBlue, 
				0px 2px 2px MediumSlateBlue,
				0px -2px 2px MediumSlateBlue, 
				2px 0px 2px MediumSlateBlue,
				-2px 0px 2px MediumSlateBlue,
				0px 0px 1em MediumSlateBlue,
				0px 0px 1em Navy,
				0px 0px 1em Navy,
				0px 0px 1em Navy;

	display     : inline-block;
	vertical-align: super;	
} 

.infamous {
	font-family : "Amarante", serif;
	font-size   : 51pt;
    line-height : 60%;
    color       : black;
	text-shadow: 2px 2px 2px red,
				-2px 2px 2px red,
				2px -2px 2px red,
				-2px -2px 2px red, 
				0px 2px 2px red,
				0px -2px 2px red, 
				2px 0px 2px red,
				-2px 0px 2px red,
				0px 0px 1em red,
				0px 0px 1em darkred,
				0px 0px 1em darkred,
				0px 0px 1em darkred;
	display     : inline-block;
	vertical-align: super;	
} 
.infamous_1 {
	position: relative;
	font-family : "Sigmar One", sans-serif;
	font-size   : 26pt;
	letter-spacing: -4px;
	z-index:15;
	color: white;
	text-shadow: 4px 4px 4px black;
	-webkit-text-stroke: 1.5px black;
	display     : inline-block;
	transform   : scale(1, 0.8);
	vertical-align: bottom;	
}
.infantry {
	color       : Olive;
	font-family : "Lobster", sans-serif;
	font-size   : 45pt;
	display     : inline-block;
	transform   : scale(1, 1.0);
	line-height : 90%;
	background-image: linear-gradient(45deg, LimeGreen 30%, DarkGreen 70%);
	-webkit-background-clip: text;
	-webkit-text-fill-color: transparent; 
	text-shadow : none;	
}
.junior {
	font-family : "Poller One", serif;
	font-size   : 39pt;
	line-height : 100%;
	transform   : scale(1, 1);
	letter-spacing: -2px;
	-webkit-text-stroke: 1px black;

	display     : inline-block;
	vertical-align: bottom;
	color       : gold;
	letter-spacing: -3px;
	text-shadow : 2px 2px 2px black,
				-2px 2px 2px black,
				2px -2px 2px black,
				-2px -2px 2px black, 
				0px 2px 2px black,
				0px -2px 2px black, 
				2px 0px 2px black,
				-2px 0px 2px black,
				4px 4px 4px blue,
				-4px 4px 4px blue,
				4px -4px 4px blue,
				-4px -4px 4px blue, 
				0px 4px 4px blue,
				0px -4px 4px blue, 
				4px 0px 4px blue,
				-4px 0px 4px blue,
				7px 7px 7px white,
				-7px 7px 7px white,
				7px -7px 7px white,
				-7px -7px 7px white, 
				0px 7px 7px white,
				0px -7px 7px white, 
				7px 0px 7px white,
				-7px 0px 7px white;					
}
.lethal_1 {
	position: relative;
	color       : purple;
	font-family : "Ruslan Display", sans-serif;
	font-size   : 45pt;
	line-height : 5%;
	display     : inline-block;
	-webkit-text-stroke: 2px black;
	% transform   : scale(1, 1.5);
	vertical-align: bottom;
}
.lethal_2 {
	position: relative;
	font-family : "Oswald", sans-serif;
	font-size   : 25pt;
	z-index: 5;
	color: darkred;
	text-shadow: 3px 3px 3px black,
				-3px 3px 3px black,
				3px -3px 3px black,
				-3px -3px 3px black, 
				0px 3px 3px black,
				0px -3px 3px black, 
				3px 0px 3px black,
				-3px 0px 3px black,
				3px 3px 3px black,
				-3px 3px 3px black,
				3px -3px 3px black,
				-3px -3px 3px black, 
				0px 3px 3px black,
				0px -3px 3px black, 
				3px 0px 3px black,
				-3px 0px 3px black,
				6px 6px 6px black;
	-webkit-text-stroke: 1px white;
	display     : inline-block;
	transform   : scale(1, 1);
	line-height : 150%;
	letter-spacing: 12px;
}

.leviathan_1 {
	font-family: "Imbue", serif;
	font-optical-sizing: auto;
	font-weight: 700;
	font-style: normal;
	position: relative;
	color       : purple;
	font-size   : 60pt;
	line-height : 5%;
	display     : inline-block;
	-webkit-text-stroke: 2px black;
	% transform   : scale(1, 1.5);
	vertical-align: bottom;
	text-shadow: 3px 3px 3px white,
				-3px 3px 3px white,
				3px -3px 3px white,
				-3px -3px 3px white, 
				0px 3px 3px white,
				0px -3px 3px white, 
				3px 0px 3px white,
				-3px 0px 3px white,
				3px 3px 3px white,
				-3px 3px 3px white,
				3px -3px 3px white,
				-3px -3px 3px white, 
				0px 3px 3px white,
				0px -3px 3px white, 
				3px 0px 3px white,
				-3px 0px 3px white,
				6px 6px 6px white;
}
.leviathan_2 {
	position: relative;
	font-family : "Fondamento", serif;
	font-size   : 40pt;
	z-index: 5;
	color: yellow;
	text-shadow: 3px 3px 3px black,
				-3px 3px 3px black,
				3px -3px 3px black,
				-3px -3px 3px black, 
				0px 3px 3px black,
				0px -3px 3px black, 
				3px 0px 3px black,
				-3px 0px 3px black,
				3px 3px 3px black,
				-3px 3px 3px black,
				3px -3px 3px black,
				-3px -3px 3px black, 
				0px 3px 3px black,
				0px -3px 3px black, 
				3px 0px 3px black,
				-3px 0px 3px black,
				6px 6px 6px black;
	-webkit-text-stroke: 1px white;
	display     : inline-block;
	transform   : scale(1, 1);
	line-height : 150%;
	letter-spacing: 10px;
}


.legacy_1 {
	color       : gold;
	font-size   : 50pt;
	-webkit-text-stroke: 3px gray;
	display     : inline-block;
	vertical-align: bottom;
	position: relative;
	line-height : 0%;
	letter-spacing: 3px;
	transform   : scale(1, 1);
	text-shadow : 4px 4px 2px black,
				-4px 4px 2px black,
				4px -4px 2px black,
				-4px -4px 2px black, 
				0px 4px 2px black,
				0px -4px 2px black, 
				4px 0px 2px black,
				-4px 0px 2px black,
				9px 7px 9px white,
				-9px 7px 9px white,
				9px -7px 9px white,
				-9px -7px 9px white, 
				0px 9px 9px white,
				0px -9px 9px white, 
				9px 0px 9px white,
				-9px 0px 9px white;		
}
.legacy_2 {
	position: relative;
	font-family : "Niconne", cursive;
	font-size   : 50pt;
	z-index: 5;
	color: red;
	text-shadow: 2px 2px 2px black,
				-2px 2px 2px black,
				2px -2px 2px black,
				-2px -2px 2px black, 
				0px 2px 2px black,
				0px -2px 2px black, 
				2px 0px 2px black,
				-2px 0px 2px black,
				5px 5px 5px white,
				-5px 5px 5px white,
				5px -5px 5px white,
				-5px -5px 5px white, 
				0px 5px 5px white,
				0px -5px 5px white, 
				5px 0px 5px white,
				-5px 0px 5px white,
				5px 5px 5px white,
				-5px 5px 5px white,
				5px -5px 5px white,
				-5px -5px 5px white, 
				0px 5px 5px white,
				0px -5px 5px white, 
				5px 0px 5px white,
				-5px 0px 5px white;
	-webkit-text-stroke: 1px red;
	display     : inline-block;
	transform   : scale(1, 1);
	line-height : 150%;
	letter-spacing: 2px;
}
.xi {
	font-family : "Kolker Brush", serif;
	font-weight : 400;
	font-size   : 90pt;
	color       : blue;
	-webkit-text-stroke: 2px blue;
	% transform   : scale(1, 1.3);
	% letter-spacing: -3px;
	display     : inline-block;
	vertical-align: bottom;
	text-shadow : 3px 3px 3px yellow,
				-3px 3px 3px yellow,
				3px -3px 3px yellow,
				-3px -3px 3px yellow, 
				0px 3px 3px yellow,
				0px -3px 3px yellow, 
				3px 0px 3px yellow,
				-3px 0px 3px yellow,
				7px 7px 7px gold,
				-7px 7px 7px gold,
				7px -7px 7px gold,
				-7px -7px 7px gold, 
				0px 7px 7px gold,
				0px -7px 7px gold, 
				7px 0px 7px gold,
				-7px 0px 7px gold;		
}
.monarchs {
	font-family : "Cinzel Decorative", serif;
	font-weight : 900;
	font-size   : 35pt;
	color       : rebeccapurple;
	transform   : scale(1, 1.3);
	letter-spacing: -3px;
	display     : inline-block;
	vertical-align: bottom;
	text-shadow : 1px 1px 1px yellow,
				-1px 1px 1px yellow,
				1px -1px 1px yellow,
				-1px -1px 1px yellow, 
				0px 1px 1px yellow,
				0px -1px 1px yellow, 
				1px 0px 1px yellow,
				-1px 0px 1px yellow,
				4px 4px 4px gold,
				-4px 4px 4px gold,
				4px -4px 4px gold,
				-4px -4px 4px gold, 
				0px 4px 4px gold,
				0px -4px 4px gold, 
				4px 0px 4px gold,
				-4px 0px 4px gold;		
}
.ravengers {
	display     : inline-block;
	% transform   : scale(1, 1.2);
	color       : indigo;
	font-family : "Pirata One", system-ui;
	font-size   : 48pt;
	-webkit-text-stroke: 2px lightblue;
	text-shadow : 2px 2px 2px black,
				-2px 2px 2px black,
				2px -2px 2px black,
				-2px -2px 2px black, 
				0px 2px 2px black,
				0px -2px 2px black, 
				2px 0px 2px black,
				-2px 0px 2px black,
				5px 5px 5px white,
				-5px 5px 5px white,
				5px -5px 5px white,
				-5px -5px 5px white, 
				0px 5px 5px white,
				0px -5px 5px white, 
				5px 0px 5px white,
				-5px 0px 5px white;
}
.righthand1 {
	color       : black;
	font-family : "Trade Winds", system-ui;
	% font-family : "Rye", serif;
	font-size   : 32pt;
	display     : inline-block;
	% transform   : scale(1, 1.3);
	-webkit-text-stroke: 1px white;
	text-shadow : 2px 2px 2px black,
				-2px 2px 2px black,
				2px -2px 2px black,
				-2px -2px 2px black, 
				0px 2px 2px black,
				0px -2px 2px black, 
				2px 0px 2px black,
				-2px 0px 2px black,
				6px 6px 0.4em red,
				0px 3px 0.4em red,
				3px 0px 0.4em red,
				0px 6px 0.4em red,
				6px 0px 0.4em red;
	line-height : 115%;		
}
.righthand2 {
	color       : white;
	font-family : "Fredericka the Great", serif;
	%font-family : "Trade Winds", system-ui;
	% font-family : "Rye", serif;
	font-size   : 32pt;
	display     : inline-block;
	% transform   : scale(1, 1.3);
	text-shadow : 2px 2px 2px black,
				-2px 2px 2px black,
				2px -2px 2px black,
				-2px -2px 2px black, 
				0px 2px 2px black,
				0px -2px 2px black, 
				2px 0px 2px black,
				-2px 0px 2px black,
				4px 4px 0.4em red,
				-4px 4px 0.4em red,
				4px -4px 0.4em red,
				-4px -4px 0.4em red, 
				0px 4px 0.4em red,
				0px -4px 0.4em red, 
				4px 0px 0.4em red,
				-4px 0px 0.4em red;
	line-height : 110%;		
}

.syndicate_1 {
	font-family : "Jockey One";	
	font-size   : 42pt;
	line-height : 20%;
	position    : relative;
	display     : inline-block;
	vertical-align: bottom;	
	color       : Red;
	-webkit-text-stroke: 1px Black;
}
.syndicate_3 {
	font-family : "Jockey One";	
	font-size   : 42pt;
	line-height : 0%;
	position    : relative;
	display     : inline-block;
	vertical-align: top;	
	color       : Red;
	-webkit-text-stroke: 1px Black;
}
.syndicate_2 {
	font-family : "Beau Rivage", cursive;	
	font-size   : 40pt;
	color       : black;
	letter-spacing: 0px;
	line-height : 80%;
	text-shadow : 2px 2px 2px White,
				-2px 2px 2px White,
				2px -2px 2px White,
				-2px -2px 2px White, 
				0px 2px 2px White,
				0px -2px 2px White, 
				2px 0px 2px White,
				-2px 0px 2px White,
				 5px 5px 5px Black,
				-5px 5px 5px Black,
				5px -5px 5px Black,
				-5px -5px 5px Black, 
				0px 5px 5px Black,
				0px -5px 5px Black, 
				5px 0px 5px Black,
				-5px 0px 5px Black;	
	position    : relative;
	z-index     :15;
	display     : inline-block;
	vertical-align: top;	
}


.tahiti {
 	display     : inline-block;
	% transform   : scale(1, 1.2);
    background-color: #f3ec78;
    background-image: linear-gradient(90deg, black 0%, darkgray 20%, gray 30%, orange 40%, yellow 50%, orange 60%, gray 70%, darkgray 80%, black 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent; 
	text-shadow : none;	
	-webkit-text-stroke: 2px white;
	font-family : "Protest Strike", sans-serif;
	font-size   : 59pt;
	letter-spacing: -5px;
}
.warheads {
	font-family : "Protest Guerrilla", sans-serif;	
	font-size   : 44pt;
	display     : inline-block;
	% transform   : scale(1, 1.5);
    background-image: radial-gradient(ellipse 50% 200% at center bottom, #F9FEDA 10%, yellow 20%, red 50%, #F32E2E 70%, black 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent; 
	-webkit-text-stroke: 1.5px white;
	text-shadow : none;	
}
.watchers {
	font-family : "UnifrakturMaguntia", cursive;	
	font-size   : 55pt;
	color       : Red;
	-webkit-text-stroke: 2px black;
	letter-spacing: -4px;
}
.youth {
	font-family : "Racing Sans One", sans-serif;	
	font-size   : 32pt;
	color       : Orange;
	% -webkit-text-stroke: 2px black;
	display     : inline-block;
	line-height : 100%;
	letter-spacing: 0px;
	text-shadow : 3px 3px 3px black,
				-3px 3px 3px black,
				3px -3px 3px black,
				-3px -3px 3px black, 
				0px 3px 3px black,
				0px -3px 3px black, 
				3px 0px 3px black,
				-3px 0px 3px black,
				7px 7px 7px white,
				-7px 7px 7px white,
				7px -7px 7px white,
				-7px -7px 7px white, 
				0px 7px 7px white,
				0px -7px 7px white, 
				7px 0px 7px white,
				-7px 0px 7px white;
}
.youth_2 {
	font-family : "Niconne", cursive;	
	font-size   : 45pt;
	color       : Red;
	-webkit-text-stroke: 2px darkred;
	letter-spacing: 0px;
	line-height : 60%;
	text-shadow : 5px 5px 5px LightYellow,
				-5px 5px 5px LightYellow,
				5px -5px 5px LightYellow,
				-5px -5px 5px LightYellow, 
				0px 5px 5px LightYellow,
				0px -5px 5px LightYellow, 
				5px 0px 5px LightYellow,
				-5px 0px 5px LightYellow;	
}
.dark {
  text-shadow : 3px 3px 3px black,
				-3px 3px 3px black,
				3px -3px 3px black,
				-3px -3px 3px black, 
				0px 3px 3px black,
				0px -3px 3px black, 
				3px 0px 3px black,
				-3px 0px 3px black;
}
.bright {
  text-shadow : 5px 5px 5px white,
				-5px 5px 5px white,
				5px -5px 5px white,
				-5px -5px 5px white, 
				0px 5px 5px white,
				0px -5px 5px white, 
				5px 0px 5px white,
				-5px 0px 5px white;
}

'''

	# Finish off the Header.
	html_file += '</style>\n'
	html_file += '</head>\n'
	html_file += f'<body style="background: #{background_color}; font-family : \'Protest Strike\', sans-serif; text-align:center;">\n'

	return html_file


if __name__ == "__main__":
	main()
