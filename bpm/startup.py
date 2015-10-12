from uvscada.util import add_bool_arg
from uvscada.bpm import startup
from uvscada.wps7 import WPS7

import usb1
import time
import sys

def open_dev(usbcontext=None):
    if usbcontext is None:
        usbcontext = usb1.USBContext()
    
    print 'Scanning for devices...'
    for udev in usbcontext.getDeviceList(skip_on_error=True):
        vid = udev.getVendorID()
        pid = udev.getProductID()
        if (vid, pid) == (0x14b9, 0x0001):
            print
            print
            print 'Found device'
            print 'Bus %03i Device %03i: ID %04x:%04x' % (
                udev.getBusNumber(),
                udev.getDeviceAddress(),
                vid,
                pid)
            return udev.open()
    raise Exception("Failed to find a device")

if __name__ == "__main__":
    import argparse 
    
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    add_bool_arg(parser, '--cycle', default=False, help='') 
    add_bool_arg(parser, '--loop', default=False, help='') 
    args = parser.parse_args()

    if args.cycle:
        print 'Cycling'
        wps = WPS7(host='raijin')
        wps.cycle([1, 2], t=2.0)
        # 1 second too short
        time.sleep(3)
        print 'Cycled'

    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext)
    dev.claimInterface(0)
    
    if args.loop:
        i = 0
        good = 0
        bad = 0
        while True:
            print i, good, bad
            try:
                startup.replay(dev)
                good += 1
            except Exception:
                print 'Error'
                bad += 1
                raise
            i += 1

    #dev.resetDevice()
    startup.replay(dev)
    startup.sm_info(dev)

    # Done!

