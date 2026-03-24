#!/usr/bin/env python3
# Encoding: UTF-8
"""file_io.py
Routines for reading/writing files and cached_data to disk.
"""

import os
import sys
import time
import re
import pickle
import glob
import requests
import __main__

from pathlib  import Path
from selenium.webdriver.common.by import By
from urllib.parse import quote, unquote

try:
	from .log_utils   import *
	from .driver_pool import *
except:
	from  log_utils   import *
	from  driver_pool import *



#88      .d88888b.   .d8888b.        d8888 888           8888888b.     d8888 88888888888 888    888 
#88     d88P" "Y88b d88P  Y88b      d88888 888           888   Y88b   d88888     888     888    888 
#88     888     888 888    888     d88P888 888           888    888  d88P888     888     888    888 
#88     888     888 888           d88P 888 888           888   d88P d88P 888     888     8888888888 
#88     888     888 888          d88P  888 888           8888888P" d88P  888     888     888    888 
#88     888     888 888    888  d88P   888 888           888      d88P   888     888     888    888 
#88     Y88b. .d88P Y88b  d88P d8888888888 888           888     d8888888888     888     888    888 
#8888888 "Y88888P"   "Y8888P" d88P     888 88888888      888    d88P     888     888     888    888 



# Default value, use the local file path
local_path = os.path.dirname(__file__)

# If frozen, work in the same directory as the executable
if getattr(sys, 'frozen', False):
	local_path = os.path.dirname(sys.executable)
# If running from the Python interpreter, use the current working dir
elif hasattr(sys, 'ps1'):
	local_path = os.getcwd()
# If imported, work in the same directory as the importing file
elif hasattr(__main__, '__file__'):
	local_path = os.path.dirname(os.path.abspath(__main__.__file__))



# Provide a consistent base path for output
def get_local_path():
	global local_path
	
	return os.path.realpath(local_path) + os.sep



# Provide a consistent base path for output
def set_local_path(new_path):
	global local_path
	local_path = os.path.realpath(os.path.dirname(new_path)) + os.sep



#8888888888     d8888  .d8888b.       888    888        d8888 888b    888 8888888b.  888      8888888 888b    888  .d8888b.  
    #88        d88888 d88P  Y88b      888    888       d88888 8888b   888 888  "Y88b 888        888   8888b   888 d88P  Y88b 
    #88       d88P888 888    888      888    888      d88P888 88888b  888 888    888 888        888   88888b  888 888    888 
    #88      d88P 888 888             8888888888     d88P 888 888Y88b 888 888    888 888        888   888Y88b 888 888        
    #88     d88P  888 888  88888      888    888    d88P  888 888 Y88b888 888    888 888        888   888 Y88b888 888  88888 
    #88    d88P   888 888    888      888    888   d88P   888 888  Y88888 888    888 888        888   888  Y88888 888    888 
    #88   d8888888888 Y88b  d88P      888    888  d8888888888 888   Y8888 888  .d88P 888        888   888   Y8888 Y88b  d88P 
    #88  d88P     888  "Y8888P88      888    888 d88P     888 888    Y888 8888888P"  88888888 8888888 888    Y888  "Y8888P88 



REMOVE_TAGS = re.compile(r'<[^>]+>')


# Sanitize Alliance Names and player names of any HTML tags.
def remove_tags(text):

	# Cleaned text is without HTML tags. Also removing hashtags.
	cleaned = REMOVE_TAGS.sub('', text.replace('#','')).strip()

	# If nothing remains, then < > was decorative, return the original entry.
	return cleaned or text
	

# Ensure filename is valid for file system.
def encode_tags(filename):
	return quote(filename, safe="!#$%&'()+,;=@[]^`{}~ ")


# Translate filename from encoded form to readable.
def decode_tags(filename):
	return unquote(filename)



@timed(level=3)
def write_file(pathname, file_content, print_path=False):

	files_generated = []

	if type(file_content) is str:
		file_content = {'':file_content}

	for filename, content in file_content.items():

		# Get the actual path and filename (sanitize this path)
		path,file = os.path.split(remove_tags(pathname+filename))

		# Encode unsafe characters
		file = encode_tags(file)

		if print_path:
			print (f'Writing {format_filename(path,file)}')

		# Verify enclosing directory exists, if not, create it.
		if not os.path.exists(path):
			os.makedirs(path)

		# Default output is UTF-8. Attempt to use it as it's more compatible.
		try:
			open(os.path.join(path,file), 'w', encoding='utf-8').write(content)
		# UTF-16 takes up twice the space. Only use it as a fallback option if errors generated during write.
		except:
			open(os.path.join(path,file), 'w', encoding='utf-16').write(content)	

		files_generated.append(os.path.join(path,file))
		
	return files_generated



def format_filename(path,file):
	return f'{ansi.cyan}{path}{os.sep}{ansi.rst}{ansi.white}{file}{ansi.rst}'



  #8888b.        d8888  .d8888b.  888    888 8888888888 8888888b.       8888888b.        d8888 88888888888     d8888 
