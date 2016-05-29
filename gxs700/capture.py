from uvscada import gxs700
from uvscada.gxs700_util import open_dev

import argparse
import glob
import os
import usb1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('--dir', default='out', help='Output dir')
    parser.add_argument('--force', '-f', action='store_true', help='Force trigger')
    parser.add_argument('--number', '-n', type=int, default=1, help='number to take')
    args = parser.parse_args()

    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext)
    gxs = gxs700.GXS700(usbcontext, dev, verbose=args.verbose)
    
    fn = ''
    
    if not os.path.exists(args.dir):
        os.mkdir(args.dir)
    
    taken = 0
    imagen = 0
    while glob.glob('%s/capture_%03d*' % (args.dir, imagen)):
        imagen += 1
    print 'Taking first image to %s' % ('%s/capture_%03d.bin' % (args.dir, imagen),)
    
    def scan_cb(itr):
        if args.force and itr == 0:
            print 'Forcing trigger'
            gxs.sw_trig()
        
    def cb(imgb):
        global taken
        global imagen
        
        fn = 'capture_%03d.bin' % imagen
        print 'Writing %s' % fn
        open(fn, 'w').write(imgb)

        fn = 'capture_%03d.png' % imagen
        print 'Decoding %s' % fn
        img = gxs700.GXS700.decode(imgb)
        print 'Writing %s' % fn
        img.save(fn)

        taken += 1
        imagen += 1
    
    gxs.cap_binv(args.number, cb, scan_cb=scan_cb)
