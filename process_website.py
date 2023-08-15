

from selenium import webdriver
from selenium.webdriver.common.by import By
from parse_contents import *
from user_and_pass import *

processed_players = {}	# roster stats for each player
char_stats = {}			# min/max stats and portrait path for individual heroes

import datetime
import time


def process_website(char_stats={}, processed_players={}):

	alliance_path = 'https://marvelstrikeforce.com/en/alliance/members'
	alliance_title = 'Alliance | MARVEL Strike Force Database'

	options = webdriver.ChromeOptions()
	options.add_argument('--log-level=3')

	# If login/password are provided, run this as a headless server.
	# If no passwords are provided, the user will need to Interactively log on to allow the rest of the process to run.
	if (scopely_user and scopely_pass) or (facebook_user and facebook_pass):
		options.add_argument('--headless=new')
	
	driver = webdriver.Chrome(options=options)
	driver.get(alliance_path)

	# Authentication Page
	if driver.title == 'MARVEL Strike Force':

		# Bypass, Scopely authentication not working yet.
		if scopely_user and scopely_pass:
		
			successful = 0
			while not successful:
				try:
					login = driver.find_element(By.ID, 'scopely-login')
					print (login)
					login.click()
					successful=1
					time.sleep(1)
				except:
					continue

			successful = 0
			while not successful:
				try:
					login_field = driver.find_element(By.CLASS_NAME, 'ant-input')
					login_field.send_keys(scopely_user)
					successful=1
				except:
					continue
					
			successful = 0
			while not successful:
				try:
					login_button = driver.find_element(By.CLASS_NAME, 'submitButton')
					login_button.click()
					time.sleep(2)
					successful=1
				except:
					continue
				
			successful = 0
			while not successful:
				try:
					use_password = driver.find_element(By.CLASS_NAME, 'link')
					use_password.click()
					time.sleep(1)
					successful=1
				except:
					continue
					
			successful = 0
			while not successful:
				try:
					pass_field = driver.find_element(By.CLASS_NAME, 'password-with-toggle')
					pass_field.send_keys(scopely_pass)
					successful = 1
				except:
					continue

			successful = 0
			while not successful:
				try:
					login_button = driver.find_element(By.CLASS_NAME, 'button')
					login_button.click()
					successful = 1
				except:
					continue
		
		# Defaulting to Facebook login.
		elif facebook_user or facebook_pass:
			login = driver.find_element(By.ID, 'facebook-login')
			login.click()
			time.sleep(1)

			#login = driver.find_element(By.ID, 'scopely-login')	# Not yet implemented.

			login_field = driver.find_element(By.ID,'email')
			login_field.send_keys(facebook_user)

			password_field = driver.find_element(By.ID,'pass')
			password_field.send_keys(facebook_pass)

			login_button = driver.find_element(By.ID,'loginbutton')
			login_button.click()

		# Waiting while you login or approve login via 2FA.
		while driver.title != alliance_title:
			time.sleep(1)

	# We are in, wait a second before starting.
	time.sleep(2)

	#alliance_info = extract_alliance_info(driver.find_element(By.ID,"app").text) 
	alliance_info = parse_alliance(driver.page_source) 

	# Remove any members in processed_players who are no longer in the alliance.
	for member in processed_players.keys():
		if member != 'alliance_info' and member not in alliance_info['members']:
			print ('%s is no longer in this alliance. Removing from the output.' % member)
			processed_players.pop[member]

	# We are in, wait a second before starting.
	time.sleep(2)

	buttons = driver.find_elements(By.CLASS_NAME, 'button')
	
	# Keep track of progress in case Selenium raises an exception on .click()
	i = 0

	line_on = 0
	
	while i<(len(buttons)-1):
		try:
			for i in range(i,len(buttons)):
				roster_name = alliance_info['order'][line_on]
				button = buttons[i]

				# Button width is the only determining factor.
				# 53/54 = Roster Button, 58/59 = Add Friend

				# This is the Add friend button. Increment the line_on.
				if button.size['width'] in (58,59):
					line_on += 1
					continue
				# This is NOT a Roster button. Skipping!
				elif button.size['width'] not in (53,54):
					continue

				# If we found the roster button on my own entry, there will not be an "Add friend" button.
				if alliance_info['me'] == roster_name:
					line_on += 1

				# We found a Roster Button. Should we click it?
				# If we already have an entry for this person, see if it's up-to-date/recent
				if roster_name in processed_players:
					time_since_last = datetime.datetime.now()-processed_players[roster_name]['last_update']
					
					# Less than an hour since last refresh, or power hasn't changed, let's skip it.
					if (time_since_last.total_seconds() < 3600) or (processed_players[roster_name]['tot_power'] == alliance_info['members'][roster_name]['tcp']):
						continue

				button.click()
				while len(driver.page_source)<1000000:
					# Still loading
					time.sleep(1)
				
				# Pass the contents to our scraping routines for stat extraction.
				parse_characters(driver.page_source, char_stats, processed_players)
				
				driver.back()
				time.sleep(1)
				while driver.title != alliance_title:
					time.sleep(1)

				# Need to refresh the buttons definition.
				buttons = driver.find_elements(By.CLASS_NAME, 'button')
		except:
			# Accidentally made it to Roster page, need to go back.
			if driver.title != alliance_title:
				driver.back()
				time.sleep(1)

			# Wait until we actually get back.
			while driver.title != alliance_title:
				time.sleep(1)

			# Refresh our button list, might have been clicking on a stale object.
			buttons = driver.find_elements(By.CLASS_NAME, 'button')

	# After everything, update processed_players with the current alliance_info.
	processed_players['alliance_info'] = alliance_info

	return char_stats,processed_players

