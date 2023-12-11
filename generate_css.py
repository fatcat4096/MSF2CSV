def add_css_header(table_name='', num_lanes=0, hist_tab=''):

	html_file = '''<!doctype html>
<html lang="en">
<head>
<title>'''+table_name+''' Info</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fira+Sans+Condensed:wght@400;700;900&display=swap" rel="stylesheet">
<style>
/* Styles for table cells */
.bold {
  font-weight : bold;
  color       : black;
}
.alliance_name {
  font-weight : 700;
  font-size   : 36pt;
}
.title_blue {
  font-weight : 700;
  font-size   : 14pt;
  background  : #B0E0E6;
}
.title_gray {
  font-weight : 700;
  font-size   : 14pt;
  background  : #DCDCDC;
}
.header_blue {
  font-weight : 700;
  background  : MidnightBlue;
  color       : white;
  white-space : nowrap;
}
.header_gray {
  font-weight : 700;
  background  : Black;
  color       : white;
  white-space : nowrap;
}
.char_blue {
  font-weight : 700;
  background  : SteelBlue;
  text-shadow : 1px 1px 2px white,
                0 0 0.8em white, 
                0 0 0.2em white;
}
.char_gray {
  font-weight : 700;
  background  : Gray;
  text-shadow : 1px 1px 2px white,
                0 0 0.8em white, 
                0 0 0.2em white;
}
.blue {
  font-weight : 700;
  background  : #B0E0E6;
  white-space : nowrap;
  color       : black;
}
.name_blue {
  font-weight : 700;
  background  : #B0E0E6;
  white-space : nowrap;
  color       : black;
  min-width   : 125px;
}
.name_blue_dim {
  font-weight : 700;
  background  : #729195;
  white-space : nowrap;
  color       : black;
  min-width   : 125px;
}
.name_alt {
  font-weight : 700;
  background  : #00BFFF;
  white-space : nowrap;
  color       : black;
}
.name_alt_dim {
  font-weight : 700;
  background  : #007ca5;
  white-space : nowrap;
  color       : black;
}
.name_gray {
  font-weight : 700;
  background  : #DCDCDC;
  white-space : nowrap;
  color       : black;
  min-width   : 125px;
}
.name_gray_dim {
  font-weight : 700;
  background  : #8f8f8f;
  white-space : nowrap;
  color       : black;
  min-width   : 125px;
}
.name_galt {
  font-weight : 700;
  background  : #A9A9A9;
  white-space : nowrap;
  color       : black;
}
.name_galt_dim {
  font-weight : 700;
  background  : #6d6d6d;
  white-space : nowrap;
  color       : black;
}
.subtitle {
  font-size   : 12pt;
  font-weight : normal;
}
.image {
  background  : Black;
}
.power {
  font-weight : 700;
  background  : Maroon;
  color       : white;
  min-width   : 60px;
}
.hist {
  background  : #282828;
  color       : #919191;
}
/* Style tab links */
.tablink {
  background  : #888;
  color       : white;
  float       : left;
  border      : none;
  outline     : none;
  cursor      : pointer;
  padding     : 14px 16px;
  font-size   : 24px;
  font-family : 'Fira Sans Condensed';
  font-weight : 900;
  width       : '''+str(int(100/(num_lanes+[3,2][not hist_tab]))) +'''%;	/* Adding 2 for Roster Analysis and Alliance Info tabs, 3 if there's also history. */
}
.tablink:hover {
  background  : #555;
}
.tabcontent {
  background  : #343734;
  display     : none;
  padding     : 70px 20px;
  height      : 100%;
}
'''
	# Quick and dirty CSS to allow Tabbed implementation for raids with lanes.
	for num in range(num_lanes):
		html_file += '#Lane%i {background: #343734;}\n' % (num+1)

	if hist_tab:
		html_file += '#Hist {background: #343734;}\n'

	html_file += '#AllianceInfo {background: #343734;}\n'	

	# Finish off the Header.
	html_file += '</style>\n'
	html_file += '</head>\n'
	html_file += '<body style="background: #343734; font-family: \'Fira Sans Condensed\', sans-serif; text-align:center;">\n'

	# If num_lanes == 0, not using the tabbed interface.
	if num_lanes:
		for num in range(num_lanes):
			tab_name = ['ROSTER INFO', 'LANE %s' % (num+1)][num_lanes>1]

			if table_name:
				tab_name = '%s %s' % (table_name.upper(), tab_name)

			html_file += '''<button class="tablink" onclick="openPage('Lane%i', this)" %s>%s</button>''' % (num+1,['','id="defaultOpen"'][not num],tab_name) + '\n'

		if hist_tab:
			html_file += '''<button class="tablink" onclick="openPage('Hist1', this)">%s</button>''' % (hist_tab) + '\n'

		# And a tab for Roster Analysis and one for Alliance Info
		html_file += '''<button class="tablink" onclick="openPage('RosterAnalysis', this)">ROSTER ANALYSIS</button>''' + '\n'
		html_file += '''<button class="tablink" onclick="openPage('AllianceInfo', this)">ALLIANCE INFO</button>''' + '\n'

	return html_file

