#!/usr/bin/env python3
# Encoding: UTF-8
"""extract_traits.py
Quick hack to pull live trait data from MSF.gg
"""

import urllib.request

def extract_traits():
	page = urllib.request.urlopen('https://marvelstrikeforce.com/static/js/2.8f35720e0540d0dc8fb8.js')
	buffer = str(page.read())

	chars_from_trait = {}

	start_idx = 0
	while buffer.find('Playable',start_idx+1) != -1:
		# Find first character
		start_idx = buffer.find('Playable',start_idx+1)
		# Look backward to find the name.
		char_idx = buffer.rfind('Name:"',0,start_idx)+6
		char_end = buffer.find('"',char_idx)
		char     = buffer[char_idx:char_end]
		# Look forward to find the traits.
		traits_idx = buffer.find('traits:',start_idx)+7
		traits_end = buffer.find(']',traits_idx)+1
		traits     = eval(buffer[traits_idx:traits_end])
		#
		for trait in traits:
			chars_from_trait.setdefault(trait,{})
			chars_from_trait[trait][char]=1

	return chars_from_trait


# Pull trait info from msf.gg
chars_from_trait = extract_traits()