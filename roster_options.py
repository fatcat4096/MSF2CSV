"""roster_options.py
Picklists and enumerations for use in the /roster report menus.
Also routines to parse the input into valid table_format entries.
"""

from enum import Enum

from msf_shared import msf2csv, get_choices

# Extract names of Traits from the Table definitions to create Enum definitions.
def get_traits(table,lane_num= 0):

	# Grab the appropriate lane.
	lane = table['lanes'][lane_num]

	# Extract the trait definitions from this lane.
	trait_list = ['All Sections'] + [msf2csv.get_section_label(section) for section in lane]

	# Load those traits up into a dict to be used for an Enum definition.
	return {key:trait_list.index(key) for key in trait_list}


# Enum definitions used for Discord Picklists in slash commands.
SECT_DD7       = Enum('SECT_DD7',       get_traits(msf2csv.tables['dd7']))
SECT_DD8       = Enum('SECT_DD8',       get_traits(msf2csv.tables['dd8']))
SECT_SPOTLIGHT = Enum('SECT_SPOTLIGHT', get_traits(msf2csv.tables['spotlight']))
SECT_ORCHIS    = Enum('SECT_ORCHIS',    get_traits(msf2csv.tables['orchis']))

# Build list for the lanes/section for autocomplete.
SECT_ALL_CHARS = ['All Sections', 'Mutant', 'Bio', 'Skill', 'Mystic', 'Tech']
SECT_INCUR     = list(get_traits(msf2csv.tables['incur']))
SECT_DD6       = list(get_traits(msf2csv.tables['dd6']))
SECT_TEAMS     = list(get_traits(msf2csv.tables['teams']))

CHOICES_ALL_CHARS = get_choices(SECT_ALL_CHARS)
CHOICES_INCUR     = get_choices(SECT_INCUR)
CHOICES_DD6       = get_choices(SECT_DD6)
CHOICES_TEAMS     = get_choices(SECT_TEAMS)

# Build lists for other autocompletes
FORMATS = [msf2csv.tables[format]['name'] for format in msf2csv.tables]

BY_CHAR_LIST  = list(msf2csv.get_cached('char_list'))
BY_TRAIT_LIST = {msf2csv.translate_name(trait).replace('<br>',' '):trait for trait in sorted(['Non-Mythic','Non-Legendary','Non-Minion']+list(msf2csv.get_cached('trait_list')))}

CHOICES_FORMATS  = get_choices(FORMATS)
CHOICES_BY_CHAR  = get_choices(BY_CHAR_LIST)
CHOICES_BY_TRAIT = get_choices(BY_TRAIT_LIST)

ANY_OR_ALL = {
	'ALL of these traits': 'all',
	'ANY of these traits': 'any',
	}

SPOT_DIFF = {
	'Normal':5,
	'Diff 1':6,
	'Diff 2':9,
	}

ORCHIS_DIFF = {
	'Normal':0,
	'Diff 1':8,
	'Diff 2':9,
	'Diff 3':10,
	}

COLORS = {
	'Balanced':'set',
	'Extended':'list',
	'Original':'',
	}

DEFAULTS = {
	'Save Defaults':1,
	'Reset Defaults':2
	}


CHOICES_ANY_ALL      = get_choices(ANY_OR_ALL)
CHOICES_SPOTLIGHT    = get_choices(SPOT_DIFF)
CHOICES_ORCHIS       = get_choices(ORCHIS_DIFF)
CHOICES_COLORS       = get_choices(COLORS)
CHOICES_DEFAULTS     = get_choices(DEFAULTS)



ISO_LVL     = {f'{int((x+4)/5)}-{(x+4)%5+1}':x for x in list(range(13,0,-1))}

CHOICES_ISO = get_choices(ISO_LVL)

def process_min_iso(table_format, min_iso):

	# Integer entered. Use it.
	if min_iso in [str(x) for x in ISO_LVL.values()]:
		table_format['min_iso'] = int(min_iso)

	# Use dict value or None if no match
	elif ISO_LVL.get(min_iso):
		table_format['min_iso'] = ISO_LVL[min_iso]

		

