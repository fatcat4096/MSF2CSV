#!/usr/bin/env python3
# Encoding: UTF-8
"""file_io.py
Routines for reading/writing files and cached_data to disk.
"""

from log_utils import *

import os
import sys
import time
import re
import pickle
import importlib
import copy
import glob

try:	import strike_teams as strike_temp
except:	pass

try:	import raids_and_lanes
except:	pass

from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import quote, unquote



TAG_RE = re.compile(r'<[^>]+>')

# Ensure filename is valid for file system.
def encode_tags(filename):
	return quote(filename, safe="!#$%&'()+,;=@[]^`{}~ ")



# Translate filename from encoded form to readable.
def decode_tags(filename):
	return unquote(filename)



# Sanitize Alliance Names and player names of any HTML tags.
def remove_tags(text):

	# Cleaned text is without HTML tags. Also removing hashtags.
	cleaned = TAG_RE.sub('', text.replace('#','')).strip()

	# If nothing remains, then < > was decorative, return the original entry.
	return cleaned or text
	


@timed(level=3)
def get_local_path():
	# If not frozen, work in the same directory as this script.
	path = os.path.dirname(__file__)

	# If frozen, work in the same directory as the executable.
	if getattr(sys, 'frozen', False):
		path = os.path.dirname(sys.executable)

	return os.path.realpath(path) + os.sep



@timed(level=3)
def write_file(pathname, file_content, print_path=True):

	files_generated = []

	if type(file_content) is str:
		file_content = {'':file_content}

	for filename in file_content:

		# Get the actual path and filename (sanitize this path)
		path,file = os.path.split(remove_tags(pathname+filename))

		if print_path:
			print (f'Writing {format_filename(os.path.join(path,file))}')

		# Verify enclosing directory exists, if not, create it.
		if not os.path.exists(path):
			os.makedirs(path)

		# Default output is UTF-8. Attempt to use it as it's more compatible.
		try:
			open(os.path.join(path,file), 'w', encoding='utf-8').write(file_content[filename])
		# UTF-16 takes up twice the space. Only use it as a fallback option if errors generated during write.
		except:
			open(os.path.join(path,file), 'w', encoding='utf-16').write(file_content[filename])	

		files_generated.append(os.path.join(path,file))
		
	return files_generated



@timed(level=3)
def html_to_images(html_files=[], print_path=True, render_wait=0.1):
	
	files_generated = []
	
	# Start by creating a Selenium driver.
	options = webdriver.ChromeOptions()
	options.add_argument('--log-level=3')
	options.add_argument('--headless=new')

	options.add_experimental_option('excludeSwitches', ['enable-logging'])

	# The html_files list contains paths to the html files.
	for file in html_files:
		
		driver = webdriver.Chrome(options=options)

		# Start by opening each file with our Selenium driver.
		driver.get(r'file:///'+file)

		# Give it just a moment to render the page.
		time.sleep(render_wait)

		# Set the height/width of the window accordingly
		height = driver.execute_script('return document.documentElement.scrollHeight')
		width  = driver.execute_script('return document.documentElement.scrollWidth')

		# Look for the farthest right element.
		tables = driver.find_elements(By.TAG_NAME, "table")
		
		min_width = 360
		for table_idx, table in enumerate(tables):
			min_width = max(table.rect['x']+table.rect['width'], min_width)

			# Report table stats. 
			#print ('Index:',table_idx, 'table:',table.rect, 'min_width:',min_width, 'width:',width)

		driver.set_window_size(min_width+40, height+450)

		png_filename = file[:-4]+'png'

		# Report the file being written.
		if print_path:
			print (f"Writing {format_filename(png_filename)}")

		# Then use Selenium to render these pages to disk as images. 
		body = driver.find_element(By.TAG_NAME, "body")
		body.screenshot(png_filename)
		files_generated.append(png_filename)

		# Close the driver to prevent memory leaks.
		driver.close()

		"""# Finally, clean up the original files. 
		try:
			os.remove(file)
		except Exception as exc:
			print (f"EXCEPTION: {type(exc).__name__}: {exc}")
		"""
	return files_generated



def format_filename(filename):
	return f'{ansi.cyan}{os.path.dirname(filename)}{os.sep}{ansi.bold}{os.path.basename(filename)}{ansi.reset}'



