# This file contains the Strike Teams used for HTML file output.
#
# Move entries between strike teams and reorder players within strike teams. 
# Include lane dividers, i.e. "----" to indicate which players are in which lanes/clusters.
#
# Also, you can add entries in strike_teams dict and use them in output in msf2csv.py.
# These teams will be saved and included in cached alliance information.
#
# DELETE THIS FILE TO AUTO-GENERATE A NEW ONE WITH CURRENT ALLIANCE MEMBERS.

strike_teams = {}

# Used for Incursion Raid output.
strike_teams["incur"] = [
[### Strike team 1 ###]
	"FatCat",
	"Joey",
	"----",
	"sjhughes",
	"Ramalama",
	"Jutch",
	"----",
	"DrFett",
	"lanceb22",
	"Daner",
],
[### Strike team 2 ###]
	"Zen Master",
	"BigDiesel",
	"----",
	"EXfieldy",
	"HeadHunter2838",
	"mgmf",
	"----",
	"Kenny Powers",
	"keithchyiu",
	"FabiooBessa",
],
[### Strike team 3 ###]
	"Shammy",
	"RadicalEvil",
	"----",
	"Underdog",
	"Snicky",
	"Unclad",
	"----",
	"Flashie",
	"Incredibad",
	"Zairyuu",
]]

# Used for Gamma Raids and other output.
strike_teams["other"] = [
[### Strike team 1 ###]
	"sjhughes",
	"Joey",
	"Jutch",
	"Daner",
	"----",
	"Ramalama",
	"FatCat",
	"lanceb22",
	"DrFett",
],
[### Strike team 2 ###]
	"keithchyiu",
	"FabiooBessa",
	"Zen Master",
	"EXfieldy",
	"----",
	"HeadHunter2838",
	"Kenny Powers",
	"BigDiesel",
	"mgmf",
],
[### Strike team 3 ###]
	"Underdog",
	"Snicky",
	"Shammy",
	"RadicalEvil",
	"----",
	"Flashie",
	"Unclad",
	"Incredibad",
	"Zairyuu",
]]
