
from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from parse_contents import *

from time import sleep

import datetime
import keyring
import os
import pickle
import traceback

def process_website(alliance_name, char_stats={}, processed_players={}):

	alliance_path = 'https://marvelstrikeforce.com/en/alliance/members'
	alliance_title = 'Alliance | MARVEL Strike Force Database'

	options = webdriver.ChromeOptions()
	options.add_argument('--log-level=3')

	scopely_cred  = keyring.get_credential('scopely'+alliance_name,'')
	facebook_cred = keyring.get_credential('facebook'+alliance_name,'')

	# If login/password are provided, run this as a headless server.
	# If no passwords are provided, the user will need to Interactively log on to allow the rest of the process to run.
	#if scopely_cred or facebook_cred:
	#	options.add_argument('--headless=new')
	
	driver = webdriver.Chrome(options=options)
	driver.get(alliance_path)

	# Default to Scopely Login, does not require 2FA.
	if scopely_cred:
		scopely_login(driver, scopely_cred.username, scopely_cred.password)

	# If Scopely login not defined, use Facebook login instead.
	elif facebook_cred:
		facebook_login(driver, facebook_cred.username, facebook_cred.password)
		
	# Waiting while you login or approve login via 2FA.
	while driver.title != alliance_title:
		sleep(1)

	# We are in, wait a second before starting.
	sleep(1)

	alliance_info = parse_alliance(driver.page_source) 

	# Remove any members in processed_players who are no longer in the alliance.
	for member in list(processed_players):
		if member != 'alliance_info' and member not in alliance_info['members']:
			print ('%s is no longer in this alliance. Removing from the output.' % member)
			del processed_players[member]

	# We are in, wait a second before starting.
	sleep(1)

	buttons = driver.find_elements(By.CLASS_NAME, 'button')
	
	# Keep track of progress in case Selenium raises an exception on .click()
	i = 0

	line_on = 0

	watching_the_y = False
	previous_y     = 0
	
	while i<(len(buttons)-1):
		try:
			for i in range(i,len(buttons)):
				button = buttons[i]

				# See if the button we're looking at is on the next line.
				if watching_the_y and previous_y != button.location['y']:
					line_on += 1
					watching_the_y = False
				
				roster_name = alliance_info['order'][line_on]

				# Button width is the only determining factor.
				# 53/54 = Roster Button, 58/59 = Add Friend or Copy Discord ID

				# This and Add Friend button or Copy Discord ID. Start watching the Y value.
				if button.size['width'] in (58,59):
					watching_the_y = True
					previous_y = button.location['y']
					continue
				# This is NOT a Roster button. Skipping!
				elif button.size['width'] not in (53,54):
					continue

				# If we found the roster button on my own entry, there will not be an "Add friend" button.
				if alliance_info['me'] == roster_name:
					watching_the_y = True
					previous_y = button.location['y']

				# We found a Roster Button. Should we click it?
				# If we already have an entry for this person, see if it's up-to-date/recent
				if roster_name in processed_players and 'last_download' in processed_players[roster_name]:
					time_since_last = datetime.datetime.now()-processed_players[roster_name]['last_download']
					
					# Less than an hour since last refresh, or power hasn't changed, let's skip it.
					if (time_since_last.total_seconds() < 3600) or (processed_players[roster_name]['tot_power'] == alliance_info['members'][roster_name]['tcp']):
						print ("Found",roster_name,"but",["too soon,","unchanged,"][time_since_last.total_seconds() > 3600],"skipping...")
						continue

				button.click()

				timer = 0
				
				# Page loads in sections, will be > 1MB after roster information loads.
				while len(driver.page_source)<1000000:
					# Still loading
					sleep(1)
					timer += 1
					
					# Call refresh if load failed to complete after 5 seconds.
					if timer == 5:
						driver.refresh()
					# Just give up after 10 seconds.
					elif timer == 10:
						break

				# If page loaded, pass contents to scraping routines for stat extraction.
				if len(driver.page_source)>1000000:
					parse_characters(driver.page_source, char_stats, processed_players)
					processed_players[roster_name]['last_download'] = datetime.datetime.now()
				
				# Back up and move on to the next roster on the page.
				driver.back()
				sleep(1)
				while driver.title != alliance_title:
					sleep(1)

				# Need to refresh the buttons definition.
				buttons = driver.find_elements(By.CLASS_NAME, 'button')
		except:
			# Exception thrown when button->click() called while button is offscreen
			#traceback.print_exc()
			
			#print("TRIPPED!")
			
			# Accidentally made it to Roster page, need to go back.
			if driver.title != alliance_title:
				driver.back()
				sleep(1)

			# Wait until we actually get back.
			while driver.title != alliance_title:
				sleep(1)

			# Refresh our button list, might have been clicking on a stale object.
			buttons = driver.find_elements(By.CLASS_NAME, 'button')

	# Close the Selenium session.
	driver.close()

	# After everything, update processed_players with the current alliance_info.
	processed_players['alliance_info'] = alliance_info

	# cache the updated roster info to disk.
	pickle.dump([char_stats,processed_players],open('cached_data-'+alliance_name,'wb'))

	return char_stats,processed_players


def get_strike_teams(driver,raid='alpha',diff=0):
	#
	strike_teams = []
	#
	for team_num in range(3):
		wait = WebDriverWait(driver, 10)
		#
		driver.get('https://marvelstrikeforce.com/en/alliance/maps/raid_%s_d/%i?strikeTeam=%i' % (raid, diff, team_num+1))
		wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'alliance-user')))
		#
		strike_teams.append(parse_teams(driver.page_source))
	#
	return strike_teams


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