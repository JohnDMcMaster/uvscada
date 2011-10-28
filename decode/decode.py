#!/usr/bin/env python
import Image
import sys
import time

image_in = None
if len(sys.argv) > 1:
	image_in = sys.argv[1]
if image_in is None:
	image_in = "image.bin"
image_out = None
if len(sys.argv) > 2:
	image_out = sys.argv[2]

def decode_orig():
	width = 640
	height = 480 * 3
	net_size = width * height * 3

	print 'Net size: %d\n' % net_size

	f = open(image_in, "r")
	image = Image.new("RGB", (width, height), "White")

	for y in range(0, height):
		for x in range(0, width):
			# putpixel(self, (x, y), (R, G, B))
			R = ord(f.read(1))
			G = ord(f.read(1))
			B = ord(f.read(1))
			image.putpixel((x, y), (R, G, B))

	'''
	for y in range(0, 40):
		for x in range(0, 40):
			image.putpixel((x, y), (255, 255, 255))
	'''

	if image_out:
		image.write(image_out)
	else:
		image.show()
	time.sleep(3)

def decode2():
	width = 640
	height = 480 * 3

	f = open(image_in, "r")
	image = Image.new("RGB", (width, height), "White")

	for y in range(0, height):
		for x in range(0, width):
			# putpixel(self, (x, y), (R, G, B))
			#R = ord(f.read(1))
			R = 0
			G = ord(f.read(1))
			#B = ord(f.read(1))
			B = 0
			image.putpixel((x, y), (R, G, B))

	#image.show()
	#time.sleep(3)
	#image.save(


def decode_SGBRG8():
	'''
	Require interpolation
	Read two lines at a time
	'''
	width = 640
	#width = 642
	height = 480
	
	
	f = open(image_in, "r")
	image = Image.new("RGB", (width, height), "White")
	
	# Skip offset
	#f.read(254)
	f.read(1)
	f.read(640 * 480 * 3)
	
	for y in range(0, height, 2):
		# GBGB
		# RGRG
		line0 = f.read(width)
		#line0 = f.read(width)
		#line0 = f.read(width)
		
		line1 = f.read(width)
		#line1 = f.read(width)
		#line1 = f.read(width)
		for x in range(0, width):
			R = ord(line1[x])
			G = ord(line0[x])
			# make even
			B = ord(line0[x - (x % 2)])
			image.putpixel((x, y), (R, G, B))
		for x in range(0, width):
			R = ord(line1[x])
			# Make odd
			G = ord(line1[x - (x % 2) + 1])
			# make even
			B = ord(line0[x - (x % 2)])
			image.putpixel((x, y + 1), (R, G, B))
	image.show()

#decode_orig()
#decode2()
decode_SGBRG8()

