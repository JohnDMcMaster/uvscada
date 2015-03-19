# https://github.com/vpelletier/python-libusb1
# Python-ish (classes, exceptions, ...) wrapper around libusb1.py . See docstrings (pydoc recommended) for usage.
import usb1
# Bare ctype wrapper, inspired from library C header file.
import libusb1
import binascii

def nulls(s, offset):
    return s[offset:s.find('\x00', offset)]

def dump_eeprom(dev):
    '''
    Example contents:
    0000   aa 55 aa 55 42 05 00 00  3a 07 00 00 32 31 30 33  .U.UB...:...2103
    0010   32 33 31 36 36 33 00 00  00 00 00 00 00 00 00 00  231663..........
    0020   00 00 00 00 00 00 00 00  00 00 00 00 46 61 69 72  ............Fair
    0030   63 68 69 6c 64 20 49 6d  61 67 69 6e 67 00 ff ff  child Imaging...
    0040   ff ff ff ff ff ff ff ff  ff ff ff ff 53 4c 32 30  ............SL20
    0050   38 30 33 30 32 2d 47 32  00 ff ff ff ff ff ff ff  80302-G2........
    0060   ff ff ff ff ff ff ff ff  ff ff ff ff 00 ff ff ff  ................
    0070   ff ff ff ff ff ff ff ff  ff ff ff ff ff ff ff ff  ................
    0080   ff ff ff ff ff ff ff ff  ff ff ff ff 52 65 76 20  ............Rev 
    0090   4e 52 00 ff ff ff ff ff  ff ff ff ff ff ff ff ff  NR..............
    00a0   ff ff ff ff ff ff ff ff  ff ff ff ff 37 2f 31 37  ............7/17
    00b0   2f 32 30 31 32 00 00 ff  ff ff ff ff ff ff ff ff  /2012...........
    00c0   ff ff ff ff ff ff ff ff  ff ff ff ff 37 2f 31 37  ............7/17
    00d0   2f 32 30 31 32 20 31 32  3a 34 34 00 ff ff ff ff  /2012 12:44.....
    00e0   ff ff ff ff ff ff ff ff  ff ff ff ff 46 61 69 72  ............Fair
    00f0   63 68 69 6c 64 20 49 6d  61 67 69 6e 67 00 ff ff  child Imaging...
    '''
    print 'Reading EEPROM'
    res = dev.controlRead(0xC0, 0xB0, 0x0010, 0x0000, 256)
    if len(res) != 256:
        raise Exception("wanted 256 bytes but got %d" % (len(res),))
    print
    print 'Read EEPROM okay'
    print 'Serial number:   %s' % nulls(res, 0x0C)
    print 'Vendor1:         %s' % nulls(res, 0x2C)
    print 'Product:         %s' % nulls(res, 0x4C)
    print 'Rev:             %s' % nulls(res, 0x8C)
    print 'Date1:           %s' % nulls(res, 0xAC)
    print 'Date2:           %s' % nulls(res, 0xCC)
    print 'Vendor2:         %s' % nulls(res, 0xEC)

pidvid2name = {
        #(0x5328, 0x2009): 'Dexis Platinum (pre-enumeration)'
        (0x5328, 0x2030): 'Gendex GXS700 (post enumeration)'
        #(0x5328, 0x202F): 'Gendex GXS700 (pre-enumeration)'
        }

if __name__ == "__main__":
    usbcontext = usb1.USBContext()
    print 'Scanning for devices...'
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
            dump_eeprom(udev.open())

