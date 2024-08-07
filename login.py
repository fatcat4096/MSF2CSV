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
# Establish where csv files will be downloaded to.
csv_file_path = os.path.realpath(base_file_path) + os.sep + 'csv' + os.sep
if not os.path.exists(csv_file_path):
	os.makedirs(csv_file_path)



@timed(level=3)
def get_driver(headless=False):

	global csv_file_path
	
	# Build the driver
	options = webdriver.ChromeOptions()
	options.add_argument('--log-level=3')
	options.add_argument('--accept-lang=en-US')	
	options.add_experimental_option('excludeSwitches', ['enable-logging'])
	
	prefs = {"download.default_directory" : csv_file_path}
	options.add_experimental_option("prefs",prefs)

	# If headless requested, run this as a headless server.
	if headless:
		options.add_argument('--headless=new')

	driver = webdriver.Chrome(options=options)
	driver.csv_file_path = csv_file_path
	
	return driver



# Login to the website. Return a Selenium Driver object for a given login.
#
# If no login specified, use the default login

@timed(level=3)
def login(prompt=False, headless=False, external_driver=None, scopely_login=''):

	# If we were passed in a cached driver, we're ready to go.
	if external_driver:
		driver = external_driver

	# If a new driver, still need to login:
	else:
		# Start by checking to see if we have / need credentials.
		scopely_login, scopely_pass = get_scopely_creds(prompt, scopely_login)

		driver = get_driver(headless)

		# Start at the alliance_info page.
		scopely_website_login(driver, scopely_login, scopely_pass)

	# Waiting while you login manually, automatically, or approve login via 2FA.
	try:
		WebDriverWait(driver, 300).until(EC.presence_of_element_located((By.CLASS_NAME, 'alliance-members')))

		# Wait until page has fully displayed
		WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "H2")))

	# If our page doesn't include the Alliance Members table, never successfully logged in. 
	except TimeoutException:
		print("Timed out. Unable to complete login.")

		return

	# Click on the Accept Cookies button if it is presented. This dialog prevents roster processing.
	accept_cookies_btn = driver.find_elements(By.ID,'onetrust-accept-btn-handler')
	if accept_cookies_btn:
		accept_cookies_btn[0].click()

	# Pull out the current username and alliance_name. 
	extract_user_and_alliance(driver)
	
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
	try:
		wait = WebDriverWait(driver, 10)
	
		# Start at the alliance_info page.
		driver.get('https://marvelstrikeforce.com/en/alliance/members')

		# Click on the Scopely Login button.
		login = wait.until(EC.element_to_be_clickable((By.ID, 'scopely-login')))
		login.click()

		# Find and enter Scopely ID for login.
		login_field = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'ant-input')))
		login_field.send_keys(scopely_user)

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
	
			# Find login field and enter password to complete login process.
			pass_field = wait.until(EC.presence_of_element_located((By.XPATH,f'//input[@data-test-id="InputPassword"]')))	
			pass_field.send_keys(scopely_pass)
\
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



def extract_user_and_alliance(driver):

	# Unsure if I really need the try/except setup.
	try:
		# Open the user menu
		buttons = []
		while not buttons:
			buttons = [button for button in driver.find_elements(By.CLASS_NAME, 'user-menu-trigger') if button.aria_role == 'button']

		# Open the user menu
		buttons[0].click()

		# Make note of Username
		username = []
		while not username:
			username = [elem for elem in driver.find_elements(By.ID, 'graphic-menu-title') if elem.aria_role == 'generic' and elem.text]

		# Make note of Alliance Name
		alliance_name = []
		while not alliance_name:
			alliance_name = [elem for elem in driver.find_elements(By.ID, 'alliance-graphic-menu-title') if elem.aria_role == 'generic' and elem.text]

		# Close the menu after information extracted
		buttons[0].click()

		# May need to make note of color information here. 
		driver.username      = remove_tags(username[0].text)
		driver.alliance_name = remove_tags(alliance_name[0].text).strip()

	except TimeoutException:
		print("Timed out. user-menu-trigger never became available.")

		soup = BeautifulSoup(driver.page_source, 'html.parser')
		write_file ('./TimeoutException.html', soup.prettify())
		raise

	except ElementClickInterceptedException:
		print ("ElementClickInterceptedException")

		soup = BeautifulSoup(driver.page_source, 'html.parser')
		write_file ('./InterceptedException.html', soup.prettify())
		raise

	return
		

