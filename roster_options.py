"""roster_options.py
Picklists and enumerations for use in the /roster report menus.
Also routines to parse the input into valid table_format entries.
"""

from enum import Enum
from discord.app_commands import Choice
from msf_shared import msf2csv, get_choices, timed



# Extract names of Traits from the Table definitions to create Enum definitions.
def get_traits(table,lane_num=0, all_sections=True):

	# Grab the appropriate lane
	lane = table['lanes'][lane_num]

	# Include All Sections? 
	ALL_SECTIONS = ['All Sections'] if all_sections else []

	# Extract the trait definitions from this lane
	trait_list = ALL_SECTIONS + [msf2csv.get_section_label(section) for section in lane]

	# Load those traits up into a dict to be used for an Enum definition
	return {key:trait_list.index(key)+(not all_sections) for key in trait_list}



# Enum definitions used for Discord Picklists in slash commands.
SECT_ANNI      = get_traits(msf2csv.tables['anni'])
SECT_SPOTLIGHT = get_traits(msf2csv.tables['spotlight'])
SECT_THUNDER   = get_traits(msf2csv.tables['thunderstrike'])
SECT_ALL_CHARS = get_traits(msf2csv.tables['all_chars'], all_sections=False)
SECT_PROFX     = get_traits(msf2csv.tables['profx'])
SECT_BLUE      = get_traits(msf2csv.tables['blue'])
SECT_DD8       = get_traits(msf2csv.tables['dd8'])
SECT_DD6       = get_traits(msf2csv.tables['dd6'])
SECT_DD5       = get_traits(msf2csv.tables['dd5'])
SECT_DD7       = get_traits(msf2csv.tables['dd7'])
SECT_TEAMS     = get_traits(msf2csv.tables['teams'])

CHOICES_ANNI      = get_choices(SECT_ANNI)
CHOICES_SPOTLIGHT = get_choices(SECT_SPOTLIGHT)
CHOICES_THUNDER   = get_choices(SECT_THUNDER)
CHOICES_ALL_CHARS = get_choices(SECT_ALL_CHARS)
CHOICES_PROFX     = get_choices(SECT_PROFX)
CHOICES_BLUE      = get_choices(SECT_BLUE)
CHOICES_DD8       = get_choices(SECT_DD8)
CHOICES_DD7       = get_choices(SECT_DD7)
CHOICES_DD6       = get_choices(SECT_DD6)
CHOICES_DD5       = get_choices(SECT_DD5)
CHOICES_TEAMS     = get_choices(SECT_TEAMS)

# Battleworld lists for autocomplete.
SECT_ZONE    = {f'Zone {x+1}':x+1 for x in range(4)}
SECT_MISSION = {'All Sections':0} | {f'Mission {x+1}':x+1 for x in range(6)}

CHOICES_ZONE     = get_choices(SECT_ZONE)
CHOICES_MISSION  = get_choices(SECT_MISSION)

# Build lists for other autocompletes
FORMATS = {msf2csv.tables[format]['name']:format for format in sorted(msf2csv.tables)}

BY_CHAR_LIST  = list(msf2csv.get_cached('char_list'))
BY_TRAIT_LIST = {msf2csv.translate_name(trait).replace('<br>',' '):trait for trait in sorted(['Non-Mythic','Non-Legendary','Non-Minion']+list(msf2csv.get_cached('trait_list')))}

CHOICES_FORMATS  = get_choices(FORMATS)
CHOICES_BY_CHAR  = get_choices(BY_CHAR_LIST)
CHOICES_BY_TRAIT = get_choices(BY_TRAIT_LIST)



# Update table_format with the only_lane flags
def process_lane(table_format, lane):
	
	# Extract the value if not an int
	if isinstance(lane, Choice) or isinstance(lane, Enum):
		lane = lane.value
	
	if lane:
		table_format['only_lane'] = lane



# Update table_format with the only_section flags
def process_section(table_format, section):
	
	# Extract the value if not an int
	if isinstance(section, Choice) or isinstance(section, Enum):
		section = section.value
	
	if section:
		table_format['only_section'] = section



ANY_OR_ALL = {
	'ALL of these traits': 'all',
	'ANY of these traits': 'any',
	}

COLORS = {
	'Balanced':'set',
	'Original':'',
	}

DEFAULTS = {
	'Save Defaults':1,
	'Reset Defaults':2
	}

MAP_TYPE = {
	'Annihilation Omega':'anni_omega', 
	'Annihilation Omega (No Lanes)':'anni_omega-nolanes', 
	'Annihilation Normal':'anni_normal-lanes', 
	'Annihilation Normal (No Lanes)':'anni_normal-nolanes', 
	'Spotlight':'spotlight', 
	'Spotlight (No Lanes)':'spotlight-nolanes',
	'Thunderstrike':'thunderstrike-lanes', 
	}

