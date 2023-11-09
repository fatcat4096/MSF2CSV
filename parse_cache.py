#!/usr/bin/env python3
# Encoding: UTF-8
"""parse_cache.py
Routines used to build and update the parse cache.  

These are used to de-duplicate entries in the historical data structures of alliance_info.
"""

# Create a cache of entries to optimize our cached_data.
def build_parse_cache(alliance_info, parse_cache):

	# Let's process these Historical entries in chronological order. 
	hist_list = sorted(alliance_info.get('hist',[]))

	for entry in hist_list:

		# Iterate through all the members and chars from this history entry.
		for member in alliance_info['hist'][entry]:
		
			member_info = alliance_info['hist'][entry][member]

			for char in member_info:

				# Skip the tot_power and last_updated entries.
				if type(member_info[char]) is not dict:
					continue

				# Index everything by power.
				power = member_info[char]['power']

				# Convert old format to the new, only needs to be done once.
				if type(power) is str:
					for key in member_info[char]:
						member_info[char][key] = int(member_info[char][key])
					power = int(power)
					
				# Get a list of other entries already added at this same power.
				cached_entries = parse_cache.setdefault(power,[])

				# If this entry already exists, update the current entry to point at the cached one.
				if member_info[char] in cached_entries:
						member_info[char] = cached_entries[cached_entries.index(member_info[char])]
						continue

				# Otherwise, add the current entry to cached entry list.
				cached_entries.append(member_info[char])

	# After History has been processed. Update alliance_info['members'][member]['processed_chars'] with the same info.
	for member in alliance_info['members']:
	
		processed_chars = alliance_info['members'][member].get('processed_chars',[])

		# Iterate through characters in the members with rosters.
		for char in processed_chars:

			# Skip the tot_power and last_updated entries.
			if type(processed_chars[char]) is not dict:
				continue

			# Index everything by power.
			power = processed_chars[char]['power']

			# Get a list of other entries already added at this same power.
			cached_entries = parse_cache.setdefault(power,[])

			# If this entry already exists, update the current entry to point at the cached one.
			if processed_chars[char] in cached_entries:
					processed_chars[char] = cached_entries[cached_entries.index(processed_chars[char])]
					continue

			# Otherwise, add the current entry to cached entry list.
			cached_entries.append(processed_chars[char])


# Update parse_cache if this is a new entry.
# Updat the entry if already in the parse_cache
def update_parse_cache(processed_chars,char_name,parse_cache):
	
	# Will index everything by power.
	power = processed_chars[char_name]['power']
	
	# Get a list of other entries already added at this same power.
	cached_entries = parse_cache.setdefault(power,[])
	
	# Look for a duplicate entry in that list and use it if available.
	for entry in cached_entries:
		if processed_chars[char_name] == entry:
			processed_chars[char_name] = entry
			return
	
	# If none available, add the current entry to list.
	cached_entries.append(processed_chars[char_name])


