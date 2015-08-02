#!/usr/bin/env python
'''
Planner test harness
'''

from uvscada import planner
from uvscada.cnc_hal import lcnc_ar
#from config import get_config
from uvscada.util import add_bool_arg
from uvscada.imager import MockImager

import argparse
import json
import os
import shutil

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Planner module command line')
    parser.add_argument('--host', default='mk-test', help='Host.  Activates remote mode')
    parser.add_argument('--port', default=22617, type=int, help='Host port')
    parser.add_argument('--overwrite', action='store_true')
    add_bool_arg(parser, '--dry', default=True)
    parser.add_argument('scan_json', nargs='?', default='scan.json', help='Scan parameters JSON')
    parser.add_argument('out', nargs='?', default='out/default', help='Output directory')
    args = parser.parse_args()

    if os.path.exists(args.out):
        if not args.overwrite:
            raise Exception("Refusing to overwrite")
        shutil.rmtree(args.out)
    os.mkdir(args.out)
    
    hal = lcnc_ar.LcncPyHalAr(host=args.host, local_ini='config/xray/rsh.ini', dry=args.dry)
    imager = MockImager()
    try:
        #config = get_config()
    
        # Sensor *roughly* 1 x 1.5"
        # 10 TPI stage
        # Run in inch mode long run but for now stage is set for mm
        # about 25 / 1850
        img_sz = (1850, 1344)
        p = planner.Planner(json.load(open(args.scan_json)), hal, imager=imager,
                    img_sz=img_sz, unit_per_pix=(1.5/img_sz[0]),
                    out_dir=args.out,
                    progress_cb=None,
                    dry=args.dry,
                    log=None, verbosity=2)
        p.run()
    finally:
        hal.ar_stop()
