#!/usr/bin/env python3
# Encoding: UTF-8
"""msf2csv.py
Unpacks all MHTML files in the local directory to find the character file from MSF.GG. 
Passes this HTMl to the parse_contents() routines to scrape and pass back to the top level.

This routine is largely obsolete now. Way easier to download the roster info directly from msf.gg

Derived from mhtifier.py code by Ilan Irad
See: https://github.com/Modified/MHTifier
"""

# Standard library modules do the heavy lifting. Ours is all simple stuff.
from parse_contents import *

import email, email.message
import os


# We will look for MHTML in the same directory as this file.
try:
	path = os.path.dirname(__file__)+os.sep
# Sourcing locally, no __file__ object.
except:
	path = '.'+os.sep

 
def process_mhtml(path=path):

	processed_players = {}	# roster stats for each player
	char_stats = {}			# min/max stats and portrait path for individual heroes
	
	# Iterate through the directory looking for MHTML files.
	for file in os.listdir(path):

		# Skip if not MHTML
		if file[-5:] != "mhtml":
			continue

		# If file hasn't been seen before or updated, need to process it again.
		mtime = os.path.getmtime(os.path.join(path,file))
		if file in file_dates and mtime <= file_dates[file]:
			continue
		# Open the .mhtml file for reading. 
		mht = open(os.path.join(path,file), "rb")
		print("Unpacking "+file+"...")

		# Read entire MHT archive -- it's a multipart(/related) message.
		a = email.message_from_bytes(mht.read()) 
		
		parts = a.get_payload()
		if not type(parts) is list:
			parts = [a] 		# Single 'str' part, so convert to list.
																			
		# Look for the 'character' file among the file parts.
		for part in parts: 
			content_type = part.get_content_type() # String coerced to lower case of the form maintype/subtype, else get_default_type().			
			file_path    = part.get("content-location") or "index.html" # File path. Expecting root HTML is only part with no location.

			# Ignore the path, focus on the filename.
			decoded_file = file_path.split('/')[-1]

			# Only the characters.html file has relevant data.
			if decoded_file == 'characters':
				parse_characters(part.get_payload(decode=True), char_stats, processed_players, path)

	return char_stats,processed_players


