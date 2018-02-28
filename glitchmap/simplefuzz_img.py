#!/usr/bin/env python

import argparse
from PIL import Image
import numpy as np
import json
import base64

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

#(r, g, b)
status2c = {
    # While
    'secure': (255, 255, 255),
    # Red
    'overcurrent': (255, 0, 0),
    'overcurrent': (255, 0, 0),
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Post process fuzzing')
    parser.add_argument('fin', help='Input file')
    args = parser.parse_args()

    print 'Loading...'
    jlf = open(args.fin, 'r')
    
    metaj = json.loads(jlf.readline())

    cols = metaj['cols']
    rows = metaj['rows']
    print 'Size: %dc x %dr' % (cols, rows)
    print 'Plotting...'
    im = Image.new("RGB", (cols, rows), "white")
    nlines = 0
    allzeros = 0
    allones = 0
    matches = 0
    others = 0
    exceptions = 0
    for row in xrange(rows):
        for col in xrange(cols):
            for samplei in xrange(3):
                j = json.loads(jlf.readline())
                # {"devfg": {"config": {"secure": true, "user_id1": 16383, "user_id0": 16383, "user_id3": 16383, "user_id2": 16383, "conf_word": 3}, "code": "AAAAA...AAAAAAAAAAAA=", "data": "AA...AAAAAAAAAA="}, "dumpi": 1, "y": 0.0, "x": 0.0, "type": "sample", "col": 0, "row": 0}
                def decode(k):
                    data = j['devcfg'].get(k)
                    if data is None:
                        return None
                    return base64.b64decode(data)
            
                code, data, config = (None, None, None)
                if 'devcfg' in j:
                    code = decode('code')
                    data = decode('data')
                    config = j['devcfg']['config']
    
                c = (0, 0, 255)
                # Exception, namely overcurrent
                if 'e' in j:
                    e = j['e']
                    #print e
                    c = (255, 0, 0)
                    exceptions += 1
                # Shoud have this if no error
                elif code is not None:
                    # All 0's => protected
                    def allzero():
                        for c in code:
                            if c != '\x00':
                                return False
                        return True
                    def allone():
                        for c in code:
                            if c not in ('\xFF', '\x3F'):
                                return False
                        return True
                    def ismatch():
                        ref = open('/home/mcmaster/doc/ext/uvscada/ic/pic/pic16f84_minipro-code_cnt16.bin', 'r').read()
                        for refc, readc in zip(ref, code):
                            if refc != readc:
                                return False
                        return True
                    if allzero():
                        allzeros += 1
                        c = (64, 64, 64)
                    elif allone():
                        allones += 1
                        c = (0, 0, 0)
                    elif ismatch():
                        matches += 1
                        c = (0, 255, 0)
                    # Some other state
                    else:
                        others += 1
                        c = (127, 127, 127)
                else:
                    print j
                    raise Exception('No code, no exception')
                    #c = (16, 16, 16)

                im.putpixel((col, row), c)
                nlines += 1
    
    print 'Have %d / %d points' % (nlines, rows * cols * 3)
    print '  All 0:       %d' % allzeros
    print '  All 1:       %d' % allones
    print '  Matches:     %d' % matches
    print '  Others:      %d' % others
    print '  Exceptions:  %d' % exceptions

    fnout = args.fin.replace('.jl', '.png')
    if fnout == args.fin:
        raise Exception('Expecting .jl file')
    print 'Saving to %s...' % fnout
    im.save(fnout)

    print 'Done'

