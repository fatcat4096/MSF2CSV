#!/usr/bin/env python3
# Encoding: UTF-8
"""html_shared.py
Routines used by one or more of the html generation routines in msf2csv.py.
"""

from log_utils import timed

import string

from html_cache import make_next_color_id
from gradients import *



# Just hide the messiness.
#@timed(level=3)
def get_tab_header(content):
	return '<table>\n<tr><td class="tlnk" style="width:100%;">'+content+'</td></tr>\n</table>'



#@timed
def extract_color(alliance_name):
	alt_color = ''

	check_for_color = ''.join(alliance_name.split()).lower()

	# If we have a color, clean it up and extract it.
	if '<color=' in check_for_color:
			color_name = check_for_color.split('<color=')[1].split('>')[0].replace('#','')

			# Is this a hex number or a named color?
			hex_or_named = ['','#'][all(char in string.hexdigits for char in color_name)]

			alt_color=' style="color:%s%s";' % (hex_or_named, color_name)

	return alt_color



# Translate value to a color from the Heat Map gradient.
def get_value_color(val_range, value, html_cache, stale_data, stat='power', under_min=False, hist_date=None, use_range=False, darken_amt=0):

	# Base case. Return 'hist' if 0.
	if not val_range or not value:
		return 'hist'
	
	# Even distribution of color
	elif use_range=='set' or hist_date:
		min_val = 1
		max_val = 1000

		# Remove zero from the set when calculating distribution.
		new_range = sorted(set([x for x in val_range if x]))

		# For historical data, there's always room to grow.
		if hist_date:
			new_range.append(new_range[-1]+1)

		# Base case, avoid div by zero error
		if len(new_range) == 1:
			value = 1000
		elif value not in new_range:
			value = -1
		else:
			value = 1+1000/(len(new_range)-1)*(new_range.index(value))

	# Weighted distribution, skews higher
	elif use_range == 'list':
		min_val = 0
		max_val = 1000
		new_range = sorted(val_range, reverse=True)
		if value not in new_range:
			value = -1
		else:
			value = 1000/len(new_range)*(len(new_range)-new_range.index(value))

	# Standard handling
	else:
		min_val = min(val_range)
		max_val = max(val_range)

		# Ignore min_val of 0.
		if not min_val:
			new_range = [x for x in val_range if x]
			if new_range:
				min_val = min(new_range)
	
	return get_value_color_ext(min_val, max_val, value, html_cache, stale_data, stat, under_min, hist_date, darken_amt)



def get_value_color_ext(min_val, max_val, value, html_cache, stale_data=False, stat='power', under_min=False, hist_date=None, darken_amt=0):
	
	# If we've specified an inverted range, flip the calculation on its head.
	if min_val > max_val:
		min_val, max_val = max_val, min_val

		# 0 Stays 0, max_val goes to 1, 1 goes to mex_value
		if value:
			value = (max_val - value) + 1

	# Special treatment for the '0' fields. 
	if not value:
		return 'hist'

	# Tweak gradients for Tier, ISO, Level, and Red/Yellow stars.

	# Force Historical Data to use generic handling
	if hist_date:
		mid_val = (((max_val-min_val)*0.5)+min_val)
		color = get_scaled_value(min_val, mid_val, max_val, value, hist_date)
	# ISO Coloring is special: green, blue, purple depending on ISO tier
	elif stat == 'iso':
		color = iso_color_scale[value-1]
	elif stat == 'tier':
		mid_val = max(0,max_val-3)
		color = get_scaled_value(0, mid_val, max_val, value, hist_date)
	elif stat == 'lvl':
		mid_val = max(0,max_val-10)
		color = get_scaled_value(0, mid_val, max_val, value, hist_date)
	#elif stat in ('op'):
	#	color = get_scaled_value(0, 9, 11, value, hist_date)
	elif stat in ('bas','spc','ult','pas'):
		mid_val = max(0,max_val-1)
		color = get_scaled_value(0, mid_val, max_val, value, hist_date)
	elif stat in ('yel'):
		color = get_scaled_value(0, 5, 7, value, hist_date)
	elif stat in ('red'):
		color = get_scaled_value(0, 6, 10, value, hist_date)
	elif stat == 'rank':
		color = get_scaled_value(1, 13, 25, (25-value), hist_date)
	elif stat == 'avail':
		color = get_scaled_value(0, 5, 15, value, hist_date)
	# Everything else, generic handling.
	else:
		mid_val = (((max_val-min_val)*0.5)+min_val)
		color = get_scaled_value(min_val, mid_val, max_val, value, hist_date)
	
	# Dim values slightly if under the minimum specified for the report.
	if under_min and not hist_date:
		color = darken(color)
	elif darken_amt:
		color = darken(color,darken_amt)

	# If data is more than a week old, make grayscale to indicate stale data.
	if stale_data:
		color = grayscale(color)

	# Cache this color away for class definitions later.
	return make_next_color_id(html_cache, color)



