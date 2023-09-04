# This file contains the Strike Teams used for HTML file output.
#
# Move entries between strike teams and reorder players within strike teams. 
# Include lane dividers, i.e. "----" to indicate which players are in which lanes/clusters.
#
# Also, you can add entries in strike_teams dict and use them in output in msf2csv.py.
# These teams will be saved and included in cached alliance information.
#
# DELETE THIS FILE TO AUTO-GENERATE A NEW ONE WITH CURRENT ALLIANCE MEMBERS

strike_teams = {}

# Used for Incursion Raid output.
strike_teams['incur'] = [ 
[### Strike Team 1 ###]
	"Joey",
	"Jutch",
	"----",
	"FatCat",
	"sjhughes",
	"Ramalama",
	"----",
	"lanceb22",
	"Daner",
	"DrFett",
],
[### Strike Team 2 ###]
	"Shammy",
	"BigDiesel",
	"----",
	"EXfieldy",
	"mgmf", 
	"HeadHunter2838",
	"----",
	"Kenny Powers",
	"keithchyiu",
	"FabiooBessa",
],
[### Strike Team 3 ###]
	"Zen Master", 
	"----",
	"RadicalEvil", 
	"Underdog", 
	"Snicky", 
	"Zairyuu", 
	"----",
	"Unclad", 
	"Incredibad", 
	"Flashie",
]]

# Used for Gamma Raids and other output.
strike_teams['other'] = [
[### Strike Team 1 ###]
	"FatCat",
	"Joey",
	"Daner",
	"Jutch",
	"sjhughes",
	"Ramalama",
	"DrFett",
	"lanceb22",
],
[### Strike Team 2 ###]
	"Shammy",
	"HeadHunter2838",
	"keithchyiu",
	"mgmf",
	"BigDiesel",
	"Kenny Powers",
	"EXfieldy",
	"FabiooBessa",
],
[### Strike Team 3 ###]
	"Zen Master",
	"Incredibad",
	"Underdog",
	"Snicky",
	"Zairyuu",
	"Flashie",
	"Unclad",
	"RadicalEvil",
]]