@timed(level=3)
def write_cached_data(alliance_info, file_path='', timestamp='update', filename='', encode=True):
	
	# If no file_path, provided get one out of alliance_info or use local dir as default.
	if not file_path:
		file_path = alliance_info.get('file_path', get_local_path())

	# Remove the file_path temporarily, before we write to disk.
	# Also permanently remove 'traits', 'trait_file', 'scripts', and 'portraits'.
	for key in ('file_path','traits','portraits','scripts','trait_file'):
		if key in alliance_info:
			del alliance_info[key]

	# Ensure we are just using the path name
	if os.path.isfile(file_path):
		file_path = os.path.realpath(os.path.dirname(file_path))

	# Ensure the enclosing directory exists.
	if not os.path.exists(file_path):
		os.makedirs(file_path)

	# Construct the file name and encode if invalid characters are included.
	file_name = filename or alliance_info.get('name')
	if encode:
		file_name = encode_tags(file_name)
		
	file_path += os.sep + 'cached_data-' + file_name + '.msf'
	
	# If we don't want to indicate this file has changed, save the current timestamp.
	if timestamp != 'update':
		if os.path.exists(file_path):
			ctime = os.path.getctime(file_path)
			mtime = os.path.getmtime(file_path)
		else:
			ctime = mtime = time.time()
	
	# Write the .msf file. 
	pickle.dump(alliance_info,open(file_path, 'wb'))

	# Need to keep original timestamp? (change unrelated to roster data)
	if timestamp == 'keep':
		os.utime(file_path, (ctime, mtime))
	# Need to backdate the modification? (Force a refresh on next request)
	elif timestamp == 'back':
		day_old = time.time() - 60*60*24
		os.utime(file_path, (ctime, day_old))
	
	# Stash the path and filename inside of alliance_info. 
	alliance_info['file_path'] = file_path
	


# Load a pickled cache file from cached_data directory
@timed(level=3)
def load_cached_file(file):
	data={}

	# Load the requested information if it exists
	file_path = get_local_path() + f'cached_data{os.sep}defaults{os.sep}cached_{file}'

	if os.path.exists(file_path):
		data = pickle.load(open(file_path,'rb'))

	return data



# Load a pickled cache file from cached_data directory
@timed(level=3)
def write_cached_file(data, file):

	# Ensure the enclosing directory exists.
	cached_path = get_local_path() + f'cached_data{os.sep}defaults{os.sep}'

	if not os.path.exists(cached_path):
		os.makedirs(cached_path)	

	pickle.dump(data, open(cached_path + f'cached_{file}', 'wb'))



# Has it been less than 24 hours since last update of cached_data?
@timed(level=3)
def fresh_enough(alliance_or_file):

	last_refresh = age_of(alliance_or_file)

	return last_refresh and last_refresh < 86400
		


# Returns second since last refresh.
def age_of(alliance_or_file):

	# If a name of an alliance is passed in, find the relevant alliance_info instead.
	# If alliance_info was passed in, just use it directly.
	alliance_info = find_cached_data(alliance_or_file) if type(alliance_or_file) is str else alliance_or_file

	# Use modification date info for the Alliance Info found.
	if alliance_info and type(alliance_info) is dict:
		last_refresh = time.time()-os.path.getmtime(alliance_info['file_path'])
	
	# Couldn't find a matching cached_data for this alliance, asking about a file instead?
	else:
		cached_file = get_local_path() + f'cached_data{os.sep}cached_{alliance_or_file}' 

		# Not a file either, return False.
		if not os.path.exists(cached_file):
			return False

		# Use modification date info for the file found.
		last_refresh = time.time()-os.path.getmtime(cached_file)

	# If it's less than 24 hours old, it's fresh enough.
	return last_refresh



# Handle the file list cleanly.
@timed(level=3)
def retire_cached_data(file_or_alliance=''):

	# Find the original file based on the alliance_name provided
	alliance_info = find_cached_data(file_or_alliance)
	
	# Pull out the resolved file path
	OLD_PATH = alliance_info.get('file_path')
	NEW_PATH = OLD_PATH.replace('\\cached_data-','\\OLD_DATA-')

	if os.path.exists(NEW_PATH):
		NEW_PATH += str(len(glob.glob(f'{NEW_PATH}*'))+1)

	# Attempt the rename of this file
	os.rename(OLD_PATH, NEW_PATH)



