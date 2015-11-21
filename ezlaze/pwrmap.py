#!/usr/bin/env python

from uvscada.cnc_hal import lcnc_ar
from uvscada.ezlaze import EzLaze
from uvscada.k2750 import K2750

import argparse
import time
import sys
#from PIL import Image
import csv

def main(hal, dmm, el):
    # 50x max ap size
    # Very approx
    SPOT = 0.06
    
    hal.mv_abs({'x': -SPOT, 'y': -SPOT})
    
    cwf = open('pwrmap.csv', 'wb')
    cw = csv.writer(cwf)
    cw.writerow(["col", "row", "close", "open", "delta"])
    
    rows = 4
    cols = 4
    
    # Takes some time to settle
    # Close early
    el.shut_close()
    for row in xrange(rows):
        hal.mv_abs({'x': -SPOT, 'y': row * SPOT})
        for col in xrange(cols):
            hal.mv_abs({'x': col * SPOT})
            curr_close = dmm.curr()
            el.shut_open()
            curr_open = dmm.curr()
            el.shut_close()
            curr_delta = curr_open - curr_close
            cw.writerow([col, row, curr_close, curr_open, curr_delta])
            print '%dc, %dr: %0.9f A' % (col, row, curr_delta)

    print 'Ret home'
    hal.mv_abs({'x': 0, 'y': 0})
    print 'Movement done'

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Use ezlaze with LinuxCNC to carve a bitmap')
    parser.add_argument('--dmm', default='/dev/ttyUSB0', help='K2750 serial port')
    parser.add_argument('--laser', default='/dev/ttyUSB1', help='ezlaze serial port')
    parser.add_argument('--host', default='mk-bs', help='LinuxCNC host')
    parser.add_argument('--dry', action='store_true', help='Dry run')
    #parser.add_argument('fout', help='Store data to')
    args = parser.parse_args()

    hal = None
    try:
        print
        print 'Initializing LCNC'
        hal = lcnc_ar.LcncPyHalAr(host=args.host, dry=args.dry, log=None)

        print
        print 'Initializing DMM'
        dmm = K2750(args.dmm)

        # frickin laser
        print
        print 'Initializing laser'
        el = EzLaze(args.laser)

        main(hal, dmm, el)
    finally:
        print 'Shutting down hal'
        if hal:
            hal.ar_stop()
