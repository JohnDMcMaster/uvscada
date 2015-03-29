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

def decode():
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
        image_out = image_in.replace('.bin', '.png')

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
        image.save(image_out)
        image.show()
        open('image-single.bin', 'w').write(bin)
        return
    else:
        print 'Saving image'
        image.save(image_out)
        #print 'Saving binary'
        #open('frame_%04d.bin' % frame, 'w').write(bin)
        return

decode()

