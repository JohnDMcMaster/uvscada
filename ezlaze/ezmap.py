#!/usr/bin/env python

from uvscada.cnc_hal import lcnc_ar
from uvscada.ezlaze import EzLaze
from PIL import Image
import argparse
import time
import sys

def main(hal, el, im):
    '''
    Full spot size using 10x objective: 330 um x 330 um
    About 20 shots to make easily visible
    '''
    SPOT = 0.33
    # lets make it 30 to improve contrast better
    SHOTS = 30
    if args.dry:
        SHOTS = 0

    print
    print 'Beginning main program'

    el.on()
    
    black = 0
    white = 0
    
    hal.mv_abs({'x': -1, 'y': -1})
    for row in xrange(im.size[1]):
        hal.mv_abs({'x': -1, 'y': row * SPOT})
        for col in xrange(im.size[0]):
            # Burn white areas represented as 0
            # (black anodized => white)
            if im.getpixel((col, row)):
                sys.stdout.write('#')
                sys.stdout.flush()
                black += 1
            else:
                sys.stdout.write(' ')
                sys.stdout.flush()
                hal.mv_abs({'x': col * SPOT})
                el.pulse(SHOTS)
                white += 1
        sys.stdout.write('\n')
        sys.stdout.flush()

    print 'Movement done'
    print 'Black pixels: %d' % black
    print 'White pixels: %d' % white
    print 'Laser shots: %d' % (white * SHOTS)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Use ezlaze with LinuxCNC to carve a bitmap')
    parser.add_argument('--port', default='/dev/ttyUSB0', help='ezlaze serial port')
    parser.add_argument('--host', default='mk-test', help='LinuxCNC host')
    parser.add_argument('--dry', action='store_true', help='Dry run')
    parser.add_argument('image', help='Image to burn')
    args = parser.parse_args()

    hal = None
    try:
        print
        print 'Initializing LCNC'
        hal = lcnc_ar.LcncPyHalAr(host=args.host, dry=args.dry, log=None)

        # frickin laser
        print
        print 'Initializing laser'
        el = EzLaze(args.port)

        main(hal, el, Image.open(args.image))
    finally:
        print 'Shutting down hal'
        if hal:
            hal.ar_stop()

