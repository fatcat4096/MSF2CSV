# MSF2CSV
Converts Marvel Strike Force information from MSF.gg into a HTML table with a heat map for player/character stats

# History: 
MSF.gg used to have a CSV download option which made it easy to load up full roster stats for everyone in the alliance. 
During a recent "upgrade" this button was removed. Likely a temporary issue, but it still leaves Alliance leaders in a bad spot.
This is my attempt at a solution to the problem. I hope you enjoy it.
Feel free to provide feedback, questions, comments, etc. My username is "fatcat4096" on Discord. 

# Current Status:
As this package is no longer being used as a standalone app, I have slowly been removing functionality used by these workflows.
* Library no longer supports saved credentials for automatic login to the Scopely MSF website
* Library no longer supports scraping roster information from website via a Selenium session
* Support for parsing of downloaded .csv files will be removed.
* Command line support for image generation from existing cached_data.msf files is present but may be removed in the future

Our intent for this library is to continue to support:
* Download of alliance roster information via the MSF API from the Scopely website into cached_data.msf files
* Rendering of that cached data into a variety of reports, with a multitude of configurable options and custom queries available

# Requirements:
1. Install Python 3.x from Python.org
2. Install required packages from a command prompt: <code>python -m pip install -r requirements.txt</code>
3. Double click on msf2csv.py

# Configuration:
* The reports to output and Lane/Section defintions are in Raids_and_lanes.py. Instructions for configuration are in the file header.