# Do the ugly calculations here.
def get_scaled_value(min_val, mid_val, max_val, value, hist_date=None):

	# If Hist Date, any growth is a positive. Start with bottom value as orange and go to top of range as green
	if hist_date:
		mid_val = min_val
		yellow_point = 0.2

	# Define midpoint once, in case we'd like to skew it.
	else:
		yellow_point = 0.5
	
	# If we're in the lower "half" of our range, calculate the spread from red to yellow
	if value < mid_val:
		scaled_value = ((value-min_val)/max(1,mid_val-min_val)) * yellow_point
	# Top "half" is yellow to green.
	else:
		scaled_value = ((value-mid_val)/max(1,max_val-mid_val)) * (1-yellow_point) + yellow_point 

	# Ensure the scaled_value is between 0% and 100%
	scaled_value = max(0, scaled_value)		# min of 0%
	scaled_value = min(1, scaled_value)		# max of 100%

	# Translate the scaled_value into a color from the color_scale list.
	max_colors   = len(color_scale)-1
	scaled_value = int(scaled_value * max_colors)
	
	return color_scale[scaled_value]



# Generate Labels for each section from either label info or trait names.
def get_section_label(section):
	
	# If a label specified, use it.
	if section.get('label'):
		return section.get('label','').replace('-<br>','').replace('<br>',' ')

	# Otherwise, just join the translated traits.
	return ', '.join([translate_name(trait) for trait in section['traits']]).replace('-<br>','').replace('<br>',' ')



