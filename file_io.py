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
import requests

try:	import strike_teams as strike_temp
except:	pass

try:	import raids_and_lanes
except:	pass

from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import quote, unquote
from pathlib import Path
from datetime import datetime



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
	


def get_local_path():
	# If not frozen, work in the same directory as this script.
	path = os.path.dirname(__file__)

	# If frozen, work in the same directory as the executable.
	if getattr(sys, 'frozen', False):
		path = os.path.dirname(sys.executable)

	return os.path.realpath(path) + os.sep



@timed(level=3)
def write_file(pathname, file_content, print_path=False):

	files_generated = []

	if type(file_content) is str:
		file_content = {'':file_content}

	for filename in file_content:

		# Get the actual path and filename (sanitize this path)
		path,file = os.path.split(remove_tags(pathname+filename))

		# Encode unsafe characters
		file = encode_tags(file)

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
def html_to_images(html_files, proc_name='msf2csv', print_path=False, render_wait=0.1, output_path=None):

	# Handle base case of single file or URL
	if type(html_files) == str:
			html_files = [html_files]
	
	files_generated = []

	# Start by getting a Selenium driver
	driver = get_driver(proc_name)

	# The html_files list contains paths to the html files.
	for file in html_files:
		# Start by opening each file with our Selenium driver.
		driver.get(file if 'http' in file else Path(file).as_uri())

		# Give it just a moment to render the page.
		#time.sleep(render_wait)

		# Set the height/width of the window accordingly
		height = driver.execute_script('return document.documentElement.scrollHeight')
		width  = driver.execute_script('return document.documentElement.scrollWidth')

		# Look for the farthest right element.
		tables = driver.find_elements(By.TAG_NAME, "table")
		
		min_width = 360
		for table_idx, table in enumerate(tables):
			min_width = max(table.rect['x']+table.rect['width'], min_width)

		driver.set_window_size(min_width+40, height+450)

		png_filename = f'{output_path}{os.path.basename(file)}.png' if output_path else f'{file[:-5]}.png'

		# Report the file being written.
		if print_path:
			print (f"Writing {format_filename(png_filename)}")

		# Then use Selenium to render these pages to disk as images. 
		body = driver.find_element(By.TAG_NAME, "body")
		body.screenshot(png_filename)
		files_generated.append(png_filename)
		
		"""# Finally, clean up the original files. 
		try:
			os.remove(file)
		except Exception as exc:
			print (f"EXCEPTION: {type(exc).__name__}: {exc}")
		"""

	# Put the driver back in the avail_pool for reuse
	release_driver(driver)

	return files_generated



def format_filename(filename):
	return f'{ansi.cyan}{os.path.dirname(filename)}{os.sep}{ansi.rst}{ansi.white}{os.path.basename(filename)}{ansi.rst}'



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
def load_cached_file(file):
	data={}

	# Load the requested information if it exists
	file_path = get_local_path() + f'cached_data{os.sep}defaults{os.sep}cached_{file}'

	if os.path.exists(file_path):
		data = pickle.load(open(file_path,'rb'))

	return data



# Load a pickled cache file from cached_data directory
def write_cached_file(data, file):

	# Ensure the enclosing directory exists.
	cached_path = get_local_path() + f'cached_data{os.sep}defaults{os.sep}'

	if not os.path.exists(cached_path):
		os.makedirs(cached_path)	

	pickle.dump(data, open(cached_path + f'cached_{file}', 'wb'))



# Has it been less than 24 hours since last update of cached_data?
def fresh_enough(alliance_or_file):

	last_refresh = age_of_cached_data(alliance_or_file)

	return last_refresh and last_refresh < 86400
		


# Returns second since last refresh.
def age_of_cached_data(alliance_or_file):

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
def retire_cached_data(file_or_alliance=''):

	# Find the original file based on the alliance_name provided
	alliance_info = find_cached_data(file_or_alliance)
	
	# Short circuit if nothing found
	if not alliance_info:
		return
	
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

	# Short circuit if alliance_info provided for name
	if type(file_or_alliance) is dict and file_or_alliance.get('name'):
		return file_or_alliance

	# Short circuit for bad data
	elif type(file_or_alliance) is not str:
		return alliance_info

	# Something was passed in:
	elif file_or_alliance:

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

				# Find file even if marked retired
				for data_type in ['cached_data', 'OLD_DATA']:

					# Look for name with encoding, without encoding, and do a reverse search ignoring tags and encoding
					for file_list in [glob.glob(os.path.join(local_path,f'{data_type}-{file_or_alliance}.msf')),
									  glob.glob(os.path.join(local_path,f'{data_type}-{encode_tags(file_or_alliance)}.msf')),
									  [x for x in glob.iglob(os.path.join(local_path,f'{data_type}-*.msf')) if remove_tags(decode_tags(x)).lower().endswith(f'{os.sep}{data_type}-{file_or_alliance}.msf')]]:
						if len(file_list) == 1:
							break
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
	if os.path.isfile(local_path+alliance_name+os.sep+'strike_teams.py') or os.path.isfile(local_path+alliance_name+os.sep+'raids_and_lanes.py'):

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



