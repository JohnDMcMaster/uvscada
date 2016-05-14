# Product Code useful?

from uvscada.util import hexdump
from uvscada.ppro import opr_i2s, stat_i2so
from uvscada.ppro_util import load_logst

import argparse
import csv
import glob
import os
import time
import matplotlib.pyplot as plt
import shutil

def replaces(s, frm, to):
    sret = s.replace(frm, to)
    if sret == s:
        raise ValueError("%s => s/%s/%s/ => %s" % (s, frm, to, sret))
    return sret

def k2fn(k):
    return k.replace(' ', '_').replace('[', '').replace(']', '')

def plot_all(datast, dout):
    print 'Plotting...'
    for k in datast[0][1]:
        if k in ('fn', 'AC Check Flag', 'Application Version', 'crc', 'res1', 'res2', 'seq', 'seqn', 'Product Code'):
            continue
        if args.verbose:
            print k
        plt.clf()
        #plt.gca().get_yaxis().get_major_formatter().set_scientific(False)
        y = [x[1][k] for x in datast]
        # skip emptyish sets
        if not any(y[0:100]):
            continue
        try:
            plt.plot(y)
        except:
            print y
            raise
        plt.savefig('%s/%s.png' % (dout, k2fn(k)))

def plot_k(datast, fout, k):
    print 'Plotting %s...' % (fout,)
    if args.verbose:
        print k
    plt.clf()
    #plt.gca().get_yaxis().get_major_formatter().set_scientific(False)
    y = [x[1][k] for x in datast]
    try:
        plt.plot(y)
    except:
        print y
        raise
    plt.savefig(fout)

def process(fin, dout):
    print 'Processing %s => %s' % (fin, dout)
    #return
    
    if os.path.exists(dout):
        shutil.rmtree(dout)
    os.mkdir(dout)
    
    print 'Loading...'
    # FIXME: how to graph discretes?
    limit = None
    if args.limit:
        limit = lambda itr: itr < args.limit
    if args.range:
        lo, hi = args.range.split(':')
        lo = int(lo)
        hi = int(hi)
        limit = lambda itr: lo <= itr <= hi
    #limit = lambda itr: itr < 250
    datast = load_logst(fin, convert=False, limit=limit)
    print 'Loaded %d records' % len(datast)
    if not datast:
        raise ValueError("No points")
    
    # Plot
    if 1:
        plot_all(datast, dout)

    # Max mAh reported
    if 1:
        cap = max([x[1]['Output Capacity[1]'] for x in datast])
        print 'Capacity: %0.3f Ah' % (cap / 1000.,)

    # Last charge current
    if 1:
        ma = 0
        for _t, data in datast:
            if opr_i2s[data['Operation Mode[1]']] == 'CHARGE':
                ma = data['Output Current[1]']
        print 'Last charge mA: %d' % (ma,)
        # Seems to terminate at 0.5C
        orig_cap = ma * 2
        print 'Orig cap: %0.3f Ah' % (orig_cap / 1000.,)
    
    if 1:
        print 'Battery health: %02.1f%%' % (100.0 * cap / orig_cap,)

    # Times at mode/status changes
    if 1:
        print 'Checking times'
        lastt = None
        last = None
        starts = [0]
        for thisi, (thist, this) in enumerate(datast):
            if last and (this['Operation Mode[1]'] != last['Operation Mode[1]'] or this['Operation Status[1]'] != last['Operation Status[1]']):
                print '  % 6d @ %s: OM % -12s => % -12s, OS % -16s => % -16s @ %02d:%02d' % (
                        thisi, time.asctime(time.localtime(lastt)),
                        opr_i2s[last['Operation Mode[1]']], opr_i2s[this['Operation Mode[1]']],
                        stat_i2so[last['Operation Status[1]']], stat_i2so[this['Operation Status[1]']],
                        last['Minute[1]'], last['Second[1]'],
                        )
                starts.append(thisi)
            lastt = thist
            last = this
        
        print 'Subplots'
        os.mkdir(os.path.join(dout, 'CHARGE'))
        os.mkdir(os.path.join(dout, 'DISCHARGE'))
        for starti, start in enumerate(starts):
            if starti == len(starts) - 1:
                end = len(datast) - 1
            else:
                end = starts[starti + 1]
            subset = datast[start:end]
            # Grouping into dirs now
            modes = opr_i2s[subset[0][1]['Operation Mode[1]']]
            if modes == 'DISCHARGE':
                for k in (
                        'Average Voltage[1]',
                        'Output Voltage[1]',
                        'Output Current[1]'):
                    fout = '%s/DISCHARGE/%s_%02d.png' % (dout, k2fn(k), starti)
                    plot_k(subset, fout, k)
            elif modes == 'CHARGE':
                for k in (
                        'Output Current[1]',
                        'Output Voltage[1]'):
                    fout = '%s/CHARGE/%s_%02d.png' % (dout, k2fn(k), starti)
                    plot_k(subset, fout, k)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze data')
    parser.add_argument('--verbose', action='store_true', help='')
    parser.add_argument('--limit', default=None, type=int, help='')
    parser.add_argument('--range', default=None, type=int, help='')
    parser.add_argument('fin', help='Input file')
    parser.add_argument('dout', default=None, nargs='?', help='')
    args = parser.parse_args()
    
    fin = args.fin
    dout = args.dout
    
    if os.path.isdir(fin):
        for fin2 in sorted(glob.glob(fin + '/*.jl')):
            print
            dout = replaces(fin2, '.jl', '')
            process(fin2, dout)
    else:
        if dout is None:
            dout = replaces(fin, '.jl', '')
        process(fin, dout)

