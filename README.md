# MSF2CSV
Converts Marvel Strike Force information from MSF.gg into a HTML table with a heat map for player/character stats

# History: 
MSF.gg used to have a CSV download option which made it easy to load up full roster stats for everyone in the alliance. 
During a recent "upgrade" this button was removed. Likely a temporary issue, but it still leaves Alliance leaders in a bad spot.
This is my attempt at a solution to the problem. I hope you enjoy it.
Feel free to provide feedback, questions, comments, etc. My username is "fatcat4096" on Discord. 
	
# Requirements:
1. Install Python
2. Install Beautiful Soup 4 -- 'pip install beautifulsoup4'
3. Install Selenium -- 'pip install selenium'

# Configuration:
* Add your own login / pass to user_and_pass.py if you want the script to run headless and download alliance/roster data without intervention
* In msf2csv.py, uncomment the call to 'process_website' in order to allow it to pull data from msf.gg. Currently configured to use cached data for dev.
* In msf2csv.py, define your own strike teams at the top of the file. Use of '----' is optional but will define lanes between groups of players.
* Edit the calls to generate_html if you want different filters (via min_iso and min_tier) or different data to be shown (via keys)

# Usage:
1. Install packages.
2. Configure as desired above.
3. Double click on the mht2csv.py file. 

# Output:
This project originally produced the CSV file MSF.gg used to give us. I have since abandoned this. 
Instead, I am focusing on producing immediately usable tables that I used to create manually. Currently, this includes:
1. A table showing Power, Gear Tier and ISO. One section per Origin, filtered to only heroes with at least one at ISO 2-4 and Gear Tier 16.
2. A table showing  the meta heroes for each section of Incursion.
3. A table with tabs for ecah of the the meta heroes for each section of Gamma.

# To-Do:
1. Clean up the Selenium code used to log in. Current use of system timer is super basic.
2. Clean up the use of CSS. Keep playing with font options.
3. Clean up the code that generates the Alliance Info tab. Is not elegant. 


