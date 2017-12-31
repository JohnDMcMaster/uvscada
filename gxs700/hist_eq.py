#!/usr/bin/env python
import argparse
import os
import glob

from uvscada import gxs700

def process_png(fin, fout, hist_eq=False):
    print 'Reading %s...' % fin
    buff = open(fin, 'r').read()
    print 'Decoding image...'
    img = gxs700.GXS700.decode(buff)
    print 'Saving %s...' % fout
    img.save(fout)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Equalize 16 bit GXS700 image histogram')
    parser.add_argument('fin', help='File name in')
    parser.add_argument('fout', default=None, nargs='?', help='File name out')
    args = parser.parse_args()

    if os.path.isdir(args.fin):
        dout = args.fout
        if dout == args.fin or not dout:
            raise Exception("Couldn't auto name output dir")

        if not os.path.exists(args.fout):
            os.mkdir(args.fout)
        for fn in glob.glob(os.path.join(args.fin, '*.png')):
            fout = os.path.join(args.fout, os.path.basename(fn).replace('.png', '_e.png'))
            process_png(fn, fout)
    else:
        fout = args.fout or args.fin.replace('.png', '_e.png')
        if fout == args.fin:
                raise Exception("Couldn't auto name output file")
        process_png(args.fin, fout)
    print 'Done'
