#!/usr/bin/env python3
# Encoding: UTF-8
"""msf_api.py
Basic implementation of MSF API
"""


import base64
import requests
import secrets
import time

from requests.adapters  import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse       import quote_plus


# Redirect URI for Enroll-a-Bot
REDIRECT_URI = 'https://enroll-a-bot.netlify.app/enroll.html'

# Static URLs for requests
API_ENDPOINT    = 'https://api.marvelstrikeforce.com'
OAUTH_ENDPOINT  = 'https://hydra-public.prod.m3.scopelypv.com/oauth2/auth'
TOKEN_ENDPOINT  = 'https://hydra-public.prod.m3.scopelypv.com/oauth2/token'
REVOKE_ENDPOINT = 'https://hydra-public.prod.m3.scopelypv.com/oauth2/revoke'


# Generate a Session ID and URL to link account
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
def construct_token(CLIENT_ID, CLIENT_SECRET):

	# Base64 encode the combined Client ID and Secret
	CLIENT_TOKEN = base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode('ascii')).decode('ascii')

	return CLIENT_TOKEN



# Verify access_token is valid -- give ourselves a minute to complete workflow
def auth_valid(AUTH):
	return AUTH and AUTH.get('expires_at') and time.time() + 60 < AUTH['expires_at']



#888888b.   .d88888b.   .d8888b. 88888888888      8888888b.  8888888888 .d88888b.  888     888 8888888888 .d8888b. 88888888888 .d8888b.  
#88   Y88b d88P" "Y88b d88P  Y88b    888          888   Y88b 888       d88P" "Y88b 888     888 888       d88P  Y88b    888    d88P  Y88b 
#88    888 888     888 Y88b.         888          888    888 888       888     888 888     888 888       Y88b.         888    Y88b.      
#88   d88P 888     888  "Y888b.      888          888   d88P 8888888   888     888 888     888 8888888    "Y888b.      888     "Y888b.   
#888888P"  888     888     "Y88b.    888          8888888P"  888       888     888 888     888 888           "Y88b.    888        "Y88b. 
#88        888     888       "888    888          888 T88b   888       888 Y8b 888 888     888 888             "888    888          "888 
#88        Y88b. .d88P Y88b  d88P    888          888  T88b  888       Y88b.Y8b88P Y88b. .d88P 888       Y88b  d88P    888    Y88b  d88P 
#88         "Y88888P"   "Y8888P"     888          888   T88b 8888888888 "Y888888"   "Y88888P"  8888888888 "Y8888P"     888     "Y8888P"  
                                                                              #8b


# Headers used for POST requests
def post_headers(CLIENT_TOKEN):

	return {	'Content-Type' : 'application/x-www-form-urlencoded',
				'Authorization': f'Basic {CLIENT_TOKEN}' }



# Request for original AUTH token
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


  #8888b.  8888888888 88888888888      8888888b.  8888888888 .d88888b.  888     888 8888888888 .d8888b. 88888888888 .d8888b.  
#88P  Y88b 888            888          888   Y88b 888       d88P" "Y88b 888     888 888       d88P  Y88b    888    d88P  Y88b 
#88    888 888            888          888    888 888       888     888 888     888 888       Y88b.         888    Y88b.      
#88        8888888        888          888   d88P 8888888   888     888 888     888 8888888    "Y888b.      888     "Y888b.   
#88  88888 888            888          8888888P"  888       888     888 888     888 888           "Y88b.    888        "Y88b. 
#88    888 888            888          888 T88b   888       888 Y8b 888 888     888 888             "888    888          "888 
#88b  d88P 888            888          888  T88b  888       Y88b.Y8b88P Y88b. .d88P 888       Y88b  d88P    888    Y88b  d88P 
 #Y8888P88 8888888888     888          888   T88b 8888888888 "Y888888"   "Y88888P"  8888888888 "Y8888P"     888     "Y8888P" 



# Return a new or existing Requests Session
def get_session(AUTH_OR_TOKEN):

	# Is this AUTH with an established session?
	if type(AUTH_OR_TOKEN) is dict:

		# create a Session if one hasn't been added yet
		return AUTH_OR_TOKEN.setdefault('session', get_session(AUTH_OR_TOKEN['access_token']))

	# Create a Requests session 
	session = requests.Session()

	# Re-use the same Auth headers for all requests
	session.headers = {
		'x-api-key'     : '17wMKJLRxy3pYDCKG5ciP7VSU45OVumB2biCzzgw',
		'Authorization' : f'Bearer {AUTH_OR_TOKEN}'
	}

	# Automate retries and incremental backoff on failure
	retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
	session.mount('http://',  HTTPAdapter(max_retries=retries))
	session.mount('https://', HTTPAdapter(max_retries=retries))
	
	return session
	
	

