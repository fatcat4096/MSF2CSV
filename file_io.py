#!/usr/bin/env python3
# Encoding: UTF-8
"""file_io.py
Routines for reading/writing files and cached_data to disk.
"""


import os
import sys
import re
import pickle

from selenium import webdriver
from selenium.webdriver.common.by import By

TAG_RE = re.compile(r'<[^>]+>')


# Sanitize Alliance Names and player names of any HTML tags.
def remove_tags(text):
    return TAG_RE.sub('', text)
	

def get_local_path():
	# If not frozen, work in the same directory as this script.
	path = os.path.dirname(__file__)

	# If frozen, work in the same directory as the executable.
	if getattr(sys, 'frozen', False):
		path = os.path.dirname(sys.executable)

	return os.path.realpath(path) + os.sep
	
	
def write_file(filename, content, print_path=True):

	# Sanitize to remove HTML tags.
	filename = remove_tags(filename)
	if print_path:
		print ("Writing %s" % (filename))

	# Default output is UTF-8. Attempt to use it as it's more compatible.
	try:
		open(filename, 'w').write(content)
	# UTF-16 takes up twice the space. Only use it as a fallback option if errors generated during write.
	except:
		open(filename, 'w', encoding='utf-16').write(content)	


def write_image_files(pathname, html_files={}, print_path=True):
	
	files_generated = []
	
	# Start by creating a Selenium driver.
	options = webdriver.ChromeOptions()
	options.add_argument('--log-level=3')
	options.add_argument('--headless=new')
	options.add_experimental_option('excludeSwitches', ['enable-logging'])


	# The html_files dict contains multiple html files
	for file in html_files:
		
		driver = webdriver.Chrome(options=options)

		# Start by writing each to disk.
		write_file(pathname+file+'.html', html_files[file], False)

		# Next, open the file with our Selenium driver.
		driver.get(r'file:///'+pathname+file+'.html')
		
		# Set the height/width of the window accordingly
		height = driver.execute_script('return document.documentElement.scrollHeight')
		width  = driver.execute_script('return document.documentElement.scrollWidth')
		driver.set_window_size(width+20, height+450)

		# Report the file being written.
		if print_path:
			print ("Writing %s" % (pathname+file+'.png'))		

		# Then use Selenium to render these pages to disk as images. 
		body = driver.find_element(By.TAG_NAME, "body")
		body.screenshot(pathname+file+'.png')
		files_generated.append(pathname+file+'.png')

		# Finally, clean up the original files. 
		os.remove(pathname+file+'.html')

	return files_generated


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


def write_cached_data(alliance_info, file_path=''):
	
	# If no file_path, provided get one out of alliance_info or use local dir as default.
	if not file_path:
		file_path = alliance_info.get('file_path', get_local_path())

	# Remove the file_path temporarily, before we write to disk.
	if 'file_path' in alliance_info:
		del alliance_info['file_path']

	# Ensure we are just using the path name
	if os.path.isfile(file_path):
		file_path = os.path.realpath(os.path.dirname(file_path))

	# Ensure the enclosing directory exists.
	if not os.path.exists(file_path):
		os.makedirs(file_path)
	
	# Construct the file name
	file_name = 'cached_data-'+remove_tags(alliance_info['name'])+'.msf'
	
	# Write the .msf file. 
	pickle.dump(alliance_info,open(file_path + os.sep + file_name, 'wb'))
	
	# Stash the path and filename inside of alliance_info. 
	alliance_info['file_path'] = file_path + os.sep + file_name


# Handle the file list cleanly.
def find_cached_data(file_or_alliance=''):

	alliance_info = {}

	# Remove any HTML tags in the provided input
	file_or_alliance = remove_tags(file_or_alliance)
	
	# If a valid MSF filename passed in, use it as the only entry in file_list.
	if file_or_alliance[-4:] == ('.msf') and os.path.exists(file_or_alliance) and os.path.isfile(file_or_alliance):
		file_list = [file_or_alliance]

	# Start our search with a list of all the MSF files in the local directory.
	else:
		file_list = [file for file in os.listdir(get_local_path()) if os.path.isfile(file) and 'cached_data' in file and file_or_alliance+'.msf' in file]
	
	# If alliance_name provided but didn't find a conclusive result, go deeper 
	if len(file_list) != 1 and file_or_alliance:

		# Search the cached_data directory if it exists.
		file_path = get_local_path()+'cached_data'+os.sep
		if os.path.exists(file_path) and os.path.isdir(file_path):
			file_list = [file_path+file for file in os.listdir(file_path) if os.path.isfile(file_path+file) and 'cached_data-' in file and file_or_alliance+'.msf' in file]
	
	# If a single MSF file was found, use it, otherwise search was inconclusive.
	if len(file_list) == 1:
		alliance_info = load_cached_data(file_list[0])
		
	return alliance_info


# Insert the local directory at the front of path to override packaged versions.
sys.path.insert(0, get_local_path())