INC_HIST = {
	'No History':None,
	'History Below, Use Oldest':11,
	'History Below, Choose Date':1,
	'History on Right, Use Oldest':12,
	'History on Right, Choose Date':2,
	'Select Players, Use Oldest':13,
	'Select Players, Choose Date':3,
	}

INC_HIST_BASE = {
	'None':0,
	'Standard History':1,
	}

CHOICES_HIST      = get_choices(INC_HIST)
CHOICES_HIST_BASE = get_choices(INC_HIST_BASE)

# Update table_format with the correct flags.
def process_history(table_format, history):

	# If we're asking for Standard History, can only have one section per file.
	if history in (1,11):
		table_format['inc_hist'] = True
		table_format['sections_per'] = 1

	# Inline History isn't compatible with spanning, Other Chars, split display
	elif history in (2,12):
		table_format['inc_hist'] = True
		table_format['side_hist'] = True
		table_format['only_side'] = False
		table_format['span'] = False
		table_format['max_others'] = 0

	# Inline History is shorter, 
	elif history in (3,13):
		table_format['inline_hist'] = True

		# Select individual members to report on.
		table_format['select_members'] = True

		# Display rank for each team's STP within alliance
		table_format['inc_rank'] = True

		# Filter out any heroes that haven't changed by at least 25% 
		table_format['min_change_filter'] = 0.25

		# Allow more sections per image. Should still be short.
		table_format['sections_per'] = 7

	# Just use oldest date available?
	if history in (11,12,13):
		table_format['use_oldest'] = True



CHOOSE_INFO = {
	'Pwr, Lvl, Tier, ISO':1,
	'Pwr, Yel, Red':2,
	'Pwr, Iso, Class':3,
	'All avail':4,
	'Let me choose...':5,
	}

CHOOSE_SUMMARY = {
	'STP, Rank':11,
	'STP, Avail':12,
	'STP, Rank, Avail':13,
	}

CHOICES_INFO    = get_choices(CHOOSE_INFO)
CHOICES_SUMMARY = get_choices(CHOOSE_SUMMARY)

# Update table_format with the correct flags.
def process_choose_info(table_format, choose_info):

	if choose_info == 1:
		table_format['inc_keys'] = ['power', 'lvl', 'tier', 'iso']
	
	elif choose_info == 2:
		table_format['inc_keys'] = ['power', 'yel', 'red']

	elif choose_info == 3:
		table_format['inc_keys'] = ['power', 'iso']
		table_format['inc_class'] = True
	
	elif choose_info == 4:
		table_format['inc_keys'] = ['power', 'lvl', 'tier', 'iso', 'yel', 'red', 'abil']
		table_format['inc_class'] = True
	
	elif choose_info == 5:
		table_format['custom_keys'] = True 

	# Team Power Summary options
	elif choose_info == 11:
		table_format['inc_keys'] = ['stp','rank']

	elif choose_info == 12:
		table_format['inc_keys'] = ['stp','avail']

	elif choose_info == 13:
		table_format['inc_keys'] = ['stp','rank','avail']



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

CHOICES_MEM  = get_choices(WHICH_MEM)
CHOICES_NOST = get_choices(WHICH_NOST)

# Update table_format with the correct flags.
def process_which_members(table_format, which_members):

	# If sorting by STP, add dividers to indicate the bottom three.
	if which_members == 1:
		table_format['sort_by'] = 'stp'
		table_format['inc_dividers'] = '53'
		table_format['only_side'] = False

	# Ignore Strike teams or only specific strike teams.
	elif which_members in [2,3,4,5]:
		table_format['only_team'] = which_members-2
	
	elif which_members == 6:
		table_format['select_members'] = True

		# Allow more sections per image. Should still be short.
		table_format['sections_per'] = 7

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



OTHER_OPTS = {
	'No Span':3,
	'All One Image':4,				# (sections_per:0)
	'One Image Per Section':5,
	'HTML File':6,					# (forces sections_per:0)
	}

CHOICES_OPTS = get_choices(OTHER_OPTS)

# Update table_format with the correct flags.
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