CHOICES_ANY_ALL      = get_choices(ANY_OR_ALL)
CHOICES_COLORS       = get_choices(COLORS)
CHOICES_DEFAULTS     = get_choices(DEFAULTS)
CHOICES_MAP_TYPE     = get_choices(MAP_TYPE)



ANNI_DIFF = {f'Diff {x}':x for x in range(1,11)} 
SPOT_DIFF = {'Normal':0, 'Diff 1':1, 'Diff 2':2}
THUN_DIFF = {'Normal':0, 'Thunderstruck':1}

CHOICES_ANNI_DIFF    = get_choices(ANNI_DIFF)
CHOICES_SPOT_DIFF    = get_choices(SPOT_DIFF)
CHOICES_THUN_DIFF    = get_choices(THUN_DIFF)

# Set min_iso appropriately based on difficulty
def process_difficulty(table_format, difficulty):

	# Annihilation uses one lookup table
	if difficulty is not None and table_format.get('output') == 'anni':

		# Apply Lane overlays based on difficulty
		CHAMPIONS  = ['Brawn', 'Moon Girl', 'Ms. Marvel', 'Nova (Sam Alexander)', 'Spider-Man (Miles)']
		TBOLTS     = ['Ghost', 'Hyperion', 'Songbird', 'Taskmaster', 'Victoria Hand']

		label = {
				1 : {x:'No<br>Restrictions' for x in range(1,7)},
				2 : {x:'No<br>Restrictions' for x in range(1,7)},
				3 : {x:'' for x in range(1,7)},
				4 : {x:'' for x in range(1,7)},
				5 : {x:'' for x in range(1,7)},
				6 : {x:'' for x in range(1,7)},
				7 : {x:'' for x in range(1,7)},
				8 : {6:'Bio<br>(Champions<br>or T-Bolts)'},
				9 : {6:'Bio<br>(Champions<br>or T-Bolts)'},
				10: {x:None for x in range(1,7)},
			}.get(difficulty, {})				

		traits     =  {x:['All'] for x in (1,2)}.get(difficulty)	
		max_others =  {x:10 for x in range(1,8)}.get(difficulty)				
		meta       =  {x:[] for x in range(1,8)}.get(difficulty)				
		meta_last  = ({x:[] for x in range(1,8)} | {x:CHAMPIONS+TBOLTS for x in (8,9)}).get(difficulty)

		table_format['lane_overlay'] = [{'label':label.get(1), 'traits':traits, 'max_others':max_others, 'meta':meta},
										{'label':label.get(2), 'traits':traits, 'max_others':max_others, 'meta':meta},
										{'label':label.get(3), 'traits':traits, 'max_others':max_others, 'meta':meta},
										{'label':label.get(4), 'traits':traits, 'max_others':max_others, 'meta':meta},
										{'label':label.get(5), 'traits':traits, 'max_others':max_others, 'meta':meta},
										{'label':label.get(6), 'traits':traits, 'max_others':max_others, 'meta':meta_last}]		

		# Finally, also set min_iso based on difficulty
		min_iso = {
			1:0,
			2:1,
			3:3,
			4:5,
			5:8,
			6:10,
			7:11,
			}.get(difficulty, 13)
		table_format['min_iso'] = min_iso

	# Thunderstrike Raid is all or nothing
	elif difficulty is not None and table_format.get('output') == 'thunderstrike':
		table_format['min_tier'] = {0:1}.get(difficulty, 20)

	# Only other option is Spotlight
	elif difficulty is not None:
		table_format['min_iso'] = {0:0, 1:12}.get(difficulty, 13)



WHICH_MEM =  {
	'Split: None'        :12,
	'Split: Left/Right'  :13,
	'Split: Strike Teams':14,
	'Only Strike Team 1' :3,
	'Only Strike Team 2' :4,
	'Only Strike Team 3' :5,
	'Only Left Side'     :10,
	'Only Right Side '   :11,
	'Sort STs by STP'    :1,
	'Sort All by STP'    :2,
	'Let me choose...'   :6,
	}

WHICH_NOST = {
	'Sort All by STP'    :7,
	'Sort All by TCP'    :8,
	'Sort All by Avail'  :9,

	'Let me choose...'   :6,
	}

