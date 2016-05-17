#!/usr/bin/env python
import argparse
import os
import glob

from uvscada import gxs700
from uvscada.gxs700_util import histeq

def process(fin, fout):
    print 'Reading %s...' % fin
    buff = open(fin, 'r').read()
    if args.hist_eq:
        print 'Equalizing histogram...'
        buff = histeq(buff)
    print 'Decoding image...'
    img = gxs700.GXS700.decode(buff)
    print 'Saving %s...' % fout
    img.save(fout)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--hist-eq', '-e', action='store_true', help='Equalize histogram')
    parser.add_argument('fin', help='File name in')
    parser.add_argument('fout', default=None, nargs='?', help='File name out')
    args = parser.parse_args()

    if os.path.isdir(args.fin):
        if args.fout is None:
            raise Exception("dir requires fout")
        if not os.path.exists(args.fout):
            os.mkdir(args.fout)
        for fn in glob.glob(os.path.join(args.fin, '*.bin')):
            fout = os.path.join(args.fout, os.path.basename(fn).replace('.bin', '.png'))
            process(fn, fout)
    else:
        if args.fout is None:
            if args.fin.find('.bin') < 0:
                raise Exception("Can't guess output file name")
            args.fout = args.fin.replace('.bin', '.png')
            if args.hist_eq:
                args.fout = args.fout.replace('.png', '_e.png')
        process(args.fin, args.fout)
    print 'Done'
