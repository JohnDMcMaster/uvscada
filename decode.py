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


decode_orig()
#decode2()