#88P  Y88b      d88888 d88P  Y88b 888    888 888        888  "Y88b      888  "Y88b      d88888     888        d88888 
#88    888     d88P888 888    888 888    888 888        888    888      888    888     d88P888     888       d88P888 
#88           d88P 888 888        8888888888 8888888    888    888      888    888    d88P 888     888      d88P 888 
#88          d88P  888 888        888    888 888        888    888      888    888   d88P  888     888     d88P  888 
#88    888  d88P   888 888    888 888    888 888        888    888      888    888  d88P   888     888    d88P   888 
#88b  d88P d8888888888 Y88b  d88P 888    888 888        888  .d88P      888  .d88P d8888888888     888   d8888888888 
 #Y8888P" d88P     888  "Y8888P"  888    888 8888888888 8888888P"       8888888P" d88P     888     888  d88P     888 
 
 

@timed(level=3)
def write_cached_data(alliance_info, file_path='', timestamp='update', filename='', encode=True):
	
	# If no file_path, provided get one out of alliance_info or use local dir as default.
	if not file_path:
		file_path = alliance_info.get('file_path', get_local_path())

	# Remove the file_path temporarily, before we write to disk.
	# Also permanently remove 'traits', 'trait_file', 'scripts', and 'portraits'.
	for key in ('file_path','traits','portraits','scripts','trait_file'):
		alliance_info.pop(key, None)

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
		
	file_path += f'{os.sep}cached_data-{file_name}.msf'
	
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
		cached_file = f'{get_local_path()}cached_data{os.sep}cached_{alliance_or_file}' 

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
def find_cached_data(file_or_alliance='SIGMA Infamously Strange'):

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
		file_list = glob.glob(file_or_alliance)
		
		# Check local directories and deeper
		if len(file_list) != 1:
		
			# Look in local directory, subdirectory named for alliance, and cached_data directory
			local_path = f'{get_local_path()}cached_data'

			# Find file even if marked retired
			for data_type in ['cached_data', 'OLD_DATA']:

				# Look for name with encoding, without encoding, and do a reverse search ignoring tags and encoding
				for file_list in [
									glob.glob(os.path.join(local_path,f'{data_type}-{encode_tags(file_or_alliance)}.msf')),
									[x for x in glob.iglob(os.path.join(local_path,f'{data_type}-*.msf')) if remove_tags(decode_tags(os.path.basename(x)[len(data_type)+1:])).lower() == f'{file_or_alliance}.msf'],
									glob.glob(os.path.join(local_path,f'{data_type}-{file_or_alliance}.msf')),
								  ]:
					if len(file_list) == 1:
						break
				if len(file_list) == 1:
					break

	# If a single MSF file was found, use it, otherwise search was ambiguous.
	if len(file_list) == 1:
		alliance_info = pickle.load(open(file_list[0],'rb'))

		# Stash the path away inside alliance_info for later use. 
		if type(alliance_info) is dict:
			alliance_info['file_path'] = os.path.realpath(file_list[0])

	return alliance_info



#88      .d88888b.   .d8888b.        d8888 888           8888888 888b     d888  .d8888b.        .d8888b.        d8888  .d8888b.  888    888 8888888888 
#88     d88P" "Y88b d88P  Y88b      d88888 888             888   8888b   d8888 d88P  Y88b      d88P  Y88b      d88888 d88P  Y88b 888    888 888        
#88     888     888 888    888     d88P888 888             888   88888b.d88888 888    888      888    888     d88P888 888    888 888    888 888        
#88     888     888 888           d88P 888 888             888   888Y88888P888 888             888           d88P 888 888        8888888888 8888888    
#88     888     888 888          d88P  888 888             888   888 Y888P 888 888  88888      888          d88P  888 888        888    888 888        
#88     888     888 888    888  d88P   888 888             888   888  Y8P  888 888    888      888    888  d88P   888 888    888 888    888 888        
#88     Y88b. .d88P Y88b  d88P d8888888888 888             888   888   "   888 Y88b  d88P      Y88b  d88P d8888888888 Y88b  d88P 888    888 888        
#8888888 "Y88888P"   "Y8888P" d88P     888 88888888      8888888 888       888  "Y8888P88       "Y8888P" d88P     888  "Y8888P"  888    888 8888888888 



# Cache file if not already, return rel path to local cache
def local_img_cache(url, req_html=False):

	# Where should assets be downloaded to for local caching?
	asset_cache = f'{get_local_path()}images{os.sep}assets{os.sep}'
	if not os.path.exists(asset_cache):
		os.makedirs(asset_cache)

	file_path = f'{asset_cache}{Path(url).name}'
	
	if not os.path.exists(file_path):
		try:
			response = requests.get(url, stream=True)
			response.raise_for_status()  # Raises an HTTPError for bad responses
			with open(file_path, 'wb') as file:
				for chunk in response.iter_content(chunk_size=8192):
					file.write(chunk)

			print (f'{ansi.ltyel}Caching locally:{ansi.rst} {ansi.gray}{url=:90} => ../images/assets/{ansi.rst}{ansi.white}{Path(url).name}{ansi.rst}')

		# If download fails, delete any partial file and return url instead
		except requests.exceptions.RequestException as e:

			# Notify of failure
			print(f"{ansi.ltred}Error downloading file:{ansi.rst} {ansi.white}{e}{ansi.rst}")

			# Clean up any partial file
			if os.path.exists(file_path):
				os.remove(file_path)

			# Advise use of URL instead
			return url

	return url if req_html else f'../images/assets/{Path(url).name}'
	


