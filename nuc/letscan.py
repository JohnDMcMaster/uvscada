#!/usr/bin/env python

'''
Use a Sherline 2000 CNC Z axis to scan a LND alpha window GM tube
Use Gamma Spectacular to acquire data through sound port
Allows gathering CPM vs distnace which is basically LET curve

Currently only doing pulses, but in the future should do spectra
'''
from uvscada.cnc_hal import lcnc_ar

import sys
import time
import csv
import argparse

PRINT_QUICK = 10
STEP_T = 120.0
ZMAX = 5.0

from uvscada.nuc import pulser
from uvscada.nuc import alsa_util

def cap(hal, csv_fn):
    print 'Configuring ALSA'
    asrc = alsa_util.ALSASrc()
    
    print 'looping'
    samplen = 0
    tlast = time.time()
    psr = pulser.Pulser()
    agen = asrc.gen()
    # Count pulses at each step
    stat_step = pulser.PulserStat()
    stat_step.tprint = 0
    # Periodically print info during each step
    stat_mon = psr.PulserStat()

    def mvz(z):
        hal.mv_abs({'z': z}, limit=False)

    def gen_exp():
        yield 0.000
        
        itr = 0
        zil = 0
        while True:
            z = 0.001 * (1.2 ** itr)
            if z > ZMAX:
                break
            
            # skip if less than backlash
            if z < 0.002:
                itr += 1
                continue
            
            '''
            zi = int(z * 1000)
            if zi == zil:
                itr += 1
                continue
            '''
            
            yield z
            itr += 1
    
    def gen_lin():
        return [x / 1000. for x in xrange(0, int(ZMAX * 1000), int(0.2 * 1000))]

    fd = open(csv_fn, 'w')
    cw = csv.writer(fd)
    cw.writerow(['t', 'dt', 'z', 'n', 'pulses'])
    stepn = 0

    #for z in gen_exp():
    for z in gen_lin():
        print
        stepn += 1
        print 'Pos %0.4f, n %d' % (z, stepn)
        # Move into position
        mvz(z)
        
        # Now collect pulses for a minute
        psr.last()
        stat_step.rstl()
        stat_mon.rstl()
        
        while True:
            sample = agen.next()
            pulse = psr.next(sample)
            stat_step.next(sample, pulse)
            stat_mon.next(sample, pulse)

            t1 = time.time()
            dt = t1 - stat_step.tlast
            if dt > STEP_T:
                row = ['%0.1f' % stat_step.tlast, '%0.1f' % dt , '%0.4f' % z, stepn, stat_step.pulsesl]
                cw.writerow(row)
                fd.flush()
                print row
                break

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('fn', nargs='?', default='out.csv', help='csv out')
    args = parser.parse_args()

    hal = None
    try:
        print 'Initializing HAL'
        hal = lcnc_ar.LcncPyHalAr(host='cnc', username='mcmaster', dry=False, log=None)
        #hal._cmd('G91 G1 Z0.01 F1')
        cap(hal, args.fn)
        #print hal.limit()
        #hal.mv_abs({'z': 0}, limit=False)
    finally:
        print 'Shutting down hal'
        if hal:
            hal.ar_stop()
