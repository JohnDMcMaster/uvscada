# https://github.com/vpelletier/python-libusb1
# Python-ish (classes, exceptions, ...) wrapper around libusb1.py . See docstrings (pydoc recommended) for usage.
import usb1
# Bare ctype wrapper, inspired from library C header file.
import libusb1
import binascii
import sys
import argparse

verbose = False

def nulls(s, offset):
    end = s.find('\x00', offset)
    if end < 0:
        return s[offset:]
    else:
        return s[offset:end]

def hexdumps(*args, **kwargs):
    '''Hexdump by returning a string'''
    buff = StringIO.StringIO()
    kwargs['f'] = buff
    hexdump(*args, **kwargs)
    return buff.getvalue()

def hexdump(data, label=None, indent='', address_width=8, f=sys.stdout):
    def isprint(c):
        return c >= ' ' and c <= '~'

    bytes_per_half_row = 8
    bytes_per_row = 16
    data = bytearray(data)
    data_len = len(data)
    
    def hexdump_half_row(start):
        left = max(data_len - start, 0)
        
        real_data = min(bytes_per_half_row, left)

        f.write(''.join('%02X ' % c for c in data[start:start+real_data]))
        f.write(''.join('   '*(bytes_per_half_row-real_data)))
        f.write(' ')

        return start + bytes_per_half_row

    pos = 0
    while pos < data_len:
        row_start = pos
        f.write(indent)
        if address_width:
            f.write(('%%0%dX  ' % address_width) % pos)
        pos = hexdump_half_row(pos)
        pos = hexdump_half_row(pos)
        f.write("|")
        # Char view
        left = data_len - row_start
        real_data = min(bytes_per_row, left)

        f.write(''.join([c if isprint(c) else '.' for c in str(data[row_start:row_start+real_data])]))
        f.write((" " * (bytes_per_row - real_data)) + "|\n")

def dump_eeprom(dev, verbose=False):
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
    print
    print 'Reading EEPROM 1'
    # cap2 443-444
    res = dev.controlRead(0xC0, 0xB0, 0x0010, 0x0000, 256)
    if verbose:
        hexdump(res)
    if len(res) != 256:
        raise Exception("wanted 256 bytes but got %d" % (len(res),))
    print 'Read EEPROM okay'
    print 'Serial number:   %s' % nulls(res, 0x0C)
    print 'Vendor1:         %s' % nulls(res, 0x2C)
    print 'Product:         %s' % nulls(res, 0x4C)
    print 'Rev:             %s' % nulls(res, 0x8C)
    print 'Date1:           %s' % nulls(res, 0xAC)
    print 'Date2:           %s' % nulls(res, 0xCC)
    print 'Vendor2:         %s' % nulls(res, 0xEC)


    '''
    0000   ff ff ff ff ff ff ff ff  ff ff ff ff ff ff ff ff  ................
    0010   ff ff ff ff ff ff ff ff  ff ff ff ff ff ff ff ff  ................
    0020   ff ff ff ff ff ff ff ff  ff ff ff ff ff ff ff ff  ................
    0030   ff ff ff ff ff ff ff ff  ff ff ff ff ff ff ff ff  ................
    0040   ff ff ff ff ff ff ff ff  ff ff ff ff ff ff ff ff  ................
    0050   ff ff ff ff ff ff ff ff  ff ff ff ff ff ff ff ff  ................
    0060   ff ff ff ff ff ff ff ff  ff ff ff ff 73 74 35 5f  ............st5_
    0070   66 63 63 6d 6f 73 64 20  72 31 34 2e 39 00 ff ff  fccmosd r14.9...
    0080   ff ff ff ff ff ff ff ff  ff ff ff ff ff ff ff ff  ................
    0090   ff ff ff ff ff ff ff ff  ff ff ff ff ff ff ff ff  ................
    00a0   ff ff ff ff ff ff ff ff  ff ff ff ff ff ff ff ff  ................
    00b0   ff ff ff ff ff ff ff ff  ff ff ff ff ff ff ff ff  ................
    00c0   ff ff ff ff ff ff ff ff  ff ff ff ff ff ff ff ff  ................
    00d0   ff ff ff ff ff ff ff ff  ff ff ff ff ff ff ff ff  ................
    00e0   ff ff ff ff ff ff ff ff  ff ff ff ff 31 00 ff ff  ............1...
    00f0   ff ff ff ff 31 39 2e 35  30 30 30 00 31 39 2e 35  ....19.5000.19.5
    '''
    print
    print 'Reading EEPROM 2'
    # cap2 445-446
    res = dev.controlRead(0xC0, 0xB0, 0x0010, 0x0100, 256)
    if verbose:
        hexdump(res)
    if len(res) != 256:
        raise Exception("wanted 256 bytes but got %d" % (len(res),))
    print 'Read EEPROM okay'
    print 'something:       %s' % nulls(res, 0x6C)
    print '1:               %s' % nulls(res, 0xEC)
    print 'something:       %s' % nulls(res, 0xF4)
    print 'something:       %s' % nulls(res, 0xFC)


    '''
    0000   30 30 30 00 30 2e 30 30  30 30 00 ff 37 35 00 ff  000.0.0000..75..
    0010   ff ff ff ff 00 53 54 00  ff ff ff ff ff ff ff ff  .....ST.........
    0020   ff ff ff ff ff ff ff ff  ff ff ff ff ff ff ff ff  ................
    0030   ff ff ff ff                                      ....
    '''
    print
    print 'Reading EEPROM 3'
    # cap2 447-448
    res = dev.controlRead(0xC0, 0xB0, 0x0010, 0x0200, 52)
    if verbose:
        hexdump(res)
    if len(res) != 52:
        raise Exception("wanted 52 bytes but got %d" % (len(res),))
    print 'Read EEPROM okay'
    print 'something:       %s' % nulls(res, 0x00)
    print 'something:       %s' % nulls(res, 0x04)
    print 'something:       %s' % nulls(res, 0x0C)
    print 'something:       %s' % nulls(res, 0x15)


pidvid2name = {
        #(0x5328, 0x2009): 'Dexis Platinum (pre-enumeration)'
        (0x5328, 0x2030): 'Gendex GXS700 (post enumeration)'
        #(0x5328, 0x202F): 'Gendex GXS700 (pre-enumeration)'
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    args = parser.parse_args()

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
            dump_eeprom(udev.open(), args.verbose)

