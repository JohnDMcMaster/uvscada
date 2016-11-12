#!/usr/bin/env python

from uvscada import gp307
from uvscada import bnbser
from uvscada import statistics

import argparse
import time
import math

def fmts(f):
    return ' %2.1E' % f

def fmte(f):
    return ' %2.3E' % f

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='I leave all that I own to my cat guppy')
    parser.add_argument('--host', default=None, help='Serial port')
    parser.add_argument('--port', default=5000, help='Serial port')
    parser.add_argument('--diff', action='store_true', help='Print simple diff')
    parser.add_argument('--stat', action='store_true', help='log10 u + std over last min')
    # Every 5 seconds => stability over 1 minute
    parser.add_argument('--trend-n', type=int, default=12, help='Samples')
    parser.add_argument('--dev', default='/dev/ttyUSB0', help='Serial port')
    parser.add_argument('fn', nargs='?', help='Log file name')
    args = parser.parse_args()

    f = None
    if args.fn:
        print 'Logging to %s' % args.fn
        f = open(args.fn, 'w')
        f.write('t, IG, A, B\n')
        f.flush()
    
    if args.host:
        ser = bnbser.BNBRawT(host=args.host)
    gp = gp307.GP307(args.dev, ser=ser)
    
    lasts = []
    
    print 'Waiting for data...'
    while True:
        this = gp.get()
        ig, a, b = this
        
        igstr = gp307.fmt(ig)
        astr = gp307.fmt(a)
        bstr = gp307.fmt(b)
        
        t = time.time()
        print '%s: IG %s, A %s, B %s' % (time.strftime('%F %T'), igstr, astr, bstr)
        
        if args.diff and lasts:
            last = lasts[0]
            diff = [x - y for x, y in zip(this, last)]
            print '    D IG %s, A %s, B %s' % (fmts(diff[0]), fmts(diff[1]), fmts(diff[2]))
        
        if f:
            f.write('%s, %s, %s, %s\n' % (t, igstr, astr, bstr))
            f.flush()
    
        lasts = [this] + lasts[0:args.trend_n - 1]

        if args.stat and len(lasts) > 1:
            s = ''
            for chan in zip(*lasts):
                chanl = [math.log(x, 10) for x in chan]
                sd = statistics.stdev(chanl)
                u = statistics.mean(chanl)
                s += '(%s, %s) ' % (fmte(u), fmte(sd))
            print '    % 3u %s' % (len(lasts), s)
