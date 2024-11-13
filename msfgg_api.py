#!/usr/bin/env python3
# Encoding: UTF-8
"""msf_api.py
Basic implementation of MSF API
"""


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
def get_session_and_link(CLIENT_ID, DISCORD_CMD = 'alliance'):

	# Generate the shared secret and use as the session_id
	SESSION_ID = secrets.token_bytes(32).hex()

	# Specify the requested scopes
	SCOPE_REQ = quote_plus('openid offline m3p.f.pr.pro m3p.f.ar.pro m3p.f.ar.ros')

	# Create the final Link
	LINK_URL = f'{OAUTH_ENDPOINT}?response_type=code&client_id={CLIENT_ID}&redirect_uri={quote_plus(REDIRECT_URI)}&state={DISCORD_CMD}:keys:{SESSION_ID}&scope={SCOPE_REQ}'

	return SESSION_ID, LINK_URL



# Construct and encode our Client Token from MSF.gg app registration
def construct_token(CLIENT_ID, CLIENT_SECRET):

	# Base64 encode the combined Client ID and Secret
	CLIENT_TOKEN = base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode('ascii')).decode('ascii')

	return CLIENT_TOKEN



# Verify access_token is valid -- give ourselves a minute to complete workflow
def auth_valid(AUTH):
	return AUTH and AUTH.get('expires_at') and time.time() + 60 < AUTH['expires_at']



# Headers used for POST requests
def post_headers(CLIENT_TOKEN):
	return {	'Content-Type' : 'application/x-www-form-urlencoded',
				'Authorization': f'Basic {CLIENT_TOKEN}' }



# Headers used for GET requests
def get_headers(ACCESS_TOKEN):
	return {	'x-api-key': '17wMKJLRxy3pYDCKG5ciP7VSU45OVumB2biCzzgw',
				'Authorization': f'Bearer {ACCESS_TOKEN}' }



# Request for original AUTH token
def request_auth(AUTH_CODE, CLIENT_TOKEN):

	# Send the request to the Token Endpoint
	params = {	'grant_type'   : 'authorization_code',
				'code'         : AUTH_CODE,
				'redirect_uri' : REDIRECT_URI }

	# Send request for token
	auth_token = requests.post(
		headers = post_headers(CLIENT_TOKEN),
		url     = TOKEN_ENDPOINT,
		data    = params
	)

	return auth_token



# Request for a refresh AUTH using the Refresh token
def refresh_auth(AUTH, CLIENT_TOKEN):

	# Request a refresh from the Token Endpoint
	params = {	'grant_type'    : 'refresh_token',
				'refresh_token' : AUTH['refresh_token'] }

	# Send request for new access_token
	auth_token = requests.post(
		headers = post_headers(CLIENT_TOKEN),
		url     = TOKEN_ENDPOINT,
		data    = params
	)

	# If bad response, return the stale AUTH
	if not auth_token.ok:
		return AUTH

	parse_auth(auth_token, AUTH)



# Update AUTH with info from Response
def parse_auth(auth_token, AUTH={}):

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
def request_player_info(ACCESS_TOKEN):

	# Send request for Alliance Info
	response = requests.get(
		headers = get_headers(ACCESS_TOKEN),
		url     = f'{API_ENDPOINT}/player/v1/card', 
	)

	return response



# Need this for the Alliance name and stats
def request_alliance_info(ACCESS_TOKEN):

	# Send request for Alliance Info
	response = requests.get(
		headers = get_headers(ACCESS_TOKEN),
		url     = f'{API_ENDPOINT}/player/v1/alliance/card', 
	)

	# If bad response, return None
	if not response.ok:
		return

	return response



# Need this for the Alliance members 	
def request_alliance_members(ACCESS_TOKEN):

	# Send request for Alliance Info
	response = requests.get(
		headers = get_headers(ACCESS_TOKEN),
		url     = f'{API_ENDPOINT}/player/v1/alliance/members',
	)

	# If bad response, return None
	if not response.ok:
		return

	return response



# Need this for the Roster information 	
def request_member_roster(ACCESS_TOKEN, memberid, asOf=None):

	# Send request for new access_token
	response = requests.get(
		headers = get_headers(ACCESS_TOKEN),
		url     = f'{API_ENDPOINT}/player/v1/roster/member/{memberid}',	# Individual roster request  
		params  = {'since':asOf} if asOf else {}, 						# Hash for previous API request
	)

	# May not need. See what's in response.json()
	if response.status_code == 344:
		print (f'Data is UNCHANGED. Nothing to update.')
		print (f'{response.json()=}')
		return {}
	# If bad response, return None
	elif not response.ok:
		return

	return response



# Request all character information -- used for Char names, Portrait info
def request_char_info(ACCESS_TOKEN):

	# Send request for Character Info
	response = requests.get(
		headers =  get_headers(ACCESS_TOKEN),
		url     = f'{API_ENDPOINT}/game/v1/characters',
		params  = {'stats':'playable'},
	)

	# If bad response, return None
	if not response.ok:
		return

	return response



# Request all trait information -- used for extracted traits
def request_traits(ACCESS_TOKEN):

	# Send request for Trait List
	response = requests.get(
		headers =  get_headers(ACCESS_TOKEN),
		url     = f'{API_ENDPOINT}/game/v1/traits',
	)

	# If bad response, return None
	if not response.ok:
		return

	return response
