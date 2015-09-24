# https://github.com/vpelletier/python-libusb1
# Python-ish (classes, exceptions, ...) wrapper around libusb1.py . See docstrings (pydoc recommended) for usage.
import usb1
# Bare ctype wrapper, inspired from library C header file.
import libusb1
import argparse
from uvscada.gxs700_util import open_dev
import os
from uvscada import gxs700
import glob

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('--number', '-n', type=int, default=1, help='number to take')
    args = parser.parse_args()

    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext)
    gxs = gxs700.GXS700(usbcontext, dev, verbose=args.verbose)
    
    fn = ''
    
    taken = 0
    imagen = 0
    while glob.glob('capture_%03d*' % imagen):
        imagen += 1
    print 'Taking first image to %s' % ('capture_%03d.bin' % imagen,)
    
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
    
    gxs.cap_binv(args.number, cb)

