#!/usr/bin/env python3
# Encoding: UTF-8
"""file_io.py
Routines to create a ready and waiting reserve of Selenium drivers.
"""


import os
import psutil

from datetime import datetime
from selenium import webdriver

try:
	from .log_utils import *
except ModuleNotFoundError:
	from  log_utils import *



#888888b.  8888888b.  8888888 888     888 8888888888 8888888b.       8888888b.   .d88888b.   .d88888b.  888
#88  "Y88b 888   Y88b   888   888     888 888        888   Y88b      888   Y88b d88P" "Y88b d88P" "Y88b 888
#88    888 888    888   888   888     888 888        888    888      888    888 888     888 888     888 888
#88    888 888   d88P   888   Y88b   d88P 8888888    888   d88P      888   d88P 888     888 888     888 888
#88    888 8888888P"    888    Y88b d88P  888        8888888P"       8888888P"  888     888 888     888 888
#88    888 888 T88b     888     Y88o88P   888        888 T88b        888        888     888 888     888 888
#88  .d88P 888  T88b    888      Y888P    888        888  T88b       888        Y88b. .d88P Y88b. .d88P 888
#888888P"  888   T88b 8888888     Y8P     8888888888 888   T88b      888         "Y88888P"   "Y88888P"  88888888



driver_pool = {}



# Keep drivers open and allow them to be re-used.
@timed(level=3)
def get_driver(proc_name='', force_new=False):
	global driver_pool

	# Create the active and avail pools if necessary
	active_pool = driver_pool.setdefault('active',{})
	avail_pool  = driver_pool.setdefault('avail',{})

	show_driver_pool('before get_driver')

	driver = None

	# If a driver is available already, provide the existing driver
	if avail_pool and not force_new:
		
		# Grab the available driver, don't fail if we miss
		driver = avail_pool.pop(list(avail_pool)[0], None)

	# If we didn't find an available driver, create a new one
	if not driver:
		driver = create_new_driver(proc_name)

	# If we have a driver...
	if driver:
		# Note job start time in the driver
		driver.last_used = datetime.now()
		
		# Use job start time as key in the active pool
		active_pool[driver.last_used] = driver

	show_driver_pool('after get_driver')

	return driver



# Create a Selenium driver if requested
def create_new_driver(proc_name):
	options = webdriver.ChromeOptions()

	# Indicate which process launched this driver
	options.add_argument(f'--window-name="{proc_name}"')

	# Add all the important options
	options.add_argument('--headless=new')
	options.add_argument('--no-sandbox')
	options.add_argument('--disable-dev-shm-usage')
	options.add_argument('--disable-gpu')
	options.add_argument('--disable-extensions')
	service = webdriver.ChromeService(service_args=["--enable-chrome-logs"])

	# For linux, explicitly specify the chromedriver to use
	if os.name == 'posix':
		service.path = '/usr/bin/chromedriver'

	# Actually create the driver
	driver = webdriver.Chrome(service=service, options=options)

	# Set internal info on driver with initial values
	driver.pid        = driver.service.process.pid
	driver.last_used  = driver.creation_date = datetime.now()
	driver.times_used = 0

	# print (f'Created NEW driver: {driver.pid:>5}')
	
	return driver



# Check driver in at the end of use.
@timed(level=3)
def release_driver(driver, also_release=None):
	global driver_pool

	# Create the active and avail pools if necessary
	active_pool = driver_pool.setdefault('active',{})
	avail_pool  = driver_pool.setdefault('avail',{})

	# Initialize the mutables
	if also_release is None:
		also_release = []

	show_driver_pool('before release_driver')

	# If returning driver, add to avail_pool - key is creation_date
	if driver:
		avail_pool[driver.creation_date] = driver

		# Add driver to list to release from active pool
		also_release.append(driver)

	# Clean up active_pool
	for driver in also_release:
		active_pool.pop(driver.last_used, None)
	
	show_driver_pool('after release_driver')
	
	return



# Walk and kill process tree for old, failed, or abandoned web drivers
def kill_process_tree(pid_list, logger=print):

	show_driver_pool('before kill_process_tree')

	driver_count = proc_count = 0

	for pid in pid_list:

		try:
			proc = psutil.Process(pid)
			child_procs = []

			# Kill off all the child processes first
			for child_proc in proc.children(recursive=True):
				child_proc.kill()

				# Keep track of how many children processes we found
				child_procs.append(child_proc.pid)

			# Log info before killing the process
			children = f"{', '.join([f'{ansi.bold}{x:>5}{ansi.rst}' for x in sorted(child_procs)])}"
			logger (f'{ansi.ltred}Killed{ansi.rst} process {ansi.ltyel}{proc.name()}{ansi.rst} PID: {ansi.ltyel}{proc.pid:>5}{ansi.rst}' + (f' and {len(child_procs)} child procs: {children}' if child_procs else ''))

			# Finally, kill the top process from the PID list
			proc.kill()

			# What's our body count?
			driver_count += 1
			proc_count   += 1 + len(child_procs)

		# Ignore issues with accessing process information
		except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
			pass

	if driver_count or proc_count:
		logger (f'Terminated {ansi.ltyel}{driver_count} web drivers{ansi.rst}, {proc_count} total processes killed')

	show_driver_pool('after kill_process_tree')

	return driver_count



def show_driver_pool(task = ''):
	global driver_pool

	"""# Create the active and avail pools if necessary
	active_pool = driver_pool.setdefault('active',{})
	avail_pool  = driver_pool.setdefault('avail',{})

	active_used = ',  '.join([f'PID: {ansi.ltyel}{active_pool[driver].pid:>5}{ansi.rst} Used: {active_pool[driver].times_used}' for driver in active_pool])+(2*(len(active_pool)-1)*' ') if active_pool else f'{ansi.dkgray}{'empty':^18}{ansi.rst}'
	avail_used  = ',  '.join([f'PID: {ansi.ltyel}{ avail_pool[driver].pid:>5}{ansi.rst} Used: { avail_pool[driver].times_used}' for driver in  avail_pool]) if  avail_pool else f'{ansi.dkgray}{'empty':^18}{ansi.rst}'

	if active_pool|avail_pool:
		task = f' after {ansi.ltcyan}{task[6:]}{ansi.rst}' if task.startswith('after') else task
		task = f'before {ansi.ltcyan}{task[7:]}{ansi.rst}' if task.startswith('before') else task
		print (f'{'DRIVERS':>10} {task:35}{ansi.white}ACTIVE:{ansi.rst}  {active_used:50} {ansi.white}AVAIL:{ansi.rst}  {avail_used:75}')"""


