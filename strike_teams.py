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
	"Drankou",
	"Jutch",
	"Schvotz",
	"Hillboy3.0",
	"RadicalEvil",
	"Daner",
	"Shika",
	"Joey",
],
[### Strike team 2 ###]
	"BigDiesel",
	"Jay",
	"sjhughes",
	"Flashie",
	"FatCat",
	"EXfieldy",
	"silentwitness",
	"Shammy",
],
[### Strike team 3 ###]
	"Zen Master",
	"LUCKY_BASTARD",
	"Grizzera",
	"Incredibad",
	"Fenrir",
	"Bestiafa",
	"Unclad",
	"Zairyuu",
]]

# Used for Spotlight Raids and other output.
strike_teams["spotlight"] = [
[### Strike team 1 ###]
	"Hillboy3.0",
	"Daner",
	"Flashie",
	"Joey",
	"Schvotz",
	"Jutch",
	"Drankou",
	"Shika",
],
[### Strike team 2 ###]
	"RadicalEvil",
	"FatCat",
	"sjhughes",
	"EXfieldy",
	"Shammy",
	"Jay",
	"BigDiesel",
	"silentwitness",
],
[### Strike team 3 ###]
	"LUCKY_BASTARD",
	"Grizzera",
	"Fenrir",
	"Zen Master",
	"Bestiafa",
	"Unclad",
	"Incredibad",
	"Zairyuu",
]]