#88    888 88888888888 888b     d888 888           88888888888 .d88888b.       8888888 888b     d888        d8888  .d8888b.  8888888888 .d8888b.  
#88    888     888     8888b   d8888 888               888    d88P" "Y88b        888   8888b   d8888       d88888 d88P  Y88b 888       d88P  Y88b 
#88    888     888     88888b.d88888 888               888    888     888        888   88888b.d88888      d88P888 888    888 888       Y88b.      
#888888888     888     888Y88888P888 888               888    888     888        888   888Y88888P888     d88P 888 888        8888888    "Y888b.   
#88    888     888     888 Y888P 888 888               888    888     888        888   888 Y888P 888    d88P  888 888  88888 888           "Y88b. 
#88    888     888     888  Y8P  888 888               888    888     888        888   888  Y8P  888   d88P   888 888    888 888             "888 
#88    888     888     888   "   888 888               888    Y88b. .d88P        888   888   "   888  d8888888888 Y88b  d88P 888       Y88b  d88P 
#88    888     888     888       888 88888888          888     "Y88888P"       8888888 888       888 d88P     888  "Y8888P88 8888888888 "Y8888P"  



@timed(level=3)
def html_to_images(html_files, proc_name='msf2csv', print_path=False, render_wait=0.1, output_path=None):

	# Handle base case of single file or URL
	if type(html_files) == str:
			html_files = [html_files]
	
	files_generated = []

	# Start by getting a Selenium driver
	driver = get_driver(proc_name)

	failed_drivers = []

	# The html_files list contains paths to the html files.
	for file in html_files:
		
		# If we have any issues, try again until we hit 3 failures
		while len(failed_drivers) < 3:
			try:
				show_driver_pool('before html_to_images')
				
				# Start by opening each file with our Selenium driver.
				driver.get(file if 'http' in file else Path(file).as_uri())
	
				#print (f'Generating image with Driver PID: {driver.pid:>5}')
	
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
		
				# Increment the image_count
				driver.times_used += 1
		
				break
			except Exception as exc:
				
				print (f'EXCEPTION: {exc}')
				
				# Take note of any driver issues, will kill at the end
				failed_drivers.append(driver)
					
				# Get another driver and try it again
				driver = None if len(failed_drivers) == 3 else get_driver(proc_name)

	# If any failures, kill their process trees
	kill_process_tree([x.pid for x in failed_drivers])
	
	# Put the driver back in the avail_pool for reuse
	release_driver(driver, failed_drivers)

	# no driver == failed 3x, raise exception
	if not driver:
		raise

	return files_generated



  #8888b.  888      8888888888        d8888 888b    888 888     888 8888888b.        .d88888b.  888      8888888b.       8888888888 8888888 888      8888888888 .d8888b.  
#88P  Y88b 888      888              d88888 8888b   888 888     888 888   Y88b      d88P" "Y88b 888      888  "Y88b      888          888   888      888       d88P  Y88b 
#88    888 888      888             d88P888 88888b  888 888     888 888    888      888     888 888      888    888      888          888   888      888       Y88b.      
#88        888      8888888        d88P 888 888Y88b 888 888     888 888   d88P      888     888 888      888    888      8888888      888   888      8888888    "Y888b.   
#88        888      888           d88P  888 888 Y88b888 888     888 8888888P"       888     888 888      888    888      888          888   888      888           "Y88b. 
#88    888 888      888          d88P   888 888  Y88888 888     888 888             888     888 888      888    888      888          888   888      888             "888 
#88b  d88P 888      888         d8888888888 888   Y8888 Y88b. .d88P 888             Y88b. .d88P 888      888  .d88P      888          888   888      888       Y88b  d88P 
  #8888P"  88888888 8888888888 d88P     888 888    Y888  "Y88888P"  888              "Y88888P"  88888888 8888888P"       888        8888888 88888888 8888888888 "Y8888P"  



# Default cleanup is any files older than 24 hours
def cleanup_old_files(local_path, age=1, ext=''):
	try:
		# Get just the base path if a filename has been passed in
		if not os.path.isdir(local_path):
			local_path = os.path.dirname(local_path)

		# Age in days
		cutoff_date = time.time() - age * 24 * 3600

		# Process files just in explicit path, no dirs and no deeper
		for item in Path(local_path).expanduser().glob(f'*{ext}'):
			if item.is_file():
				if os.stat(item).st_mtime < cutoff_date:
					#print (f'{ansi.bold}Deleting:{ansi.rst} {item}')
					os.remove(item)

	# Catch all exceptions. Don't let this be a reason for failure
	except Exception as exc:
		print (f'{ansi.ltred}EXCEPTION:{ansi.rst} {ansi.gray}{type(exc).__name__}: {exc}{ansi.rst}')
