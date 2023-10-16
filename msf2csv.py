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


# If no name specified, default to the alliance for the Login player
def main(alliance_name='', csv=False, nohist=False, prompt=False, force=False, exportblock=False, importblock='', output=''):

	# Parse alliance info from importblock and update rosters from website.
	if importblock:
		alliance_info = decode_block(importblock)

	# Load roster info directly from cached data or the website.
	else:
		alliance_info = get_alliance_info(alliance_name, prompt, force)

	print ()

	# Build a default path and filename. 
	filename = os.path.dirname(alliance_info['file_path']) + os.sep + alliance_info['name'] + datetime.datetime.now().strftime("-%Y%m%d-")

	# Generate Export Block, CSV or HTML?
	if exportblock:
		alliance_block = encode_block(alliance_info)
		write_file(filename+'block.txt', alliance_block)
		print ("Encoded Alliance for SIGMA Bot:",alliance_block)
	elif csv:
		# Original file format. Requested for input to projects using old CSV format.
		 write_file(filename+"original.csv", generate_csv(alliance_info))
	elif output:
		if output in tables['active']+['roster_analysis','alliance_info']:
			write_image_files(os.path.dirname(alliance_info['file_path']) + os.sep + alliance_info['name']+'-', generate_html_files(alliance_info, tables.get(output,{}), nohist, output=output))
	else:
		# Generate the active html files specified in tables.py
		cached_tabs = {}
		for table in tables['active']:
			write_file(filename+table+'.html', generate_tabbed_html(alliance_info, tables[table], nohist, cached_tabs))


# Parse arguments
if __name__ == '__main__':

	parser = argparse.ArgumentParser(description='Create HTML tables from MSF roster data.')
	parser.add_argument('file_or_alliance', type=str, nargs='?',
						help='specify a cached_data file or alliance_name input', default='')
	parser.add_argument('-c', '--csv', action='store_true', 
						help='generate csv output instead of html tables')
	parser.add_argument('-f', '--force', action='store_true', 
						help='force download of roster data, regardless of timing')
	parser.add_argument('-n', '--nohist', action='store_true', 
						help='exclude history tab from output')
	parser.add_argument('-o', '--output', type=str,
						help='output images of specific tables instead of tabbed HTML')
	parser.add_argument('-p' , '--prompt', action='store_true', 
						help='prompt and store credentials')
	group = parser.add_mutually_exclusive_group()
	group.add_argument('-e', '--exportblock', action='store_true', 
						help='export definition block for an Alliance')
	group.add_argument('-i', '--importblock', type=str,
						help='import definition block for an Alliance')
						
	# Have not added verbose output for debug yet.
	#parser.add_argument("-v", "--verbose", action="store_true", 
	#					help="increase output verbosity")

	args = parser.parse_args()

	main(args.file_or_alliance, args.csv, args.nohist, args.prompt, args.force, args.exportblock, args.importblock, args.output) # Just run myself

