#!/usr/bin/env python

import argparse
import time
import sys
from PIL import Image
import datetime
import csv
import numpy as np
import math
import statistics

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Use ezlaze with LinuxCNC to carve a bitmap')
    parser.add_argument('fin', help='Input file')
    args = parser.parse_args()

    print 'Loading...'
    crf = open(args.fin, 'r')
    header = crf.readline()
    cr = csv.reader(crf)
    cols = 0
    rows = 0
    vals = {}
    for crow in cr:
        #print crow
        col = int(crow[1])
        row = int(crow[2])
        iclose = float(crow[3])
        iopen = float(crow[4])
        idelta = float(crow[5])
        #v = iopen
        #v = iclose
        v = idelta

        cols = max(col + 1, cols)
        rows = max(row + 1, rows)
        #vals[(col, row)] = v
        vals[(col, row)] = vals.get((col, row), []) + [v]
    
    def mk_valsl():
        valsl = []
        for row in xrange(rows):
            for col in xrange(cols):
                try:
                    raw = vals[(col, row)]
                # processing a partial set
                except KeyError:
                    print 'WARNING: partial set'
                    return valsl
                # Just average for now
                valsl.append(sum(raw) / len(raw))
        return valsl
        
    valsl = mk_valsl()
    
    # take log
    if 0:
        mval = min(valsl) - 0.0001
        print 'Min: %f' % mval
        # Prevent negative current issues
        valsl = [math.log(x - mval) for x in valsl]
    
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

    if 1:
        print 'Equalizing...'
        valsl = histeq(valsl)
    
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

    fnout = args.fin.replace('.csv', '.png')
    print 'Saving to %s...' % fnout
    im.save(fnout)

    print 'Done'

