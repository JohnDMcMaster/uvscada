from uvscada import zscnc
from uvscada.k2750 import K2750
from uvscada.zscnc import floats

import argparse
import json
import os
import time

def save(pins, fn, vendor='', product='', desc='', pack=''):
    j = {
        'vendor': vendor,
        'product': product,
        'desc': desc,
        'pack': pack,
        'scan': pins,
    }
    open(fn, 'w').write(json.dumps(j, indent=4, sort_keys=True))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Impedance scanner')
    parser.add_argument('--vendor', default='')
    parser.add_argument('--product', default='')
    parser.add_argument('--desc', default='')
    parser.add_argument('--pack', required=True, help='dip40, sdip64')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing file')
    parser.add_argument('jout', nargs='?', help='Store .json')
    args = parser.parse_args()

    if args.jout:
        if os.path.exists(args.jout) and not args.overwrite:
            raise Exception("Refusing to overwrite")

    k = K2750(port='/dev/ttyUSB0')
    z = zscnc.ZscnSer(device='/dev/ttyACM1')
    
    print 'Ready'
    zscnc.rst_verify(z, k)
    pins = zscnc.scan(z, k, pack=args.pack, verbose=True)
    if args.jout:
        save(pins, args.jout,
                vendor=args.vendor, product=args.product, desc=args.desc, pack=args.pack)
