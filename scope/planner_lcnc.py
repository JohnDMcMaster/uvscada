#!/usr/bin/env python
'''
Planner test harness
'''

from uvscada import planner
from uvscada import planner_hal
from uvscada.lcnc.client import LCNCRPC
from uvscada.imager import MockImager

import argparse        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Planner module command line')
    # ssh -L 22617:localhost:22617 mk-xray
    parser.add_argument('--host', help='Host.  Activates remote mode')
    parser.add_argument('--port', default=22617, type=int, help='Host port')
    parser.add_argument('scan_json', nargs='?', default='scan.json', help='Scan parameters JSON')
    parser.add_argument('out', nargs='?', default='out', help='Output directory')
    args = parser.parse_args()

    if args.host:
        linuxcnc = LCNCRPC(args.host, args.port)
    else:
        import linuxcnc
    
    imager = MockImager()

    hal = planner_hal.LcncPyHal(dry=True, log=None, imager=imager, linuxcnc=linuxcnc)
    # 20x objective
    p = planner.Planner(args.scan_json, hal, img_sz=(544, 400), out_dir=args.out,
                progress_cb=None,
                overwrite=True, dry=True,
                img_scalar=1,
                log=None, verbosity=2)
    p.run()
