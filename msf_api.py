#!/usr/bin/env python3
# Encoding: UTF-8
"""msf_api.py
Basic implementation of MSF API
"""


from log_utils import timed

from urllib.parse import quote_plus
import base64
import requests
import secrets
import time

# Redirect URI for Enroll-a-Bot
REDIRECT_URI = 'https://enroll-a-bot.netlify.app/enroll.html'

# Static URLs for requests
API_ENDPOINT    = 'https://api.marvelstrikeforce.com'
OAUTH_ENDPOINT  = 'https://hydra-public.prod.m3.scopelypv.com/oauth2/auth'
TOKEN_ENDPOINT  = 'https://hydra-public.prod.m3.scopelypv.com/oauth2/token'
REVOKE_ENDPOINT = 'https://hydra-public.prod.m3.scopelypv.com/oauth2/revoke'


# Generate a Session ID and URL to link account
@timed(level=3)
def get_session_and_link(CLIENT_ID, SESSION_ID=None):

	# Name of the slash command in MSF RosterBot
	DISCORD_CMD = 'alliance'

	# Generate the shared secret (if not provided) and use as the session_id
	if not SESSION_ID:
		SESSION_ID = secrets.token_bytes(32).hex()

	# Specify the requested scopes
	SCOPE_REQ = quote_plus('openid offline m3p.f.pr.pro m3p.f.ar.pro m3p.f.ar.ros')

	# Create the final Link
	LINK_URL = f'{OAUTH_ENDPOINT}?response_type=code&client_id={CLIENT_ID}&redirect_uri={quote_plus(REDIRECT_URI)}&state={DISCORD_CMD}:keys:{SESSION_ID}&scope={SCOPE_REQ}'

	return SESSION_ID, LINK_URL



# Construct and encode our Client Token from MSF.gg app registration
@timed(level=3)
def construct_token(CLIENT_ID, CLIENT_SECRET):

	# Base64 encode the combined Client ID and Secret
	CLIENT_TOKEN = base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode('ascii')).decode('ascii')

	return CLIENT_TOKEN



# Verify access_token is valid -- give ourselves a minute to complete workflow
@timed(level=3)
def auth_valid(AUTH):
	return AUTH and AUTH.get('expires_at') and time.time() + 60 < AUTH['expires_at']



# Headers used for POST requests
@timed(level=3)
def post_headers(CLIENT_TOKEN):

	return {	'Content-Type' : 'application/x-www-form-urlencoded',
				'Authorization': f'Basic {CLIENT_TOKEN}' }



# Headers used for GET requests
@timed(level=3)
def get_headers(ACCESS_TOKEN):

	# Extract the ACCESS_TOKEN if provided full AUTH
	if type(ACCESS_TOKEN) is dict:
		ACCESS_TOKEN = ACCESS_TOKEN['access_token']

	return {	'x-api-key': '17wMKJLRxy3pYDCKG5ciP7VSU45OVumB2biCzzgw',
				'Authorization': f'Bearer {ACCESS_TOKEN}' }



# Request for original AUTH token
@timed(level=3)
def request_auth(AUTH_CODE, CLIENT_TOKEN):

	# Attempt up to three times
	for x in range(3):

		# Send the request to the Token Endpoint
		params = {	'grant_type'   : 'authorization_code',
					'code'         : AUTH_CODE,
					'redirect_uri' : REDIRECT_URI }

		# Send request for token
		response = requests.post(
			headers = post_headers(CLIENT_TOKEN),
			url     = TOKEN_ENDPOINT,
			data    = params
		)

		# Exit loop if we got a successful response
		if response.ok:
			break

	return response



# Request for a refresh AUTH using the Refresh token
@timed(level=3)
def refresh_auth(AUTH, CLIENT_TOKEN):

	# Attempt up to three times
	for x in range(3):

		# Request a refresh from the Token Endpoint
		params = {	'grant_type'    : 'refresh_token',
					'refresh_token' : AUTH['refresh_token'] }

		# Send request for new access_token
		response = requests.post(
			headers = post_headers(CLIENT_TOKEN),
			url     = TOKEN_ENDPOINT,
			data    = params
		)

		# If valid response, parse the AUTH returned then return
		if response.ok:
			parse_auth(response, AUTH)
			break

	return response



# Update provided AUTH with info from Response
@timed(level=3)
def parse_auth(auth_token, AUTH):

	token_data = auth_token.json()

	AUTH.update({
		'access_token' : token_data['access_token'],
		'expires_at'   : token_data['expires_in'] + int(time.time()),
		'refresh_token': token_data.get('refresh_token'),
		'scope'        : token_data['scope'],
		'token_type'   : token_data['token_type'],
		'updated'      : True	# Flag to update DB
	})

	return AUTH



# Need this for the name of the Player 	
@timed(level=3)
def request_player_info(ACCESS_TOKEN):

	# Attempt up to three times
	for x in range(3):

		# Send request for Alliance Info
		response = requests.get(
			headers = get_headers(ACCESS_TOKEN),
			url     = f'{API_ENDPOINT}/player/v1/card', 
		)

		# Exit loop if we got a successful response
		if response.ok:
			break

		#print ('API request -- request_player_info() failed, retrying...')

	return response



# Need this for the Alliance name and stats
@timed(level=3)
def request_alliance_info(ACCESS_TOKEN):

	# Attempt up to three times
	for x in range(3):

		# Send request for Alliance Info
		response = requests.get(
			headers = get_headers(ACCESS_TOKEN),
			url     = f'{API_ENDPOINT}/player/v1/alliance/card', 
		)

		# Exit loop if we got a successful response
		if response.ok:
			break

		#print ('API request -- request_alliance_info() failed, retrying...')

	return response


# Need this for the Alliance members 	
@timed(level=3)
def request_alliance_members(ACCESS_TOKEN):

	# Attempt up to three times
	for x in range(3):

		# Send request for Alliance Info
		response = requests.get(
			headers = get_headers(ACCESS_TOKEN),
			url     = f'{API_ENDPOINT}/player/v1/alliance/members',
		)

		# Exit loop if we got a successful response
		if response.ok:
			break

		#print ('API request -- request_alliance_members() failed, retrying...')

	return response



# Need this for the Roster information 	
@timed(level=3)
def request_member_roster(ACCESS_TOKEN, memberid, asOf=None):

	PARAM_SINCE = {'since':asOf} if asOf else {}

	# Attempt up to three times
	for x in range(3):

		# Send request for new access_token
		response = requests.get(
			headers = get_headers(ACCESS_TOKEN),
			url     = f'{API_ENDPOINT}/player/v1/roster/member/{memberid}',	# Individual roster request  
			params  = {'statsFormat':'csv'} | PARAM_SINCE, 							# Hash for previous API request
		)

		# Exit loop if we got a successful response
		if response.ok:
			break

		#print ('API request -- request_member_roster() failed, retrying...')

	return response



# Request all character information -- used for Char names, Portrait info
@timed(level=3)
def request_char_info(ACCESS_TOKEN, PLAYABLE=True):

	# Attempt up to three times
	for x in range(3):

		# Send request for Character Info
		response = requests.get(
			headers =  get_headers(ACCESS_TOKEN),
			url     = f'{API_ENDPOINT}/game/v1/characters',
			params  = {
						'itemFormat':'id',
						'traitFormat':'id',
						'status':'playable' if PLAYABLE else 'unplayable',
					  },
		)

		# Exit loop if we got a successful response
		if response.ok:
			break

		#print ('API request -- request_char_info() failed, retrying...')

	return response


