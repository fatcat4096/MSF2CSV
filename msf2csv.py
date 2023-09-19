#!/usr/bin/env python3
# Encoding: UTF-8
"""msf2csv.py
Transform stats from MSF.gg into readable tables with heatmaps.
"""

import os
import datetime
import sys
import time
import argparse


from process_website import *       # Routines to get Roster data from website
from generate_html import *         # Routines to generate the finished tables.		


# If no name specified, default to the alliance for the Login player 
def main(alliance_name='', cached_data='', csv=False, nohist=False, prompt=False, force=False):

	# Load roster info directly from cached data or the website.
	alliance_info = get_alliance_info(alliance_name, cached_data, prompt, force)
								 
	# If not frozen, work in the same directory as this script.
	path = os.path.dirname(__file__)

	# If frozen, work in the same directory as the executable.
	if getattr(sys, 'frozen', False):
		path = os.path.dirname(sys.executable)

	# Build a default path and filename. 
	filename = path + os.sep + alliance_info['name'] + datetime.datetime.now().strftime("-%Y%m%d-")

	# Generate CSV or HTML?
	if csv:
		# Original file format. Requested for input to projects using old CSV format.
		 write_file(filename+"original.csv", generate_csv(alliance_info))
	else:
		# Generate the active html files specified in tables.py
		for table in tables['active']:
			write_file(filename+table+'.html', generate_html(alliance_info, nohist, tables[table]))

	time.sleep(1)


def write_file(filename, content):
	# Default output is UTF-8. Attempt to use it as it's more compatible.
	try:
		open(filename, 'w').write(content)
	# UTF-16 takes up twice the space. Only use it as a fallback option if errors generated during write.
	except:
		open(filename, 'w', encoding='utf-16').write(content)	
	print ("Writing %s" % (filename))


# Parse arguments
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description="Create HTML tables from MSF roster data.")
	parser.add_argument("file_or_alliance", type=str, nargs='?',
						help="specify a cached_data file or alliance_name input", default='')
	parser.add_argument("-c", "--csv", action="store_true", 
						help="generate csv output instead of html tables")
	parser.add_argument("-f", "--force", action="store_true", 
						help="force download of roster data, regardless of timing")
	parser.add_argument("-n" , "--nohist", action="store_true", 
						help="exclude history tab from output")
	parser.add_argument("-p" , "--prompt", action="store_true", 
						help="prompt and store credentials")
	# Have not added verbose output for debug yet.
	#parser.add_argument("-v", "--verbose", action="store_true", 
	#					help="increase output verbosity")

	args = parser.parse_args()

	if '.msf' in args.file_or_alliance:
		cached_data   = args.file_or_alliance
		alliance_name = ''
	else: 
		cached_data   = ''
		alliance_name = args.file_or_alliance
		
	main(alliance_name, cached_data, args.csv, args.nohist, args.prompt, args.force) # Just run myself

