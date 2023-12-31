def add_css_header(table_name='', num_lanes=0, hist_tab=''):

	html_file = '''<!doctype html>
<html lang="en">
<head>
<title>'''+table_name+''' Info</title>
<meta charset="UTF-8">
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
.blu_btn:hover {
  background  : DodgerBlue;
  cursor      : pointer;  
}
.ltb_btn {
  font-weight : 700;
  background  : #B0E0E6;
  white-space : nowrap;
  color       : black;
}
.ltb_btn:hover {
  background  : LightCyan;
  cursor      : pointer;  
}
.red_btn {
  font-weight : 700;
  background  : DarkRed;
  color       : white;
  min-width   : 60px;
}
.red_btn:hover {
  background  : Red;
  cursor      : pointer;  
}
.blk_btn:hover {
  background  : SlateGray;
  cursor      : pointer;  
}
.url_btn:hover {
  font-weight : 900;  
}
.header_gray {
  font-weight : 700;
  background  : Black;
  color       : white;
  white-space : nowrap;
}
.char_blue {
  height  : 40px;
  font-weight : 700;
  background  : SteelBlue;
  text-shadow : 1px 1px 2px white,
                0 0 0.8em white, 
                0 0 0.2em white;
}
.char_gray {
  height  : 40px;
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
.tt {
  position: relative;
}
.tt .ttt {
  visibility: hidden;
  width: 100px;
  background-color: black;
  color: #fff;
  text-align: center;
  border-radius: 6px;
  padding: 5px 0;
  position: absolute;
  z-index: 1;
  top: 150%;
  left: 50%;
  margin-left: -50px;
  opacity: 0;
  transition: opacity 1s;
}
.tt .ttt::after {
  content: "";
  position: absolute;
  bottom: 100%;
  left: 50%;
  margin-left: -5px;
  border-width: 5px;
  border-style: solid;
  border-color: transparent transparent black transparent;
}
.tt:hover .ttt {
  visibility: visible;
  opacity: 1;
}
.skirmisher {
  background:
    url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADcAAAA3CAQAAAAC0hrNAAAEdklEQVRYw72YXYiUVRiAn5lvzui8Wa6bLIuYJRpdrKZllFhgURBsbSX0Y15YoBArFVQ3203Q1QYW/cGKZhdCBJEIQUZ0JbRbti3ksv5gMpCiq6ya++dZ3bO708XMrt/POd/3zey251wM8845PPP+nfO+J0PVQ5bwGOCFxBkAhvlNj7n3ZpnXkalBu3Ucs4jHK587OejWrxbtFnPdIs1X5he8IHfMnzHr6OAZFzAGJzvlkVkAF1aFk518RessNHzOBnTgZAe7gefl0ZqBe9kSNWnWAfuUOqCObZKfSx9mHbDbK1+2sXqWQVOIxQVgUMfrNetXBr7oB4bSXLbTwW0B0Vma9cnAmgfYDEwHQvkwW8krLLIiB9nFYT1s89l2KVlmW2RdTnLilWdFskr2WveWpCTX5NVpH3oBzdp9Zrw17lW/mMt+gZkyU6ZUnhXJNXWCAhus+i3kSc6oopkI4NQSBhDqUREPnDedSW4yg+oEBe4j7wCeVWfMhA9n/lF/cIQiGRpZEFi+XH1ndCrgYqeGT1BU5wK3lpk0V82f6id6GGaFL2SWckH1TBsuAQgb3Sb1LJtumL9VFz/TzyKWVYQr+d6MJke+GVTHUG6g59h2Q/1LJz0cpcAqYCl96rhfP1mm7lYNqkEtVCN+uRmNBSZepsvkaTkgV+SI+PJK8nJQxmRMxqRLmiQjgfyVBtktNy0pMe4lmmfEFFU3ndQxYM7PRLHHVprIkeMu1nOUy8a/57rqpcCDkXpmKn3JsCik3Q++f90lTRI6DqUgh6Lapb7N9ah2h8pG9rEmDOTc/1U8ZNnE16wLegGJLszNKB/6UesqkQ/xAVuSFuWkBWj3FW7loN7D/qp1XJ68JMcKoGm+ytosGUtpOxlOSMlK4DbT45jIrgnxAorkYnwXmwT30DHj3GvAEEOsqEW7XMp1a9N4Jo0x53Wkw4nFU5HTjryeDHwv1Yoboo+JxFV75kg7fYH3ORwL1OzS++fMd/pkLFDzjgU2nBbnUS+hqlGf4kMOOTXbFxFO2lpVTz0MNEfk9zOgTpvxQCxcUkWWsDqUPJpd+oAlut6lLXrfufLuTtpBvg1eOvov+Yj+SoJPX5U/WmFv0W4rAd1pXu8AngrezHo8WmPTaodBjpsxwE/IyDc60InrG4lx9Rof22EMe+oSZ8hjb4vzPE6/Om1M+nNDdtDhgF2l2TMjZkT1kmdtpFgvAzcxkB4orXzphulur1xtqV7EAZT0QGmlPdSuTY+LtOjumZbEjKhjiKMYFTZTVCdURmVUxl26y3Y+t3ZQ0M9W/Xug4YqtfhfwFEVOArhwlkbUD/vV0r1KI2284Sith/gMgHBkliovSW8nw6LNciPv8WaKWj7dKDHAS7dgkWdCM6r6KDhMWv24QkvZZw5cgg+rG5d5VneHz34cwPWp6xi7Ga9EYVZcBZhlwyyAA+U8S4UDM6qOh3yY1Cr7g+4CLwd9loCrwYcZH2yrdrxUxLSTFeAa8lXhYmCxuApQWEOOUuKr9RQlSlyMg8F/jeGn03RF7n0AAAAASUVORK5CYII=)
    no-repeat
    center center;
    background-size: 16px 16px;
}
.raider {
  background:
    url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADcAAAA3CAQAAAAC0hrNAAAFW0lEQVRYw9WYXWwUVRTHf6Ud5LSw1lhj+bCCoJhCUfkQlCXgg+tHDQ8GAllUiEaTEjVBIqEoSMpDSYzIk40JQULCBgFjQqjRGNTEFTVpoDBmSbQFXCtpCJYWYS9Lpx0fdnZ2ZndmP2h58LzsnXPPzG/+59577p2FEZlMlamlxI/h/2MSkC2l3TEydVs5kfUCE26ftqfl5yzPc7LpNgGlVjrkQ5dHk6Ni3iJQ7pD78vZ/JpdkmcszV0wxxZRNUlk6bqFslHKfvnGyXBLSIVVZL5DCJWSDaKKJVgpupXzn95YyQzrElM0u30y5ZOFMuZ4CloLbKF1yv2ePJvvFlITM8NTmAJaC2yemrPLsWSummLJfxvloywCrilx3UkM9sMyjZxYfA/CNuuFwL+eerMBKdhAucgylRgbElKhU5/R8IaaY0i2THL7Jci5LW1rh626cX1WZCUADDVmwN3kRgO/VRdtXRphpnk+pZDfriiliMwkAATdOZtFiNQ843AGafNNUyW7WZUbZD/eQ9fusqx5+yl0AnOWMI/Z58hWESnaxKj2GnjiptlXVS63t3swiqxVR/2R2BZqoyDsRxtNK2FInZVLmEVJn/U6n3nrsk2whVWWu0+6IbGRJwZk3MQ0cQ5CgjM2BzbbbISuRn9ieTnXKEdtU5EKuA6hgG7AN91YymWE7zUEpUybbecTu3eNI+5K82gYB6GEXB+lXBlbWW2WN+tsR1uAY0wYaZLpDQy/RErT9wl6OqGvpyxRuKU28b79xuWv6BwjyNmJfR4k7tDX6goZo50snKoOD90RXn1vt8qzF3UrAcdWubjq0BXxRO9HdqBQuffN2+UOdtPRMcsU4HxnjqGPRhzxQl4gQoRNDmbmdFfRZrYfZLOvVZaDOWsxeFlV9djvM3R6oNuIkvVDOZAKsRGcH0EC5Ly7i0BZ29XTRxjHirn3CXTzmsTijDqBF2tVJgr6wGLpDW7oUGFygjYjq9Tv1MJsQIWJ8UEHS1dcma6imzAd3OJ1Kmcgb1mI5QRtf06eGPVEPECTMIuI0q3Zyqt3jNNlvnW1JDjpqTQ1wgmZ0dcX7hM0iXiPIJCBCs4qnxq4/K+4dlN804byt7VUi7FXHPUF3spAQK5hCOXCRZrXfa6rY8T64Iyqd+HpafFANNNLIE7bjEM3qnNe6K2QXOGa3f1Q3cw+DBHmF+Yy3R76PrexxR1ZwrUhcVPWkm+5HSDVPESZIrSv+K1rUr/nWXT4bdu1xzm04TNCxXaV1tbBX/eu1zItTF3ftA8hYprGaFTkgMOngrVxdadwNYChPHbFSk0ml1NHICoKM9Yz8iJ2Zo4V3Mgvj9lmgII0EfVfmWdarH/I9Jq0uv52hVxawjhd8QTBIGy3+upy4Qd+1lt7BjzEnb0Q3zepw4SlQgQlZdTPXQgX6e3nXPZX8cf2j8OVcywEGROcwnXR519CUlUkVsJrWnC+YW7MEXXTyLTo65O4SZQAihEcNiHXY09E5js5lNZhxlwMYhvYbikcZvT8pAjzIYl5mFfM00fqMqw4cGMPaSZIsoHKUcAMkOcVPRIkS53djyJHM9Dc3a2mlZkSYLuLoxIkRA3rAPYKuY4JUEi4JaALDKHqIESNGN3HwO7Pk4FIf+rQysUgd3ejo6BgkGXJOifw102nt1LEhz0nTPkT5n738Lac0GwktxnXmFyhr8AxztbhxYYQ4MBLanwwUAZxGSBvUug01IhwYVzWdJPMZV+DuCSzlXi1mXBkRDoykppNkDlUF7teYy0LtL63XGBwBzgImeKwgEKbwEle008UA8+ziRlI7z0BRQAgxSzut9RvD+cP+AySHvqQVsfC/AAAAAElFTkSuQmCC)
    no-repeat
    center center;
    background-size: 16px 16px;
}
.healer {
  background:
    url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADcAAAA3CAQAAAAC0hrNAAADQElEQVRYw+2YTUhUURSAvzd/ejCiH7KoxIjIsvyhooKwRYui2kkQ2LZatwmaEi0JtT+zApE21UJwm0wW1FLCNmHJQNFOW0SFFUTXGfVNixnHeTNz33u+GaeC7tvc+86d+91z7jn3nHkGjk0qEdw0E4BPakY/xUdJW8BRt00MstHVWglglLN884yTTUTYsYjtO2zMV1SYY/OVEmaDk2qGPMBMTzipZpidhWkiFS5xUs0wtRgFwfy0yH4XuBSs0OanjoFsYA5OanjOds+QBImM0WYeykExtHEnNUTYolnqhc35r2dbXlkN9zkjIyqRB2cLu0WXRmIA67nNIQ1wgFMLwAyYfJCE5rkpQQfXqJcRSciIrEiNQ3I3/esJaUqa1Jeh2WOtZj1ctLvnAdRbLvCKQIY3LOhTxSOOiAH+DDNu1cLCKu7sJbMTwXfA6KwCCPo5zL60cCUHeB2cdGPG0CKibVW6F5I7WStNSFNAapmzdZCw1YyymuVWpdRkhkmnbPZSxUCA3bAIWDlXabbMGZRzKVTCUfkqu3yXAwOggkrLuLw4Cag3L2yJEtCDpYDpi4dJZjTz4zkZzlBmEbL5H6nEQNZxAYBlADRmiffSJwuZvFtNFIijjhbWaKW72JXu/6DbmzENNZfuf3ed16cp+6vO7j/O/ZbmmPvX4g54ZgmLBotslPepXrw4uDFOA5BMs31ZuNecTyWgX95xITHm85eKpd7FQMpzYjCQH6PiEijt2U2VECeNtHh1FS+wCBvy4Xx5Y8WneW9i8tnyX+6ne5gX7fq5Z8H9cA+DAGPAU45qzWIQSvsmKs5Lb2YE4HJySoMMZ5Wg18Wfrv1PSpn7M5OPmvJ4RtrnPXOcME8xU0/2p4tejrmrpKWeIa1mnepKCqdM9YYwTzQT19HHcWeg1BOhSiPsUO3WuBt3BNoWsLLHGZbhmcokKmHguBbYKl9sLsIuDWyWznlYViCoqFwiRjPgzzjD5N25ln6bbOYjqIG10qONOzUuHZic0Gix2CidpVVdsw1zNS4dRbrJcmB5bxUVlQ6XnxTtWpy2bJjmElNRogXCpmlTN0qVgDSwpcFpYUuBi+lhbhJQgK+uq0yAXj0MfgMWkSUrQcRlKAAAAABJRU5ErkJggg==)
    no-repeat
    center center;
    background-size: 16px 16px;
}
.striker {
  background:
    url(data:image/png;base64,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)
    no-repeat
    center center;
    background-size: 16px 16px;
}
.fortifier {
  background:
    url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADcAAAA3CAQAAAAC0hrNAAAD6klEQVRYw+WYz2sjZRjHP5PMpH27+dEutuyWOO5CoFtxUHGhq6SCyyK7bEEPHqQnF/Qgy3oVwdNePIgHQboXr/ofFIuCvfSyi65Lxy2JZglMtyFsuzTB1DdNJomHTkLTZDppdhJBn0sg7zvvZ57n+b7v+8yj4GEiwDw6AHWPqaOAxZqU7lMCDNVUzxkf8DXhntfb5jPxnSy7DQc9QnmDJcZO8PqnuMy2lrYrfeDEDZYYPWG8Qlwh5wYM+gwDsLnqBnTFiY/4pi8Y2MBVctqGXe0RJ27x5Yly1i4/FZXLFLVftIAWsOseOHGLLzj1jJrXmKfEPfDA+QI7EM08Je4dxilHUCqfcLsFq1Ohwh55SpTYo0CBMs2MNAAYRyNKlChhwkwSRkVrrbvH53wrS27b/CZfARnAIk2WLFmeUqZCGag5iHZTCBIExogRI8YMceLEmUQnwm1C4o78q8M7EeJjklhsYGKBzPcbRSGAOGPoGBjMcofvD4CHcQnAAlnx53wUzfN4GuTjrrnz05o4Wed/Yn0EUzjPyMaAcEIQ4zQRznCGcSbaBncokCdPmR2K7B+fK+UYD6bQSWLwAmc5yxgNZ38dfaZOnTo19thiiy1+xMKi2K2I6MCJCKdJYpBkCp2RvlJUwcLiN1ZJy4wLTkTQWcTgFZ73TRt/kuY+y5gHvioAIkaC97iGMbBy6VeW+YGUIl6jzhKGL3fA8VZmTeVFFC4NZdONkhxynTn0snaYQPs/HcywSpTaMHPXGJqHjV6+gDpt3/kd6cc7L3vKE8CkyC5FioBTVVEDosAUMUDnHKADz7lfa6rL+5fIkMbExOKJ8+9u99pDNL2ccLCzJEiQYJoRgu1o9cgllMJknTUsdihTkz3ISDaDmycPpPlJCEYZ5zwGBgbTxJu3T9O7AmmWMTHlo2fXhJRIdsnys5gEZp37Mw6K+BABrJKW1YEWgDpv8rYiwk2lDRj3b9SbPRd+YoIIEIcjF3GOv4EcEDiuo9IDTpxDx+ACM0wDcWIup0UOyPEYCwuTByC3e8aJAOeZY46L6I6EPQ+ntrXyWJiY3CVDQdpulVgIMLjOFV4ijOZDbZJnjRVMud6BEy/zDovMDEQhq6ywItdb21yM8C6fIgYkyLdIsHKoFWDXtHWqXPIhhN1sk4WDgLY6D3ZZ+50yc1QJ+QzLcE1udDQ6bKk9ZJ+kz7gs12W6a1/FAb7uY0izLMiUaxvHltpDKr7lMMtCM4wuXSNban9Q5Q3qrbFGnwfjIxblA88WnF3SUuyT9GqteuA2eV/e7anj5wAv9ikaxZH+/c4hFw/skpYiwKuoNE7cLlDYZAHT7jL0DxwOPN+oQlyWAAAAAElFTkSuQmCC)
    no-repeat
    center center;
    background-size: 16px 16px;
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
   var tooltips = doc.getElementsByClassName("ttt");
   while(tooltips.length > 0){
     tooltips[0].remove();
   }
   return doc.body.textContent || "";
}

function sort(n,table_name,header_lines) {
  sortx(n,table_name,header_lines,0)
}

function sortx(n,table_name,header_lines,rows_to_sort) {
  var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
  table = document.getElementById(table_name);
  if (rows_to_sort == 0) {
    rows_to_sort = table.rows.length - header_lines;
  }
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
    for (i = header_lines; i < (header_lines + rows_to_sort - 1); i++) {
      // Start by saying there should be no switching:
      shouldSwitch = false;
      /* Get the two elements you want to compare,
      one from current row and one from the next: */
      x = strip(rows[i].getElementsByTagName("TD")[n].innerHTML);
      y = strip(rows[i+1].getElementsByTagName("TD")[n].innerHTML);
      /* Check if the two rows should switch place,
      based on the direction, asc or desc: */
      if (dir == "asc") {
		if (isNaN(x) || isNaN(y)) {
          // Use string comparison for alpha elements.
          if (x.toLowerCase() > y.toLowerCase()) {
            // If so, mark as a switch and break the loop:
            shouldSwitch = true;
            break;
          }
		} else {
          // Use numeric comparison for numbers.
          if (Number(x) > Number(y)) {
            shouldSwitch = true;
            break;
          }
		}
      } else if (dir == "desc") {
		if (isNaN(x) || isNaN(y)) {
          // Use string comparison for alpha elements.
          if (x.toLowerCase() < y.toLowerCase()) {
            // If so, mark as a switch and break the loop:
            shouldSwitch = true;
            break;
          }
		} else {
          // Use numeric comparison for numbers.
          if (Number(x) < Number(y)) {
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
