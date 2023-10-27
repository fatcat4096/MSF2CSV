#!/usr/bin/env python3
# Encoding: UTF-8
"""msf2csv.py
Transform stats from MSF.gg into readable tables with heatmaps.
"""


import os
import datetime
import argparse

from alliance_block	 import *             # Routines to encode/decode the alliance block.
from process_website import *             # Routines to get Roster data from website.
from file_io         import *             # Routines to read and write files to disk.
from generate_html   import *             # Routines to generate the finished tables.
from generate_csv    import generate_csv  # Routines to generate the original csv files.
from io              import StringIO      # Allow capture of stdout for return to bot.


# If no name specified, default to the alliance for the Login player
def main(alliance_name='', csv=False, rosters_only=False, prompt=False, headless=False, export_block=False, import_block='', force='', table_format={}, output='', images_only=False):

	# Capture stdout to return to bot.
	if rosters_only or import_block:
		temp_stdout = StringIO()
		sys.stdout = temp_stdout

	# Parse alliance info from import_block and update rosters from website.
	if import_block:

		## SHOULD ADD SOME SORT OF VERIFICATION/SANITY CHECK RE FORMAT OF THE BLOCK TO IMPORT TO PREVENT BAD DATA INJECTION
		decode_block(import_block)

	# Load roster info directly from cached data or the website.
	else:
		alliance_info = get_alliance_info(alliance_name, prompt, force, headless)

	# If we're done, restore sys.stdout and return the captured output
	if rosters_only or import_block:
		sys.stdout = sys.__stdout__
		return temp_stdout.getvalue()

	print ()

	# Build a default path and filename. 
	filename = os.path.dirname(alliance_info['file_path']) + os.sep + alliance_info['name'] + datetime.datetime.now().strftime("-%Y%m%d-")

	# Generate Export Block?
	if export_block:
		alliance_block = encode_block(alliance_info)
		write_file(filename+'block.txt', alliance_block)
		print ("Encoded Alliance for SIGMA Bot:",alliance_block)

	# Generate CSV?
	elif csv:
		 write_file(filename+"original.csv", generate_csv(alliance_info))

	# If images_only, we're going to request output 
	elif images_only:
	
		if output in tables['active']+['roster_analysis','alliance_info']:
		
			pathname = os.path.dirname(alliance_info['file_path'])+os.sep+alliance_info['name']+'-'
		
			html_files = generate_html_files(alliance_info, tables.get(output,{}), table_format, output)
			html_files = write_file(pathname, html_files, print_path=False)
			return html_to_images(html_files)
			
		else:
			print("--output FORMAT must be one of the following:\n"+str(tables['active']+['roster_analysis','alliance_info']))

	# Default: Generate all active html files specified in tables
	else:
		# Output only specific formats.
		if output:
			
			if output in tables['active']+['roster_analysis','alliance_info']:

				pathname = os.path.dirname(alliance_info['file_path'])+os.sep+alliance_info['name']+'-'

				html_files = generate_html_files(alliance_info, tables.get(output,{}), table_format, output)
				return write_file(pathname, html_files)
			
			else:
				print("--output FORMAT must be one of the following:\n"+str(tables['active']+['roster_analysis','alliance_info']))

		# Otherwise, output every active format.
		else:
			cached_tabs = {}
			for table in tables['active']:
				write_file(filename+table+'.html', generate_tabbed_html(alliance_info, tables[table], table_format, cached_tabs))



# Parse arguments
if __name__ == '__main__':

	formatter = lambda prog: argparse.HelpFormatter(prog, max_help_position=40)
	parser = argparse.ArgumentParser(formatter_class=formatter, description='Create HTML tables from MSF roster data.')

	parser.add_argument('file_or_alliance', type=str, nargs='?',
						help='specify a cached_data file or alliance_name input', default='')
	
	## MAYBE HAVE A SEPARATE CALL TO GET AGE OF CACHED_DATA FILE? 
	## MAYBE HAVE THIS BE PART OF THE RETURN WHEN WE REQUEST WHICH CACHED_DATA WE HAVE RIGHTS TO? 
	#parser.add_argument('-a', '--age', action='store_true', 
	#					help='just get age of cached roster data, generate no output')
	parser.add_argument('-c', '--csv', action='store_true', 
						help='just generate csv output, no html tables')
	parser.add_argument('-p' , '--prompt', action='store_true', 
						help='prompt and store credentials')
	parser.add_argument('-r', '--rosters_only', action='store_true', 
						help='just update cached data from web, no output (forces headless)')
	parser.add_argument('--headless', action='store_true', 
						help='hide web browser driver during roster processing')

	# Import or Export Alliance Block info.
	group2 = parser.add_mutually_exclusive_group()
	group2.add_argument('-e', '--export_block', action='store_true', 
						help='export definition block for an Alliance')
	group2.add_argument('--import_block', type=str, metavar='BLOCK', 
						help='import definition block for an Alliance')

	# Force fresh roster downloads or force use of cached data.
	group1 = parser.add_mutually_exclusive_group()
	group1.add_argument('-f', '--fresh', action='store_true', 
						help='force download of Alliance roster data, regardless of timing')
	group1.add_argument('-s', '--stale', action='store_true',
						help='prevent download of Alliance roster data, regardless of timing')

	# Table Formatting flags. 
	parser.add_argument('--min_iso', type=int, metavar='N',
						help='minimum ISO level for inclusion in output')
	parser.add_argument('--min_tier', type=int, metavar='N',
						help='minimum Gear Tier for inclusion in output')
	parser.add_argument('--max_others', type=int, metavar='N',
						help='max characters in Others section; 0 is no max')
	parser.add_argument('-n', '--no_hist', action='store_true', 
						help='exclude History info from output')
	parser.add_argument('--only_lane', type=int, metavar='N',
						help='only output ONE lane of a given format')
	parser.add_argument('--only_section', type=int, metavar='N',
						help='only output ONE section of a given lane')

	# Output a single format? Output images instead?
	parser.add_argument('--output', type=str, metavar='FORMAT',
						help='only output ONE format from the list of active formats', default='')
	parser.add_argument('--images_only', action='store_true',
						help='output PNG files instead of HTML, requires -o/--output', default='')						
	args = parser.parse_args()

	# Rosters_only forces Fresh download of roster data.
	force = ['','fresh','stale'][args.fresh-args.stale]
	if args.rosters_only:
		force = 'fresh'
	
	# Rosters Only forces Headless operation, Decode Block always operates headlessly
	headless = args.rosters_only or args.headless

	if args.images_only and not args.output:
		parser.error ("--images_only requires --output FORMAT to be specified")
	
	# Group the Formatting flags into a single argument
	table_format = {'min_iso':args.min_iso, 'min_tier':args.min_tier, 'max_others':args.max_others, 'only_lane':args.only_lane, 'only_section':args.only_section, 'no_hist':args.no_hist}
	
	main(args.file_or_alliance, args.csv, args.rosters_only, args.prompt, headless, args.export_block, args.import_block, force, table_format, args.output, args.images_only) # Just run myself

