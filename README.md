# MSF2CSV
Converts Marvel Strike Force roster files from MHTML into a HTML table with a heat map for player/character stats

# History: 
MSF.gg used to have a CSV download option which made it easy to load up full roster stats for everyone in the alliance. 
During a recent "upgrade" this button was removed. Likely a temporary issue, but it still leaves Alliance leaders in a bad spot.
This is a rudimentary solution to the problem. Takes more work, but it does produce a good result.
Feel free to provide feedback, questions, comments, etc. My username is "fatcat4096" on Discord. 
	
# Requirements:
1. Install Python
2. Install Beautiful Soup 4 -- 'pip install beautifulsoup4

# Usage:
1. From the MSF website Alliance view, navigate into the Roster page for each member of your alliance.
2. On each member's Roster page, right click on the background and Save As a "Webpage, single file (*.mhtml)"
3. Actual name of the MHTML file is not critical. Player name for the CSV file is taken from the HTML.
4. Double click on the mht2csv.py file. 

# Output:
This project originally produced the CSV file MSF.gg used to give us. I have since abandoned this. 
Instead, I am focusing on producing immediately usable tables that I used to create manually. Currently, this includes:
1. A table showing Power, Gear Tier and ISO. One section per Origin, filtered to only heroes with at least one at ISO 2-4 and Gear Tier 16.
2. A table with just the meta heroes for each section of Incursion.
Another format is planned for Gamma 4.5 planning purposes.  

# Issues
1. Wish we didn't need to save users' roster pages individually. Not sure how to resolve this info from the top level Alliance page.
2. Would be great if we could save the URLs to each member (in parsing comments) and use these Player IDs to get updates later.
3. If nothing else, this simplistic approach avoids the complexities of having to deal with webpage authentication. 


