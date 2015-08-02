#!/usr/bin/env python
'''
Planner test harness
'''

from uvscada import planner
from uvscada.cnc_hal import lcnc_ar
#from config import get_config
from uvscada.util import add_bool_arg
from uvscada.imager import MockImager
from uvscada.imager import Imager
from uvscada import gxs700

import argparse
import json
import os
import shutil
import threading
import pycurl
import time

SW_HV = 1
SW_FIL = 2

def switch(n, on):
    state = 'ON' if on else 'OFF'
    c = pycurl.Curl()
    c.setopt(c.URL, 'http://energon/outlet?%d=%s' % (n, state))
    c.setopt(c.WRITEDATA, open('/dev/null', 'w'))
    c.setopt(pycurl.USERPWD, '%s:%s' % (os.getenv('WPS7_USER', 'admin'), os.getenv('WPS7_PASS', '')))
    c.perform()
    c.close()

class XrayImager(Imager):
    def __init__(self, dry):
        Imager.__init__(self)
        self.dry = dry
        # About 3 seconds exposure required for range I'm using
        self.shot_on = 3
        # 10% duty cycle
        self.shot_off = 27

        print 'Warming filament...'
        # Should dry do this?
        # Tests WPS connectivity and shouldn't fire the x-ray
        switch(SW_FIL, 1)
        time.sleep(5)
        self.fire_last = 0
        
        self.gxs.wait_trig_cb = self.fire

    def fire(self):
        print 'Checking head temp'
        wait = self.shot_wait - time.time() - self.fire_last
        if wait > 0:
            print 'Waiting %0.1f sec for head to cool...' % wait
            if self.dry:
                print 'DRY: skip wait'
            else:
                time.sleep(wait)
        print 'Head ready'
        
        try:
            if self.dry:
                print 'DRY: not firing'
            else:
                print 'X-RAY: BEAM ON %0.1f sec' % self.shot_on
                switch(SW_HV, 1)
                time.sleep(self.shot_on)
            self.fire_last = time.time()
        finally:
            print 'X-RAY: BEAM OFF'
            switch(SW_HV, 0)

    def get(self):
        img_bin = self.gxs.cap_bin()
        print 'x-ray: decoding'
        img_dec = gxs700.GXS700.decode(img_bin)
        # Cheat a little
        img_dec.raw = img_bin
        return img_dec

def take_picture(planner, fn_base):
    planner.hal.settle()
    if not planner.dry:
        img_dec = planner.imager.get()
        open(fn_base + '.bin', 'w').write(img_dec.raw)
        img_dec.save(fn_base + '.tif')
    planner.all_imgs += 1

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
        planner = planner.Planner(json.load(open(args.scan_json)), hal, imager=imager,
                    img_sz=img_sz, unit_per_pix=(1.5/img_sz[0]),
                    out_dir=args.out,
                    progress_cb=None,
                    dry=args.dry,
                    log=None, verbosity=2)
        planner.take_picture = take_picture
        planner.run()
    finally:
        hal.ar_stop()
