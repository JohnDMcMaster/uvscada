#!/usr/bin/env python
import matplotlib.pyplot as plt

import argparse        
import csv
import os
import sys

def hms(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Use LeCroy 2228A test mode to collect calibration data')
    parser.add_argument('--force', action='store_true', help="Overwrite files if they already exist")
    parser.add_argument('fn', help='File name in')
    parser.add_argument('dir', nargs='?', default=None, help='Output dir')
    args = parser.parse_args()

    data = []
    f = open(args.fn)
    
    if args.dir is None:
        args.dir = os.path.splitext(args.fn)[0]
    
    print 'Saving to %s' % (args.dir,)
    
    if os.path.exists(args.dir):
        if not args.force:
            raise Exception("Refusing to overwrite existing data")
    else:
        os.mkdir(args.dir)
    
    tm = 9.6
    
    hdr = f.readline()

    csvr = csv.reader(f, delimiter=',')
    
    ts = []
    vs = []
    off = None
    
    # old without t
    # slot,iter,ch0,ch1,ch2,ch3,ch4,ch5,ch6,ch7
    if len(hdr) == 10:
        for row in csvr:
            ts.append(int(row[1]) * tm)
            v = [int(v) for v in row[2:]]
            if off is None:
                off = v
            vs.append([vi - offi for vi, offi in zip(v, off)])
    # old without t
    # slot,iter,t,ch0,ch1,ch2,ch3,ch4,ch5,ch6,ch7
    else:
        csvr = csv.reader(f, delimiter=',')
        
        ts = []
        vs = []
        off = None
        for row in csvr:
            ts.append(float(row[2]))
            v = [int(v) for v in row[3:]]
            if off is None:
                off = v
            vs.append([vi - offi for vi, offi in zip(v, off)])
    total_t = ts[-1] - ts[0]
    
    vs = zip(*vs)
    
    # Plot everything together
    if 1:
        for 
            colors = 'rgbybmcr'
            pargs = []
            for i in xrange(8):
                pargs.extend([ts, vs[i], colors[i]])
            plt.plot(*pargs)
            
            #plt.semilogy([small for (t, small, large) in data])
            #plt.plotting(semilogy)
            
            plt.title('All drift over %s' % hms(total_t))
            plt.xlabel('Sample #')
            plt.ylabel('ADC delta')
            #plt.show()
            plt.savefig(os.path.join(args.dir, 'all.png'))

    # Individual
    if 1:
        for i in xrange(8):
            plt.clf()
            plt.plot(ts, vs[i], 'b-')
            
            plt.title('CH%d over %s' % (i, hms(total_t)))
            plt.xlabel('Sample #')
            plt.ylabel('ADC delta')
            #plt.show()
            plt.savefig(os.path.join(args.dir, 'ch%d.png' % i))

