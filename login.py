#!/usr/bin/env python3
# Encoding: UTF-8
"""login.py
Log on to MSF.gg and return a driver to use for parsing.
"""

from bs4 import BeautifulSoup

from log_utils import *

import __main__
import getpass
import keyring
import os
import sys
import time
import glob

import json
import tempfile
from functools import reduce

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait

from generate_local_files import *
from file_io import remove_tags


# Default value, use the local file path.
base_file_path = os.path.dirname(__file__)

# If frozen, work in the same directory as the executable.
if getattr(sys, 'frozen', False):
	base_file_path = os.path.dirname(sys.executable)
# If imported, work in the same directory as the importing file.
elif hasattr(__main__, '__file__'):
	base_file_path = os.path.dirname(os.path.abspath(__main__.__file__))

# Establish where csv and chromium files will reside.
csv_file_path = os.path.realpath(base_file_path) + os.sep + 'csv' + os.sep
chromium_path = csv_file_path + 'chromium' + os.sep
if not os.path.exists(chromium_path):
	os.makedirs(chromium_path)


class ChromeWithPrefs(webdriver.Chrome):
	def __init__(self, *args, options=None, user_data_dir='', profile_dir='Default', **kwargs):
		if options:
			self._handle_prefs(options, user_data_dir, profile_dir)

		super().__init__(*args, options=options, **kwargs)

		# If path not specified, remove the user_data_dir when quitting
		if not user_data_dir:
			self.keep_user_data_dir = False

	@staticmethod
	def _handle_prefs(options, user_data_dir, profile_dir):
		if prefs := options.experimental_options.get("prefs"):

			# turn a (dotted key, value) into a proper nested dict
			def undot_key(key, value):
				if "." in key:
					key, rest = key.split(".", 1)
					value = undot_key(rest, value)
				return {key: value}

			# undot prefs dict keys
			undot_prefs = reduce(
				lambda d1, d2: {**d1, **d2},  # merge dicts
				(undot_key(key, value) for key, value in prefs.items()),
			)

			# create a user_data_dir and add its path to the options
			user_data_dir = os.path.normpath(tempfile.mkdtemp() if not user_data_dir else user_data_dir)
			options.add_argument(f"--user-data-dir={user_data_dir}")
			options.add_argument(f'--profile-directory={profile_dir}')

			# create the preferences json file in its default directory
			default_dir = os.path.join(user_data_dir, profile_dir)
			if not os.path.exists(default_dir):
				os.makedirs(default_dir)

			prefs_file = os.path.join(default_dir, "Preferences")
			with open(prefs_file, encoding="latin1", mode="w") as f:
				json.dump(undot_prefs, f)

			# remove the experimental_options to avoid an error
			del options._experimental_options["prefs"]



@timed(level=3)
def alt_get_driver(scopely_login='baker_michael@hotmail.com', session='0', headless=False):

	global csv_file_path
	global chromium_path

	# Create a directory for the Selenium session
	user_data_dir = chromium_path + session + os.sep

	options = webdriver.ChromeOptions()
	options.add_argument('--log-level=3')
	options.add_argument('--accept-lang=en-US')
	options.add_experimental_option('excludeSwitches', ['enable-logging'])

	# Make sure we know where the CSV files will be downloaded to
	prefs = {"download.default_directory" : csv_file_path}
	options.add_experimental_option("prefs",prefs)

	# If headless requested, run this as a headless server
	if headless:
		options.add_argument('--headless=new')

	driver = ChromeWithPrefs(options=options, user_data_dir=user_data_dir, profile_dir=scopely_login)
	driver.scopely_login = scopely_login
	driver.session       = session
	driver.csv_file_path = csv_file_path

	# Start at the alliance_info page.
	driver.get('https://marvelstrikeforce.com/en/alliance/members')
	time.sleep(0.3)

	return driver