# Need this for the name of the Player 	
def request_player_info(AUTH_OR_TOKEN):

	# Extract the session if provided full AUTH
	session = get_session(AUTH_OR_TOKEN)

	# Send request for Alliance Info
	return session.get(
		url     = f'{API_ENDPOINT}/player/v1/card', 
	)



# Need this for the Alliance name and stats
def request_alliance_info(AUTH_OR_TOKEN):

	# Extract the session if provided full AUTH
	session = get_session(AUTH_OR_TOKEN)

	# Send request for Alliance Info
	return session.get(
		url     = f'{API_ENDPOINT}/player/v1/alliance/card', 
	)


# Need this for the Alliance members 	
def request_alliance_members(AUTH_OR_TOKEN):

	# Extract the session if provided full AUTH
	session = get_session(AUTH_OR_TOKEN)

	# Send request for Alliance Info
	return session.get(
		url     = f'{API_ENDPOINT}/player/v1/alliance/members',
	)



# Need this for the Roster information 	
def request_member_roster(AUTH_OR_TOKEN, memberid, asOf=None):

	# Extract the session if provided full AUTH
	session = get_session(AUTH_OR_TOKEN)

	PARAM_SINCE = {'since':asOf} if asOf else {}

	# Send request for new access_token
	return session.get(
		url     = f'{API_ENDPOINT}/player/v1/roster/member/{memberid}',	# Individual roster request  
		params  = {'statsFormat':'csv'} | PARAM_SINCE, 							# Hash for previous API request
	)



# Request all character information -- used for Char names, Portrait info
def request_char_info(AUTH_OR_TOKEN, PLAYABLE=True):

	# Extract the session if provided full AUTH
	session = get_session(AUTH_OR_TOKEN)

	# Send request for Character Info
	return session.get(
		url     = f'{API_ENDPOINT}/game/v1/characters',
		params  = {
					'itemFormat':'id',
					'traitFormat':'id',
					'status':'playable' if PLAYABLE else 'unplayable',
				  },
	)



# Request gear tier info -- used for calculating gear tier costs for a character
def request_char_details(AUTH_OR_TOKEN, char_name):

	# Extract the session if provided full AUTH
	session = get_session(AUTH_OR_TOKEN)

	# Send request for Character Info
	return session.get(
		url     = f'{API_ENDPOINT}/game/v1/characters/{char_name}',
		params  = {
					'statsFormat':'csv',
					'charInfo':'none',
					'costumes':'none',
					'abilityKits':'none',
					'pieceInfo':'none',
					'pieceDirectCost':'part',
					'subPieceInfo':'none',
					'charAdoption':'full',
				  },
	)



# Request XP required for each Player Level -- use to translate to gold cost to level up
def request_upgrade_info(AUTH_OR_TOKEN, fieldId='characterLevelTotalXp'):

	# Extract the session if provided full AUTH
	session = get_session(AUTH_OR_TOKEN)

	# Send request for Character Info
	return session.get(
		url     = f'{API_ENDPOINT}/game/v1/upgradeData/{fieldId}',
	)



# Request XP required for each Player Level -- use to translate to gold cost to level up
def request_recruit_info(AUTH_OR_TOKEN, style=None, tcp=None):
	
	# Extract the session if provided full AUTH
	session = get_session(AUTH_OR_TOKEN)

	params = {'perPage':100}
	
	if tcp:
		params['tcp'] = tcp
	if style:
		params['style'] = style

	# Send request for Character Info
	return session.get(
		url     = f'{API_ENDPOINT}/player/v1/applicant/applicants',
		params  = params,
	)



# Request XP required for each Player Level -- use to translate to gold cost to level up
def request_recruit_roster(AUTH_OR_TOKEN, applicantId=None):
	
	# Extract the session if provided full AUTH
	session = get_session(AUTH_OR_TOKEN)

	print (f'{applicantId=}')
	
	# Send request for Character Info
	return session.get(
		url     = f'{API_ENDPOINT}/player/v1/applicant/applicants/{applicantId}',
	)
	