#!/usr/bin/env python

'''
Scans across a die
Assumes laser pointer pointed at die not under active control
Also works for microscope shining (possibly with diaghragm mask)
Finds areas that changes chip operation
Dumbed down version of "ezfuzz"
'''

from uvscada.cnc_hal import lcnc_ar
from uvscada.benchmark import time_str
import bpmicro.startup
import bpmicro.pic16f84.read

import argparse
import time
import datetime
import os
import json
import base64
import md5
import binascii

def do_run(hal, bp, width, height, dry, fout, samples=1):
    # Use focus to adjust
    SPOT = 0.05

    hal.mv_abs({'x': -1, 'y': -1})

    jf = fout

    xstep = width / SPOT / 2.0
    ystep = height / SPOT / 2.0
    cols = int(xstep)
    rows = int(ystep)
    tstart = time.time()

    def read_fw():
        # There are some occasional glitches even with a good device
        # Try a few times
        # Although might get overcurrents or stuff like that...will have to figure that out
        for atry in xrange(3):
            return bpmicro.pic16f84.read.replay(bp.dev, cont=True)
        else:
            return None

    print 'Dummy firmware read'
    trstart = time.time()
    _buff = read_fw()
    trend = time.time()
    tread = trend - trstart
    print 'Read time: %0.1f' % tread

    # FIXME: estimate
    tmove = 0.1
    tsample = tread + tmove
    print 'Sample time: %0.1f' % tsample
    nsamples = cols * rows
    print 'Taking %dc x %dr x %ds => %d net samples => ETA %s' % (cols, rows, samples, nsamples, time_str(tsample * nsamples))

    posi = 0
    for row in xrange(rows):
        y = row * SPOT
        hal.mv_abs({'x': -1, 'y': y})
        for col in xrange(cols):
            posi += 1
            x = col * SPOT
            hal.mv_abs({'x': x})
            print '%s taking %d / %d @ %dc, %dr' % (datetime.datetime.utcnow(), posi, nsamples, col, row)
            # Hit it a bunch of times in case we got unlucky
            for dumpi in xrange(samples):
                if dry:
                    fw = ''
                else:
                    fw = read_fw()
                # Some crude monitoring
                # Top histogram counts would be better though
                print '  %d: %s' % (dumpi, binascii.hexlify(md5.new(fw).digest()))

                j = {'row': row, 'col': col, 'x': x, 'y': y, 'dumpi': dumpi, 'bin': base64.b64encode(fw)}
                if jf:
                    jf.write(json.dumps(j) + '\n')
                    jf.flush()

    print 'Ret home'
    hal.mv_abs({'x': 0, 'y': 0})
    print 'Movement done'
    tend = time.time()
    print 'Took %s' % time_str(tend - tstart)

def run(cnc_host, dry, width, height, fnout, samples=1, force=False):
    hal = None

    fout = None
    if not force and os.path.exists(fnout):
        raise Exception("Refusing to overwrite")
    if not dry:
        fout = open(fnout, 'w')

    try:
        print
        print 'Initializing LCNC'
        hal = lcnc_ar.LcncPyHalAr(host=cnc_host, dry=dry, log=None)

        print
        print 'Initializing programmer'
        bp = bpmicro.startup.get()

        print
        print 'Running'
        do_run(hal=hal, bp=bp, width=width, height=height, dry=dry, fout=fout, samples=samples)
    finally:
        print 'Shutting down hal'
        if hal:
            hal.ar_stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Use ezlaze to fuzz dice')
    parser.add_argument('--cnc', default='mk', help='LinuxCNC host')
    parser.add_argument('--dry', action='store_true', help='Dry run')
    parser.add_argument('--force', action='store_true', help='Overwrite file')
    parser.add_argument('--samples', type=int, default=1, help='Number of times to read each location')
    parser.add_argument('--width', type=float, default=1, help='X width (ie in mm)')
    parser.add_argument('--height', type=float, default=1, help='y height (ie in mm)')
    parser.add_argument('fout', nargs='?', default='scan.jl', help='Store data to, 1 JSON per line')
    args = parser.parse_args()

    run(cnc_host=args.cnc, dry=args.dry, width=args.width, height=args.height, fnout=args.fout, samples=args.samples, force=args.force)
