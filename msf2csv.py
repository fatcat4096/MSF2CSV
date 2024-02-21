#!/usr/bin/env python3
# Encoding: UTF-8
"""msf2csv.py
Transform stats from MSF.gg into readable tables with heatmaps.
"""


import os, sys
import argparse

from process_website import *             # Routines to get Roster data from website.
from file_io         import *             # Routines to read and write files to disk.
from generate_html   import *             # Routines to generate the finished tables.
from generate_csv    import generate_csv  # Routines to generate the original csv files.


# If no name specified, default to the alliance for the Login player
def main(alliance_name='', csv=False, prompt=False, headless=False, force='', table_format={}, roster_url='', external_driver=None):

	##
	## Just a junker placeholder until I come back and do it right. 
	##
	
	if roster_url:
		roster_url = roster_url.split('/')[-2]
		alliance_info = find_cached_data(roster_url)
		if not alliance_info:
			driver = external_driver or login()

			# Start with the Alliance that's asking.
			alliance_info = find_cached_data('SIGMA Infamously Strange')
			alliance_info['members'][roster_url] = {'url': roster_url}
			
			# Get original list of members
			original_members = list(alliance_info['members'])
			
			# Grab roster info for this Army of One.
			rosters_output = process_rosters(driver, alliance_info, only_new=True) 
			update_history(alliance_info)			

			# Determine who was added
			new_member = [member for member in alliance_info['members'] if alliance_info['members'][member].get('url') == roster_url][0]
			alliance_info['name'] = new_member

			new_strike = [[new_member]]
			
			# Update the Strike Teams to only include this member.
			alliance_info['strike_teams'] = {'custom':new_strike}

			# Write cached data -- DON'T DO THIS IN THE FINAL VERSION. 
			write_cached_data(alliance_info, file_name=roster_url)
			
		# Create required structures
		pathname = get_local_path()
		# Request output for this Member
		for output in tables:
			table_format = {'strike_teams':'custom', 'span':False, 'inc_pos':True}
			write_file(f'{pathname}{alliance_info["name"]}-{output}.html', generate_tabbed_html(alliance_info, tables.get(output), table_format))
		return
	
	# Load roster info directly from cached data or the website.
	else:
		alliance_info = get_alliance_info(alliance_name, prompt, force, headless, external_driver)

	# If we're done, the captured output is being returned as 'alliance_info'
	if force == 'rosters_only':
		return alliance_info

	print ()

	# Build a default path and filename. 
	pathname = os.path.dirname(alliance_info['file_path']) + os.sep + 'reports' + os.sep + alliance_info['name'] + '-'

	output         = table_format.get('output')
	external_table = table_format.get('external_table')
	output_format  = table_format.get('output_format','tabbed')
	valid_output   = list(tables)+['roster_analysis','alliance_info', 'by_char']

	# Generate CSV?
	if csv:
		 write_file(pathname+"original.csv", generate_csv(alliance_info))

	# Output only a specific report.
	elif external_table or output:

		if external_table or output in valid_output:
		
			# If requesting tabbed output, this is our destination.
			if output_format == 'tabbed' and output in tables:
				html_files = {output+'.html': generate_tabbed_html(alliance_info, tables.get(output), table_format)}
			# Otherwise, we need to generate the one page.
			else:
				html_files = generate_html(alliance_info, external_table or tables.get(output), table_format)

			# If 'image' was requested, we need to convert the HTML files to PNG images.
			if output_format == 'image':
				html_files = write_file(pathname, html_files, print_path=False)
				html_files = html_to_images(html_files)
			# If not, just need write the html files out.
			else:
				html_files = write_file(pathname, html_files)

			return html_files
		else:
			print("--output FORMAT must be one of the following:\n"+str(valid_output))

	# Default: If no output specified, generate tabbed html output for every defined format.
	else:
		for output in tables:
			write_file(pathname+output+'.html', generate_tabbed_html(alliance_info, tables.get(output), table_format))

	# If running Frozen executable, stop here before dismissing dialog box. 
	if getattr(sys, 'frozen', False):
		input ('\nSUCCESS! The reports listed above have been generated.')	


