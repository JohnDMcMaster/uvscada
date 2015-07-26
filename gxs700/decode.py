#!/usr/bin/env 
import argparse
import numpy as np
import struct

from uvscada import gxs700

# http://www.janeriksolem.net/2009/06/histogram-equalization-with-python-and.html
def histeq(buff, nbr_bins=256):
    height = 1850
    width = 1344
    depth = 2
    
    im =  np.zeros(1850 * 1344)
    i = 0
    for y in range(height):
        line0 = buff[y * width * depth:(y + 1) * width * depth]
        for x in range(width):
            b0 = ord(line0[2*x + 0])
            b1 = ord(line0[2*x + 1])
            
            # FIXME: 16 bit pixel truncation to fit into png
            im[i] = (b1 << 8) + b0
            i += 1


    #get image histogram
    imhist,bins = np.histogram(im.flatten(),nbr_bins,normed=True)
    cdf = imhist.cumsum() #cumulative distribution function
    cdf = 255 * cdf / cdf[-1] #normalize
    
    #use linear interpolation of cdf to find new pixel values
    im2 = np.interp(im.flatten(),bins[:-1],cdf)
    
    #return im2.reshape(im.shape), cdf
    rs = im2.reshape(im.shape)
    
    ret = bytearray()
    for i in xrange(len(rs)):
        ret += struct.pack('>H', int(rs[i]))
    return str(ret)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--hist-eq', '-e', action='store_true', help='Equalize histogram')
    parser.add_argument('fin', help='File name in')
    parser.add_argument('fout', default=None, nargs='?', help='File name out')
    args = parser.parse_args()

    if args.fout is None:
        if args.fin.find('.bin') < 0:
            raise Exception("Can't guess output file name")
        args.fout = args.fin.replace('.bin', '.png')

    print 'Reading image...'
    buff = open(args.fin, 'r').read()
    if args.hist_eq:
        print 'Equalizing histogram...'
        buff = histeq(buff)
    print 'Decoding image...'
    img = gxs700.GXS700.decode(buff)
    print 'Saving image...'
    img.save(args.fout)
    print 'Done'
