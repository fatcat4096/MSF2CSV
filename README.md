# MSF2CSV
Converts Marvel Strike Force information from MSF.gg into a HTML table with a heat map for player/character stats

# History: 
MSF.gg used to have a CSV download option which made it easy to load up full roster stats for everyone in the alliance. 
During a recent "upgrade" this button was removed. Likely a temporary issue, but it still leaves Alliance leaders in a bad spot.
This is my attempt at a solution to the problem. I hope you enjoy it.
Feel free to provide feedback, questions, comments, etc. My username is "fatcat4096" on Discord. 
	
# Requirements:
1. Install Python 3.x from Python.org
2. Install Beautiful Soup 4, KeyRing, and Selenium -- 'pip install -r requirements.txt'
3. Double click on msf2csv.py

# Configuration:
* Members of Strike Teams are configurable in strike_teams.py. If contents of this file DON'T pertain to your Alliance (or if this file has been deleted), the system will automatically attempt to build another. To do so, it will first check the Team definitions on MSF.gg for Incursion and Gamma raids. If these aren't available, it will generate a generic file template with the current alliance members broken up into 3 groups of 8. 
* The files to output and Lane/Section defintions are in Raids_and_lanes.py. Remove files you don't need from the active list. Change Min_iso and Min_tier to match the level of raid you're running. Change the displayed keys if you like. If this file is broken or deleted, it will be regenerated using default parameters.
* NOTE: If building a frozen version of this script to distribute, EXCLUDE both raids_and_lanes.py and strike_teams.py from the package, as these will both be auto-generated in the same directory as the EXE on first run and the results will be editable by end users, e.g.:
* 		pyinstaller msf2csv.py --onefile --exclude-module strike_teams --exclude-module raids_and_lanes.py

# Usage:
* At first run, the script will prompt you as to whether you want to store your credentials for Login. These credentials will be stored locally in KeyRing and used only for MSF.gg login.
* If you would prefer not to store credentials, the system will give you five minutes to log into your desired account. Once in, processing will resume.
* If you need to update passwords or initially did not enter a password, delete the noprompt file in the local directory to allow the script to prompt again.
* The script will by default use the cached_data file for 24 hours without requesting updated information from the website, there is a flag on the process_website call which will FORCE it to check website information each run.

# To-Do:
1. Looking at an option to output to Google Sheets.
2. Toying with the idea of a report that tracks changes over time, so that you can see where your players are building and validate that people are building the teams required.
3. I've been told that Linux-based installations require a 3rd party provider to use KeyRing. MacOS and Windows should support it without any additional. Please provide info if you get things working on Linux.


