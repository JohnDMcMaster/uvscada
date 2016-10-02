#!/usr/bin/env python

from uvscada import gp307
import time
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='I leave all that I own to my cat guppy')
    parser.add_argument('--dev', default='/dev/ttyUSB0', help='Serial port')
    parser.add_argument('fn', nargs='?', help='Log file name')
    args = parser.parse_args()

    f = None
    if args.fn:
        print 'Logging to %s' % args.fn
        f = open(args.fn, 'w')
        f.write('t, IG, A, B\n')
        f.flush()
    
    gp = gp307.GP307(args.dev)
    
    print 'Waiting for data...'
    while True:
        ig, a, b = gp.get()
        
        igstr = gp307.fmt(ig)
        astr = gp307.fmt(a)
        bstr = gp307.fmt(b)
        
        t = time.time()
        print '%s: IG %s, A %s, B %s' % (time.strftime('%F %T'), igstr, astr, bstr)
        
        if f:
            f.write('%s, %s, %s, %s\n' % (t, igstr, astr, bstr))
            f.flush()
    
