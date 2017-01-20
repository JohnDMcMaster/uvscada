import argparse
import json
import os
import time
import math

'''
def save(pins, fn, vendor='', product='', desc='', pack=''):
    j = {
        'vendor': vendor,
        'product': product,
        'desc': desc,
        'pack': pack,
        'scan': pins,
    }
    open(fn, 'w').write(json.dumps(j, indent=4, sort_keys=True))
'''

def normalize(j):
    vals = j['scan']
    #average = sum(vals.values()) / len(vals)
    vals_ref = {}
    for kval, val in vals.iteritems():
        # Ground is about 1.5
        if val > 5.0 and not math.isinf(val):
            vals_ref[int(kval)] = val
    
    #val_ref = min(vals_ngnd.values())
    val_ref = sum(vals_ref.values()) / len(vals_ref)
    #print 'ref: %f' % val_ref
    
    return dict([(int(k), math.log(x / val_ref, 10)) for k, x in vals.iteritems()])

def diff(l, r):
    # inf - inf => nan
    #return [a - b for a, b in zip(l, r)]
    ret = {}
    for k in l:
        a = l[k]
        b = r[k]
        if math.isinf(a) and math.isinf(b):
            ret[k] = 0
        else:
            ret[k] = a - b
    return ret

PINS = lambda: xrange(1, 65, 1)

def score(fnl, fnr, verbose=False):
    l = json.load(open(fnl, 'r'))
    r = json.load(open(fnr, 'r'))
    ln = normalize(l)
    rn = normalize(r)
    #print 'ln', ln
    #print 'rn', rn
    dn = diff(ln, rn)
    #print 'dn', dn
    #import sys
    #sys.exit(0)
    
    def floats(f):
        if f is float('inf') or f is float('-inf') or f is float('nan'):
            return '%f' % f
        return '%1.3f' % f
    
    if verbose:
        #print dn
        for pin in PINS():
            print '% 3u: %s' % (pin, floats(dn[pin]))
    
    # rms
    # How to weight open vs intact?
    # limit diff to something like order 6
    # (ie 1 ohm vs 10M)
    score = 0
    #score_vals = [x in dn[pin].values() if (not math.isinf(x) and not math.isinf(x))]
    score_vals = []
    for x in dn.values():
        if math.isinf(x) or math.isinf(x):
            x = 6.0
        score_vals.append(min(abs(x), 6.0))
    score_avg = sum(score_vals) / len(score_vals)
    score_rms = math.sqrt(sum([(x - score_avg)**2 for x in score_vals]))
    if verbose:
        print 'Score: %0.3f' % score_rms
    return score_rms

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Impedance scanner')
    parser.add_argument('l', help='')
    parser.add_argument('r', help='')
    args = parser.parse_args()

    score(args.l, args.r, verbose=True)
