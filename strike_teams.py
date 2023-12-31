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
	"mgmf",
	"Commander Zoster",
	"----",
	"sjhughes",
	"Bolivar",
	"Jutch",
	"----",
	"DrFett",
	"Joey",
	"Daner",
],
[### Strike team 2 ###]
	"HeadHunter2838",
	"Shammy",
	"----",
	"BigDiesel",
	"Flashie",
	"silentwitness",
	"----",
	"FatCat",
	"CrazyMunch",
	"FabiooBessa",
],
[### Strike team 3 ###]
	"Zen Master",
	"RadicalEvil",
	"----",
	"BIZARNAGE",
	"Snicky",
	"Unclad",
	"----",
	"EXfieldy",
	"Incredibad",
	"Zairyuu",
]]

# Used for Incursion 2 Raid output.
strike_teams["incur2"] = [
[### Strike team 1 ###]
	"mgmf",
	"Commander Zoster",
	"sjhughes",
	"Bolivar",
	"----",
	"Jutch",
	"DrFett",
	"Joey",
	"Daner",
],
[### Strike team 2 ###]
	"HeadHunter2838",
	"Shammy",
	"BigDiesel",
	"Flashie",
	"----",
	"silentwitness",
	"FatCat",
	"CrazyMunch",
	"FabiooBessa",
],
[### Strike team 3 ###]
	"Zen Master",
	"RadicalEvil",
	"BIZARNAGE",
	"Snicky",
	"----",
	"Unclad",
	"EXfieldy",
	"Incredibad",
	"Zairyuu",
]]

# Used for Gamma Raids and other output.
strike_teams["gamma"] = [
[### Strike team 1 ###]
	"sjhughes",
	"Commander Zoster",
	"Jutch",
	"Daner",
	"----",
	"Joey",
	"FatCat",
	"Bolivar",
	"DrFett",
],
[### Strike team 2 ###]
	"CrazyMunch",
	"FabiooBessa",
	"Shammy",
	"EXfieldy",
	"----",
	"HeadHunter2838",
	"silentwitness",
	"BigDiesel",
	"mgmf",
],
[### Strike team 3 ###]
	"BIZARNAGE",
	"Snicky",
	"Zen Master",
	"RadicalEvil",
	"----",
	"Flashie",
	"Unclad",
	"Incredibad",
	"Zairyuu",
]]
