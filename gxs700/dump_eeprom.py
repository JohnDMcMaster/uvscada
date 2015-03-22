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

def dump_loop(req, max_read, dump_addr, dump_len, do_hexdump=True):
    bin = ''
    to_dump = dump_len
    addr_cur = dump_addr
    while to_dump > 0:
        l_this = max(to_dump, to_dump - max_read)
        l_this = min(l_this, max_read)
        print
        print 'Addr 0x%04X, len 0x%04X' % (addr_cur, l_this)
        
        res = dev.controlRead(0xC0, 0xB0, req, addr_cur, l_this)
        bin += res
        if hexdump:
            hexdump(res)
        if len(res) != l_this:
            print "WARNING: wanted 0x%04X bytes but got 0x%04X" % (dump_len, len(res),)
        to_dump -= l_this
        addr_cur += l_this
    return bin

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('--fn', '-f', help='write bin to filename')
    parser.add_argument('--fn2', '-F', help='write bin to filename')
    parser.add_argument('--all', '-a', action='store_true', help='dump entire EEPROM (2k)')
    parser.add_argument('addr', nargs='?', default='0', help='address')
    parser.add_argument('len', nargs='?', default='0x234', help='length')
    args = parser.parse_args()

    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext)

    print
    print 'Reading EEPROM'
    dump_addr = int(args.addr, 0)
    if args.all:
        dump_len = 0x800
    else:
        dump_len = int(args.len, 0)
    bin = dump_loop(0x0010, EEPROM_RMAX, dump_addr, dump_len, do_hexdump=(not (args.fn or args.all)))
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
    

    During the power-up sequence, internal logic checks the I2C-compatible port for the connection of an EEPROM whose first byte
    is either 0xC0 or 0xC2. If found, it uses the VID/PID/DID values in the EEPROM in place of the internally stored values (0xC0),
    or it boot-loads the EEPROM contents into internal RAM (0xC2). If no EEPROM is detected, FX2 enumerates using internally
    stored descriptors. The default ID values for FX2 are VID/PID/DID (0x04B4, 0x8613, 0xxxyy).
    
    Def VID: 0x04B4 
    Def PID: 0x8613 

    (0x5328, 0x2009): 'Dexis Platinum (pre-enumeration)',
    (0x5328, 0x202F): 'Gendex GXS700 (pre-enumeration)',

    gendex bad post torture
    for i in xrange(0x100):
        print 'Write %d' % i
        dev.controlWrite(0x40, 0xB0, 0x000C, i, chr(i))
    
    00000000  41 41 41 41 41 41 06 07  08 09 0A 0B 0C 0D 0E 0F  |AAAAAA..........|
    00000010  10 11 12 13 14 15 16 17  18 19 1A 1B 1C 1D 1E 1F  |................|
    00000020  20 21 22 23 24 25 26 27  28 29 2A 2B 2C 2D 2E 2F  | !"#$%&'()*+,-./|
    00000030  30 31 32 33 34 35 36 37  38 39 3A 3B 3C 3D 3E 3F  |0123456789:;<=>?|
    00000040  40 41 42 43 44 45 46 47  48 49 4A 4B 4C 4D 4E 4F  |@ABCDEFGHIJKLMNO|
    00000050  50 51 52 53 54 55 56 57  58 59 5A 5B 5C 5D 5E 5F  |PQRSTUVWXYZ[\]^_|
    00000060  60 61 62 63 64 65 66 67  68 69 6A 6B 6C 6D 6E 6F  |`abcdefghijklmno|
    00000070  70 71 72 73 74 75 76 77  78 79 7A 7B 7C 7D 7E 7F  |pqrstuvwxyz{|}~.|
    
    indicates I can def write to at least one of the EPROMs
    but looks like serial was in *two* ROMs
    
    confiremd by writing increment every 32 bytes
    2k eeprom
    '''
    print
    print
    print
    print 'Secondary'

    if args.all:
        dump_len = 0x2000
    else:
        dump_len = 0x80
    # wraps around 0x2000
    buff = dump_loop(0x0B, 0x80, 0x0000, dump_len, do_hexdump=(not (args.fn2 or args.all)))    
    if args.fn2:
        open(args.fn2, 'w').write(buff)

