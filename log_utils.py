# Resurrected code from 2008. Previously part of common_utils.py, now standalone as log_utils.py.
#
# TODO:
# * Rewrite log_leave. Some very old coding styles in here.
# * Change to rename only files of same transaction_id, i.e. MSFRosterBot, or base python.log for msf2csv.py from command line.


import time
import os
import sys
import asyncio

from functools import wraps
from pathlib   import Path
from typing    import Callable, Any

import logging

import __main__

# Default value, use the local file path.
log_file_path = os.path.dirname(__file__)

# If frozen, work in the same directory as the executable.
if getattr(sys, 'frozen', False):
	log_file_path = os.path.dirname(sys.executable)
# If imported, work in the same directory as the importing file.
elif hasattr(__main__, '__file__'):
	log_file_path = os.path.dirname(os.path.abspath(__main__.__file__))

# Create a directory for the logfiles.
log_file_path = os.path.realpath(log_file_path) + os.sep + 'trace' + os.sep
if not os.path.exists(log_file_path):
	os.makedirs(log_file_path)

# 'reporting_level' controls whether we log at all. Set to 0 to disable logging.
# 'reporting_threshold' controls how long a call has to take before we start reporting time required.
# ----------------------------------------------------
reporting_level     = 3		# Level 0 = no logging, 1 = basic logs, 2 = basic reporting, 3 = detailed reporting, 4 = task/dossier info
reporting_threshold = 2.00


# Decorator that implements all logging and keeps track of call stats.
def timed(func_=None, level=4, init=False, handoff=False):
	"""
	Decorator to log test start and end time of a function
	"""

	def _decorator(func):

		@wraps(func)
		def wrapped_func(*args: Any, **kwargs: Any) -> Any:

			log_file = None

			LOG_CALL = level<=reporting_level

			# See if we've been passed a log_file from async code. Use a log_file if we are explicitly passed it.
			if 'log_file' in kwargs and kwargs['log_file']:
				log_file = kwargs['log_file']

			# Look for a log file if reporting_level > 0.
			elif reporting_level:

				# If INIT flag hasn't been set, lets look for a log_file
				if not init: 
					log_file = find_log_file()

				# If log_file not defined, there isn't an active log file yet.
				# If INIT flag is set, start a new one here.)
				if not log_file and init:
					log_file = log_init(func.__name__)

			# If we have a valid logger, tally and log the call
			if log_file:

				# Tally the call
				log_file['stack'].append({'func':func.__name__, 'time_in':time.time()})

				# Only output to logs if under reporting_threshold
				if LOG_CALL:
					log_call(log_file, *args, **kwargs)

			# Get the result from the wrapped function call
			result = func(*args, **kwargs)

			# If we have a valid logger, log the result
			if log_file:
				log_leave(log_file, LOG_CALL, result)
			
			# Return the result to whoever called this.
			return result

		@wraps(func)
		async def wrapped_func_async(*args: Any, **kwargs: Any) -> Any:
		
			log_file = None

			LOG_CALL = level<=reporting_level

			# See if we've been passed a log_file from async code. Use a log_file if we are explicitly passed it.
			if 'log_file' in kwargs and kwargs['log_file']:
				log_file = kwargs['log_file']

			# Look for a log file if reporting_level > 0.
			elif reporting_level:
			
				# If INIT flag hasn't been set, lets look for a log_file
				if not init: 
					log_file = find_log_file()

				# If log_file not defined, either INIT flag was set or there isn't an active log yet.
				# (INIT flag means this is an atomic command and deserves own log file. Start a new one here.)
				if not log_file and init:

					# Since we're in Async code, see if we can find 
					# a valid Discord Context to pull username from
					context = None
					for arg in args:
						if 'author' in dir(arg):
							context = arg
							break

					# Initialize the log_file
					log_file = log_init(func.__name__, context=context)

			# If we have a valid logger, tally and log the call
			if log_file:

				# Tally the call
				log_file['stack'].append({'func':func.__name__, 'time_in':time.time()})

				# Only output to logs if under reporting_threshold
				if LOG_CALL:
					log_call(log_file, *args, **kwargs)
					
			# Get the result from the wrapped function call
			result = await func(*args, **kwargs)

			# If we have a valid logger, log the result
			if log_file:
				log_leave(log_file, LOG_CALL, result)

			# Return the result to whoever called this.
			return result

		return wrapped_func_async if asyncio.iscoroutinefunction(func) else wrapped_func

	if callable(func_):
		return _decorator(func_)
	elif func_ is None:
		return _decorator
	else:
		raise RuntimeWarning("Positional arguments are not supported.")



