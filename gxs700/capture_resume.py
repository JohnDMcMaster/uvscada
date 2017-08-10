'''
Capture data by taking over previously started capture
'''

from uvscada import gxs700
from uvscada import gxs700_util
from uvscada import util

import argparse
import glob
import os

from uvscada.gxs700_util import usb1, open_dev, gxs700_fw

def ez_open_ex(verbose=False):
    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext, verbose=verbose)

    # FW load should indicate size
    vid = dev.getDevice().getVendorID()
    pid = dev.getDevice().getProductID()
    _desc, size = gxs700_fw.pidvid2name_post[(vid, pid)]

    print 'size: %d' % size
    return usbcontext, dev, gxs700.GXS700(usbcontext, dev, verbose=verbose, size=size, init=False)

def cap_binv(self, n, cap_cb, loop_cb=lambda: None, scan_cb=lambda itr: None):
    #self._cap_setup()

    taken = 0
    while taken < n:
        imgb = self._cap_bin(scan_cb=scan_cb)
        rc = cap_cb(imgb)
        # hack: consider doing something else
        if rc:
            n += 1
        taken += 1
        self.cap_cleanup()
        loop_cb()

    self.hw_trig_disarm()


def run(force):
    def scan_cb(itr):
        if force and itr % 10000 == 0:
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
                buff = gxs700_util.histeq(imgb)
            else:
                buff = imgb
            img = gxs700.GXS700.decode(buff)
            print 'Writing %s' % fn
            img.save(fn)

        if args.png:
            save(os.path.join(args.dir, 'capture_%03d.png' % imagen[0]), eq=False)
            if args.hist_eq:
                save(os.path.join(args.dir, 'capture_%03de.png' % imagen[0]), eq=True)

        imagen[0] += 1

    #_usbcontext, _dev, gxs = gxs700_util.ez_open_ex(verbose=args.verbose)
    _usbcontext, _dev, gxs = ez_open_ex(verbose=args.verbose)

    if not os.path.exists(args.dir):
        os.mkdir(args.dir)

    imagen = [0]
    while glob.glob('%s/capture_%03d*' % (args.dir, imagen[0])):
        imagen[0] += 1
    print 'Taking first image to %s' % ('%s/capture_%03d.bin' % (args.dir, imagen[0]),)

    #gxs.cap_binv(args.number, cb, scan_cb=scan_cb)
    cap_binv(gxs, args.number, cb, scan_cb=scan_cb)

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
