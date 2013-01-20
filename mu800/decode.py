#!/usr/bin/env python

'''
Sync seems to show up in upper left
Slightly darker stripe one pixel in
Essentially along the red pixels
'''

try:
    import psyco
    psyco.full()
except ImportError:
    print 'Note: failed to import psyco'


import Image
import sys
import time
import os

image_in = None
if len(sys.argv) > 1:
    image_in = sys.argv[1]
if image_in is None:
    image_in = "image.bin"
image_out = None
if len(sys.argv) > 2:
    image_out = sys.argv[2]


def hexdump(data, prefix = ''):
	'''
	[mcmaster@gespenst icd2prog-0.3.0]$ hexdump -C /bin/ls |head
	00000000  7f 45 4c 46 01 01 01 00  00 00 00 00 00 00 00 00  |.ELF............|
	00000010  02 00 03 00 01 00 00 00  f0 99 04 08 34 00 00 00  |............4...|
	00017380  00 00 00 00 01 00 00 00  00 00 00 00              |............|
	'''
	import sys
	
	size = len(data)
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
		pos = hexdumpHalfRow(data, pos)
		pos = hexdumpHalfRow(data, pos)

		sys.stdout.write("|")

		#Char view
		i = row_start
		while i < row_start + g_bytesPerRow and i < size:
			c = data[i]
			def isprint(c):
			    return c >= ' ' and c <= '~'
			if isprint(c):
				sys.stdout.write("%c" % c)
			else:
				sys.stdout.write("%c" % '.')
			i += 1
		while i < row_start + g_bytesPerRow:
			sys.stdout.write(" ")
			i += 1

		sys.stdout.write("|\n")


def decode_mu800():

    file_size = statinfo = os.stat(image_in).st_size
    print 'File size: %u' % file_size
    if 1:
        if 0:
            width = 800
            height = 600
        if 0:
            width = 1600
            height = 1200
        if 1:
            width = 3264
            height = 2448
    elif file_size == 800 * 600:
        print 'File matches 800X600'
        width = 800
        height = 600
    elif file_size == 1600 * 1200:
        print 'File matches 1600X1200'
        width = 1600
        height = 1200
    elif file_size == 3264 * 2448:
        width = 3264
        height = 2448
    else:
        raise Exception('Failed to ID file dimension')
        
    print 'Decoding %ux%u' % (width, height)

    f = open(image_in, "r")
    
    # First frame or two are dark
    # 800x600 is unpredictable
    #f.read(width * height * 1 + width * 514 + 736)
    f.read(width * height * 2 + width * 0 + 0)
        
    image = None
    first_loop = True
    # no need to reallocate each loop
    image = Image.new("RGB", (width, height), "Yellow")
    frame = 0
    while True:
        frame += 1
        bin = ''
        print
        print 'Rendering frame %d...' % frame
        for y in range(0, height, 2):
            # GBGB
            # RGRG
            line0 = f.read(width)
            bin += line0
            line1 = f.read(width)
            bin += line1
        
            '''
            if y == 0:
                print 'Line 0:'
                hexdump(line0, '  ')
            '''
        
            if y % (height / 10) == 0:
                print 'Rendering y = %d / %d...' % (y, height)
        
            '''
            GRGRGR...
            BGBGBG...
            '''
            for x in range(0, width, 2):
                R = 0
                G = ord(line0[x + 0])
                B = 0
                image.putpixel((x + 0, y + 0), (R, G, B))
            for x in range(0, width, 2):
                R = ord(line0[x + 1])
                G = 0
                B = 0
                image.putpixel((x + 1, y + 0), (R, G, B))
            for x in range(0, width, 2):
                R = 0
                G = 0
                B = ord(line1[x + 0])
                image.putpixel((x + 0, y + 1), (R, G, B))
            for x in range(0, width, 2):
                R = 0
                G = ord(line1[x + 1])
                B = 0
                image.putpixel((x + 1, y + 1), (R, G, B))
                
        if 1:
            print 'Displaying image (%u bytes)' % len(bin)
            image.save('image.png')
            image.show()
            open('image-single.bin', 'w').write(bin)
            return
        else:
            print 'Saving image'
            image.save('frame_%04d.png' % frame)
            print 'Saving binary'
            open('frame_%04d.bin' % frame, 'w').write(bin)
            #return
decode_mu800()


