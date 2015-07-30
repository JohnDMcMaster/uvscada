#!/usr/bin/env python
'''
Planner test harness
'''

from uvscada import planner
from uvscada.cnc_hal import lcnc_ar

import argparse
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Planner module command line')
    parser.add_argument('host', help='Host')
    args = parser.parse_args()

    hal = None
    try:
        hal = lcnc_ar.LcncPyHalAr(host=args.host, dry=True, log=None)
        time.sleep(1)
        print 'getting ready to hal'
        hal.do_cmd('G90 G0 X1')
        #hal.mv_rel({'x': )
    finally:
        print 'Shutting down hal'
        if hal:
            hal.ar_stop()