WHICH_ADDST = {
	'Sort All by STP'    :7,
	'Sort All by TCP'    :8,
	'Sort All by Avail'  :9,

	'Annihilation Strike Teams'  :21,
	'Only Annihilation ST1'  :22,
	'Only Annihilation ST2'  :23,
	'Only Annihilation ST3'  :24,

	'Spotlight Strike Teams'  :25,
	'Only Spotlight ST1'  :26,
	'Only Spotlight ST2'  :27,
	'Only Spotlight ST3'  :28,

	'Let me choose...'   :6,
	}

CHOICES_MEM   = get_choices(WHICH_MEM)
CHOICES_NOST  = get_choices(WHICH_NOST)
CHOICES_ADDST = get_choices(WHICH_ADDST)

# Update table_format with the correct flags
def process_which_members(table_format, which_members):

	# If sorting by STP, add dividers to indicate the bottom three
	if which_members == 1:
		table_format['sort_by'] = 'stp'
		table_format['inc_dividers'] = '53'
		table_format['only_side'] = False

	# Ignore Strike teams or only specific strike teams
	elif which_members in [2,3,4,5]:
		table_format['only_team'] = which_members-2
	
	elif which_members == 6:
		table_format['pick_members'] = True

		# Display rank for each team's STP within alliance
		table_format['inc_rank'] = True
	
	elif which_members == 7:
		table_format['sort_by'] = 'stp'
	elif which_members == 8:
		table_format['sort_by'] = 'tcp'
	elif which_members == 9:
		table_format['sort_by'] = 'avail'
		table_format['inc_avail'] = True
	
	elif which_members == 10:
		table_format['only_side'] = 'left'
	elif which_members == 11:
		table_format['only_side'] = 'right'
	elif which_members == 12:
		table_format['only_side'] = False
	elif which_members == 13:
		table_format['only_side'] = 'both'
	elif which_members == 14:
		table_format['only_side'] = False
		table_format['span'] = True

	# Allow Annihilation STs on non-raid reports
	elif which_members in range(21,25):
		table_format['strike_teams'] = 'annihilation'

		if which_members in range(22,25):
			table_format['only_team'] = which_members-21

	# Allow Spotlight STs on non-raid reports
	elif which_members in range(25,28):
		table_format['strike_teams'] = 'spotlight'

		if which_members in range(26,28):
			table_format['only_team'] = which_members-25

	# If we're requesting thin data and multiple sections, stack them up!
	if (table_format.get('only_side') or table_format.get('only_team') or table_format.get('pick_members') or table_format.get('span')) and not table_format.get('only_section'):
	
		# Allow more sections per image. Should still be short
		table_format['sections_per'] = 6



CHOOSE_INFO = {
	'Pwr, Tier, ISO, OP':1,
	'Pwr, Lvl, Tier, ISO':2,
	'Pwr, Yel, Red':3,
	'Pwr, Iso, Class':4,
	'Pwr, Lvl, Tier, ISO':2,
	'All but Abilities, OP':7,
	'All avail':5,
	'Let me choose...':6,
	}

CHOOSE_ANALYSIS = {
	'All avail':15,
	'Yellow, Red, Diamonds':13,
	'Let me choose...':6,
	}

CHOICES_INFO     = get_choices(CHOOSE_INFO)
CHOICES_ANALYSIS = get_choices(CHOOSE_ANALYSIS)

# Update table_format with the correct flags
def process_choose_info(table_format, choose_info):

	if choose_info == 1:
		table_format['inc_keys'] = ['power', 'tier', 'iso', 'op']
	
	elif choose_info == 2:
		table_format['inc_keys'] = ['power', 'lvl', 'tier', 'iso']
	
	elif choose_info == 3:
		table_format['inc_keys'] = ['power', 'yel', 'red']

	elif choose_info == 4:
		table_format['inc_keys'] = ['power', 'iso']
		table_format['inc_class'] = True
	
	elif choose_info == 5:
		table_format['inc_keys'] = ['power', 'lvl', 'tier', 'iso', 'op', 'yel', 'red', 'abil']
		table_format['inc_class'] = True
	
	elif choose_info == 7:
		table_format['inc_keys'] = ['power', 'lvl', 'tier', 'iso', 'yel', 'red']
		table_format['inc_class'] = True
	
	elif choose_info == 6:
		table_format['custom_keys'] = True 

	# Roster Analysis Choose Info Options
	
	elif choose_info == 13:
		table_format['inc_keys'] = ['yel', 'red']

	elif choose_info == 15:
		table_format['inc_keys'] = ['yel', 'red', 'lvl', 'iso', 'tier', 'abil', 'op']



ISO_LVL     = {f'{int((x+4)/5)}-{(x+4)%5+1}':x for x in list(range(15,0,-1))}

