'''
with the bad eeprom connected it didn't register sensor ID
however it did still do state probes
does this mean that it would continue to work even with a wiped eeprom?
how did I wipe it?

What is EEPROM1?
Could it be an FPGA and the bitstream is no longer loading?
Think its a SmartFusion
could be talking to an ARM/FPGA over SPI or something like that
what could cause it to stop booting?
Is there a mode pin I set?
Wrote a bad register to it?
 

eeprom1
    read:  controlRead( 0xC0, 0xB0, 0x0010
    write: 
eeprom2
    read:  controlRead( 0xC0, 0xB0, 0x000B
    write: controlWrite(0x40, 0xB0, 0x000C
'''

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

