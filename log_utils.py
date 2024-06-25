# Resurrected code from 2008. Previously part of common_utils.py, now standalone as log_utils.py.
#
# TODO:
# * Rewrite log_leave. Some very old coding styles in here.
# * Change log_clear() to create Trace/ if doesn't exist and clean up log files that haven't been written to in a week. 
# * Change to rename only files of same transaction_id, i.e. MSFRosterBot, or base python.log for msf2csv.py from command line.


import time
import os
import sys
import traceback
import asyncio
import inspect

from functools import wraps
from typing import Callable, Any

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

			# See if we've been passed a log_file from async code. Use a log_file if we are explicitly passed it.
			if 'log_file' in kwargs and kwargs['log_file']:
				log_file = kwargs['log_file']
			# Only continue looking if we are supposed to be logging.
			elif level<=reporting_level:

				# If INIT flag hasn't been set, lets look for a log_file
				if not init: 
					log_file = find_log_file()

				# If log_file not defined, there isn't an active log file yet.
				# If INIT flag is set, start a new one here.)
				if not log_file and init:
					log_file = log_init(func.__name__)

			# If we have a valid logger, log the call
			if log_file and level<=reporting_level:
				log_call(log_file, func.__name__, *args, **kwargs)

			# Get the result from the wrapped function call
			ret = func(*args, **kwargs)

			# If we have a valid logger, log the return
			if log_file and level<=reporting_level:
				log_leave(log_file, ret)
			
			# Return the result to whoever called this.
			return ret

		@wraps(func)
		async def wrapped_func_async(*args: Any, **kwargs: Any) -> Any:
		
			log_file = None

			# See if we've been passed a log_file from async code. Use a log_file if we are explicitly passed it.
			if 'log_file' in kwargs and kwargs['log_file']:
				log_file = kwargs['log_file']
			# Only continue looking if we are supposed to be logging.
			elif level<=reporting_level:
			
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
					
			# If we have a valid logger, log the call
			if log_file and level<=reporting_level:
				log_call(log_file, func.__name__, *args, **kwargs)

			# Get the result from the wrapped function call
			ret = await func(*args, **kwargs)

			# If we have a valid logger, log the return
			if log_file and level<=reporting_level:
				log_leave(log_file, ret)

			# Return the result to whoever called this.
			return ret

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
	
	date_time = time.strftime("%Y.%m.%d-%H%M%S",time.localtime(time.time()))

	logger = logging.getLogger(calling_func+date_time)
	logger.setLevel(logging.INFO)

	username = f'-{context.author.name}' if context else ''

	# Specify a filename for the logfile.
	filename = f"{log_file_path}python.{date_time}{username}-{calling_func}.log"
	
	file_handler = logging.FileHandler(filename=filename, encoding="utf-8", mode="w")
	file_handler_formatter = logging.Formatter(
		"[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{"
	)
	file_handler.setFormatter(file_handler_formatter)

	# Add the handlers
	logger.addHandler(file_handler)

	log_file = {'logger':logger, 'stack':[{'func':calling_func,'time_in':time.time()}]}

	# Stash this log file into the calling frame for all to use.
	inspect.stack()[2][0].f_locals['log_file'] = log_file
	
	return log_file



# Find a variable by name in the Python stack
def find_log_file():
	
	# Skip this frame and the calling function.
	for frame in inspect.stack()[2:]:
		
		# Look for variable explicitly lower in the stack.
		if 'log_file' in frame[0].f_locals and frame[0].f_locals['log_file']:
			return frame[0].f_locals['log_file']

	return



# Utility function used by decorator to log and track function calls/returns
# --------------------------------------------------------------------------
def log_call(log, call_to_func, *i_arg, **kwarg):

	# Pull out the pieces to work with.
	logger = log['logger']
	stack  = log['stack']

	# Note the calling func from the top of the stack.
	call_from_func = stack[-1]['func']
	stack.append({'func':call_to_func, 'time_in':time.time()})

	level = "   "*(len(stack)-2)
	
	logger.info(f">>>{level} Calling {call_to_func}({','.join(map(log_repr,i_arg))}) from {call_from_func}()")
	logger.info(f">>>{level}    Now in {call_to_func}")

	return



