#!/usr/bin/env python3
# Encoding: UTF-8
"""login.py
Log on to MSF.gg and return a driver to use for parsing.
"""

import time
import getpass
import keyring
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait


# Login to the website. Return the Selenium Driver object.
def login(prompt=False, headless=False, url = 'https://marvelstrikeforce.com/en/alliance/members'):

	options = webdriver.ChromeOptions()
	options.add_argument('--log-level=3')
	options.add_argument('--accept-lang=en-US')	
	options.add_experimental_option('excludeSwitches', ['enable-logging'])

	facebook_cred, scopely_cred = get_creds(prompt)

	# If login/password are provided, run this as a headless server.
	# If no passwords are provided, the user will need to Interactively log on to allow the rest of the process to run.
	if headless: #scopely_cred or facebook_cred:
		options.add_argument('--headless=new')

	driver = webdriver.Chrome(options=options)
	driver.get(url)

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

	return driver


# Check for saved credentials. If none saved, ask if would like to cache them.
def get_creds(prompt, facebook_cred = None, scopely_cred = None):

	# If frozen, work in the same directory as the executable.
	app_format = ['python','frozen'][getattr(sys, 'frozen', False)]

	facebook_login = keyring.get_password(f'msf2csv.facebook.{app_format}', 'msfgg.facebook.login')
	if facebook_login:
		facebook_cred = keyring.get_credential(f'msf2csv.facebook.{app_format}', facebook_login)

	scopely_login = keyring.get_password(f'msf2csv.scopely.{app_format}','msfgg.scopely.login')
	if scopely_login:
		scopely_cred  = keyring.get_credential(f'msf2csv.scopely.{app_format}',scopely_login)

	# Check for prompt flag or presence of 'noprompt' file. 
	if prompt or not (facebook_cred or scopely_cred):

		# If prompt flag not used, ask if person would like to cache their credentials
		if prompt or input("Would you like to cache your credentials? (Y/N): ").upper() == 'Y':

			# Ask which login they would like to use.
			if input("Welcome to MSF2CSV!\n\nWould you like to cache 'F'acebook or 'S'copely credentials? (F/S): ").upper() == "F":

				# Prompt for each login / pass and store in keyring.
				facebook_login = input("Facebook Login: ")
				keyring.set_password(f'msf2csv.facebook.{app_format}', 'msfgg.facebook.login', facebook_login)
				keyring.set_password(f'msf2csv.facebook.{app_format}', facebook_login, getpass.getpass(prompt="Facebook Password:"))

				# Load the credential before returning.
				facebook_cred = keyring.get_credential(f'msf2csv.facebook.{app_format}',facebook_login)
			else:
				scopely_login = input("Scopely Login: ")
				keyring.set_password(f'msf2csv.scopely.{app_format}', 'msfgg.scopely.login', scopely_login)
				keyring.set_password(f'msf2csv.scopely.{app_format}', scopely_login, getpass.getpass(prompt="Scopely Password:"))

				# Load the credential before returning.
				scopely_cred = keyring.get_credential(f'msf2csv.scopely.{app_format}',scopely_login)

	return facebook_cred, scopely_cred


# Auto Login via Scopely authentication using cached credentials.
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


