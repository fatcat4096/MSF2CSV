#!/usr/bin/env python3
# Encoding: UTF-8
"""login.py
Log on to MSF.gg and return a driver to use for parsing.
"""

from log_utils import *

import time
import getpass
import keyring
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from generate_local_files import *

@timed(level=3)
def get_driver(headless=False):

	# Build the driver
	options = webdriver.ChromeOptions()
	options.add_argument('--log-level=3')
	options.add_argument('--accept-lang=en-US')	
	options.add_experimental_option('excludeSwitches', ['enable-logging'])

	prefs = {"download.default_directory" : "C:\\Users\\baker\\dev\\msf\\csv"}
	options.add_experimental_option("prefs",prefs)

	# If headless requested, run this as a headless server.
	if headless:
		options.add_argument('--headless=new')

	return webdriver.Chrome(options=options)


# Login to the website. Return a Selenium Driver object for a given login.
#
# If no login specified, use the default login

@timed(level=3)
def login(prompt=False, headless=False, external_driver=None, scopely_login=''):

	alliance_info_url = 'https://marvelstrikeforce.com/en/alliance/members'

	# If we were passed in a cached driver, we're ready to go.
	if external_driver:
		driver = external_driver

	# If a new driver, still need to login:
	else:
		# Start by checking to see if we have / need credentials.
		scopely_login, scopely_pass = get_scopely_creds(prompt, scopely_login)

		driver = get_driver(headless)
		# Start at the alliance_info page.
		driver.get(alliance_info_url)

		scopely_website_login(driver, scopely_login, scopely_pass)

	# If our page doesn't include the Alliance Members table, never successfully logged in. 

	# Waiting while you login manually, automatically, or approve login via 2FA.
	try:
		WebDriverWait(driver, 300).until(EC.presence_of_element_located((By.CLASS_NAME, 'alliance-members')))
	except TimeoutException:
		print("Timed out. Unable to complete login.")

		# NEED TO MAKE SURE THAT CALLING ROUTINE HANDLES driver == None PROPERLY
		return

	# Click on the Accept Cookies button if it is presented. This dialog prevents roster processing.
	accept_cookies_btn = driver.find_elements(By.ID,'onetrust-accept-btn-handler')
	if accept_cookies_btn:
		accept_cookies_btn[0].click()

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
	
		# Click on the Scopely Login button.
		login = wait.until(EC.element_to_be_clickable((By.ID, 'scopely-login')))
		login.click()

		# Find and enter Scopely ID for login.
		login_field = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'ant-input')))
		login_field.send_keys(scopely_user)
				
		login_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'submitButton')))
		login_button.click()

		# If user is relying on access e-mail from Scopely, then no password is used.
		# Return control to the user and allow them to click on the link in the e-mail to complete login.
		if scopely_pass == 'wait-for-email':
			return

		# Enter password instead of using e-mailed link.
		use_password = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'link')))
		use_password.click()
				
		# Find login field and enter password to complete login process.
		pass_field = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'password-with-toggle')))
		pass_field.send_keys(scopely_pass)

		login_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'button')))
		login_button.click()

	except TimeoutException:
		print("Timed out. Unable to complete login.")


def click_on_csv_button(driver):
	button = driver.find_elements(By.CLASS_NAME, 'download-button')

	# Only call click if button was located.
	if button:
		button[0].click()
		
	return driver.find_elements(By.CLASS_NAME, 'download-option')

def click_on_info_button(driver):
	downloads = click_on_csv_button(driver)

	# Narrow down the search to the "INFO" Download Option.
	button = downloads[0].find_elements(By.TAG_NAME, 'button')

	# Only call click if button was located.
	if button:
		button[0].click()						
	
def click_on_roster_button(driver):
	downloads = click_on_csv_button(driver)

	# Narrow down the search to the "INFO" Download Option.
	button = downloads[1].find_elements(By.TAG_NAME, 'button')

	# Only call click if button was located.
	if button:
		button[0].click()						