# Quick and dirty translation to shorter or better names.
def translate_name(value):
	TRANSLATE_NAME = {	"City Hero": "City<br>Hero",
						"City Villain": "City<br>Villain",
						"Global Hero": "Global<br>Hero",
						"Global Villain": "Global<br>Villain",
						"Cosmic or Legendary": "Cosmic or<br>Legendary",
						"Legendary Non-Horseman": "Legendary<br>Non-Horse",
						"Legendary + Apoc": "Legendary<br>+ Apoc",
						"Avenger": "Avengers",
						"AForce": "A-Force",
						"AbsoluteAForce": "Absolute<br>A-Force",
						"AlphaFlight": "Alpha Flight",
						"AnniversaryElite": "Anniversary<br>Elite",
						"Asgard": "Asgardians",
						"Astonishing": "Astonishing<br>X-Men",
						"Astonishing X-Men": "Astonishing<br>X-Men",
						"BionicAvenger": "Bionic<br>Avengers",
						"Bionic Avengers": "Bionic<br>Avengers",
						"BlackOrder": "Black<br>Order",
						"Brotherhood": "B'Hood",
						"ChaosTeam": "Chaos Team",
						"DarkHunter": "Dark<br>Hunters",
						"Defender": "Defenders",
						"Eternal": "Eternals",
						"FantasticFour": "Fantastic<br>Four",
						"FantasticFourMCU": "Fantastic<br>Four (MCU)",
						"HeroesForHire": "H4H",
						"HellfireClub": "Hellfire<br>Club",
						"HiveMind": "Hive-Mind",
						"ImmortalXMen": "Immortal<br>X-Men",
						"InsidiousSix": "Insidious<br>Six",
						"InfinityWatch": "Infinity<br>Watch",
						"Infinity Watch": "Infinity<br>Watch",
						"Invader": "Invaders",
						"KnowhereHeist": "Knowhere<br>Heist",
						"MarvelMoms": "Marvel Moms",
						"MastersOfEvil": "Masters<br>Of Evil",
						"Masters Of Evil": "Masters<br>Of Evil",
						"MercsForMoney": "Mercs For<br>Money",
						"Mercs For Money": "Mercs For<br>Money",
						"MightyAvenger": "Mighty<br>Avengers",
						"MsfOriginal": "MSF Original",
						"MSFOriginal": "MSF Original",
						"NewAvenger": "New<br>Avengers",
						"New Avengers": "New<br>Avengers",
						"NewWarrior": "New<br>Warriors",
						"New Warriors": "New<br>Warriors",
						"OutOfTime": "Out of Time",
						"Pegasus": "PEGASUS",
						"PhoenixForce": "Phoenix<br>Force",
						"PoolPals": "Pool Pals",
						"PowerArmor": "Power Armor",
						"PymTech": "Pym Tech",
						"Ravager": "Ravagers",
						"SecretAvenger": "Secret<br>Avengers",
						"SecretDefender": "Secret<br>Defenders",
						"Secret Defenders": "Secret<br>Defenders",
						"SecretWarrior": "Secret<br>Warriors",
						"SinisterSix": "Sinister<br>Six",
						"Sinister Six": "Sinister<br>Six",
						"SpiderVerse": "Spiders",
						"SpiritoFVengeance": "Spirit oF<br>Vengeance",
						"SpiderSociety": "Spider<br>Society",
						"Spider Society": "Spider<br>Society",
						"Starjammer": "Starjammers",
						"SuperiorSix": "Superior<br>Six",
						"Symbiote": "Symbiotes",
						"TangledWeb": "Tangled<br>Web",
						"Uncanny": "Uncanny<br>X-Men",
						"UncannyAvenger": "Uncanny<br>Avengers",
						"Unlimited": "Unlimited<br>X-Men",
						"Unlimited X-Men": "Unlimited<br>X-Men",
						"WarDog": "War Dogs",
						"Wave1Avenger": "Wave 1<br>Avengers",
						"WeaponX": "Weapon X",
						"WebSlinger": "Web Slinger",
						"WebWarrior": "Web<br>Warriors",
						"XFactor": "X-Factor",
						"Xforce": "X-Force",
						"Xmen": "X-Men",
						"XTreme": "X-Treme X-Men",
						"X-Treme X-Men": "X-Treme<br>X-Men",
						"YoungAvenger": "Young<br>Avengers",
						"Young Avengers": "Young<br>Avengers",
						"A.I.M. Monstrosity":"A.I.M.<br>Monstrosity",
						"A.I.M. Researcher":"A.I.M.<br>Researcher",
						"Agatha Harkness":"Agatha<br>Harkness",
						"Black Panther (1MM)":"Black Panther<br>(1MM)",
						"Black Panther (Shuri)":"Black Panther<br>(Shuri)",
						"Captain America":"Captain<br>America",
						"Captain America (Sam)":"Capt. America<br>(Sam)",
						"Captain America (WWII)":"Capt. America<br>(WWII)",
						"Captain Britain":"Captain<br>Britain",
						"Cosmic Ghost Rider":"Cosmic<br>Ghost Rider",
						"Daimon Hellstrom":"Daimon<br>Hellstrom",
						"Doctor Octopus":"Doctor<br>Octopus",
						"Doctor Strange":"Doctor<br>Strange",
						"Doctor Voodoo":"Doctor<br>Voodoo",
						"Elsa Bloodstone":"Elsa<br>Bloodstone",
						"Emma Frost (X-Men)":"Emma Frost<br>(X-Men)",
						"Franklin Richards":"Franklin<br>Richards",
						"Ghost Rider (Robbie)":"Ghost Rider<br>(Robbie)",
						"Green Goblin (Classic)":"Green Goblin<br>(Classic)",
						"Hand Blademaster":"Hand<br>Blademaster",
						"Hand Sorceress":"Hand<br>Sorceress",
						"Howard The Duck":"Howard<br>The Duck",
						"Hydra Armored Guard":"Hydra<br>Arm Guard",
						"Hydra Grenadier":"Hydra<br>Grenadier",
						"Hydra Rifle Trooper":"Hydra<br>Rifle Trooper",
						"Hydra Scientist":"Hydra<br>Scientist",
						"Invisible Woman":"Invisible<br>Woman",
						"Invisible Woman (MCU)":"Invisible<br>Woman (MCU)",
						"Iron Man (Infinity War)":"Iron Man<br>(Infinity War)",
						"Iron Man (Zombie)":"Iron Man<br>(Zombie)",
						"Ironheart (MKII)": "Ironheart<br>(MKII)",
						"Juggernaut (Zombie)":"Juggernaut<br>(Zombie)",
						"Kang the Conqueror":"Kang<br>the Conqueror",
						"Korath the Pursuer":"Korath<br>the Pursuer",
						"Kraven the Hunter":"Kraven<br>the Hunter",
						"Kree Royal Guard":"Kree<br>Royal Guard",
						"Lady Deathstrike":"Lady<br>Deathstrike",
						"Madelyne Pryor":"Madelyne<br>Pryor",
						"Mercenary Lieutenant":"Mercenary<br>Lieutenant",
						"Mercenary Riot Guard":"Mercenary<br>Riot Guard",
						"Mercenary Sniper":"Mercenary<br>Sniper",
						"Mercenary Soldier":"Mercenary<br>Soldier",
						"Mister Fantastic":"Mister<br>Fantastic",
						"Mister Fantastic (MCU)":"Mister<br>Fantastic (MCU)",
						"Mister Negative":"Mister<br>Negative",
						"Mister Sinister":"Mister<br>Sinister",
						"Ms. Marvel (Classic)": "Ms. Marvel<br>(Classic)",
						"Ms. Marvel (Hard Light)": "Ms. Marvel<br>(Hard Light)",
						"Omega Red (Phoenix Force)":"Omega Red<br>(P. Force)",
						"Proxima Midnight":"Proxima<br>Midnight",
						"Phantom Rider":"Phantom<br>Rider",
						"Ravager Boomer":"Ravager<br>Boomer",
						"Ravager Bruiser":"Ravager<br>Bruiser",
						"Ravager Stitcher":"Ravager<br>Stitcher",
						"Rocket Raccoon":"Rocket<br>Raccoon",
						"Ronan the Accuser":"Ronan<br>the Accuser",
						"S.H.I.E.L.D. Assault":"S.H.I.E.L.D.<br>Assault",
						"S.H.I.E.L.D. Medic":"S.H.I.E.L.D.<br>Medic",
						"S.H.I.E.L.D. Operative":"S.H.I.E.L.D.<br>Operative",
						"S.H.I.E.L.D. Security":"S.H.I.E.L.D.<br>Security",
						"S.H.I.E.L.D. Trooper":"S.H.I.E.L.D.<br>Trooper",
						"Scarlet Witch (Zombie)":"Scarlet Witch<br>(Zombie)",
						"Scientist Supreme":"Scientist<br>Supreme",
						"Sebastian Shaw":"Sebastian<br>Shaw",
						"Spider-Man (Big Time)":"Spider-Man<br>(Big Time)",
						"Spider-Man (Miles)":"Spider-Man<br>(Miles)",
						"Spider-Man (Noir)":"Spider-Man<br>(Noir)",
						"Spider-Man (Pavitr)":"Spider-Man<br>(Pavitr)",
						"Spider-Man (Symbiote)":"Spider-Man<br>(Symbiote)",
						"Spider-Man 2099":"Spider-Man<br>2099",
						"Star-Lord (Annihilation)":"Star-Lord<br>(Annihilation)",
						"Star-Lord (T'Challa)":"Star-Lord<br>(T'Challa)",
						"Strange (Heartless)":"Strange<br>(Heartless)",
						"Superior Spider-Man":"Superior<br>Spider-Man",
						"Thor (Infinity War)":"Thor<br>(Infinity War)",
						"X23":"X-23",
						}
	return TRANSLATE_NAME.get(value,value)