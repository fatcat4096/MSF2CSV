#!/usr/bin/env python3
# Encoding: UTF-8
"""gradients.py
Source is an excellent writeup by Ben Southgate
See: https://bsouthga.dev/posts/color-gradients-with-python
"""

def hex_to_RGB(hex):
	''' "#FFFFFF" -> [255,255,255] '''
	# Pass 16 to the integer function for change of base
	return [int(hex[i:i+2], 16) for i in range(1,6,2)]


def RGB_to_hex(RGB):
	''' [255,255,255] -> "#FFFFFF" '''
	# Components need to be integers for hex to make sense
	RGB = [int(x) for x in RGB]
	return "#"+"".join(["0{0:x}".format(v) if v < 16 else
						 "{0:x}".format(v) for v in RGB])


def darken(hex,darken_amt=0.4):
	''' Takes in a hex color and returns the same color
		taken to 60% brightness. '''
	return RGB_to_hex([int((1-darken_amt)*x) for x in hex_to_RGB(hex)])


def grayscale(hex):
	''' Takes in a hex color and returns the same color
		taken to 60% brightness. '''
	r,g,b = hex_to_RGB(hex)
	bnw = int(r * 0.299 + g * 0.587 + b * 0.114) & 0xff
	return RGB_to_hex([bnw,bnw,bnw])
	

def color_dict(gradient):
	''' Takes in a list of RGB sub-lists and returns dictionary of
		colors in RGB and hex form for use in a graphing function
		defined later on '''
	return {"hex":[RGB_to_hex(RGB) for RGB in gradient],
			"r":[RGB[0] for RGB in gradient],
			"g":[RGB[1] for RGB in gradient],
			"b":[RGB[2] for RGB in gradient]}


def linear_gradient(start_hex, finish_hex="#FFFFFF", n=10):
	''' returns a gradient list of (n) colors between
		two hex colors. start_hex and finish_hex
		should be the full six-digit color string,
		inlcuding the number sign ("#FFFFFF") '''
	# Starting and ending colors in RGB form
	s = hex_to_RGB(start_hex)
	f = hex_to_RGB(finish_hex)
	# Initilize a list of the output colors with the starting color
	RGB_list = [s]
	# Calcuate a color at each evenly spaced value of t from 1 to n
	for t in range(1, n):
		# Interpolate RGB vector for color at the current value of t
		curr_vector = [
			int(s[j] + (float(t)/(n-1))*(f[j]-s[j]))
			for j in range(3)
		]
	# Add it to our list of output colors
		RGB_list.append(curr_vector)
	return color_dict(RGB_list)


def polylinear_gradient(colors, n):
	''' returns a list of colors forming linear gradients between
		all sequential pairs of colors. "n" specifies the total
		number of desired output colors '''
	# The number of colors per individual linear gradient
	n_out = int(float(n) / (len(colors) - 1))
	# returns dictionary defined by color_dict()
	gradient_dict = linear_gradient(colors[0], colors[1], n_out)
	#
	if len(colors) > 1:
		for col in range(1, len(colors) - 1):
			next = linear_gradient(colors[col], colors[col+1], n_out)
			for k in ("hex", "r", "g", "b"):
				# Exclude first point to avoid duplicates
				gradient_dict[k] += next[k][1:]
	#
	return gradient_dict


# Linear gradient from red, to yellow, to green. 
# Costly to calculate, so only doing it once.
color_scale = polylinear_gradient(['#f05d41','#edf74d','#52e332'],1000)['hex']

iso_color_scale   = polylinear_gradient(['#EFFF17','#52e332'],5)['hex'] 
iso_color_scale  += polylinear_gradient(['#B1DDFF','#0090FF'],5)['hex']
iso_color_scale  += polylinear_gradient(['#C7A7FF','#A52EEA'],5)['hex']
