#!/usr/bin/env python

from uvscada import statistics

import argparse
import time
import sys
from PIL import Image
import datetime
import csv
import numpy as np
import math
import math

# http://www.janeriksolem.net/2009/06/histogram-equalization-with-python-and.html
#def histeq(buff, nbr_bins=0x10000):
def histeq(buff, nbr_bins=0x100):
    im = np.array(buff)

    #get image histogram
    imhist, bins = np.histogram(im.flatten(), nbr_bins,normed=True)
    cdf = imhist.cumsum() #cumulative distribution function
    #cdf = (nbr_bins - 1) * cdf / cdf[-1] #normalize
    cdf = 255 * cdf / cdf[-1] #normalize
    #print cdf[0:10]
    
    #use linear interpolation of cdf to find new pixel values
    im2 = np.interp(im.flatten(), bins[:-1], cdf)
    rs = im2.reshape(im.shape)
    
    return rs

def scale(buff):
    low = min(buff)
    high = max(buff)
    print 'Lo: %0.6f' % low
    print 'Hi: %0.6f' % high
    for i in xrange(len(buff)):
        buff[i] = 255. * (buff[i] - low) / (high - low)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Use ezlaze with LinuxCNC to carve a bitmap')
    parser.add_argument('fin', help='Input file')
    args = parser.parse_args()

    print 'Loading...'
    crf = open(args.fin, 'r')
    
    cols = 0
    rows = 0
    vals = {}
    valsl = []
    for l in crf:
        '''
        {'close': [
            (1449558422.238357, 0.00695190066)],
        'open': [
            (1449558423.600868, 0.00695164315),
             (1449558424.116635, 0.00695024803),
             (1449558424.635478, 0.00694888504), 
          (1449558425.154403, 0.00694787549)], 
          'col': 0, 
          'row': 0}
        '''
        j = eval(l, {"__builtins__": {}})
        rows = max(rows, j['row'])
        cols = max(cols, j['col'])

        def diff(l):
            ret = []
            for i in xrange(len(l) - 1):
                ret.append(l[i + 1] - l[i])
            return ret
        
        opened = [x[1] for x in j['open']]
        # About first 100 points seems to be actual resposne region
        opened = opened[:100]
        # Velocity
        openedp = diff(opened)
        # Acceleration
        openedpp = diff(openedp)
        
        # Delta
        # pwrmap_6_5v_lots_maxmin100.png
        if 0:
            val = max(opened) - min(opened)
        # Power dip
        if 1:
            def sign(x):
                return math.copysign(1, x)
            m0 = sign(openedpp[0])
            for i in xrange(1, len(openedpp)):
                if sign(m0) != sign(openedpp[i]):
                    break
            # Account for second derrivitive
            val = opened[i + 2] - opened[0]
        
        valsl.append(val)

    print 'Cols: %d' % cols
    print 'Rows: %d' % rows

    # Limit numbers that are more than a few std dev away
    # this messes up way that hist eq currently works
    # although not entirely sure why
    # helped a lot
    if 1:
        print valsl[0:10]
        sd = statistics.stdev(valsl)
        u = statistics.mean(valsl)
        sds = 2
        print 'Mean: %f' % u
        print 'SD: %f' % sd
        keep_min = u - sd * sds
        keep_max = u + sd * sds
        print 'Keeping'
        print '  Min: %f' % keep_min
        print '  Max: %f' % keep_max
        valsl = [min(keep_max, x) for x in valsl]
        valsl = [max(keep_min, x) for x in valsl]

    if 0:
        print 'Equalizing...'
        valsl = histeq(valsl)

    if 1:
        print 'Scaling...'
        scale(valsl)
    
    print 'Plotting...'
    im = Image.new("RGB", (cols, rows), "white")
    i = 0
    for row in xrange(rows):
        for col in xrange(cols):
            try:
                raw = valsl[i]
            # processing a partial set
            except IndexError:
                print 'WARNING: partial set'
                break
            if 1:
                v = int(raw)
                #print vals[i], raw, v
                im.putpixel((col, row), (v, v, v))
            if 0:
                print raw
                v = int(raw * 0x10000)
                r = min((v >> 0), 0xFF)
                g = min((v >> 8), 0xFF)
                b = (v >> 16) & 0xFF
                print r, g, b
                im.putpixel((col, row), (r, g, b))
            
            i += 1

    fnout = args.fin.replace('.pyv', '.png')
    print 'Saving to %s...' % fnout
    im.save(fnout)

    print 'Done'