# Creater a logger object for use in a command.
def log_init(calling_func, context=None):

	global log_file_path
	
	date_time = time.strftime("%y.%m.%d-%H%M%S",time.localtime(time.time()))

	logger = logging.getLogger(calling_func+'-'+date_time)	
	logger.setLevel(logging.INFO)

	username = f'-{context.author.name}' if context else ''

	# Specify a filename for the logfile.
	filename = f"{log_file_path}python.{date_time}{username}-{calling_func}.log"
	
	file_handler = logging.FileHandler(filename=filename, encoding="utf-8", mode="w")
	file_handler_formatter = logging.Formatter(
		"[{asctime}] [{levelname:<8}]: {message}", "%Y-%m-%d %H:%M:%S", style="{"
	)
	file_handler.setFormatter(file_handler_formatter)

	# Add the handlers
	logger.addHandler(file_handler)

	log_file = {'logger':logger, 'stack':[{'func':calling_func,'time_in':time.time()}]}

	# Stash this log file into the calling frame for all to use.
	sys._getframe(2).f_locals['log_file'] = log_file
	
	return log_file



# Find an existing log_file in the Python stack
def find_log_file():

	# Skips this frame and the calling function.
	idx = 2
	
	# Iterate deeper until found.
	try:
		while not sys._getframe(idx).f_locals.get('log_file'):
			idx += 1
	# No more stack. Didn't find log_file.
	except ValueError:
		return
	# Return the log_file for local use.
	return sys._getframe(idx).f_locals.get('log_file')



# Find an existing variable in the Python stack
def find_var(var='log_file', idx=2):

	# Iterate deeper until found.
	try:
		while not sys._getframe(idx).f_locals.get(var):
			idx += 1
	# No more stack. Didn't find variable.
	except ValueError:
		return
	# Return the variable for local use.
	return sys._getframe(idx).f_locals.get(var)

	
	
# Utility function used by decorator to log and track function calls/returns
# --------------------------------------------------------------------------
def log_call(log, *i_arg, **kwarg):

	# Pull out the pieces to work with.
	logger = log['logger']
	stack  = log['stack']

	level = "   "*(len(stack)-2)
	
	logger.info(f">>>{level} Calling {stack[-1]['func']}({','.join(map(log_repr,i_arg))}) from {stack[-2]['func']}()")
	logger.info(f">>>{level}    Now in {stack[-1]['func']}")

	return



# Quick and dirty repr to be called when logging arguments.
def log_repr(val):

	# Is the item we're logging a familiar object?
	if type(val) is dict:
		if 'hist' in val:
			return '{ALLIANCE_INFO}'
		elif 'lanes' in val:
			return '{TABLE}'

	# Just truncate anything else at 100 chars.
	return repr(val)[:100]



# Really need to re-write this.