# Quick and dirty repr to be called when logging arguments.
def log_repr(val):

	# Is the item we're logging a familiar object?
	if type(val) is dict:
		if val.get('hist'):
			return '{ALLIANCE_INFO}'
		elif val.get('lanes'):
			return '{TABLE}'

	# Just truncate anything else at 100 chars.
	return repr(val)[:100]



# Really need to re-write this.
# I don't think it's handling the final log_leave() call correctly.

# Utility function used by decorator to log and track function calls/returns
# --------------------------------------------------------------------------
def log_leave(log, ret, **kwarg):

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
			called = new_top.get('called')
			if called:
				del new_top['called']

	if not func:
		return

	level  = len(stack)
	l_time = time.asctime(time.localtime(time.time()))

	log_buffer = ''
	level = "   "*(level-1)

	if reporting_level > 1 and called.get('time_in'):
		log_buffer += f"INF{level}    Generating report...\n\n========================================  =======  =========  ==========  ======\n"
		if reporting_level > 2 and called and called.get('time_in') > reporting_threshold:
			log_buffer += f"Report for: {func:<28}  # Calls  Time/Call  Total Time  % Time\n"
			log_buffer += "----------------------------------------  -------  ---------  ----------  ------\n"
			log_buffer += '%-40s  % 5s    % 7.3f s  % 8.3f s % 6.1f%%\n' % (func,'n/a',called[func][0],called['time_in'],100*called[func][0]/called['time_in'])

			if len(called) > 2:
				log_buffer += "-----------Calls-by-Subroutine----------  -------  ---------  ----------  ------\n"
				report_list = [item for item in called if item not in ('time_in',func)]

				for item in sorted(report_list, key=lambda x: -called[x][0]):
					call = called[item]
					log_buffer += '%-40s  % 5s    % 7.3f s  % 8.3f s % 6.1f%%\n' % (item,call[1],call[0]/call[1],call[0],100*call[0]/called['time_in'])
			log_buffer += f"========================================  =======  =========  ==========  ======\n"
		else:
			log_buffer += 'Report for: %-28s  % 5s    % 7.3f s  % 8.3f s % 6.1f%%\n========================================  =======  =========  ==========  ======\n' % (func,1,time_in,time_in,100)

		logger.info(log_buffer)

	logger.info(f'<<<{level}    Leaving {func}(), return value = {log_repr(ret)}')
	logger.info(f'<<<{level} Now in {new_func}()')

	return



"""
# Do we still need these? 
# ---------------------------------------------------
def log_clear():
	try:
		# Get the list of current python.log files.
		base_dir = './trace/'
		log_files = [x for x in os.listdir(base_dir) if 'python' in x]
		
		# Use the standard rename for python.log files. 
		# Leave transaction_id based log files for 1 week before cleanup. 
		# python
		
		# Rename the python.log and python.old files gracefully.
		for log_file in ['.log','.old']:
			if 'python'+log_file in log_files:
				datetime = time.strftime("%Y.%m.%d-%H%M%S",time.localtime(os.stat(base_dir+'python'+log_file)[8]))
		
				for ext in ['']+['.'+repr(x) for x in range(1,10)]:
					if not os.path.exists(base_dir+'python.'+datetime+log_file+ext):
						try:
							os.rename(base_dir+'python'+log_file,base_dir+'python.'+datetime+log_file+ext)
						except:
							pass
							# exc = exception_info()
							# log_err('Error clearing log:\n',exc)
						break
		
		log_files = [x for x in os.listdir(base_dir) if x.find('python')!=-1]
		
		# Only keep the 10 most recent log files. 
		for x in range(len(log_files) - 10):
			pass # safe_remove(base_dir+log_files[x])
		
	except:
		pass
		# exc = exception_info()
		# log_err('Error clearing log:\n',exc)
	return



# Do we still need these?
# --------------------------------------------------------------------
def log_inf(*i_arg,**kwarg):
	if kwarg.get('level',1)>reporting_level:
		return

	log_file = find_log_file()
	level = "   "*(len(log_file['stack'])-1)

	log_file['logger'].info(f"INF {level}Message: {', '.join(map(repr,i_arg))}")

	return
"""