CHOICES_ISO = get_choices(ISO_LVL)

def process_min_iso(table_format, min_iso):

	# Integer entered. Use it
	if min_iso in [str(x) for x in ISO_LVL.values()]:
		table_format['min_iso'] = int(min_iso)

	# Use dict value or None if no match
	elif ISO_LVL.get(min_iso):
		table_format['min_iso'] = ISO_LVL[min_iso]



YEL_STARS   = {f'{x+1}':x+1 for x in range(6,1,-1)}
CHOICES_YEL = get_choices(YEL_STARS)



RED_STARS   = {f'{x-6}\U0001F48E' if x>6 else f'{x+1}':x+1 for x in range(11,-1,-1)}
CHOICES_RED = get_choices(RED_STARS)



INC_HIST = {
	'No History':0,
	'History Below, Use Oldest':11,
	'History Below, Choose Date':1,
	'History on Right, Use Oldest':12,
	'History on Right, Choose Date':2,
	'Inline History, Choose Players, Use Oldest':13,
	'Inline History, Choose Players and Date':3,
	}

INC_HIST_ANALYSIS = {
	'No History':0,
	'Compare vs Oldest Entry':11,
	'Choose Date...':1,
	}

INC_PROG_ANALYSIS = {
	'No Progressive View':0,
	'Include Progressive View':1,
	}

CHOICES_HIST          = get_choices(INC_HIST)
CHOICES_HIST_ANALYSIS = get_choices(INC_HIST_ANALYSIS)
CHOICES_PROG_ANALYSIS = get_choices(INC_PROG_ANALYSIS)

# Update table_format with the correct flags.
def process_history(table_format, history):

	# Special processing for by_char
	if table_format.get('output') == 'by_char':
		table_format['inc_hist']   = history != 0
		table_format['use_oldest'] = history == None
		
	# Inline History is shorter, 
	elif history in (3,13):
		table_format['inline_hist'] = True

		# Select individual members to report on
		table_format['pick_members'] = True

		# Display rank for each team's STP within alliance
		table_format['inc_rank'] = True

		# Only include toons which have changed 
		table_format['min_change_filter'] = True

		# Allow more sections per image. Should still be short
		table_format['sections_per'] = 6

	# If we're asking for Standard History, can only have one section per file
	elif history in (1,11):
		table_format['inc_hist'] = True
		table_format['sections_per'] = 1

	# Inline History isn't compatible with spanning, Other Chars, split display
	elif history in (2,12):
		table_format['inc_hist'] = True
		table_format['side_hist'] = True
		table_format['only_side'] = False
		table_format['span'] = False
		table_format['max_others'] = 0

	# Just use oldest date available?
	if history in (11,12,13):
		table_format['use_oldest'] = True



OTHER_OPTS = {
	'No Span':3,
	'All One Image':4,				# (sections_per:0)
	'One Section Per Image':5,
	'One Member Per Image':7,		# (sections_per:0. pick_members:True)
	'Four Members Per Image':8,		# (sections_per:0. pick_members:True)
	'HTML File':6,					# (sections_per:0)
	}

TRAIT_OPTS = {
	'One Member Per Image':7,		# (sections_per:0. pick_members:True)
	'Four Members Per Image':8,		# (sections_per:0. pick_members:True)
	'HTML File':6,					# (sections_per:0)
	}

SUMMARY_OPTS = {
	'HTML File':6,					# (sections_per:0)
	}

CHOICES_OPTS    = get_choices(OTHER_OPTS)
CHOICES_TRAIT   = get_choices(TRAIT_OPTS)
CHOICES_SUMMARY = get_choices(SUMMARY_OPTS)

# Update table_format with the correct flags
def process_other_opts(table_format, other_opts):

	if other_opts == 3:
		table_format['span'] = False
	elif other_opts == 4:
		table_format['sections_per'] = 0
	elif other_opts == 5:
		table_format['sections_per'] = 1
	elif other_opts == 6:
		table_format['sections_per'] = 0
		table_format['output_format'] = 'html'
	elif other_opts in (7,8):
		table_format['sections_per'] = 0
		table_format['pick_members'] = True
		table_format['num_per_image'] = {7:1, 8:4}.get(other_opts)



SHOW_OLD = {
	'Remove OLD entries':0,
	'Show OLD entries':1,
	'Show ONLY summary':2,
	}

CHOICES_SHOW_OLD = get_choices(SHOW_OLD)



