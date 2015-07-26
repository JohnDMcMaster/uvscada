'''
Related tools:
-fxload: tool that we want to feed into (also IDA...)
-cycfx2prog: allows dumping memory but not to bin or hex
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
from util import hexdump

verbose = False

def ram_r(dev, addr, datal):
    bs = 16
    offset = 0
    ret = bytearray()
    while offset < datal:
        l = min(bs, datal - offset)
        #print 'Read 0x%04X: %d' % (addr + offset, l)
        ret += dev.controlRead(0xC0, 0xA0, addr + offset, 0x0000, l, timeout=1000)
        offset += bs
    return str(ret)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('fout', nargs='?', default=None, help='File out')
    args = parser.parse_args()

    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext)

    print
    print 'Reading memory'

    # The FX2 has eight kbytes of internal program/data RAM,
    # Only the internal eight kbytes and scratch pad 0.5 kbytes RAM spaces have the following access:

    '''
    The available RAM spaces are 8 kbytes from
    0x0000-0x1FFF (code/data) and 512 bytes from 0xE000-0xE1FF (scratch pad RAM).
    '''
    r = ram_r(dev, 0x0000, 0x2000)
    #r = ram_r(dev, 0xE000, 0x2000)
    if args.fout:
        if args.fout.find('.hex') >= 0:
            pass
        else:
            open(args.fout, 'w').write(r)
    else:
        hexdump(r)

