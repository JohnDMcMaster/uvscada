# https://github.com/vpelletier/python-libusb1
# Python-ish (classes, exceptions, ...) wrapper around libusb1.py . See docstrings (pydoc recommended) for usage.
import usb1
# Bare ctype wrapper, inspired from library C header file.
import libusb1
import binascii
import sys
import argparse
from util import hexdump
from util import open_dev

verbose = False

def nulls(s, offset):
    end = s.find('\x00', offset)
    if end < 0:
        return s[offset:]
    else:
        return s[offset:end]

# At least 0x400 size EEPROM
# with just over 0x200 used
# higher addresses read FF, so its hard to tell how big it actually is
# (ie didn't wrap around)
# 0x200 seems to work but original code uses 0x100
#EEPROM_RMAX = 0x200
EEPROM_RMAX = 0x100
def eeprom_r(dev, addr, l):
    # gives all 0's if you request more than 0x200 bytes
    if l > 0x200:
        raise Exception("Invalid read size 0x%04X" % l)
    res = dev.controlRead(0xC0, 0xB0, 0x0010, addr, l)
    if len(res) != l:
        raise Exception("requested 0x%04X bytes but got 0x%04X" % (dump_len, len(res),))
    return res

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('--fn', '-f', help='write bin to filename')
    parser.add_argument('addr', nargs='?', default='0', help='address')
    parser.add_argument('len', nargs='?', default='0x234', help='length')
    args = parser.parse_args()

    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext)

    print
    print 'Reading EEPROM'
    dump_addr = int(args.addr, 0)
    dump_len = int(args.len, 0)
    
    bin = ''
    to_dump = dump_len
    addr_cur = dump_addr
    while to_dump > 0:
        l_this = max(to_dump, to_dump - EEPROM_RMAX)
        l_this = min(l_this, EEPROM_RMAX)
        print
        print 'Addr 0x%04X, len 0x%04X' % (addr_cur, l_this)
        
        res = dev.controlRead(0xC0, 0xB0, 0x0010, addr_cur, l_this)
        bin += res
        hexdump(res)
        if len(res) != l_this:
            print "WARNING: wanted 0x%04X bytes but got 0x%04X" % (dump_len, len(res),)
        to_dump -= l_this
        addr_cur += l_this
    if args.fn:
        open(args.fn, 'w').write(bin)


    '''
    gendex bad
    00000000  41 41 41 41 41 41 41 41  49 41 41 00 00 00 00 00  |AAAAAAAAIAA.....|
    00000010  41 41 41 41 41 41 41 41  41 41 41 41 41 41 41 41  |AAAAAAAAAAAAAAAA|
    00000020  32 30 31 35 2F 30 33 2F  31 39 2D 32 31 3A 34 34  |2015/03/19-21:44|
    00000030  3A 34 33 3A 30 38 37 41  41 41 41 41 41 41 41 41  |:43:087AAAAAAAAA|
    00000040  32 31 30 33 32 33 31 36  36 33 00 FF FF 00 74 E2  |2103231663....t.|
    00000050  FF FF FF FF FF FF FF FF  FF FF FF FF FF FF FF FF  |................|
    00000060  FF FF FF FF FF FF FF FF  FF FF FF FF FF FF FF FF  |................|
    00000070  FF FF FF FF FF FF FF FF  FF FF FF FF FF FF FF FF  |................|
    
    dexis good
    00000000  C0 28 53 09 20 00 00 01  54 00 00 00 54 00 00 00  |.(S. ...T...T...|
    00000010  FF FF FF FF FF FF FF FF  FF FF FF FF FF FF FF FF  |................|
    00000020  32 30 31 34 2F 30 37 2F  31 36 2D 31 37 3A 35 36  |2014/07/16-17:56|
    00000030  3A 31 35 3A 34 34 38 FF  FF FF FF FF FF FF FF FF  |:15:448.........|
    00000040  30 31 33 30 36 33 31 32  32 31 00 FF FF 00 39 AD  |0130631221....9.|
    00000050  FF FF FF FF FF FF FF FF  FF FF FF FF FF FF FF FF  |................|
    00000060  FF FF FF FF FF FF FF FF  FF FF FF FF FF FF FF FF  |................|
    00000070  FF FF FF FF FF FF FF FF  FF FF FF FF FF FF FF FF  |................|
    '''
    print
    print
    print
    print 'Secondary'
    buff = dev.controlRead(0xC0, 0xB0, 0x0B, 0x2000, 0x80, timeout=100)
    hexdump(buff)

