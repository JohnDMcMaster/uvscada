'''
Goal
print voltage/current
'''

from bp1410_fw import load_fw

# https://github.com/vpelletier/python-libusb1
# Python-ish (classes, exceptions, ...) wrapper around libusb1.py . See docstrings (pydoc recommended) for usage.
import usb1
# Bare ctype wrapper, inspired from library C header file.
import libusb1
import argparse
import os
import binascii
import time
import struct

def validate_read(expected, actual, msg, allow=False):
    if expected != actual:
        print 'Failed %s' % msg
        print '  Expected;   %s' % binascii.hexlify(expected,)
        print '  Actual:     %s' % binascii.hexlify(actual,)
        for i in xrange(min(len(expected), len(actual))):
            if expected[i] != actual[i]:
                print '  First diff @ %d w/ E: 0x%02X, A: 0x%02X)' % (i, ord(expected[i]), ord(actual[i]))
                break
        if not allow:
            raise Exception('failed validate: %s' % msg)


def replay(dev):
    def bulkRead(endpoint, length, timeout=None):
        if timeout is None:
            timeout = 1000
        #time.sleep(.05)
        return dev.bulkRead(endpoint, length, timeout=timeout)

    def bulkWrite(endpoint, data, timeout=None):
        if timeout is None:
            timeout = 1000
        #time.sleep(.05)
        dev.bulkWrite(endpoint, data, timeout=timeout)
    
    def controlRead(request_type, request, value, index, length,
                    timeout=None):
        if timeout is None:
            timeout = 1000
        #time.sleep(.05)
        return dev.controlRead(request_type, request, value, index, length,
                    timeout=timeout)

    def controlWrite(request_type, request, value, index, data,
                     timeout=None):
        if timeout is None:
            timeout = 1000
        #time.sleep(.05)
        dev.controlWrite(request_type, request, value, index, data,
                     timeout=timeout)

    # Generated from packet 125/126
    # packet 125: clear 0 (ENDPOINT HALT), interface: 0x86
    controlWrite(0x02, 0x01, 0x0000, 0x0086, "")
    time.sleep(0.005)
    # Generated from packet 127/128
    # packet 127: clear 0 (ENDPOINT HALT), interface: 0x02
    controlWrite(0x02, 0x01, 0x0000, 0x0002, "")
    time.sleep(0.003)
    
    
    load_fw(dev)

    
    # XXX: do we need to renumerate here?
    # 20 ms delay
    time.sleep(0.020)
    
    
    '''
    guess not...always returned same result
    print 'scan i2c?'
    for i in xrange(0xFF):
        buff = controlRead(0xC0, 0xB0, i, i, 4096)
        if buff != '\x00\x00\x00':
            print
            print
            print i, binascii.hexlify(buff)
    return
    '''
    if 0:
        buff = bulkRead(0x86, 0x0200)
        print 'len: %d' % len(buff)
        print binascii.hexlify(buff)
        return
    
    # Generated from packet 141/142
    # Clear endpoint 0x86
    controlWrite(0x02, 0x01, 0x0000, 0x0086, "")
    # Generated from packet 143/144
    # Clear endpoint 0x02
    controlWrite(0x02, 0x01, 0x0000, 0x0002, "")
    # Generated from packet 145/146
    # Clear endpoint 0x88
    controlWrite(0x02, 0x01, 0x0000, 0x0088, "")
    
    
    # Generated from packet 147/148
    # gxs note i2c_read: controlRead(0xC0, 0xB0, 0x0A, addr, n, timeout=self.timeout)
    # close but not quite the same?
    # maybe should try scanning address space
    # tried looping, always returns 000000 regardless of wIndex or wValue
    buff = controlRead(0xC0, 0xB0, 0x0000, 0x0000, 4096)
    # NOTE:: req max 4096 but got 3
    validate_read("\x00\x00\x00", buff, "packet 147/148")
    '''
    With BP disconnected (bp1410_13_no_bp.cap):
    validate_read("\x01\xFF\x00", buff, "packet 191/192")
    '''
    if 0:
        for i in xrange(32):
            buff = controlRead(0xC0, 0xB0, i, 0, 4096)
            print i, binascii.hexlify(buff)
            # NOTE:: req max 4096 but got 3
            validate_read("\x00\x00\x00", buff, "packet 147/148")
        return
    


    # FIXME: its almost like this was missing?
    # controlRead(0xC0, ...) are always followed by bulkRead elsewhere
    if 0:
        # Generated from packet 157/158
        # xxx: when is the earliest we can do this?
        buff = bulkRead(0x86, 0x0200)
        # NOTE:: req max 512 but got 4
        print 'val 157: %s' % binascii.hexlify(buff)
        validate_read("\x08\x16\x01\x00", buff, "packet 148.5")
    
    
    
    
    
    
    '''
    General pattern in this section:
    -Clear endpoints
    -Control in request.  Takes a while
    -Bulk read
    '''
    
    
    # Generated from packet 149/150
    # Clear endpoint 0x86
    controlWrite(0x02, 0x01, 0x0000, 0x0086, "")
    # Generated from packet 151/152
    # Clear endpoint 0x02
    controlWrite(0x02, 0x01, 0x0000, 0x0002, "")
    # Generated from packet 153/154
    # Clear endpoint 0x88
    controlWrite(0x02, 0x01, 0x0000, 0x0088, "")
    
    time.sleep(0.002)

    if 0:
        # more than one causes issues
        # only 1 works but doesn't effect things later
        for i in xrange(1):
            # doesn't effect things
            #time.sleep(0.5)
            
            print 'Try extra read pre'
            buff = bulkRead(0x86, 0x0200)
            print 'extra bulk: %s' % binascii.hexlify(buff)
    
    '''
    FIXME: I fiddled with this until the code chugged along
    Need to revisit once I understand better and figure out why the Windows driver doesn't need this block
    What did I actually do here?
    
    Why don't sleeps help but extra reads (which appear to be nops) do?
    
    Bulk read doesn't work until control read has been done
    Submitting two controls in a row are redundant: the second is dropped
    The first controlRead isn't needed
    This indicates there was a stale bulk request
    
    Why does 3 loops fail but 4 pass?
    '''
    for i in xrange(4):
        print
        print '155 loop %d' % i
        # Generated from packet 155/156
        buff = controlRead(0xC0, 0xB0, 0x0000, 0x0000, 4096)
        # NOTE:: req max 4096 but got 3
        print 'val 155: %s' % binascii.hexlify(buff)
        validate_read("\x00\x00\x00", buff, "packet 155/156")

        # Generated from packet 157/158
        # xxx: when is the earliest we can do this?
        buff = bulkRead(0x86, 0x0200)
        # NOTE:: req max 512 but got 4
        print 'val 157: %s' % binascii.hexlify(buff)
        validate_read("\x08\x16\x01\x00", buff, "packet 157/158")

    # Generated from packet 159/160
    # Clear endpoint 0x86
    controlWrite(0x02, 0x01, 0x0000, 0x0086, "")
    # Generated from packet 161/162
    # Clear endpoint 0x02
    controlWrite(0x02, 0x01, 0x0000, 0x0002, "")
    # Generated from packet 163/164
    # Clear endpoint 0x88
    controlWrite(0x02, 0x01, 0x0000, 0x0088, "")
    
    for i in xrange(1):
        # Generated from packet 165/166
        buff = controlRead(0xC0, 0xB0, 0x0000, 0x0000, 4096)
        print 'val 165: %s' % binascii.hexlify(buff)
        # NOTE:: req max 4096 but got 3
        validate_read("\x00\x00\x00", buff, "packet 165/166")

        
        # freezes
        print 'bulk read 167'
        # Generated from packet 167/168
        # reference is ***111 us***
        buff = bulkRead(0x86, 0x0200, timeout=500)
        print 'val 167: %s' % binascii.hexlify(buff)
        # NOTE:: req max 512 but got 4
        validate_read("\x08\x16\x01\x00", buff, "packet 167/168")
    
    
        # Generated from packet 749/750
        bulkWrite(0x02, "\x19\x0C\x00")
        # Generated from packet 751/752
        buff = bulkRead(0x86, 0x0200)
        validate_read("\x08\x10\x33\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                  "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00", buff, "packet 751/752")

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
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    args = parser.parse_args()

    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext)
    dev.claimInterface(0)
    dev.resetDevice()
    replay(dev)

