#!/usr/bin/env python

from uvscada.cnc_hal import lcnc_ar
from uvscada.ezlaze import EzLaze
from uvscada.k2750 import K2750

import argparse
import time
import sys
#from PIL import Image
import csv
import datetime

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Use ezlaze with LinuxCNC to carve a bitmap')
    parser.add_argument('--laser', default='/dev/ttyUSB1', help='ezlaze serial port')
    parser.add_argument('--x', type=int, default=None, help='XY vlaue')
    parser.add_argument('--y', type=int, default=None, help='XY vlaue')
    parser.add_argument('--xy', type=int, default=None, help='XY vlaue')
    parser.add_argument('--square', type=int, default=None, help='Calibrated square value')
    #parser.add_argument('fout', help='Store data to')
    args = parser.parse_args()


    print args.x, args.y
    hal = None
    # frickin laser
    print
    print 'Initializing laser'
    el = EzLaze(args.laser)
    if args.square is not None:
        el.shut_square(args.square)
    else:
        el.shut(xy=args.xy, x=args.x, y=args.y)

