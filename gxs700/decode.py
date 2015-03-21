#!/usr/bin/env python

'''
1344 x 1850, 16 bit
278528 pixel
4972800 bytes
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
import glob

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


def decode3():
    print 'constructing raw'
    if 0:
        f = open('/tmp/stuff', 'w')
        i = 0
        for fn in sorted(glob.glob(image_in + '/*.bin')):
            r = open(fn, 'r').read()
            # this shows that the splotches are not correlated to packet boundaries
            # the 0x40 thing was a misreading of wireshark captures
            #f.write(r + '\xFF\xFF' * 16 + '\x00\x00' * 16)
            f.write(r)
        f = open('/tmp/stuff', 'r')
    else:
        f = open(image_in, 'r')

    height = 1850
    width = 1344
    depth = 2
    
    print 'Decoding %ux%u' % (width, height)
    #f.read(width*height*depth)

    image = None
    first_loop = True
    # no need to reallocate each loop
    image = Image.new("RGB", (width, height), "Yellow")
    frame = 0
    i = 0
    gmin = 0xFFFF
    gmax = 0
    while True:
        frame += 1
        bin = ''
        print
        print 'Rendering frame %d...' % frame
        for y in range(height):
            line0 = f.read(width*depth)
            bin += line0
        
            if y % (height / 10) == 0:
                print 'Rendering y = %d / %d...' % (y, height)
        
            for x in range(width):
                b0 = ord(line0[2*x + 0])
                b1 = ord(line0[2*x + 1])
                G = (b1 << 8) + b0
                gmin = min(G, gmin)
                gmax = max(G, gmax)
                #16 bit pixel?
                G = G/0x100
                if G > 0xFF:
                    print G
                    print i
                    print b0
                    print b1
                    raise Exception()
                G = 0xFF - G
                image.putpixel((x, y), (G, G, G))
                i += 1
           
        print 'min: 0x%04X' % gmin
        print 'max: 0x%04X' % gmax
        if 0:
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
            return

decode3()

