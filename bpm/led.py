import binascii
import time
import usb1
import libusb1
import sys
import struct

from uvscada.wps7 import WPS7

from uvscada.bpm import startup
from uvscada.bpm.startup import led_mask
from uvscada.util import hexdump, add_bool_arg

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
    parser.add_argument('status', help='') 
    args = parser.parse_args()

    if args.cycle:
        startup.cycle()

    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext)
    dev.claimInterface(0)
    startup.replay(dev)

    startup.led_mask(dev, args.status)
