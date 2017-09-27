from uvscada import gxs700
from uvscada import gxs700_util
from uvscada import util

import argparse
import glob
import os
import time

def run(force):
    def scan_cb(itr):
        if force and itr == 0:
            print 'Forcing trigger'
            gxs.sw_trig()

    def cb(imgb):
        if args.bin:
            fn = os.path.join(args.dir, 'capture_%03d.bin' % imagen[0])
            print 'Writing %s' % fn
            open(fn, 'w').write(imgb)

        def save(fn, eq):
            print 'Decoding %s' % fn
            if eq:
                tstart = time.time()
                buff = gxs700_util.histeq(imgb)
                tend = time.time()
                print '  Hist eq in %0.1f' % (tend - tstart,)
            else:
                buff = imgb
            tstart = time.time()
            img = gxs700.GXS700.decode(buff)
            tend = time.time()
            print '  Decode in %0.1f' % (tend - tstart,)
            print '  Writing %s' % fn
            img.save(fn)

        if args.png:
            save(os.path.join(args.dir, 'capture_%03d.png' % imagen[0]), eq=False)
            if args.hist_eq:
                save(os.path.join(args.dir, 'capture_%03de.png' % imagen[0]), eq=True)

        imagen[0] += 1

    _usbcontext, _dev, gxs = gxs700_util.ez_open_ex(verbose=args.verbose)

    if not os.path.exists(args.dir):
        os.mkdir(args.dir)

    imagen = [0]
    while glob.glob('%s/capture_%03d*' % (args.dir, imagen[0])):
        imagen[0] += 1
    print 'Taking first image to %s' % ('%s/capture_%03d.bin' % (args.dir, imagen[0]),)

    gxs.cap_binv(args.number, cb, scan_cb=scan_cb)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('--bin', '-b', action='store_true', help='Store .bin in addition to .png')
    parser.add_argument('--hist-eq', '-e', action='store_true', help='Equalize histogram')
    parser.add_argument('--dir', default='out', help='Output dir')
    parser.add_argument('--force', '-f', action='store_true', help='Force trigger')
    parser.add_argument('--number', '-n', type=int, default=1, help='number to take')
    util.add_bool_arg(parser, '--png', default=True)
    args = parser.parse_args()

    run(force=args.force)
