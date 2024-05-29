#!/usr/bin/env python3
# Encoding: UTF-8
"""msf2csv.py
Transform stats from MSF.gg into readable tables with heatmaps.
"""

from log_utils import *

import os, sys
import argparse

from process_website import *             # Routines to get Roster data from website.
from file_io         import *             # Routines to read and write files to disk.
from generate_html   import *             # Routines to generate the finished tables.
from generate_csv    import generate_csv  # Routines to generate the original csv files.

import datetime

# If no name specified, default to the alliance for the Login player
@timed(level=3, init=True)
def main(alliance_name='', prompt=False, headless=False, force='', table_format={}, scopely_login='', log_file=None):
	
	# Were we passed an alliance_info via alliance_name?
	if type(alliance_name) is dict and 'members' in alliance_name:
		alliance_info = alliance_name
	# Load roster info directly from cached data or the website.
	else:
		alliance_info = get_alliance_info(alliance_name, prompt, force, headless, scopely_login)

	# If we failed to retrieve alliance info, we've already explained. Just exit.
	if not alliance_info:
		return

	# Build a default path and filename. 
	pathname = os.path.dirname(alliance_info['file_path']) + os.sep + 'reports' + os.sep + alliance_info['name'] + '-'

	output         = table_format.get('output')
	external_table = table_format.get('external_table')
	output_format  = table_format.get('output_format','tabbed')
	valid_output   = list(tables)+['roster_analysis','alliance_info', 'by_char']

	# Generate CSV?
	if output == 'csv':
		 html_files = write_file(pathname+"csv.csv", generate_csv(alliance_info))
		 
		 return html_files

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

	group0 = parser.add_mutually_exclusive_group()
	group0.add_argument('alliance_name', type=str, nargs='?',
						help='e-mail address for Scopely account login', default='')

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
	group0.add_argument('--login', type=str, metavar='EMAIL',
						help='e-mail address for Scopely account login', default='')

	# Table Formatting flags. 
	parser.add_argument('--inc_avail', action='store_true', default=None,
						help='include # of avail chars, per min_iso and min_tier in output')
	parser.add_argument('--inc_class', action='store_true', default=None,
						help='include ISO Class information and confidence in output')
	parser.add_argument('--inc_hist', action='store_true', 
						help='include History info with output')
	parser.add_argument('--inc_rank', action='store_true', 
						help='include STP rank in output')
	parser.add_argument('--inc_summary', action='store_true', 
						help='include Team Power Summary in output')
	parser.add_argument('--line_wrap', type=int, metavar='N',
						help='if 1-4, lines per section; if 5+, Chars per line')
	parser.add_argument('--min_iso', type=int, metavar='N',
						help='minimum ISO level for inclusion in output')
	parser.add_argument('--min_lvl', type=int, metavar='N',
						help='minimum Char level for inclusion in output')
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
	parser.add_argument('--only_summary', action='store_true', 
						help='only output Team Power Summary')
	parser.add_argument('--only_image', action='store_true',
						help='output PNG files instead of HTML, requires -o/--output FORMAT', default='')					
	parser.add_argument('--output', type=str, metavar='FORMAT',
						help='only output ONE format from the list of formats', default='')
	parser.add_argument('--publish', action='store_true',
						help='generate HTML files and push to GitHub pages', default='')					
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
	
	# If only summary, make sure inc_summary is set as well.
	if args.only_summary and not args.inc_summary:
		args.inc_summary = True

	# If image requested, but no output specified, raise error.
	if args.only_image and not args.output:
		parser.error ("--only_image requires --output FORMAT to be specified")
	elif args.csv:
		args.output   = 'csv'
		output_format = 'csv'
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
					'inc_rank'      : args.inc_rank,
					'inc_summary'   : args.inc_summary,
					'min_iso'       : args.min_iso,
					'min_lvl'       : args.min_lvl,
					'min_tier'      : args.min_tier,
					'max_others'    : args.max_others,
					'line_wrap'     : args.line_wrap,
					'only_lane'     : args.only_lane,
					'only_section'  : args.only_section,
					'only_team'     : args.only_team,
					'only_summary'  : args.only_summary,
					'only_image'    : args.only_image,
					'output'        : args.output,
					'output_format' : output_format,
					'publish'       : args.publish,
					'sections_per'  : args.sections_per,
					'sort_by'       : args.sort_by,
					'sort_char_by'  : args.sort_char_by,
					'span'          : args.span}
	
	main(args.alliance_name, args.prompt, args.headless, force, table_format, args.login) # Just run myself
	