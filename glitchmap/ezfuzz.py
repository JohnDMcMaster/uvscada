#!/usr/bin/env python

'''
Scans across a die, shooting laser to find areas that changes chip operation
'''

from uvscada.cnc_hal import lcnc_ar
from uvscada.minipro import Minipro
from uvscada.ezlaze import EzLaze
from uvscada.benchmark import time_str
import threading
import Queue

import argparse
import time
import datetime
import os
import json
import base64
import random
import md5
import binascii

class ELT(threading.thread):
    def __init__(self, el):
        self.el = el
        self.q = Queue()
        self.running = True
        self.idle = threading.Event()
        self.idle.set()
    
    def fire(self):
        self.q.put(None)
    
    def run(self):
        while self.running:
            try:
                _t = self.q.get(True, 0.1)
            except Queue.Empty:
                continue
            
            self.idle.clear()
            self.el.fire()
            self.idle.set()

def run(hal, prog, el, elt, fout, dry=False, square=False):
    # 50x max ap size
    # Very approx
    #SPOT = 0.06

    if 0:
        # 10x
        SPOT = 0.3
        el.shut_square(square)
    if 1:
        # 10x reduced
        SPOT = 0.05
        # From trial and error
        el.shut_square(30)
    
    hal.mv_abs({'x': -SPOT, 'y': -SPOT})
    
    if not dry:
        jf = open(fout, 'wb')
    
    cols = int(4.6 / SPOT)
    rows = int(3.8 / SPOT)
    SAMPLES = 4
    tpic = SAMPLES
    npic = cols * rows
    print 'Taking %dc x %dr => %d pics => ETA %s' % (cols, rows, npic, time_str(tpic * npic))
    tstart = time.time()
    
    posi = 0
    for row in xrange(rows):
        y = row * SPOT
        hal.mv_abs({'x': -SPOT, 'y': y})
        for col in xrange(cols):
            posi += 1
            x = col * SPOT
            hal.mv_abs({'x': x})
            if dry:
                continue
            print '%s taking %d / %d @ %dc, %dr' % (datetime.datetime.utcnow(), posi, npic, col, row)
            # Hit it a bunch of times in case we got unlucky
            for dumpi in xrange(SAMPLES):
                elt.fire()
                step_ms = 0.2 / SAMPLES * 1000
                sleep_sec = (dumpi * step_ms + random.randint(0, step_ms)) / 1000.
                time.sleep(sleep_sec)
                fw = prog.read()
                # Some crude monitoring
                # Top histogram counts would be better though
                print '  %d: %s' % (dumpi, binascii.hexlify(md5.new(fw).digest()))
                
                j = {'row': row, 'col': col, 'x': x, 'y': y, 'dumpi': dumpi, 'sleep': sleep_sec, 'bin': base64.b64encode(fw)}
                jf.write(json.dump(j))
                jf.flush()
                # Make sure fires start cleanly
                elt.idle.wait(1)
                
    print 'Ret home'
    hal.mv_abs({'x': 0, 'y': 0})
    print 'Movement done'
    tend = time.time()
    print 'Took %s' % time_str(tend - tstart)

def main():
    parser = argparse.ArgumentParser(description='Use ezlaze to fuzz dice')
    #parser.add_argument('--prog', default='/dev/ttyUSB0', help='minipro serial port')
    parser.add_argument('--prog-dev', default='pic16f84', help='microchip device')
    parser.add_argument('--cnc', default='mk-bs', help='LinuxCNC host')
    parser.add_argument('--dry', action='store_true', help='Dry run')
    parser.add_argument('fout', nargs='?', default='pwrmap.csv', help='Store data to')
    args = parser.parse_args()

    if os.path.exists(args.fout):
        raise Exception("Refusing to overwrite")
    
    hal = None
    elt = None
    try:
        print
        print 'Initializing LCNC'
        hal = lcnc_ar.LcncPyHalAr(host=args.cnc, dry=args.dry, log=None)

        print
        print 'Initializing programmer'
        prog = Minipro(device=args.prog_dev)

        # frickin laser
        print
        print 'Initializing laser'
        el = EzLaze(args.ezlaze)
        # Max speed
        '''
        Readout should complete within 0.601 sec (command line)
        At 5 hz need at least 4 pulses, lets do 5 (1.0 sec)
        '''
        el.pulse(hz=5)
        el.burst(n=5)
        elt = ELT(el)
        elt.start()

        print
        print 'Running'
        run(hal, prog, el, elt, fout=args.fout, dry=args.dry)
    finally:
        print 'Shutting down laser thread'
        if elt:
            elt.running = False
        
        print 'Shutting down hal'
        if hal:
            hal.ar_stop()

if __name__ == "__main__":
    main()
