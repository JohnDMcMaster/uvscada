from uvscada.util import add_bool_arg

import argparse
import json
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

def floats(f):
    if f is float('inf') or f is float('-inf') or f is float('nan'):
        return '%f' % f
    return '%1.3f' % f

def floats6(f):
    if f is float('inf') or f is float('-inf') or f is float('nan'):
        return '%f' % f
    return '%1.6f' % f

def normalize(j):
    vals = j['scan']
    #average = sum(vals.values()) / len(vals)
    vals_ref = {}
    for kval, val in vals.iteritems():
        # Ground is about 1.5
        if val > 5.0 and not math.isinf(val):
            vals_ref[int(kval)] = val
    
    # Is it better to log before or after average?
    # Maybe better to make single outlier less devestating
    # Take log first
    if 0:
        #val_ref = min(vals_ngnd.values())
        val_ref = sum(vals_ref.values()) / len(vals_ref)
        return dict([(int(k), math.log(x / val_ref, 10)) for k, x in vals.iteritems()])
        
    if 1:
        valsl = dict([(int(k), math.log(x, 10)) for k, x in vals.iteritems()])
        vals_refl = dict([(int(k), math.log(x, 10)) for k, x in vals_ref.iteritems()])
        val_ref = sum(vals_refl.values()) / len(valsl)
        return dict([(int(k), math.log(x / val_ref, 10)) for k, x in valsl.iteritems()])

def normalize_lin(j):
    vals = j['scan']
    return dict([(int(k), x) for k, x in vals.iteritems()])

def diff(l, r):
    # inf - inf => nan
    #return [a - b for a, b in zip(l, r)]
    ret = {}
    for k in l:
        ret[k] = diff_val(l[k], r[k])
    return ret

def diff_val(l, r):
    if math.isinf(l) and math.isinf(r):
        return 0
    else:
        return l - r

PINS = lambda: xrange(1, 65, 1)

def do_score_rms(ln, rn, inf=True, verbose=False, sortv=True):
    # rms
    # How to weight open vs intact?
    # limit diff to something like order 6
    # (ie 1 ohm vs 10M)
    if ln.keys() != rn.keys():
        raise ValueError("Can't compare: l: %d, r %d entries" % (len(ln), len(rn)))
    #score_vals = [x in dn[pin].values() if (not math.isinf(x) and not math.isinf(x))]
    score_vals = []
    score_valsm = {}
    for k in ln.keys():
        # Note matching infs cancel out
        delta = diff_val(ln[k], rn[k])
        if math.isinf(delta):
            # If allowed, then incur a heavy penalty
            if inf:
                delta = 6.0
            # Otherwise throw it out
            else:
                # Unfairly lowering score on infs when excluded
                continue
                #x = 0.0
        # Curb near inf values
        delta = min(abs(delta), 6.0)
        score_this = delta * delta
        score_vals.append(score_this)
        score_valsm[k] = score_this
    if verbose:
        sorts = sorted(list(score_valsm.iteritems()), key=lambda x: x[1])
        for k, v in sorts:
            print '% 3u: %s' % (k, floats6(v))

    if verbose and not inf:
        print 'Threw out %d pins' % (len(ln) - len(score_vals),)
    return (sum(score_vals) / len(score_vals)) ** 0.5

def score(fnl, fnr, inf=True, verbose=False, cmp='log'):
    l = json.load(open(fnl, 'r'))
    r = json.load(open(fnr, 'r'))
    
    if cmp == 'log':
        ln = normalize(l)
        rn = normalize(r)
    elif cmp == 'lin' or cmp == 'abs':
        ln = normalize_lin(l)
        rn = normalize_lin(r)
    else:
        raise ValueError(cmp)
    
    #print 'ln', ln
    #print 'rn', rn
    #print 'dn', dn
    #import sys
    #sys.exit(0)
    
    if cmp == 'abs':
        dn = diff(ln, rn)
        # FIXME: hack
        for pin in PINS():
            print '% 3u: %s' % (pin, floats(dn[pin]))
        return 0
    else:
        score_rms = do_score_rms(ln, rn, inf=inf, verbose=verbose)
        
        # Prefer integers
        #ret = score_rms * 100
        ret = score_rms
        if verbose:
            print 'Score: %0.3f' % ret
        return ret

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Impedance scanner')
    add_bool_arg(parser, '--verbose', default=True, help='')
    add_bool_arg(parser, '--lin', default=False, help='')
    add_bool_arg(parser, '--inf', default=True, help='')
    parser.add_argument('--cmp', default='log', help='')
    parser.add_argument('l', help='')
    parser.add_argument('r', help='')
    args = parser.parse_args()

    ret = score(args.l, args.r, inf=args.inf, verbose=args.verbose, cmp=args.cmp)
    if not args.verbose:
        print 'Score: %0.3f' % ret