@timed(level=3)
def get_driver(headless=False):

	global csv_file_path
	
	# Build the driver
	options = webdriver.ChromeOptions()
	options.add_argument('--log-level=3')
	options.add_argument('--accept-lang=en-US')	
	options.add_experimental_option('excludeSwitches', ['enable-logging'])
	options.add_experimental_option('excludeSwitches', ['enable-automation'])
	
	prefs = {"download.default_directory" : csv_file_path}
	options.add_experimental_option("prefs",prefs)

	# If headless requested, run this as a headless server.
	if headless:
		options.add_argument('--headless=new')

	driver = webdriver.Chrome(options=options)
	driver.csv_file_path = csv_file_path
	
	# Start at the alliance_info page.
	driver.get('https://marvelstrikeforce.com/en/alliance/members')
	time.sleep(0.3)

	return driver
	
	

# Login to the website. Return a Selenium Driver object for a given login.
#
# If no login specified, use the default login

@timed(level=3)
def login(prompt=False, session='0', headless=False, driver=None, scopely_login=''):

	# If we were passed in a cached driver, we're ready to go.
	if driver:

		# Pull internal varibles back out. 
		session       = driver.session
		scopely_login = driver.scopely_login

	# Start by checking to see if we have / need credentials.
	scopely_login, scopely_pass = get_scopely_creds(prompt, scopely_login)

	# If we don't have a driver yet, grab one.
	if not driver:
		driver = get_driver(headless)
		#driver = alt_get_driver(scopely_login, session, headless)

	# Login if we aren't already.
	scopely_website_login(driver, scopely_login, scopely_pass)

	# Waiting while you login manually, automatically, or approve login via 2FA.
	try:
		WebDriverWait(driver, 300).until(EC.presence_of_element_located((By.CLASS_NAME, 'alliance-members')))

	# If our page doesn't include the Alliance Members table, never successfully logged in. 
	except TimeoutException:
		print("Timed out. Never found Alliance Info.")

		# Failed. Return None for driver
		return

	# Click on the Accept Cookies button if it is presented. This dialog prevents roster processing.
	accept_cookies_btn = driver.find_elements(By.ID,'onetrust-accept-btn-handler')
	if accept_cookies_btn:
		accept_cookies_btn[0].click()

	# Pull out the current username and alliance_name. 
	try:
		# We will be waiting for elements to appear.
		wait = WebDriverWait(driver, 10)

		# Open the user menu
		button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='navbar-menu']//a[@role='button']")))
		button.click()

		# Make note of Username
		username = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@class='navbar-menu']//div[@id='graphic-menu-title']")))
		driver.username = remove_tags(username.text).strip()

		# Make note of Alliance Name
		alliance_name = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@class='navbar-menu']//div[@id='alliance-graphic-menu-title']")))
		driver.alliance_name = remove_tags(alliance_name.text).strip()
		driver.alliance_html = alliance_name.get_attribute('innerHTML')			# We will use this for color naming.

		# Close the menu after information extracted
		button.click()

	except TimeoutException:
		print("Timed out. user-menu-trigger never became available.")

		soup = BeautifulSoup(driver.page_source, 'html.parser')
		write_file ('./TimeoutException.html', soup.prettify())

		# Failed. Return None for driver
		return

	# Download the related CSV files and remember their paths
	driver.info_csv   = download_csv_file(driver, 'info')
	driver.roster_csv = download_csv_file(driver, 'roster')

	return driver



# Check for saved credentials. If none saved, ask if would like to cache them.
@timed(level=3)
def get_scopely_creds(prompt=False, scopely_login=''):

	# If this is the first launch of a frozen executable, go ahead and prompt for login.
	first_launch = 'strike_teams' not in globals()

	# Look for a default login
	if not scopely_login:
		scopely_login = keyring.get_password('msf2csv','msfgg.scopely.default')

	# If we're requesting a prompt, first launch of a frozen executable, or no default scopely_login is defined
	# Ask for a default login and 
	if prompt or first_launch or not scopely_login:
	
		print ('\nWelcome to MSF2CSV!\n')
	
		scopely_login = input("Enter default Scopely Login (e-mail address): ")
		keyring.set_password('msf2csv', 'msfgg.scopely.default', scopely_login)

		# Setting a default value to flag if password isn't used.
		scopely_pass = getpass.getpass(prompt="Scopely Password (leave blank if using e-mail link): ") or 'wait-for-email'
		
		keyring.set_password('msf2csv', scopely_login, scopely_pass)

	scopely_pass = keyring.get_password('msf2csv',scopely_login) or 'wait-for-email'

	return scopely_login, scopely_pass



