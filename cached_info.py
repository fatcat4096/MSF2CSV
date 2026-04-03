#!/usr/bin/env python3
# Encoding: UTF-8
"""cached_info.py
Create a global cached_info structure.  
"""


import os
import pickle


from copy import copy, deepcopy


try:
	from .file_io   import get_local_path
except ModuleNotFoundError:
	from  file_io   import get_local_path


# Load up the cached_info global at launch.
cached_info = {}

# Load a pickled cache file from cached_data directory
def load_cached_file(file):
	data={}

	# Load the requested information if it exists
	file_path = f'{get_local_path()}cached_data{os.sep}defaults{os.sep}cached_{file}'

	if os.path.exists(file_path):
		data = pickle.load(open(file_path,'rb'))

	return data



# Load a pickled cache file from cached_data directory
def write_cached_file(data, file):

	# Ensure the enclosing directory exists.
	cached_path = f'{get_local_path()}cached_data{os.sep}defaults{os.sep}'

	if not os.path.exists(cached_path):
		os.makedirs(cached_path)	

	pickle.dump(data, open(f'{cached_path}cached_{file}', 'wb'))



# Just return a value from the global
def get_cached(key, refresh=False):
	global cached_info

	# Load at first request - 'char_list','char_lookup','portraits','trait_list','traits'
	if key not in cached_info or refresh:
		cached_info[key] = load_cached_file(key)
	
	return deepcopy(cached_info.get(key))
	


# Update the global with a deepcopy of any value passed in and write to disk.
def set_cached(key,value):
	global cached_info
	
	cached_info[key] = deepcopy(value)
	
	write_cached_file(value, key)



