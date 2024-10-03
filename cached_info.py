#!/usr/bin/env python3
# Encoding: UTF-8
"""cached_info.py
Create a global cached_info structure.  
"""
from log_utils import *

from copy import copy, deepcopy

from file_io import load_cached_file, write_cached_file


# Load up the cached_info global at launch.
cached_info = {}

# Just return a value from the global
@timed(level=3)
def get_cached(key):
	global cached_info

	# Load at first request - 'char_list','char_lookup','portraits','trait_list','traits'
	if key not in cached_info:
		cached_info[key] = load_cached_file(key)
	
	return deepcopy(cached_info.get(key))
	


# Update the global with a deepcopy of any value passed in and write to disk.
@timed(level=3)
def set_cached(key,value):
	global cached_info
	
	cached_info[key] = deepcopy(value)
	
	write_cached_file(value, key)