# Do standard processing for all of the above.
@timed
async def process_args(table_format, locals):

	# Load calculated defaults
	defaults = locals['defaults']

	# Set the appropriate values for only section
	process_lane(table_format, locals.get('lane') or locals.get('zone'))
	
	# Set the appropriate values for only section
	process_section(table_format, locals.get('section') or locals.get('mission'))
	
	# Set the appropriate flags if special sort is requested
	process_which_members(table_format, defaults.get('which_members'))

	# Set the appropriate flags if choose_info selected
	process_choose_info(table_format, defaults.get('choose_info'))

	# Set the appropriate flags if history requested
	process_history(table_format, defaults.get('history'))

	# Set the other available options for this report
	process_other_opts(table_format, defaults.get('other_opts'))

	# Set min_iso if explicitly set
	process_min_iso(table_format, defaults.get('min_iso'))

	# Set min_iso if difficulty set
	process_difficulty(table_format, defaults.get('difficulty'))

	# Only set min_tier if value specified
	if defaults.get('min_tier') is not None:
		table_format['min_tier'] = defaults.get('min_tier')
		
	# Only set min_level if value specified
	if defaults.get('min_level') is not None:
		table_format['min_lvl'] = defaults.get('min_level')
		
	# Only set min_yel if value specified
	if defaults.get('min_yel') is not None:
		table_format['min_yel'] = defaults.get('min_yel')

	# Only set min_red if value specified
	if defaults.get('min_red') is not None:
		table_format['min_red'] = defaults.get('min_red')

	CHAR_LIMIT = table_format.pop('char_limit', None)
	MAX_CHARS  = defaults.get('max_chars') or defaults.get('max_others')

	# Only set max_others if char_limit or max_chars specified
	if CHAR_LIMIT or MAX_CHARS is not None:

		# Enforce any defined char_limit
		table_format['max_others'] = min(CHAR_LIMIT, MAX_CHARS or CHAR_LIMIT) if CHAR_LIMIT else MAX_CHARS

		# Sort by avail 
		table_format['sort_char_by'] = 'avail'

	# Special Handling
	if defaults.get('alliance_name'):
		table_format['alliance_name'] = defaults.get('alliance_name')

	NEED_HIST = table_format.get('inc_hist') or table_format.get('inline_hist')
	HAVE_HIST = table_format.get('use_oldest')
	NEED_MEMB = table_format.get('pick_members')
	NEED_KEYS = table_format.get('custom_keys')

	# If PROMPTING for anything, defer ASAP
	if (NEED_HIST and not HAVE_HIST) or NEED_MEMB or NEED_KEYS:
		try:	await locals.get('context').interaction.response.defer(ephemeral=True)
		except:	pass

	# Merge Control Frame info in if present
	table_format |= defaults.get('control_frame', {})



# Quick reverse lookup of our picklist values
def swap_dict(dict):
	return {value: key for key, value in dict.items()}

LOOKUP_WHICH    = swap_dict(WHICH_MEM) | swap_dict(WHICH_NOST)
LOOKUP_HIST     = swap_dict(INC_HIST_ANALYSIS) | swap_dict(INC_HIST)
LOOKUP_PROG     = swap_dict(INC_PROG_ANALYSIS)
LOOKUP_INFO     = swap_dict(CHOOSE_INFO) | swap_dict(CHOOSE_ANALYSIS)
LOOKUP_OPTS     = swap_dict(OTHER_OPTS)
LOOKUP_SHOW_OLD = swap_dict(SHOW_OLD)
LOOKUP_COLORS   = swap_dict(COLORS)
LOOKUP_DIFF     = swap_dict(SPOT_DIFF) | swap_dict(ANNI_DIFF)
LOOKUP_ANY_ALL  = swap_dict(ANY_OR_ALL)

def lookup_option(arg_type, arg_value):
	if arg_type == 'show_old':
		return LOOKUP_SHOW_OLD.get(arg_value, arg_value)
	if arg_type == 'progress':
		return LOOKUP_PROG.get(arg_value, arg_value)
	if arg_type == 'colors':
		return LOOKUP_COLORS.get(arg_value, arg_value)
	if arg_type == 'any_or_all':
		return LOOKUP_ANY_ALL.get(arg_value, arg_value)
	if arg_type == 'choose_info':
		return LOOKUP_INFO.get(arg_value, arg_value)
	if arg_type == 'history':
		return LOOKUP_HIST.get(arg_value, arg_value)
	if arg_type == 'difficulty':
		return LOOKUP_DIFF.get(arg_value, arg_value)
	if arg_type == 'which_members':
		return LOOKUP_WHICH.get(arg_value, arg_value)
	if arg_type == 'other_opts':
		return LOOKUP_OPTS.get(arg_value, arg_value)
	return arg_value