#888888b.  8888888b.  8888888 888     888 8888888888 8888888b.       8888888b.   .d88888b.   .d88888b.  888
#88  "Y88b 888   Y88b   888   888     888 888        888   Y88b      888   Y88b d88P" "Y88b d88P" "Y88b 888
#88    888 888    888   888   888     888 888        888    888      888    888 888     888 888     888 888
#88    888 888   d88P   888   Y88b   d88P 8888888    888   d88P      888   d88P 888     888 888     888 888
#88    888 8888888P"    888    Y88b d88P  888        8888888P"       8888888P"  888     888 888     888 888
#88    888 888 T88b     888     Y88o88P   888        888 T88b        888        888     888 888     888 888
#88  .d88P 888  T88b    888      Y888P    888        888  T88b       888        Y88b. .d88P Y88b. .d88P 888
#888888P"  888   T88b 8888888     Y8P     8888888888 888   T88b      888         "Y88888P"   "Y88888P"  88888888



driver_pool = {}

# Keep drivers open and allow them to be re-used.
@timed(level=3)
def get_driver(proc_name='', force_new=False):
	global driver_pool

	# Create the active and avail pools if necessary
	active_pool = driver_pool.setdefault('active',{})
	avail_pool  = driver_pool.setdefault('avail',{})

	driver = None

	# There's a driver available already, provide the existing driver
	if avail_pool and not force_new:
		
		# Grab the available driver, don't fail if we miss
		driver = avail_pool.pop(list(avail_pool)[0], None)

	# If we didn't find an available driver, create a new one
	if not driver:
		driver = create_new_driver(proc_name)

	# If we have a driver...
	if driver:
		# Add one to its body count
		driver.times_used += 1

		# Note job start time in the driver
		driver.last_used = datetime.now()
		
		# Use job start time as key in the active pool
		active_pool[driver.last_used] = driver

	return driver



# Create a Selenium driver if requested
def create_new_driver(proc_name):
	options = webdriver.ChromeOptions()

	# Indicate which process launched this driver
	options.add_argument(f'--window-name="{proc_name}"')

	# Add all the important options
	options.add_argument('--headless=new')
	options.add_argument('--no-sandbox')
	options.add_argument('--disable-dev-shm-usage')
	options.add_argument('--disable-gpu')
	options.add_argument('--disable-extensions')
	service = webdriver.ChromeService(service_args=["--enable-chrome-logs"])

	# For linux, explicitly specify the chromedriver to use
	if os.name == 'posix':
		service.path = '/usr/bin/chromedriver'

	# Actually create the driver
	driver = webdriver.Chrome(service=service, options=options)

	# Set internal info on driver with initial values
	driver.pid        = driver.service.process.pid
	driver.last_used  = driver.creation_date = datetime.now()
	driver.times_used = 0
	
	return driver



# Check driver in at the end of use.
@timed(level=3)
def release_driver(driver):
	global driver_pool

	# If no driver was issued, nothing to do.
	if not driver:
		return

	# Create the active and avail pools if necessary
	active_pool = driver_pool.setdefault('active',{})
	avail_pool  = driver_pool.setdefault('avail',{})

	creation_date = driver.creation_date
	last_used     = driver.last_used

	# If there's no driver available in the avail_pool, just check this one in.
	avail_pool[creation_date] = active_pool.pop(last_used)
			
	return



#88      .d88888b.   .d8888b.        d8888 888           8888888 888b     d888  .d8888b.        .d8888b.        d8888  .d8888b.  888    888 8888888888 
#88     d88P" "Y88b d88P  Y88b      d88888 888             888   8888b   d8888 d88P  Y88b      d88P  Y88b      d88888 d88P  Y88b 888    888 888        
#88     888     888 888    888     d88P888 888             888   88888b.d88888 888    888      888    888     d88P888 888    888 888    888 888        
#88     888     888 888           d88P 888 888             888   888Y88888P888 888             888           d88P 888 888        8888888888 8888888    
#88     888     888 888          d88P  888 888             888   888 Y888P 888 888  88888      888          d88P  888 888        888    888 888        
#88     888     888 888    888  d88P   888 888             888   888  Y8P  888 888    888      888    888  d88P   888 888    888 888    888 888        
#88     Y88b. .d88P Y88b  d88P d8888888888 888             888   888   "   888 Y88b  d88P      Y88b  d88P d8888888888 Y88b  d88P 888    888 888        
#8888888 "Y88888P"   "Y8888P" d88P     888 88888888      8888888 888       888  "Y8888P88       "Y8888P" d88P     888  "Y8888P"  888    888 8888888888 



# Where should assets be downloaded to for local caching?
asset_cache = f'{os.path.dirname(__file__)}{os.sep}cached_data{os.sep}reports{os.sep}assets{os.sep}'
if not os.path.exists(asset_cache):
	os.makedirs(asset_cache)



# Cache file if not already, return rel path to local cache
def local_img_cache(url, req_html=False):

	file_path = f'{asset_cache}{Path(url).name}'
	
	if not os.path.exists(file_path):
		try:
			response = requests.get(url, stream=True)
			response.raise_for_status()  # Raises an HTTPError for bad responses
			with open(file_path, 'wb') as file:
				for chunk in response.iter_content(chunk_size=8192):
					file.write(chunk)

			print (f'{ansi.ltyel}Caching locally:{ansi.rst} {ansi.gray}{url=} => ./assets/{ansi.rst}{ansi.white}{Path(url).name}{ansi.rst}')

		# If download fails, delete any partial file and return url instead
		except requests.exceptions.RequestException as e:

			# Notify of failure
			print(f"{ansi.ltred}Error downloading file:{ansi.rst} {ansi.white}{e}{ansi.rst}")

			# Clean up any partial file
			if os.path.exists(file_path):
				os.remove(file_path)

			# Advise use of URL instead
			return url

	return url if req_html else f'./assets/{Path(url).name}'



# Insert the local directory at the front of path to override packaged versions.
sys.path.insert(0, get_local_path())

