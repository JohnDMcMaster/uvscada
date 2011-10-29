#!/usr/bin/env python

'''
Sync seems to show up in upper left
Slightly darker stripe one pixel in
Essentially along the red pixels
'''

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
	
	# Skip offset
	#f.read(254)
	f.read(640 / 2 + 300)
	f.read(640 * 480 * 2)
		
	image = None
	while True:
		image = Image.new("RGB", (width, height), "White")
		for y in range(0, height, 2):
			# GBGB
			# RGRG
			line0 = f.read(width)
			#line0 = f.read(width)
			#line0 = f.read(width)
		
			line1 = f.read(width)
			#line1 = f.read(width)
			#line1 = f.read(width)
		
			if y < 0:
				print '%03u start: 0x%02X, 0x%02X, 0x%02X, 0x%02X' % (y, ord(line0[0]), ord(line0[1]), ord(line0[2]), ord(line0[3]))
				print '%03u start: 0x%02X, 0x%02X, 0x%02X, 0x%02X' % (y + 1, ord(line1[0]), ord(line1[1]), ord(line1[2]), ord(line1[3]))
			if y < 0:
				b = 640 - 4
				print '%03u   end: 0x%02X, 0x%02X, 0x%02X, 0x%02X' % (y, ord(line0[b + 0]), ord(line0[b + 1]), ord(line0[b + 2]), ord(line0[b + 3]))
				print '%03u   end: 0x%02X, 0x%02X, 0x%02X, 0x%02X' % (y + 1, ord(line1[b + 0]), ord(line1[b + 1]), ord(line1[b + 2]), ord(line1[b + 3]))

		
			for x in range(0, width):
				R = ord(line1[x])
				G = ord(line0[x])
				# make even
				B = ord(line0[x - (x % 2)])
				if image:
					image.putpixel((x, y), (R, G, B))
			for x in range(0, width):
				R = ord(line1[x])
				# Make odd
				G = ord(line1[x - (x % 2) + 1])
				# make even
				B = ord(line0[x - (x % 2)])
				if image:
					image.putpixel((x, y + 1), (R, G, B))
		if image:
			image.show()
			break
		print
		print
		print

def hexdump(data, prefix = ''):
	'''
	[mcmaster@gespenst icd2prog-0.3.0]$ hexdump -C /bin/ls |head
	00000000  7f 45 4c 46 01 01 01 00  00 00 00 00 00 00 00 00  |.ELF............|
	00000010  02 00 03 00 01 00 00 00  f0 99 04 08 34 00 00 00  |............4...|
	00017380  00 00 00 00 01 00 00 00  00 00 00 00              |............|
	'''
	import sys
	
	g_bytesPerRow = 16
	g_bytesPerHalfRow = 8

	def hexdumpHalfRow(data, start):
		col = 0

		while col < g_bytesPerHalfRow and start + col < size:
			index = start + col
			c = data[index]
			sys.stdout.write("%.2X " % ord(c))
			col += 1

		#pad remaining
		while col < g_bytesPerHalfRow:
			sys.stdout.write("   ")
			col += 1

		#End pad
		sys.stdout.write(" ")

		return start + g_bytesPerHalfRow

	pos = 0
	while pos < size:
		row_start = pos
		i = 0

		sys.stdout.write(prefix)
		pos = hexdumpHalfRow(data, size, pos)
		pos = hexdumpHalfRow(data, size, pos)

		sys.stdout.write("|")

		#Char view
		i = row_start
		while i < row_start + g_bytesPerRow and i < size:
			c = data[i]
			if isprint(c):
				sys.stdout.write("%c", c)
			else:
				sys.stdout.write("%c", '.')
			i += 1
		while i < row_start + g_bytesPerRow:
			sys.stdout.write(" ")
			i += 1

		sys.stdout.write("|\n")

def decode_as_sensor():
	'''
	Require interpolation
	Read two lines at a time
	'''
	width = 640
	#width = 642
	height = 480
	
	
	f = open(image_in, "r")
	
	# Skip offset
	#f.read(640 / 2)
	#f.read(640)
	#f.read(640 / 2 + 300)
	f.read(640 * 480 * 2)
		
	image = None
	while True:
		image = Image.new("RGB", (width, height), "White")
		for y in range(0, height, 2):
			# GBGB
			# RGRG
			line0 = f.read(width)
			#line0 = f.read(width)
			#line0 = f.read(width)
		
			line1 = f.read(width)
			#line1 = f.read(width)
			#line1 = f.read(width)
		
			
		
			if y < 0:
				print '%03u start: 0x%02X, 0x%02X, 0x%02X, 0x%02X' % (y, ord(line0[0]), ord(line0[1]), ord(line0[2]), ord(line0[3]))
				print '%03u start: 0x%02X, 0x%02X, 0x%02X, 0x%02X' % (y + 1, ord(line1[0]), ord(line1[1]), ord(line1[2]), ord(line1[3]))
			if y < 0:
				b = 640 - 4
				print '%03u   end: 0x%02X, 0x%02X, 0x%02X, 0x%02X' % (y, ord(line0[b + 0]), ord(line0[b + 1]), ord(line0[b + 2]), ord(line0[b + 3]))
				print '%03u   end: 0x%02X, 0x%02X, 0x%02X, 0x%02X' % (y + 1, ord(line1[b + 0]), ord(line1[b + 1]), ord(line1[b + 2]), ord(line1[b + 3]))

			if False:
				temp = line0
				line0 = line1
				line1 = temp
		
			for x in range(0, width):
				R = 0
				if x % 2 == 0:
					G = 0
					B = ord(line1[x])
				else:
					G = ord(line1[x])
					B = 0
					
				if image:
					image.putpixel((x, y), (R, G, B))
			for x in range(0, width):
				B = 0
				if x % 2 == 0:
					R = 0
					G = ord(line0[x])
				else:
					R = ord(line0[x])
					G = 0
				
				if image:
					image.putpixel((x, y + 1), (R, G, B))
		if image:
			image.show()
			break
		print
		print
		print

#decode_orig()
#decode2()
#decode_SGBRG8()
decode_as_sensor()