# Handle the file list cleanly.
@timed(level=3)
def find_cached_data(file_or_alliance=''):

	alliance_info = {}

	# Short circuit for bad data
	if type(file_or_alliance) is not str:
		return alliance_info

	# Something was passed in:
	if file_or_alliance:

		# Check the local directory for something named exactly this
		path, file = os.path.split(file_or_alliance)

		for file_list in [glob.glob(os.path.join(path,file)),
						  glob.glob(os.path.join(path,encode_tags(file)))]:
			if len(file_list) == 1:
				break
		
		# Check local directories and deeper
		if len(file_list) != 1:
		
			# Look in local directory, subdirectory named for alliance, and cached_data directory
			for local_path in [get_local_path(), get_local_path()+os.sep+file_or_alliance, get_local_path()+os.sep+'cached_data']:

				# Look for name with encoding, without encoding, and do a reverse search ignoring tags and encoding
				for file_list in [glob.glob(os.path.join(local_path,f'cached_data-{file_or_alliance}.msf')),
								  glob.glob(os.path.join(local_path,f'cached_data-{encode_tags(file_or_alliance)}.msf')),
								  [x for x in glob.iglob(os.path.join(local_path,f'cached_data-*.msf')) if remove_tags(decode_tags(x)).lower().endswith(f'{os.sep}cached_data-{file_or_alliance}.msf')]]:
					if len(file_list) == 1:
						break
				if len(file_list) == 1:
					break

	# No value passed in, check local directory for single cached_data.msf file
	else:
		file_list = glob.glob(os.path.join(get_local_path,'cached_data-*.msf'))

	# If a single MSF file was found, use it, otherwise search was ambiguous.
	if len(file_list) == 1:
		alliance_info = pickle.load(open(file_list[0],'rb'))

		# Stash the path away inside alliance_info for later use. 
		if type(alliance_info) is dict:
			alliance_info['file_path'] = os.path.realpath(file_list[0])
		
		# Update file paths if we're using entry from a subdirectory named for alliance
		if f'{os.sep+file_or_alliance+os.sep}' in file_list[0]:
			check_import_path(file_or_alliance)

	return alliance_info



# Define extra formats implicitly for each lane 
def add_formats_for_lanes(tables):
	
	# Check each format for multiple defined lanes.
	for format in list(tables):
		if len(tables[format].get('lanes',[])) > 1:

			# What is each Lane called? Lane X, Zone X, etc?
			lane_name = tables[format].get('lane_name', 'Lane')

			# Customize key, name, and lane definition
			for idx,lane in enumerate(tables[format]['lanes']):
				table_key = f'{format}_{lane_name.lower()}{idx+1}'
				tables[table_key] = copy.deepcopy(tables[format])
				tables[table_key]['name']  = f"{tables[format]['name']} {lane_name.title()} {idx+1}"
				tables[table_key]['lanes'] = [lane]



# Check to see if a subdirectory exists with this alliance_name and if it contains valid python files.
# If so, change the import path to include this directory and source the files to use their definitions.
@timed(level=3)
def check_import_path(alliance_name):
	
	global strike_teams
	global tables
	
	local_path = get_local_path()
	
	# Check to see if a subdirectory exists with this alliance_name and if it contains valid python files 
	if os.path.isfile(local_path+alliance_name+'\\strike_teams.py') or os.path.isfile(local_path+alliance_name+'\\raids_and_lanes.py'):

		# If so, change the import path to this path
		# For clarity, this entry was set by us (below) to force use of local strike_teams.py and raids_and_lanes.py when using a frozen executable. 
		# This change just points our extra / added path entry to the correct location for alliance-specific files.
		sys.path[0] = local_path+alliance_name

		# Pull Strike Team definitions from a subdirectory if available.
		if 'strike_temp' in globals():
			importlib.reload(strike_temp)
			strike_teams = strike_temp.strike_teams

		# Pull Raid and Lane (table) definitions from a subdirectory if available.
		if 'raids_and_lanes' in globals():
			importlib.reload(raids_and_lanes)
			add_formats_for_lanes(raids_and_lanes.tables)
			tables = raids_and_lanes.tables
	


# Insert the local directory at the front of path to override packaged versions.
sys.path.insert(0, get_local_path())

