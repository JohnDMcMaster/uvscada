#!/usr/bin/env python
'''
Relevant modes
I (32-bit signed integer pixels)
    includes 16 bit grayscale
LA (L with alpha)
Unfortunately IA isn't a mode
For most of these applications we are stitching to maps which are "best effort" for online viewing
High precision applications will continue to work on raw data
TODO: look into options for combining layers to form tiffs etc
'''
import argparse
import os
from PIL import Image, ImageDraw
#import ImageDraw
import glob

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Mask 16 bit grayscale into 8 bit grayscale with alpha')
    parser.add_argument('--overwrite', action='store_true', help='')
    parser.add_argument('dir_in', help='')
    parser.add_argument('dir_out', help='')
    args = parser.parse_args()
    
    #mask = Image.open('mask.png').convert('L')
    
    if os.path.exists(args.dir_out):
        if not args.overwrite:
            raise Exception("Refusing to overwrite output")
    else:
        os.mkdir(args.dir_out)
    
    def im_i2l(im):
        # lame
        return im.point([i/256 for i in xrange(0x10000)],'L')

    for fn in glob.glob(os.path.join(args.dir_in, '*.png')):
        print
        print
        print 'orig'
        print fn
        imi = Image.open(fn)
        print imi.mode
        print [imi.getpixel((i, i)) for i in xrange(0, 600, 50)]
        
        # IA is not supported
        # truncate to L so we can make LA
        print
        print 'L'
        iml = im_i2l(imi)
        print iml.mode
        print [iml.getpixel((i, i)) for i in xrange(0, 600, 50)]
        
        print
        print 'LA'
        mask = Image.new('L', iml.size, color=0)
        draw = ImageDraw.Draw(mask)
        #draw.rectangle((50,80,100,200), fill=0)
        # opened in image editor to get approx coords
        polym = {
                        0:(285, 10),            1:(1570, 10),
                 7: (5, 280),                           2: (1845, 240),
                 6: (5, 1060),                          3: (1845, 1100),
                        5: (285, 1335),        4: (1570, 1335),
                    }
        draw.polygon(polym.values(), fill=255)
        iml.putalpha(mask)
        print iml.mode
        print [iml.getpixel((i, i)) for i in xrange(0, 600, 50)]
        iml.save(os.path.join(args.dir_out, os.path.basename(fn)))
        #break
