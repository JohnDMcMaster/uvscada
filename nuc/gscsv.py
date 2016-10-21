#!/usr/bin/env python

import time
import argparse
import json

from uvscada.nuc import pulser
from uvscada.nuc import alsa_util

def cap(jf):
    def jput(j):
        jf.write(json.dumps(j, sort_keys=True) + '\n')

    print 'Configuring ALSA'
    asrc = alsa_util.ALSASrc()
    
    print 'looping'
    # 400 w/o, 7300 w/ Cs-137 (1 uCi)
    psr = pulser.PHA(phi=200, plo=50)
    agen = asrc.gen()
    stat = pulser.PulserStat(tprint=args.tprint)
    
    t0 = time.time()
    while True:
        sample = agen.next()
        pulse = psr.next(sample)
        stat.next(sample, pulse)
        
        if pulse:
            jput({'t': time.time(), 'n': stat.pulses, 'v': pulse})
            if args.verbose:
                print '% 6d: % 5.1f' % (stat.pulses, pulse)
        
        if args.time and time.time() - t0 > args.time:
            print 'Break on time'
            break
        if args.number and stat.pulses > args.number:
            print 'Break on pulses'
            break

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('--tprint', '-p', type=int, default=3, help='Print interval')
    parser.add_argument('--time', '-t', type=int, default=0, help='Help')
    parser.add_argument('--number', '-n', type=int, default=0, help='Help')
    parser.add_argument('fn', nargs='?', default='out.jl', help='csv out')
    args = parser.parse_args()

    cap(open(args.fn, 'w'))


