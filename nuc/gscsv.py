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
    psr = pulser.PHA()
    agen = asrc.gen()
    stat = pulser.PulserStat(tprint=args.tprint)
    
    while True:
        sample = agen.next()
        pulse = psr.next(sample)
        stat.next(sample, pulse)
        
        if pulse:
            jput({'t': time.time(), 'n': stat.pulses, 'v': pulse})
            print '% 6d: % 5.1f' % (stat.pulses, pulse)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('--tprint', '-t', type=int, default=5, help='Print interval')
    parser.add_argument('fn', nargs='?', default='out.jl', help='csv out')
    args = parser.parse_args()

    cap(open(args.fn, 'w'))
