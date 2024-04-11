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

	# If headless requested, run this as a headless server.
	if headless:
		options.add_argument('--headless=new')

	return webdriver.Chrome(options=options)


# Login to the website. Return the Selenium Driver object.
@timed(level=3)
def login(prompt=False, headless=False, external_driver=None, url = 'https://marvelstrikeforce.com/en/alliance/members'):

	# Take care of our lazy clients
	driver = external_driver or get_driver(headless)

	# Start at the alliance_info page.
	driver.get(url)

	# If a new driver, still need to login:
	if not external_driver:

		# Start by checking to see if we have / need credentials.
		facebook_cred, scopely_cred = get_creds(prompt)

		# Default to Scopely Login, does not require 2FA.
		if scopely_cred:
			scopely_login(driver, scopely_cred.username, scopely_cred.password)

		# If Scopely login not defined, use Facebook login instead.
		elif facebook_cred:
			facebook_login(driver, facebook_cred.username, facebook_cred.password)
	
	# Waiting while you login manually, automatically, or approve login via 2FA.
	try:
		WebDriverWait(driver, 300).until(EC.presence_of_element_located((By.CLASS_NAME, 'alliance-roster')))
	except TimeoutException:
		print("Timed out. Unable to complete login.")

	# Click on the Accept Cookies button if it is presented. This dialog prevents roster processing.
	accept_cookies_btn = driver.find_elements(By.ID,'onetrust-accept-btn-handler')
	if accept_cookies_btn:
		accept_cookies_btn[0].click()

	return driver


# Check for saved credentials. If none saved, ask if would like to cache them.
@timed(level=3)
def get_creds(prompt, facebook_cred = None, scopely_cred = None):

	# If frozen, work in the same directory as the executable.
	app_format = ['python','frozen'][getattr(sys, 'frozen', False)]

	facebook_login = keyring.get_password(f'msf2csv.facebook.{app_format}', 'msfgg.facebook.login')
	if facebook_login:
		facebook_cred = keyring.get_credential(f'msf2csv.facebook.{app_format}', facebook_login)

	scopely_login = keyring.get_password(f'msf2csv.scopely.{app_format}','msfgg.scopely.login')
	if scopely_login:
		scopely_cred  = keyring.get_credential(f'msf2csv.scopely.{app_format}',scopely_login)

	# If this is the first launch of a frozen executable, go ahead and prompt for login.
	first_launch = 'strike_teams' not in globals()
			
	# Check for prompt flag or presence of 'noprompt' file. 
	if prompt or first_launch or not (facebook_cred or scopely_cred):
	
		print ('\nWelcome to MSF2CSV!\n')
	
		# If prompt flag not used, ask if person would like to cache their credentials
		if prompt or input("Would you like to cache your credentials? (Y/N): ").upper() == 'Y':

			# Ask which login they would like to use.
			if input("Would you like to cache 'F'acebook or 'S'copely credentials? (F/S): ").upper() == "F":

				# Prompt for each login / pass and store in keyring.
				facebook_login = input("Facebook Login: ")
				keyring.set_password(f'msf2csv.facebook.{app_format}', 'msfgg.facebook.login', facebook_login)
				keyring.set_password(f'msf2csv.facebook.{app_format}', facebook_login, getpass.getpass(prompt="Facebook Password: "))

				# Load the credential before returning.
				facebook_cred = keyring.get_credential(f'msf2csv.facebook.{app_format}',facebook_login)
			else:
				scopely_login = input("Scopely Login (e-mail address): ")
				keyring.set_password(f'msf2csv.scopely.{app_format}', 'msfgg.scopely.login', scopely_login)

				# Setting a default value to flag if password isn't used.
				scopely_pass = getpass.getpass(prompt="Scopely Password (leave blank if using e-mail link): ") or 'wait-for-email'
				#print (f'msf2csv.scopely.{app_format}', scopely_login, scopely_pass)
				
				keyring.set_password(f'msf2csv.scopely.{app_format}', scopely_login, scopely_pass)

				# Load the credential before returning.
				scopely_cred = keyring.get_credential(f'msf2csv.scopely.{app_format}',scopely_login)

	return facebook_cred, scopely_cred


# Auto Login via Scopely authentication using cached credentials.
@timed(level=4)
def scopely_login(driver, scopely_user, scopely_pass):
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


# Auto Login via Facebook authentication using cached credentials.
@timed(level=4)
def facebook_login(driver, facebook_user, facebook_pass):
	try:
		wait = WebDriverWait(driver, 10)
	
		# Click on the Facebook Login button.
		login = wait.until(EC.element_to_be_clickable((By.ID, 'facebook-login')))
		login.click()

		# Fill in username and password.
		login_field = wait.until(EC.presence_of_element_located((By.ID,'email')))
		login_field.send_keys(facebook_user)

		pass_field = wait.until(EC.presence_of_element_located((By.ID,'pass')))
		pass_field.send_keys(facebook_pass)

		# Click the login button to generate 2FA challenge.
		login_button = wait.until(EC.element_to_be_clickable((By.ID, 'loginbutton')))
		login_button.click()

	except TimeoutException:
		print("Timed out. Unable to complete login.")