# Utility function used by decorator to log and track function calls/returns
# --------------------------------------------------------------------------
def log_leave(log, LOG_CALL, result, **kwarg):

	logger = log['logger']
	stack  = log['stack']

	# If we're at the bottom of the stack, just return 
	if len(stack) == 1:
		return

	top  = stack.pop()

	func = top['func']

	# Calculate time spent in this function.
	time_in = time.time()-top['time_in']

	# Subtract any time spent in deeper subroutines.
	called  = top.get('called')
	if called:
		time_in -= called['time_in']

	# If there's still an entry in the stack, let's update it with some statistics.
	new_top  = stack[-1]
	new_func = new_top['func']

	if reporting_level > 2:

		# Update the list of functions called and time_in statistic
		if called:

			# If we haven't called func from this level before, 
			# initialize it with time_in and call count.
			if func not in called:
				called[func] = [time_in,1]
			# We've already called func from this level. 
			# Need to increment time_in and call count.
			else:					
				called[func][0] += time_in
				called[func][1] += 1

			# Update the total time in statistic.
			called['time_in'] += time_in
		else:
			called = {func:[time_in,1],'time_in':time_in}

		new_called = new_top.get('called')

		# If the stat dict doesn't exist. This is the first function 
		# we've called from this level. Initialize it with called.
		if new_called is None:
			new_top['called']=called

		# If the stat dict already exists, we need to merge called in.
		else:
			for key in called:
				if key == 'time_in':
					continue

				# If the function doesn't exist yet, just copy the whole key in.
				if key not in new_called:
					new_called[key] = called[key]
				# Otherwise, increment the call counter and add the 
				# time_in the top level to the time_in the current
				else:
					new_called[key][0] += called[key][0]
					new_called[key][1] += called[key][1]

			# Also need to merge called's time in.
			new_called['time_in'] += called['time_in']

		# If we've hit the bottom, we want to report *all* the calls for every iteration
		# and then clean up the call stack so we can start again anew. 
		if len(stack) == 1:
			called = new_top.pop('called', None)

	if not func or not LOG_CALL:
		return

	level = "   "*(len(stack)-1)

	if reporting_level > 1 and called.get('time_in'):
		log_buffer = [f"INF{level}    Generating report...\n========================================  =======  =========  ==========  ======"]
		if reporting_level > 2 and called and called.get('time_in') > reporting_threshold:
			log_buffer.append(f"Report for: {func:28}  # Calls  Time/Call  Total Time  % Time")
			log_buffer.append("----------------------------------------  -------  ---------  ----------  ------")
			log_buffer.append(f'{func:40}  {'n/a':>5} {called[func][0]:>10.3f} s {called['time_in']:>9.3f} s {100*called[func][0]/called['time_in']:>6.1f}%')

			if len(called) > 2:
				log_buffer.append("-----------Calls-by-Subroutine----------  -------  ---------  ----------  ------")
				report_list = [item for item in called if item not in ('time_in',func)]

				for item in sorted(report_list, key=lambda x: -called[x][0]):
					call = called[item]
					log_buffer.append(f'{item:40}  {call[1]:>5} {call[0]/call[1]:>10.3f} s {call[0]:>9.3f} s {100*call[0]/called['time_in']:>6.1f}%')
			log_buffer.append(f"========================================  =======  =========  ==========  ======")
		else:
			log_buffer.append(f'Report for: {func:28}  {1:>5} {time_in:>10.3f} s {time_in:>9.3f} s {100:>6.1f}%\n========================================  =======  =========  ==========  ======')

		logger.info('\n'.join(log_buffer))

	logger.info(f'<<<{level}    Leaving {func}(), return value = {log_repr(result)}')
	logger.info(f'<<<{level} Now in {new_func}()')

	# If we're back to 0, the call is over
	if not level:

		# Tidy up so that log files can be removed
		for handler in logger.handlers[:]:
			logger.removeHandler(handler)
			handler.close()



#Quick definitions of ansi color and formatting definitions
class ansi():
	# Colors
	black   = "\x1b[30m"
	red     = "\x1b[31m"
	green   = "\x1b[32m"
	yellow  = "\x1b[33m"
	blue    = "\x1b[34m"
	magenta = "\x1b[35m"
	cyan    = "\x1b[36m"
	dkgray  = "\x1b[90m"

	# These colors used when "bolded"
	ltred   = "\x1b[91m"
	ltgrn   = "\x1b[92m"
	ltyel   = "\x1b[93m"
	ltblu   = "\x1b[94m"
	ltmag   = "\x1b[95m"
	ltcyan  = "\x1b[96m"
	white   = "\x1b[97m"

	# Styles
	reset   = "\x1b[0m"
	bold    = "\x1b[1m"
	under   = "\x1b[4m"



def discord_ansi(msg):
	return msg.replace('[9','[1;3').replace('[3','[0;3')



def print_exc(exc):
	return f'{ansi.ltred}EXCEPTION:{ansi.reset} {type(exc).__name__}: {exc}'



def cleanup_old_files(local_path, age=7):
	# Let catch all exceptions. Don't let a command fail
	try:
		if not os.path.isdir(local_path):
			local_path = os.path.dirname(local_path)

		cutoff_date = time.time() - age * 24 * 3600

		for item in Path(local_path).expanduser().rglob('*'):
			if item.is_file():
				if os.stat(item).st_mtime < cutoff_date:
					os.remove(item)

		for item in Path(local_path).expanduser().rglob('*'):    
			if item.is_dir():
				if len(os.listdir(item)) == 0:
					os.rmdir(item)
	except Exception as exc:
		print (f"{print_exc(exc)}")



# Clean up old files at launch.
cleanup_old_files(log_file_path)
