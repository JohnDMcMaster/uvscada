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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('--all', '-a', action='store_true', help='prog entire EEPROM (8k)')
    parser.add_argument('--fn2', '-F', help='write bin to filename')
    args = parser.parse_args()

    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext)


    if 0:
        '''
        There's some funny math around the beginning
        its not a linear mapping
        seems to level out after the first 0x20 bytes
        writing to 0x10 writes to 0x0000...if large enough?
        
        think its supposed to be written 0x20 aligned
        '''
        if 0:
            '''
            the first 6 bytes are special
            but I did manage to erase them before
            00000000  FF FF FF FF FF FF 06 07  08 09 0A 0B 0C 0D 0E 0F  |................|
            00000010  10 11 12 13 14 15 16 17  18 19 1A 1B 1C 1D 1E 1F  |................|
            '''
            #for i in xrange(0x100):
            for i in xrange(0xFF):
                print 'Write %d' % i
                dev.controlWrite(0x40, 0xB0, 0x000C, i, chr(i) * 4)
        if 0:
            # does nothing
            #dev.controlWrite(    0x40, 0xB0, 0x000C, 0x0000, "\xCC" * 0x80)
        
            # writes first 0x20 bytes
            #dev.controlWrite(    0x40, 0xB0, 0x000C, 0x0010, "\xFF" * 0x80)
            dev.controlWrite(    0x40, 0xB0, 0x000C, 0x0010, "C" * 32)
        if 0:
            # writes 0x20:0x3F
            dev.controlWrite(    0x40, 0xB0, 0x000C, 0x0020, "\xDD" * 0x80)
        if 0:
            for i in xrange(0x2000 - 0x20, 0x2000, 0x20):
                print 'Write 0x%04X' % i
                dev.controlWrite(0x40, 0xB0, 0x000C, i, chr(i/0x80) * 0x20)
        dev.controlWrite(0x40, 0xB0, 0x000C, 0x0010, "A" * 32)
        sys.exit(1)


    # matches this
    # buff = dump_loop(0x0B, 0x80, 0x0000, dump_len, do_hexdump=(not (args.fn2 or args.all)))
    buf = bytearray('\xAB' * 0x2000)
    r = open(args.fn2, 'r').read()
    buf[0:len(r)] = r
    if args.all:
        size = 0x2000
    else:
        size = 0x60
    for i in xrange(0, size, 0x20):
        print 'Write 0x%04X' % i
        prog_addr = i
        if prog_addr == 0:
            # a bit screwed up...but w/e
            dat = str(buf[i:i+0x20])
            dat = dat[0x10:] + dat[0x00:0x10]
            dev.controlWrite(0x40, 0xB0, 0x000C, 0x0010, dat)
        else:
            dev.controlWrite(0x40, 0xB0, 0x000C, prog_addr, str(buf[i:i+0x20]))