# Auto Login via Scopely authentication using cached credentials.
@timed(level=4)
def scopely_website_login(driver, scopely_user, scopely_pass='wait-for-email'):

	# If we already successfully authenticated, no login to perform.
	if auth_successful(driver):
		return

	# If we didn't end up at the Alliance Info screen, we are going through authentication.
	driver.new_auth = True

	try:
		wait = WebDriverWait(driver, 10)
	
		# Click on the Scopely Login button.
		login = wait.until(EC.element_to_be_clickable((By.ID, 'scopely-login')))
		login.click()

		# Find and enter Scopely ID for login.
		login_field = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'ant-input')))
		login_field.send_keys(scopely_user)

		# Click on the Submit button.
		login_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'submitButton')))
		login_button.click()

		button = []

		# If user is relying on access e-mail from Scopely, then no password is used.
		# Return control to the user and allow them to click on the link in the e-mail to complete login.
		if scopely_pass == 'wait-for-email':

			time.sleep(1.5)

			# Link has already been sent. Nothing more to do. Let's go back and wait for the click.
			if [elem for elem in driver.find_elements(By.TAG_NAME, 'h2') if elem.text == 'Check your inbox!']:
				return 

			while not button:
				time.sleep(0.05)
				button = [button for button in driver.find_elements(By.TAG_NAME, 'button') if button.text == 'Send me a sign in link instead']

		else:
	
			print('waiting for Input Password???')
	
			# Find login field and enter password to complete login process.
			pass_field = wait.until(EC.presence_of_element_located((By.XPATH,f'//input[@data-test-id="InputPassword"]')))	
			pass_field.send_keys(scopely_pass)

			while not button:
				time.sleep(0.05)
				button = [button for button in driver.find_elements(By.TAG_NAME, 'button') if button.text == 'Sign in']

		button[0].click()

	except TimeoutException:
		print("Timed out. Unable to complete login.")



def download_csv_file(driver, filetype):

	try:
		wait = WebDriverWait(driver, 10)

		# Find the CSV Menu button
		button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'download-button')))

	except TimeoutException:
		print("Timed out. CSV menu never became available.")
		raise

	# Click on the CSV Menu button
	button.click()

	# Get the list of Download Options and focus on the correct entry.
	downloads = []
	while not downloads:
		downloads = [download for download in driver.find_elements(By.CLASS_NAME, 'download-option') if download.text.lower() == filetype]
	
	# Focus on the "INFO" button object
	buttons = []
	while not buttons:
		buttons = [button for button in downloads[0].find_elements(By.TAG_NAME, 'button') if button.text.lower() == filetype]
	
	# Click on the button to start the download. Looking for CSV files newer than NOW.
	start_time = time.time()
	buttons[0].click()						

	# Keep looking for a newly written file.
	csv_file = ''
	while not csv_file or os.path.getctime(csv_file) <= start_time:
		time.sleep(0.25)
		csv_list = glob.glob(driver.csv_file_path+f'{filetype}*.csv')
		if csv_list:
			csv_file = max(csv_list, key=os.path.getctime)
	
	# Found the new CSV file, rename it appropriately.
	new_csv = driver.csv_file_path+f'{filetype}-{driver.alliance_name}.csv'
	os.replace(csv_file, new_csv)
	
	return new_csv



def auth_successful(driver):
	return driver.current_url == 'https://marvelstrikeforce.com/en/alliance/members'

