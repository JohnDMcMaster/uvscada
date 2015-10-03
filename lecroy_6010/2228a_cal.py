#!/usr/bin/env python
'''
2228A 11 bit TDC

Test Functions: An internal start/stop is generated with approximately 80% of full scale time in response to an F(25) command. 
On-line testing and calibrations can be done with common start and common stop above.

Three switch selectable full scale time ranges
-100 ns (50 ps)
-200 ns (100 ps)
-500 ns (250 ps)

100 us conversion time

Test configuration units
-Slot 9: broken screw
-Slot 11: working screw

11 bit adc => 2048 values
Supposed to be around 75%
hex(2048 * 0.75) => 0x600

Slot 9
    CH0: 0x000632
    CH1: 0x000644
    CH2: 0x000632
    CH3: 0x000358
    CH4: 0x000637
    CH5: 0x000525
    CH6: 0x00062A
    CH7: 0x00063A

Slot 11
    CH0: 0x000699
    CH1: 0x000691
    CH2: 0x00069D
    CH3: 0x000353
    CH4: 0x000696
    CH5: 0x00069F
    CH6: 0x00068C
    CH7: 0x000686

TODO:
Really slow...why?
Poor error checking
'''

from uvscada.l6010 import L6010

import argparse        
import binascii
import csv
import sys
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Use LeCroy 2228A test mode to collect calibration data')
    parser.add_argument('--port', default='/dev/ttyUSB0', help='GPIB serial port')
    parser.add_argument('--csv', default=None, help='csv output file')
    parser.add_argument('--cycles', default=None, type=int, help='How many iterations to do')
    parser.add_argument('n', nargs='+', type=int, help='Slot numbers')
    args = parser.parse_args()

    if args.cycles is None:
        args.cycles = 999999999
    
    # Init time: 0.505
    # this can't be helped unless I disable hte clear
    tstart = time.time()
    l = L6010()
    print 'Init time: %0.3f' % (time.time() - tstart,)
    gpib = l.gpib

    if args.csv:
        csvf = open(args.csv, 'wb')
        csvw = csv.writer(csvf, delimiter=',')
        csvw.writerow(['slot', 'iter', 't'] + ['ch%d' % i for i in xrange(8)])
    else:
        csvw = None

    for n in args.n:
        # N time: 0.016
        #tstart = time.time()
        l.n = n
        #print 'N time: %0.3f' % (time.time() - tstart,)
        
        # Initialize
        '''
        pg 17
        IMPORTANT: The unit should always be initialized with an F(24)
        (Disable LAM) or an F(26) (Enable LAM) and an F(10) (Clear LAM)
        whenever the crate power is turned on.
        '''
        l.cami(n=n, f=24, a=0)
        l.cami(n=n, f=10, a=0)
    
    for cycle in xrange(args.cycles):
        for n in args.n:
            # Trigger test generator
            l.cami(n=n, f=25, a=0)
            
            t = time.time()
            print 'N%d cycle %d @ %0.1f' % (n, cycle, t)
            # Read channels, clearning on last read
            vs = []
            for ch in xrange(8):
                v = l.cami(n=n, f=2, a=ch)
                vs.append(v)
                print '  CH%d: 0x%06X' % (ch, v)
            if csvw:
                csvw.writerow([n, cycle, '%0.1f' % t] + vs)
                csvf.flush()

