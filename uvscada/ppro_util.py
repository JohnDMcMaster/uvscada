from uvscada.ppro import parse

import binascii
import time
import json

def load_logs(fn, progt=5.0, limit=None, convert=True):
    return [data for _t, data in gen_logs(fn, progt, limit, convert=convert)]

def load_logst(fn, progt=5.0, limit=None, convert=True):
    return list(gen_logs(fn, progt, limit, convert=convert))

def gen_logs(fn, progt=5.0, limit=None, verbose=False, convert=True):
    tprint = time.time()
    errs = 0
    for itr, l in enumerate(open(fn)):
        if limit and not limit(itr):
            continue
        
        if time.time() - tprint > progt:
            print '%d' % itr
            tprint = time.time()
        l = l.strip()
        if not l:
            continue
        try:
            j = json.loads(l)
        except:
            # Truncated record?
            if itr > 1:
                continue
            raise
        raw = binascii.unhexlify(j['data'])
        
        try:
            dec = parse(raw, convert=convert)
        except ValueError as e:
            # Lots of CRC errors
            # Ocassional sequence errors
            if verbose:
                print 'WARNING: %s bad packet: %s' % (itr, e)
            errs += 1
            continue
        except Exception:
            print itr
            raise
        
        yield (j['t'], dec)
    if verbose:
        print '%d packet errors' % errs
