
# Return the anchor if one exists, plus the correct ID/linked ID for the tables
def lookup_table_ids(html_cache, char_list, hist_date):
	
	# Find the anchor to use if building direct links from the report page.
	anchor = html_cache.get('chars',{}).get(char_list[0],{})		

	# If an anchor definition exists, this is a multi-tabbed file.
	if anchor:
		# We are creating the left table.
		if not hist_date:
			table_id  = anchor.get('to')
			linked_id = read_next_table_id(html_cache)
		# We are creating the historical entry.
		else:
			table_id  = make_next_table_id(html_cache)
			linked_id = anchor.get('to')
	# Single tabbed HTML. 
	else:
		# We are creating the left table.
		if not hist_date:
			table_id  = make_next_table_id(html_cache)
			linked_id = read_next_table_id(html_cache)
		# We are creating the historical entry.
		else:
			linked_id = read_prev_table_id(html_cache)
			table_id  = make_next_table_id(html_cache)

	return anchor, table_id, linked_id
	
# Creates and returns a new table_id
def make_next_table_id(html_cache):
	return html_cache.setdefault('tables',{}).setdefault(len(html_cache.get('tables',{})),f"t{len(html_cache.get('tables',{}))}")


# Calculates and returns the next table_id, doesn't change html_cache
def read_next_table_id(html_cache):
	return f"t{len(html_cache.get('tables',{}))}"


# Calculates what the previous table_id was, doesn't change html_cache		
def read_prev_table_id(html_cache):
	return f"t{len(html_cache.get('tables',{}))-1}"
		
	
# Creates and returns a anchor for this character
def make_next_anchor_id(html_cache, char, table_id):
	return html_cache.setdefault('chars',{}).setdefault(char,{'from':table_id, 'to':f"a{len(html_cache.get('chars',{}))}"})


# Creates and returns a anchor for this character
def make_next_color_id(html_cache, color):
	return html_cache.setdefault('colors',{}).setdefault(color, f"c{len(html_cache.get('colors',{}))}")

	
