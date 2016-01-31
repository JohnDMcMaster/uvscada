#!/usr/bin/env python

from uvscada.cnc_hal import lcnc_ar
from uvscada.k2750 import K2750
from uvscada.benchmark import time_str

import argparse
import time
import datetime
import os

def main3(hal, dmm):
    # 10x reduced
    SPOT = 0.05
    
    hal.mv_abs({'x': -SPOT, 'y': -SPOT})
    
    if not args.dry:
        cwf = open(args.fout, 'wb')
    
    cols = int(4.6 / SPOT)
    rows = int(3.8 / SPOT)
    tpic = 2.3
    npic = cols * rows
    print 'Taking %dc x %dr => %d pics => ETA %s' % (cols, rows, npic, time_str(tpic * npic))
    tstart = time.time()
    
    for row in xrange(rows):
        hal.mv_abs({'x': -SPOT, 'y': row * SPOT})
        for col in xrange(cols):
            hal.mv_abs({'x': col * SPOT})
            if args.dry:
                continue
            print '%s %dc, %dr: ' % (datetime.datetime.utcnow(), col, row)

            mas = []
            ts = time.time()
            while time.time() - ts < 10.0:
                t = time.time()
                curr = dmm.curr_dc()
                mas.append((t, curr))
            print '  Samples: %d' % len(mas)
            cwf.write(repr({'col': col, 'row': row, 'mA': mas}) + '\n')
            cwf.flush()

    print 'Ret home'
    hal.mv_abs({'x': 0, 'y': 0})
    print 'Movement done'
    # Convenient to be open at end to retarget
    tend = time.time()
    print 'Took %s' % time_str(tend - tstart)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Use ezlaze with LinuxCNC to carve a bitmap')
    parser.add_argument('--dmm', default='/dev/serial/by-id/usb-Prologix_Prologix_GPIB-USB_Controller_PX8ZBY4W-if00-port0', help='K2750 serial port')
    parser.add_argument('--laser', default='/dev/serial/by-id/usb-1a86_USB2.0-Ser_-if00-port0', help='ezlaze serial port')
    parser.add_argument('--host', default='mk-bs', help='LinuxCNC host')
    parser.add_argument('--dry', action='store_true', help='Dry run')
    parser.add_argument('fout', nargs='?', default='cwmap.pv', help='Store data to')
    args = parser.parse_args()

    if os.path.exists(args.fout):
        raise Exception("Refusing to overwrite")
    
    hal = None
    try:
        print
        print 'Initializing LCNC'
        hal = lcnc_ar.LcncPyHalAr(host=args.host, dry=args.dry, log=None)

        print
        print 'Initializing DMM'
        dmm = K2750(args.dmm)

        print
        print 'Running'
        main3(hal, dmm)
    finally:
        print 'Shutting down hal'
        if hal:
            hal.ar_stop()