def add_sort_scripts():
	return '''
<script>
function strip(html){
   let doc = new DOMParser().parseFromString(html, 'text/html');
   return doc.body.textContent || "";
}

function sort(n,table_name) {
  sort_table(n,table_name,1)
}

function sortn(n,table_name,header_lines) {
  var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
  table = document.getElementById(table_name);
  switching = true;
  // Set the sorting direction to ascending:
  dir = "asc";
  /* Make a loop that will continue until
  no switching has been done: */
  while (switching) {
    // Start by saying: no switching is done:
    switching = false;
    rows = table.rows;
    /* Loop through all table rows (except the
    header_lines, which contain table headers): */
    for (i = header_lines; i < (rows.length - 1); i++) {
      // Start by saying there should be no switching:
      shouldSwitch = false;
      /* Get the two elements you want to compare,
      one from current row and one from the next: */
      x = rows[i].getElementsByTagName("TD")[n];
      y = rows[i + 1].getElementsByTagName("TD")[n];
      /* Check if the two rows should switch place,
      based on the direction, asc or desc: */
      if (dir == "asc") {
		if (isNaN(x.innerHTML) || isNaN(y.innerHTML)) {
          // Use string comparison for alpha elements.
          if (strip(x.innerHTML.toLowerCase()) > strip(y.innerHTML.toLowerCase())) {
            // If so, mark as a switch and break the loop:
            shouldSwitch = true;
            break;
          }
		} else {
          // Use numeric comparison for numbers.
          if (Number(x.innerHTML) > Number(y.innerHTML)) {
            shouldSwitch = true;
            break;
          }
		}
      } else if (dir == "desc") {
		if (isNaN(x.innerHTML) || isNaN(y.innerHTML)) {
          // Use string comparison for alpha elements.
          if (strip(x.innerHTML.toLowerCase()) < strip(y.innerHTML.toLowerCase())) {
            // If so, mark as a switch and break the loop:
            shouldSwitch = true;
            break;
          }
		} else {
          // Use numeric comparison for numbers.
          if (Number(x.innerHTML) < Number(y.innerHTML)) {
            shouldSwitch = true;
            break;
          }
		}
      }
    }
    if (shouldSwitch) {
      /* If a switch has been marked, make the switch
      and mark that a switch has been done: */
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
      // Each time a switch is done, increase this count by 1:
      switchcount ++;
    } else {
      /* If no switching has been done AND the direction is "asc",
      set the direction to "desc" and run the while loop again. */
      if (switchcount == 0 && dir == "asc") {
        dir = "desc";
        switching = true;
      }
    }
  }
}
</script>
'''

# Quick and dirty Javascript to allow Tabbed implementation for raids with lanes.
def add_tabbed_footer():
	return '''
<script>
function openPage(pageName,elmnt) {
  var i, tabcontent, tablinks;
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
	tabcontent[i].style.display = "none";
  }
  tablinks = document.getElementsByClassName("tablink");
  for (i = 0; i < tablinks.length; i++) {
	tablinks[i].style.backgroundColor = "";
  }
  document.getElementById(pageName).style.display = "block";
  elmnt.style.backgroundColor = "#343734";
}

// Get the element with id="defaultOpen" and click on it
document.getElementById("defaultOpen").click();
</script>
'''