# Parse arguments
if __name__ == '__main__':

	formatter = lambda prog: argparse.HelpFormatter(prog, max_help_position=40)
	parser = argparse.ArgumentParser(formatter_class=formatter, description='Create HTML tables from MSF roster data.')

	parser.add_argument('file_or_alliance', type=str, nargs='?',
						help='specify a cached_data file or alliance_name input', default='')
	
	parser.add_argument('-c', '--csv', action='store_true', 
						help='just generate csv output, no html tables')
	parser.add_argument('-p' , '--prompt', action='store_true', 
						help='prompt and store credentials')
	parser.add_argument('--headless', action='store_true', 
						help='hide web browser driver during roster processing')

	# Force fresh roster downloads or force use of cached data.
	group1 = parser.add_mutually_exclusive_group()
	group1.add_argument('-f', '--fresh', action='store_true', 
						help='force download of Alliance roster data, regardless of timing')
	group1.add_argument('-s', '--stale', action='store_true',
						help='prevent download of Alliance roster data, regardless of timing')
	group1.add_argument('-r', '--rosters_only', action='store_true', 
						help='force download of Alliance roster data, no output (forces headless)')

	# Table Formatting flags. 
	parser.add_argument('--inc_avail', action='store_true', default=None,
						help='include # of avail chars, per min_iso and min_tier in output')
	parser.add_argument('--inc_class', action='store_true', default=None,
						help='include ISO Class information and confidence in output')
	parser.add_argument('--inc_hist', action='store_true', 
						help='include History info with output')
	parser.add_argument('--min_iso', type=int, metavar='N',
						help='minimum ISO level for inclusion in output')
	parser.add_argument('--min_tier', type=int, metavar='N',
						help='minimum Gear Tier for inclusion in output')
	parser.add_argument('--max_others', type=int, metavar='N',
						help='max characters in Others section; 0 is no max')
	parser.add_argument('--only_lane', type=int, metavar='N',
						help='only output ONE lane of a given format')
	parser.add_argument('--only_section', type=int, metavar='N',
						help='only output ONE section of a given lane')
	parser.add_argument('--only_team', type=int, metavar='N', choices=[0, 1, 2, 3],
						help='only output info for one strike team, 0 is ignore strike teams')
	parser.add_argument('--only_image', action='store_true',
						help='output PNG files instead of HTML, requires -o/--output FORMAT', default='')					
	parser.add_argument('--output', type=str, metavar='FORMAT',
						help='only output ONE format from the list of formats', default='')
	parser.add_argument('--sections_per', type=int, metavar='N',
						help='include N sections per file.')
	parser.add_argument('--sort_by', type=str, metavar='SORT', choices=['alpha','stp','tcp'],
						help="ignore strike teams, sort players by 'alpha', 'stp', or 'tcp'")
	parser.add_argument('--sort_char_by', type=str, metavar='SORT', choices=['alpha','power','avail'],
						help="sort chars by 'alpha' (default), 'power', or 'avail'.")
	parser.add_argument('--span', action='store_true', default=None,
						help='use spanning format for output, forces max_others to 0')
	parser.add_argument('--url', type=str, default=None,
						help='roster URL for solo report output')						
	args = parser.parse_args()

	# There can be only one.
	force = ''
	if args.fresh:
		force = 'fresh'
	elif args.stale:
		force = 'stale'
	elif args.rosters_only:
		force = 'rosters_only'
	
	# Rosters Only forces Headless operation, Import Block always operates headlessly
	headless = args.rosters_only or args.headless

	# If image requested, but no output specified, raise error.
	if args.only_image and not args.output:
		parser.error ("--only_image requires --output FORMAT to be specified")
	# If image requested, format is explicitly 'image'
	elif args.only_image:
		output_format = 'image'
	# If output is specified, but only_image is not, format is single page HTML. 
	elif args.output:
		output_format = 'html'
	# If no output explicitly specified, generate tabbed HTML file.
	else:
		output_format = 'tabbed'
	
	# Group the Formatting flags into a single argument
	table_format = {'inc_avail'     : args.inc_avail,
					'inc_class'     : args.inc_class,
					'inc_hist'      : args.inc_hist,
					'min_iso'       : args.min_iso,
					'min_tier'      : args.min_tier,
					'max_others'    : args.max_others,
					'only_lane'     : args.only_lane,
					'only_section'  : args.only_section,
					'only_team'     : args.only_team,
					'only_image'    : args.only_image,
					'output'        : args.output,
					'output_format' : output_format,
					'sections_per'  : args.sections_per,
					'sort_by'       : args.sort_by,
					'sort_char_by'  : args.sort_char_by,
					'span'          : args.span}
	
	main(args.file_or_alliance, args.csv, args.prompt, headless, force, table_format, roster_url=args.url) # Just run myself

