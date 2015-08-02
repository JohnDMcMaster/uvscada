# https://github.com/vpelletier/python-libusb1
# Python-ish (classes, exceptions, ...) wrapper around libusb1.py . See docstrings (pydoc recommended) for usage.
import usb1
# Bare ctype wrapper, inspired from library C header file.
import libusb1
import sys
import gxs700_fw
import gxs700

pidvid2name = {
        #(0x5328, 0x2009): 'Dexis Platinum (pre-enumeration)'
        # note: load_firmware.py loads the gendex firmware
        (0x5328, 0x2030): 'Gendex GXS700 (post enumeration)',
        # some sort of auto-load mode I activated by accident
        # no fxload required
        #(0x5328, 0x2010): 'temp',
        #(0x5328, 0x202F): 'Gendex GXS700 (pre-enumeration)'
        }

def check_device(usbcontext=None):
    if usbcontext is None:
        usbcontext = usb1.USBContext()
    
    for udev in usbcontext.getDeviceList(skip_on_error=True):
        vid = udev.getVendorID()
        pid = udev.getProductID()
        if (vid, pid) in pidvid2name.keys():
            print
            print
            print 'Found device'
            print 'Bus %03i Device %03i: ID %04x:%04x' % (
                udev.getBusNumber(),
                udev.getDeviceAddress(),
                vid,
                pid)
            return udev
    return None

def open_dev(usbcontext=None):
    '''
    Return a device with the firmware loaded
    '''
    
    if usbcontext is None:
        usbcontext = usb1.USBContext()
    
    print 'Checking if firmware load is needed'
    if gxs700_fw.load_all(wait=True):
        pass
    else:
        print 'Firmware load not needed'
    
    print 'Scanning for devices...'
    udev = check_device(usbcontext)
    if udev is None:
        raise Exception("Failed to find a device")

    dev = udev.open()
    return dev

def ez_open(verbose=False):
    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext)
    return gxs700.GXS700(usbcontext, dev, verbose=verbose)
