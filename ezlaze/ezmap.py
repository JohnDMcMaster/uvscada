#!/usr/bin/env python

from uvscada.cnc_hal import lcnc_ar
from uvscada.ezlaze import EzLaze
import argparse
import time

'''
Full spot size using 10x objective: 330 um x 330 um
About 20 shots to make easily visible
'''
SPOT = 0.33
# lets make it 30 to improve contrast better
SHOTS = 30

def main(hal, el):
    print
    print 'Beginning main program'

    el.on()
    
    hal.mv_abs({'x': SPOT * 0})
    el.pulse(SHOTS)
    hal.mv_abs({'x': SPOT * 1})
    time.sleep(3)
    hal.mv_abs({'x': SPOT * 2})
    el.pulse(SHOTS)

    print 'Movement done'

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Use ezlaze with LinuxCNC to carve a bitmap')
    parser.add_argument('--port', default='/dev/ttyUSB0', help='ezlaze serial port')
    parser.add_argument('--host', default='mk-test', help='LinuxCNC host')
    args = parser.parse_args()

    hal = None
    try:
        print
        print 'Initializing LCNC'
        hal = lcnc_ar.LcncPyHalAr(host=args.host, dry=False, log=None)

        # frickin laser
        print
        print 'Initializing laser'
        el = EzLaze(args.port)

        main(hal, el)
    finally:
        print 'Shutting down hal'
        if hal:
            hal.ar_stop()

