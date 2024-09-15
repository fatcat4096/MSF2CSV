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

try:	import strike_teams as strike_temp
except:	pass

try:	import raids_and_lanes
except:	pass

from selenium import webdriver
from selenium.webdriver.common.by import By


TAG_RE = re.compile(r'<[^>]+>')


# Sanitize Alliance Names and player names of any HTML tags.
def remove_tags(text):

	# Cleaned text is without HTML tags. Also removing hashtags.
	cleaned = TAG_RE.sub('', text.replace('#',''))

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

	# Sanitize to remove HTML tags.
	pathname = remove_tags(pathname)

	for file in file_content:

		filename = remove_tags(pathname+file)

		if print_path:
			print ("Writing %s" % (filename))

		# Verify enclosing directory exists, if not, create it.
		if not os.path.exists(os.path.dirname(pathname)):
			os.makedirs(os.path.dirname(pathname))

		# Default output is UTF-8. Attempt to use it as it's more compatible.
		try:
			open(filename, 'w', encoding='utf-8').write(file_content[file])
		# UTF-16 takes up twice the space. Only use it as a fallback option if errors generated during write.
		except:
			open(filename, 'w', encoding='utf-16').write(file_content[file])	

		files_generated.append(filename)
		
	return files_generated



@timed(level=3)
def html_to_images(html_files=[], print_path=True):
	
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
		time.sleep(0.1)
		
		# Set the height/width of the window accordingly
		height = driver.execute_script('return document.documentElement.scrollHeight')
		width  = driver.execute_script('return document.documentElement.scrollWidth')

		# Look for the farthest right element.
		tables = driver.find_elements(By.TAG_NAME, "table")
		
		min_width = 400
		for table_idx, table in enumerate(tables):
			min_width = max(table.rect['x']+table.rect['width'], min_width)

			# If we've exceeded the right edge of the frame, no need to crop. 
			if min_width >= width:
				#print ('width exceeded. Index:',table_idx, 'table:',table.rect, 'min_width:',min_width, 'width:',width)
				break

		driver.set_window_size(min(width,min_width)+22, height+450)

		png_filename = file[:-4]+'png'

		# Report the file being written.
		if print_path:
			print ("Writing %s" % (png_filename))		

		# Then use Selenium to render these pages to disk as images. 
		body = driver.find_element(By.TAG_NAME, "body")
		body.screenshot(png_filename)
		files_generated.append(png_filename)

		# Close the driver to prevent memory leaks.
		driver.close()

		# Finally, clean up the original files. 
		os.remove(file)

	return files_generated



@timed(level=3)
def load_cached_data(file_or_alliance=''):
	cached_data = {}

	# Remove any HTML tags in the provided input
	file_or_alliance = remove_tags(file_or_alliance)

	# If the provided filename wasn't a valid file, let's go looking for it.
	if not os.path.exists(file_or_alliance):
		local_path = get_local_path()

		# If Alliance Name was passed in, fix it.
		if '.msf' not in file_or_alliance:
			file_or_alliance = 'cached_data-'+file_or_alliance+'.msf'

		# Look in local directory.
		if os.path.exists(local_path + file_or_alliance):
			file_or_alliance = local_path + file_or_alliance
	
		# If a cached_data directory exists, search it.
		elif os.path.exists(local_path + 'cached_data') and os.path.exists(local_path + 'cached_data' + os.sep + file_or_alliance):
			file_or_alliance = local_path + 'cached_data' + os.sep + file_or_alliance

	# If a file was found, load it.
	if os.path.exists(file_or_alliance):
		cached_data = pickle.load(open(file_or_alliance,'rb'))

		# Stash the path away inside alliance_info for later use. 
		if type(cached_data) is dict:
			cached_data['file_path'] = os.path.realpath(file_or_alliance)

	return cached_data



@timed(level=3)
def write_cached_data(alliance_info, file_path='', timestamp='update', filename=''):
	
	# If no file_path, provided get one out of alliance_info or use local dir as default.
	if not file_path:
		file_path = alliance_info.get('file_path', get_local_path())

	# Remove the file_path temporarily, before we write to disk.
	# Also permanently remove 'traits' and 'portraits'.
	for key in ('file_path','traits','portraits'):
		if key in alliance_info:
			del alliance_info[key]

	# Ensure we are just using the path name
	if os.path.isfile(file_path):
		file_path = os.path.realpath(os.path.dirname(file_path))

	# Ensure the enclosing directory exists.
	if not os.path.exists(file_path):
		os.makedirs(file_path)
	
	alliance_name = get_alliance_name(alliance_info)

	# Construct the file name
	file_path += os.sep + 'cached_data-' + (filename or alliance_name) + '.msf'
	
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

	file_path = get_local_path() + f'cached_data{os.sep}cached_{file}'

	if os.path.exists(file_path):
		data = pickle.load(open(file_path,'rb'))

	return data



# Load a pickled cache file from cached_data directory
@timed(level=3)
def write_cached_file(data, file):

	# Ensure the enclosing directory exists.
	cached_path = get_local_path() + f'cached_data{os.sep}'
	if not os.path.exists(cached_path):
		os.makedirs(cached_path)	

	pickle.dump(data, open(cached_path + f'cached_{file}', 'wb'))



# Has it been less than 24 hours since last update of cached_data?
@timed(level=3)
def fresh_enough(alliance_or_file):

	last_refresh = age_of(alliance_or_file) < 86400

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
def find_cached_data(file_or_alliance=''):

	alliance_info = {}

	# Remove any HTML tags in the provided input
	file_or_alliance = remove_tags(file_or_alliance)
	
	# If a valid MSF filename passed in, use it as the only entry in file_list.
	if file_or_alliance[-4:] == ('.msf') and os.path.isfile(file_or_alliance):
		file_list = [file_or_alliance]

	# If an Alliance name was specified, look for that specific Alliance name.
	elif file_or_alliance:
		check_import_path(file_or_alliance)
		file_name = 'cached_data-'+file_or_alliance+'.msf'
		file_list = [file_name] if os.path.isfile(file_name) else []
	# Just look at the local directory for any file matching our naming format.
	else:
		file_list = [file for file in os.listdir(get_local_path()) if os.path.isfile(file) and file.startswith('cached_data-') and file.endswith('.msf')]

	# If alliance_name provided but didn't find a conclusive result, go deeper 
	if len(file_list) != 1 and file_or_alliance:

		# Search 1) a folder named `alliance_name` and 2) the cached_data directory, if either exists.
		for file_path in [get_local_path()+file_or_alliance+os.sep, get_local_path()+'cached_data'+os.sep]:
			if os.path.isdir(file_path) and os.path.isfile(file_path+file_name):
				file_list = [file_path+file_name]
				break
	
	# If a single MSF file was found, use it, otherwise search was inconclusive.
	if len(file_list) == 1:
		alliance_info = load_cached_data(file_list[0])
		
	return alliance_info



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
			tables = raids_and_lanes.tables



# Offer standardized process for building alliance name from alliance_info data.
def get_alliance_name(alliance_info):

	alliance_name = remove_tags(alliance_info['name'])

	if alliance_info.get('color'):
		alliance_name += '-' + alliance_info.get('color')
	
	return alliance_name
	


# Insert the local directory at the front of path to override packaged versions.
sys.path.insert(0, get_local_path())

