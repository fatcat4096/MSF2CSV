#!/usr/bin/env python3
# Encoding: UTF-8
"""msf2csv.py
Transform stats from MSF.gg into readable tables with heatmaps.
"""

import os
import datetime
import sys
import time


from process_website import *       # Routines to get Roster data from website
from generate_html import *         # Routines to generate the finished tables.		


# If no name specified, default to the alliance for the Login player 
def main(alliance_name=''):

	# Load roster info directly from cached data or the website.
	alliance_info = get_alliance_info(alliance_name)
								 
	# If not frozen, work in the same directory as this script.
	path = os.path.dirname(__file__)

	# If frozen, work in the same directory as the executable.
	if getattr(sys, 'frozen', False):
		path = os.path.dirname(sys.executable)

	# Build a default path and filename. 
	filename = path + os.sep + alliance_info['name'] + datetime.datetime.now().strftime("-%Y%m%d-")

	# Generate the active html files specified in tables.py
	for table in tables['active']:
		html_file = generate_html(alliance_info, tables[table])
		open(filename+table+'.html', 'w', encoding='utf-16').write(html_file)

	# Original file format. Requested for input to projects using old CSV format.
	#csv_file = generate_csv(alliance_info)
	#open(filename+"original.csv", 'w', encoding='utf-16').write(csv_file)

	print ("Alliance Roster tables written to: "+path)

	time.sleep(2)

if __name__ == "__main__":
	main() # Just run myself

