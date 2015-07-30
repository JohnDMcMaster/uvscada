#!/usr/bin/env python
'''
Planner test harness
'''

from uvscada import planner
from uvscada.cnc_hal import lcnc_ar

import argparse        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Planner module command line')
    parser.add_argument('host', help='Host')
    args = parser.parse_args()

    hal = lcnc_ar.LcncPyHalAr(host=args.host, dry=True, log=None)
    hal.do_cmd('G90 G0 X1')
    #hal.mv_rel({'x': )
