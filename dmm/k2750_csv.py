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
    parser.add_argument('--dmm', default='/dev/ttyUSB0', help='K2750 serial port')
    parser.add_argument('fout', help='Store data to')
    args = parser.parse_args()

    print
    print 'Initializing DMM'
    dmm = K2750(args.dmm)

    cwf = open(args.fout, 'wb')
    cw = csv.writer(cwf)
    cw.writerow(["t", "tstr", "curr"])

    while True:
        curr = dmm.curr_dc()
        r = ['%0.3f' % time.time(), datetime.datetime.utcnow().isoformat(), curr]
        print r
        cw.writerow(r)
        cwf.flush()

