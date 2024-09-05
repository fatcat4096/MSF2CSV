#!/usr/bin/env python3
# Encoding: UTF-8
"""cached_info.py
Create a global cached_info structure.  
"""
from copy import copy, deepcopy

from file_io import load_cached_file, write_cached_file


# Load up the cached_info global at launch.
cached_info = {}
for key in ('char_list','char_lookup','portraits','trait_list','traits'):
	cached_info[key] = load_cached_file(key)



# Just return a value from the global
def get_cached(key):
	global cached_info
	
	return copy(cached_info.get(key))
	


# Update the global with a deepcopy of any value passed in and write to disk.
def set_cached(key,value):
	global cached_info
	
	cached_info[key] = deepcopy(value)
	
	write_cached_file(value, key)



