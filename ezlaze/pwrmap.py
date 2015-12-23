#!/usr/bin/env python

from uvscada.cnc_hal import lcnc_ar
from uvscada.ezlaze import EzLaze
from uvscada.k2750 import K2750
from uvscada.benchmark import time_str

import argparse
import time
import sys
#from PIL import Image
import csv
import datetime
import os

def main1(hal, dmm, el):
    # 50x max ap size
    # Very approx
    #SPOT = 0.06

    shut_open = el.shut_open
    if 0:
        # 10x
        SPOT = 0.3
        el.shut_square(args.square)
    if 1:
        # 10x reduced
        SPOT = 0.05
        # From trial and error
        def shut_open():
            el.shut_square(30)
    
    hal.mv_abs({'x': -SPOT, 'y': -SPOT})
    
    if not args.dry:
        cwf = open(args.fout, 'wb')
        cw = csv.writer(cwf)
        cw.writerow(["t", "col", "row", "close", "open", "delta"])
    
    cols = int(4.6 / SPOT)
    rows = int(3.8 / SPOT)
    tpic = 2.3
    npic = cols * rows
    print 'Taking %dc x %dr => %d pics => ETA %s' % (cols, rows, npic, time_str(tpic * npic))
    tstart = time.time()
    
    # Takes some time to settle
    # Close early
    el.shut_close()
    posi = 0
    for row in xrange(rows):
        hal.mv_abs({'x': -SPOT, 'y': row * SPOT})
        for col in xrange(cols):
            posi += 1
            hal.mv_abs({'x': col * SPOT})
            if args.dry:
                continue
            print 'Taking %d / %d' % (posi, npic)
            for i in xrange(8):
                curr_close = dmm.curr_dc()
                # Time to open shutter?  Time to have effect?
                # Seems to power drift quick so think quicker => generally better
                shut_open()
                time.sleep(0.2)
                curr_open = dmm.curr_dc()
                el.shut_close()
                curr_delta = curr_open - curr_close
                cw.writerow([time.time(), col, row, curr_close, curr_open, curr_delta])
                cwf.flush()
                print '%s %dc, %dr: %0.9f A' % (datetime.datetime.utcnow(), col, row, curr_delta)
    print 'Ret home'
    hal.mv_abs({'x': 0, 'y': 0})
    print 'Movement done'
    # Convenient to be open at end to retarget
    shut_open()
    tend = time.time()
    print 'Took %s' % time_str(tend - tstart)

def main2(hal, dmm, el):
    # 50x max ap size
    # Very approx
    #SPOT = 0.06

    shut_open = el.shut_open
    if 0:
        # 10x
        SPOT = 0.3
        el.shut_square(args.square)
    if 1:
        # 10x reduced
        SPOT = 0.05
        # From trial and error
        def shut_open():
            el.shut_square(30)
    
    hal.mv_abs({'x': -SPOT, 'y': -SPOT})
    
    if not args.dry:
        cwf = open(args.fout, 'wb')
    
    cols = int(4.6 / SPOT)
    rows = int(3.8 / SPOT)
    tpic = 2.3
    npic = cols * rows
    print 'Taking %dc x %dr => %d pics => ETA %s' % (cols, rows, npic, time_str(tpic * npic))
    tstart = time.time()
    
    # Takes some time to settle
    # Close early
    el.shut_close()
    for row in xrange(rows):
        hal.mv_abs({'x': -SPOT, 'y': row * SPOT})
        for col in xrange(cols):
            hal.mv_abs({'x': col * SPOT})
            if args.dry:
                continue
            print '%s %dc, %dr: ' % (datetime.datetime.utcnow(), col, row),

            closed = []
            for i in xrange(1):
                t = time.time()
                closed.append((t, dmm.curr_dc()))
            
            shut_open()
            opened = []
            for i in xrange(4):
                time.sleep(0.5)
                t = time.time()
                curr = dmm.curr_dc()
                opened.append((t, curr))
                delta = curr - closed[0][1] 
                print '  %0.9f A' % delta,
                
            cwf.write(repr({'col': col, 'row': row, 'open': opened, 'close': closed}) + '\n')
            print
            el.shut_close()
            cwf.flush()

    print 'Ret home'
    hal.mv_abs({'x': 0, 'y': 0})
    print 'Movement done'
    # Convenient to be open at end to retarget
    shut_open()
    tend = time.time()
    print 'Took %s' % time_str(tend - tstart)

def main3(hal, dmm, el):
    # 50x max ap size
    # Very approx
    #SPOT = 0.06

    shut_open = el.shut_open
    if 0:
        # 10x
        SPOT = 0.3
        el.shut_square(args.square)
    if 1:
        # 10x reduced
        SPOT = 0.05
        # From trial and error
        def shut_open():
            el.shut_square(30, quick=True)
    
    hal.mv_abs({'x': -SPOT, 'y': -SPOT})
    
    if not args.dry:
        cwf = open(args.fout, 'wb')
    
    cols = int(4.6 / SPOT)
    rows = int(3.8 / SPOT)
    tpic = 2.3
    npic = cols * rows
    print 'Taking %dc x %dr => %d pics => ETA %s' % (cols, rows, npic, time_str(tpic * npic))
    tstart = time.time()
    
    # Takes some time to settle
    # Close early
    el.shut_close()
    for row in xrange(rows):
        hal.mv_abs({'x': -SPOT, 'y': row * SPOT})
        for col in xrange(cols):
            hal.mv_abs({'x': col * SPOT})
            if args.dry:
                continue
            print '%s %dc, %dr: ' % (datetime.datetime.utcnow(), col, row)

            closed = []
            for i in xrange(4):
                t = time.time()
                closed.append((t, dmm.curr_dc()))
            
            shut_open()
            opened = []
            ts = time.time()
            while time.time() - ts < 10.0:
                t = time.time()
                curr = dmm.curr_dc()
                opened.append((t, curr))
            print '  Samples: %d' % len(opened)
            cwf.write(repr({'col': col, 'row': row, 'open': opened, 'close': closed}) + '\n')
            el.shut_close()
            cwf.flush()

    print 'Ret home'
    hal.mv_abs({'x': 0, 'y': 0})
    print 'Movement done'
    # Convenient to be open at end to retarget
    shut_open()
    tend = time.time()
    print 'Took %s' % time_str(tend - tstart)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Use ezlaze with LinuxCNC to carve a bitmap')
    parser.add_argument('--dmm', default='/dev/serial/by-id/usb-Prologix_Prologix_GPIB-USB_Controller_PX8ZBY4W-if00-port0', help='K2750 serial port')
    parser.add_argument('--laser', default='/dev/serial/by-id/usb-1a86_USB2.0-Ser_-if00-port0', help='ezlaze serial port')
    parser.add_argument('--host', default='mk-bs', help='LinuxCNC host')
    parser.add_argument('--dry', action='store_true', help='Dry run')
    parser.add_argument('fout', nargs='?', default='pwrmap.pyv', help='Store data to')
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

        # frickin laser
        print
        print 'Initializing laser'
        el = EzLaze(args.laser)

        print
        print 'Running'
        main3(hal, dmm, el)
    finally:
        print 'Shutting down hal'
        if hal:
            hal.ar_stop()
