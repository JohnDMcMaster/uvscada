#!/usr/bin/env python
import argparse
import os
import glob
import time

from uvscada import gxs700
from uvscada import gxs700_util

def process_bin(fin, fout, hist_eq=False):
    print 'Reading %s...' % fin
    buff = open(fin, 'r').read()
    if hist_eq:
        print 'Equalizing histogram...'
        tstart = time.time()
        buff = gxs700_util.histeq(buff)
        tend = time.time()
        print '  Hist eq in %0.1f sec' % (tend - tstart,)
    print 'Decoding image...'
    tstart = time.time()
    img = gxs700.GXS700.decode(buff)
    tend = time.time()
    print '  Decode in %0.1f sec' % (tend - tstart,)
    print 'Saving %s...' % fout
    img.save(fout)

def process_png(fin, fout, hist_eq=False):
    print 'Reading %s...' % fin
    buff = open(fin, 'r').read()
    if args.hist_eq:
        print 'Equalizing histogram...'
        buff = gxs700_util.histeq(buff)
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
            process_bin(fn, fout, hist_eq=args.hist_eq)
        for fn in glob.glob(os.path.join(args.fin, '*.png')):
            fout = os.path.join(args.fout, os.path.basename(fn).replace('.png', '_e.png'))
            process_png(fn, fout, hist_eq=args.hist_eq)
    else:
        if args.fout is None:
            if args.fin.find('.bin') >= 0:
                if args.hist_eq:
                    fout = args.fin.replace('.bin', '_e.png')
                else:
                    fout = args.fin.replace('.bin', '.png')
                process_bin(args.fin, fout, hist_eq=args.hist_eq)
            elif args.fin.find('.png') >= 0:
                if args.hist_eq:
                    fout = args.fin.replace('.png', '_e.png')
                else:
                    raise Exception('Confused')
                process_png(args.fin, fout, hist_eq=args.hist_eq)
            else:
                raise Exception("Can't guess output file name")
        else:
            if args.fin.find('.bin') >= 0:
                process_bin(args.fin, args.fout, hist_eq=args.hist_eq)
            elif args.fin.find('.png') >= 0:
                process_png(args.fin, args.fout, hist_eq=args.hist_eq)
            else:
                raise Exception("Can't guess input type")
    print 'Done'
