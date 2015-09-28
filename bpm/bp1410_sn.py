'''
bp1410_13_no_bp.cap
    bp device not attached
    should show where the mcu actually starts to get involved
bp1410_14_fix_linux_bulk.cap
    linux bulk transactions caused bulk reads to stop responding
    device reset / firmware load did not fix
        broke i2c bus?
    somehow bp software clears this fault, hoping this capture shows it
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



'''
Some feature stuff looks like it may just be normal linux operation
Plug in generates following:
    0x04
    0x10
    0x14
Probably only the endpoint halts need to be minded

Feature Selector        Recipient   wValue
ENDPOINT_HALT           Endpoint    0
DEVICE_REMOTE_WAKEUP    Device      1
TEST_MODE               Device      2

A ClearFeature() request that references a feature that cannot be cleared, that does not exist, or that
references an interface or endpoint that does not exist, will cause the device to respond with a Request
Error.

If wLength is non-zero, then the device behavior is not specified.

wValue: feature selector
packet 5: set 4
    interface: 0x03
packet 9: clear 0x14
    interface: 0x03
packet 13: set 4
packet 17: clear 0x14
packet 29: set 4
packe 33: clear 0x14
packet 37: set 4
packet 41: clear 0x14
packet 73: set 4
packet 77: clear 0x14
packet 81: set 4
packet 85: clear 0x14
packet 97: set 4
packet 101: clear 0x14
packet 105: set 4
packet 110: clear 0x14

actual start?
packet 125: clear 0 (ENDPOINT HALT)
    interface: 0x86
packet 127: clear 0 (ENDPOINT HALT)
    interface: 0x00
(some control messages)
packet 141: clear 0 (ENDPOINT HALT)
    interface: 0x86
packet 143: clear 0 (ENDPOINT HALT)
    interface: 0x02
packet 145: clear 0 (ENDPOINT HALT)
    interface: 0x88
(control in)
packet 149: clear 0 (ENDPOINT HALT)
    interface: 0x86
packet 151: clear 0 (ENDPOINT HALT)
    interface: 0x02
packet 153: clear 0 (ENDPOINT HALT)
    interface: 0x88
(contro/bulk)


get status

The Recipient bits of the bmRequestType field specify the desired recipient. The data returned is the current
status of the specified recipient.

packet 7
    wLength is 4 but standard only defines 2 valid


    
'''

def preamble(dev):
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
     
    # Generated from packet 1/2
    buff = controlRead(0x80, 0x06, 0x0100, 0x0000, 40)
    # NOTE:: req max 40 but got 18
    validate_read("\x12\x01\x00\x02\xFF\xFF\xFF\x40\xB9\x14\x01\x00\x00\x00\x01\x02"
              "\x00\x01", buff, "packet 1/2")
    
    # Generated from packet 21/22
    buff = controlRead(0x80, 0x06, 0x0100, 0x0000, 18)
    validate_read("\x12\x01\x00\x02\xFF\xFF\xFF\x40\xB9\x14\x01\x00\x00\x00\x01\x02"
              "\x00\x01", buff, "packet 21/22")
    # Generated from packet 23/24
    buff = controlRead(0x80, 0x06, 0x0200, 0x0000, 46)
    validate_read("\x09\x02\x2E\x00\x01\x01\x00\xC0\x00\x09\x04\x00\x00\x04\xFF\xFF"
              "\xFF\x00\x07\x05\x02\x02\x00\x02\x00\x07\x05\x04\x02\x00\x02\x00"
              "\x07\x05\x86\x02\x00\x02\x00\x07\x05\x88\x03\x40\x00\x05", buff, "packet 23/24")
    # Generated from packet 25/26
    controlWrite(0x00, 0x09, 0x0001, 0x0000, "")
    # Generated from packet 27/28
    buff = controlRead(0x80, 0x06, 0x0100, 0x0000, 64)
    # NOTE:: req max 64 but got 18
    validate_read("\x12\x01\x00\x02\xFF\xFF\xFF\x40\xB9\x14\x01\x00\x00\x00\x01\x02"
              "\x00\x01", buff, "packet 27/28")

    # Generated from packet 45/46
    buff = controlRead(0x80, 0x06, 0x0100, 0x0000, 18)
    validate_read("\x12\x01\x00\x02\xFF\xFF\xFF\x40\xB9\x14\x01\x00\x00\x00\x01\x02"
              "\x00\x01", buff, "packet 45/46")
    # Generated from packet 47/48
    buff = controlRead(0x80, 0x06, 0x0200, 0x0000, 46)
    validate_read("\x09\x02\x2E\x00\x01\x01\x00\xC0\x00\x09\x04\x00\x00\x04\xFF\xFF"
              "\xFF\x00\x07\x05\x02\x02\x00\x02\x00\x07\x05\x04\x02\x00\x02\x00"
              "\x07\x05\x86\x02\x00\x02\x00\x07\x05\x88\x03\x40\x00\x05", buff, "packet 47/48")
    # Generated from packet 49/50
    controlWrite(0x00, 0x09, 0x0001, 0x0000, "")
    # Generated from packet 51/52
    buff = controlRead(0x80, 0x06, 0x0100, 0x0000, 18)
    validate_read("\x12\x01\x00\x02\xFF\xFF\xFF\x40\xB9\x14\x01\x00\x00\x00\x01\x02"
              "\x00\x01", buff, "packet 51/52")
    # Generated from packet 53/54
    buff = controlRead(0x80, 0x06, 0x0200, 0x0000, 9)
    validate_read("\x09\x02\x2E\x00\x01\x01\x00\xC0\x00", buff, "packet 53/54")
    # Generated from packet 55/56
    buff = controlRead(0x80, 0x06, 0x0200, 0x0000, 255)
    # NOTE:: req max 255 but got 46
    validate_read("\x09\x02\x2E\x00\x01\x01\x00\xC0\x00\x09\x04\x00\x00\x04\xFF\xFF"
              "\xFF\x00\x07\x05\x02\x02\x00\x02\x00\x07\x05\x04\x02\x00\x02\x00"
              "\x07\x05\x86\x02\x00\x02\x00\x07\x05\x88\x03\x40\x00\x05", buff, "packet 55/56")
    # Generated from packet 57/58
    buff = controlRead(0x80, 0x06, 0x0300, 0x0000, 255)
    # NOTE:: req max 255 but got 4
    validate_read("\x04\x03\x09\x04", buff, "packet 57/58")
    # Generated from packet 59/60
    buff = controlRead(0x80, 0x06, 0x0302, 0x0409, 255)
    # NOTE:: req max 255 but got 32
    validate_read("\x20\x03\x50\x00\x72\x00\x6F\x00\x67\x00\x72\x00\x61\x00\x6D\x00"
              "\x6D\x00\x65\x00\x72\x00\x20\x00\x53\x00\x69\x00\x74\x00\x65\x00", buff, "packet 59/60")
    # Generated from packet 61/62
    buff = controlRead(0x80, 0x06, 0x0300, 0x0000, 255)
    # NOTE:: req max 255 but got 4
    validate_read("\x04\x03\x09\x04", buff, "packet 61/62")
    # Generated from packet 63/64
    buff = controlRead(0x80, 0x06, 0x0302, 0x0409, 255)
    # NOTE:: req max 255 but got 32
    validate_read("\x20\x03\x50\x00\x72\x00\x6F\x00\x67\x00\x72\x00\x61\x00\x6D\x00"
              "\x6D\x00\x65\x00\x72\x00\x20\x00\x53\x00\x69\x00\x74\x00\x65\x00", buff, "packet 63/64")
    # Generated from packet 65/66
    buff = controlRead(0x80, 0x06, 0x0200, 0x0000, 9)
    validate_read("\x09\x02\x2E\x00\x01\x01\x00\xC0\x00", buff, "packet 65/66")
    # Generated from packet 67/68
    buff = controlRead(0x80, 0x06, 0x0200, 0x0000, 46)
    validate_read("\x09\x02\x2E\x00\x01\x01\x00\xC0\x00\x09\x04\x00\x00\x04\xFF\xFF"
              "\xFF\x00\x07\x05\x02\x02\x00\x02\x00\x07\x05\x04\x02\x00\x02\x00"
              "\x07\x05\x86\x02\x00\x02\x00\x07\x05\x88\x03\x40\x00\x05", buff, "packet 67/68")
    # Generated from packet 69/70
    controlWrite(0x00, 0x09, 0x0001, 0x0000, "")
    # Generated from packet 71/72
    buff = controlRead(0x80, 0x06, 0x0100, 0x0000, 18)
    validate_read("\x12\x01\x00\x02\xFF\xFF\xFF\x40\xB9\x14\x01\x00\x00\x00\x01\x02"
              "\x00\x01", buff, "packet 71/72")



    #print 'sleep'
    #time.sleep(16.5)



    # Generated from packet 89/90
    buff = controlRead(0x80, 0x06, 0x0100, 0x0000, 18)
    validate_read("\x12\x01\x00\x02\xFF\xFF\xFF\x40\xB9\x14\x01\x00\x00\x00\x01\x02"
              "\x00\x01", buff, "packet 89/90")
    # Generated from packet 91/92
    buff = controlRead(0x80, 0x06, 0x0200, 0x0000, 46)
    validate_read("\x09\x02\x2E\x00\x01\x01\x00\xC0\x00\x09\x04\x00\x00\x04\xFF\xFF"
              "\xFF\x00\x07\x05\x02\x02\x00\x02\x00\x07\x05\x04\x02\x00\x02\x00"
              "\x07\x05\x86\x02\x00\x02\x00\x07\x05\x88\x03\x40\x00\x05", buff, "packet 91/92")
    # Generated from packet 93/94
    controlWrite(0x00, 0x09, 0x0001, 0x0000, "")
    # Generated from packet 95/96
    buff = controlRead(0x80, 0x06, 0x0100, 0x0000, 64)
    # NOTE:: req max 64 but got 18
    validate_read("\x12\x01\x00\x02\xFF\xFF\xFF\x40\xB9\x14\x01\x00\x00\x00\x01\x02"
              "\x00\x01", buff, "packet 95/96")
    
    
    



    # Generated from packet 113/114
    buff = controlRead(0x80, 0x06, 0x0100, 0x0000, 18)
    validate_read("\x12\x01\x00\x02\xFF\xFF\xFF\x40\xB9\x14\x01\x00\x00\x00\x01\x02"
              "\x00\x01", buff, "packet 113/114")
    # Generated from packet 115/116
    buff = controlRead(0x80, 0x06, 0x0200, 0x0000, 46)
    validate_read("\x09\x02\x2E\x00\x01\x01\x00\xC0\x00\x09\x04\x00\x00\x04\xFF\xFF"
              "\xFF\x00\x07\x05\x02\x02\x00\x02\x00\x07\x05\x04\x02\x00\x02\x00"
              "\x07\x05\x86\x02\x00\x02\x00\x07\x05\x88\x03\x40\x00\x05", buff, "packet 115/116")
    # Generated from packet 117/118
    controlWrite(0x00, 0x09, 0x0001, 0x0000, "")
    # Generated from packet 119/120
    buff = controlRead(0x80, 0x06, 0x0100, 0x0000, 18)
    validate_read("\x12\x01\x00\x02\xFF\xFF\xFF\x40\xB9\x14\x01\x00\x00\x00\x01\x02"
              "\x00\x01", buff, "packet 119/120")
    # Generated from packet 121/122
    buff = controlRead(0x80, 0x06, 0x0200, 0x0000, 9)
    validate_read("\x09\x02\x2E\x00\x01\x01\x00\xC0\x00", buff, "packet 121/122")
    # Generated from packet 123/124
    controlWrite(0x00, 0x09, 0x0001, 0x0000, "")

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
    if 0:
        preamble()
    if 0:
        print 'sleep'
        time.sleep(5)
        print 'sending'

    '''
    
    '''
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
    if 1:
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
    for i in xrange(0):
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

    if 0:
        print
        print
        print 'control read'
        for i in xrange(4):
            # Generated from packet 155/156
            buff = controlRead(0xC0, 0xB0, 0x0000, 0x0000, 4096)
            # NOTE:: req max 4096 but got 3
            print 'val 155: %s' % binascii.hexlify(buff)
            validate_read("\x00\x00\x00", buff, "packet 155/156")

        print
        print
        print 'bulk read'
        for i in xrange(0):
            # Generated from packet 157/158
            # xxx: when is the earliest we can do this?
            buff = bulkRead(0x86, 0x0200)
            # NOTE:: req max 512 but got 4
            print 'val 157: %s' % binascii.hexlify(buff)
            validate_read("\x08\x16\x01\x00", buff, "packet 157/158")
    
    #time.sleep(0.2)
    
    # Generated from packet 159/160
    # Clear endpoint 0x86
    controlWrite(0x02, 0x01, 0x0000, 0x0086, "")
    # Generated from packet 161/162
    # Clear endpoint 0x02
    controlWrite(0x02, 0x01, 0x0000, 0x0002, "")
    # Generated from packet 163/164
    # Clear endpoint 0x88
    controlWrite(0x02, 0x01, 0x0000, 0x0088, "")

    
    #time.sleep(0.2)
    
    for i in xrange(3):
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


    return


    for i in xrange(3):
        print 'bulk read 169'
        # Generated from packet 169/170
        bulkWrite(0x02, "\x01")
        
        
        '''
        Stream protocol starts here
        Unfortunately the sizes vary as data comes in
        Seems to respond as whole messages are recieved
        We need to figure out how packetization works
        '''
        
        '''
        WARNING: some windows captures were getting shorter but I always get 136 bytes
        '''
        if 0:
            for i in xrange(16):
                buff = bulkRead(0x86, 0x0200)
                print i, 'Read %d bytes' % len(buff)
            
            return
        
        
        # Generated from packet 171/172
        buff = bulkRead(0x86, 0x0200)
        print '171 len: %d' % len(buff)
        # NOTE:: req max 512 but got 136
        '''
    -    # NOTE:: req max 512 but got 136
    +    # NOTE:: req max 512 but got 114
        '''
        '''
        -              "\x01\x00\x00\x00\x00\x00\x02\x00\x80\x01\xC0\x01\x02\x00\x01\x00"
        +              "\x01\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00"
        '''
        p171_exp = ("\x08\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24"
                  "\x00\x00\x30\x00\x8C\x00\x80\x12\x09\x00\xC0\x00\x00\x00\x09\x00"
                  "\x08\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00"
                  "\xD0\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55"
                  "\x01\x00\x00\x00\x00\x00\x02\x00\x80\x01\xC0\x01\x02\x00\x01\x00"
                  "\x00\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00"
                  "\x01\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46"
                  "\x00\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11"
                  "\x00\x00\xC0\x1E\x00\x00\x85\x00")
        print 'Exp len: %d' % len(p171_exp)
        # FIXME: revisit
        # voltages? could be fluctuating...
        '''
        Failed packet 171/172
        Expected;   0884a406020026004300c00300081024000030008c0080120900c000000009000800ff00c41e0000cc1e0000b4460000d01e0000c01e0100b01e01000000305501000000000002008001c00102000100000056100000a025000084250000000001007c2500007e2500008025000074460000381100003c1100004011000044110000c01e00008500
          
        Actual:     0884a406020026004300c0030008102400003000830030010900c000000009000800ff00c41e0000cc1e0000b4460000d01e0000c01e0100b01e01000000305501000000000002008001d00102000100000056100000a025000084250000000001007c2500007e2500008025000074460000381100003c1100004011000044110000c01e00008500
        First diff @ 20 w/ E: 0x8C, A: 0x83)
          
        Actual:     0884a406020026004300c0030008102400003000830030010900c000000009000800ff00c41e0000cc1e0000b4460000d01e0000c01e0100b01e01000000305501000000000002008001d00102000100000056100000a025000084250000000001007c2500007e2500008025000074460000381100003c1100004011000044110000c01e00008500
        First diff @ 22 w/ E: 0x80, A: 0x30)
          
        Actual:     0884a406020026004300c0030008102400003000830030010900c000000009000800ff00c41e0000cc1e0000b4460000d01e0000c01e0100b01e01000000305501000000000002008001d00102000100000056100000a025000084250000000001007c2500007e2500008025000074460000381100003c1100004011000044110000c01e00008500
        First diff @ 23 w/ E: 0x09, A: 0x01)
          
        think this is a operation counter
        saw it changing in some of the reference traces
        ignore for now
        
        E: 8c008012
        A: 83003001
        
        
        ...and theres more
        First diff @ 74 w/ E: 0xC0, A: 0xD0)

        '''
        p171_exp = p171_exp[0:20] + '\x83\x00\x30\x01' + p171_exp[24:]
        p171_exp = p171_exp[0:74] + '\xD0' + p171_exp[75:]
        validate_read(p171_exp, buff, "packet 171/172")
    
    
    for i in xrange(3):
        # Generated from packet 173/174
        bulkWrite(0x02, "\x43\x19\x00\x00\x00\x3B\x7E\x25\x00\x00\xFE\xFF\x3B\x7C\x25\x00"
                  "\x00\xFE\xFF\x00")
        # Generated from packet 175/176
        buff = bulkRead(0x86, 0x0200)
        # NOTE:: req max 512 but got 5
        validate_read("\x08\xA4\x06\x02\x00", buff, "packet 175/176")
    
    for i in xrange(1):
        # Generated from packet 177/178
        bulkWrite(0x02, "\x01")
        
        
        '''
        Expected;   0884a406020026004300c00300081024000030008c0080120900c000000009000800ff00c41e0000cc1e0000b4460000d01e0000c01e0100b01e01000000305501000000000002008001c00102000100000056100000a025000084250000000001007c2500007e2500008025000074460000381100003c1100004011000044110000c01e00008500
        Actual:     0884a406020026004300c0030008102400003000830030010900c000000009000800ff00c41e0000cc1e0000b4460000d01e0000c01e0100b01e01000000305501000000000002008001d00102000100000056100000a025000084250000000001007c2500007e2500008025000074460000381100003c1100004011000044110000c01e00008500

        First diff @ 20 w/ E: 0x8C, A: 0x83)
        '''
        # Generated from packet 179/180
        buff = bulkRead(0x86, 0x0200)
        p_exp =  ("\x08\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24"
                  "\x00\x00\x30\x00\x8C\x00\x80\x12\x09\x00\xC0\x00\x00\x00\x09\x00"
                  "\x08\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00"
                  "\xD0\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55"
                  "\x01\x00\x00\x00\x00\x00\x02\x00\x80\x01\xC0\x01\x02\x00\x01\x00"
                  "\x00\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00"
                  "\x01\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46"
                  "\x00\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11"
                  "\x00\x00\xC0\x1E\x00\x00\x85\x00")
        # FIXME
        p_exp = p_exp[0:20] + '\x83\x00\x30\x01' + p_exp[24:]
        p_exp = p_exp[0:74] + '\xD0' + p_exp[75:]
        # NOTE:: req max 512 but got 136
        validate_read(p_exp, buff, "packet 179/180")
        
    
    
    for i in xrange(0):
        # Generated from packet 181/182
        bulkWrite(0x02, "\x0E\x00")
        
        
        '''
        This is an EEPROM/flash read?
        
        S/N: 34346
            0x0000862a
            \x33\x34\x33\x34\x36
            2a86
        Try to verify see something similar with 1600
            S/N: 28781
            0x706d
            6d70
            
          Expected;   083a00903200002a8601953c36900020000100d60501007224223900000000bf1d2000
          Actual:     083a009032a7022a8601953c3690001f000100d60501007224223900000000271f2000
          First diff @ 5 w/ E: 0x00, A: 0xA7)
        
        
        1400U cap
        jackpot!
        validate_read("\x08\x36\x00\xB2\x32\xC0\x03\x6D\x70\x01\x96\x1A\x41\x96\x00\x20"
                  "\x00\x01\x00\x40\x06\x01\x00\x42\x28\x02\x36\x00\x00\x00\x00\xB0"
                  "\x9C\x20\x00", buff, "packet 271/272")
        '''
        # Generated from packet 183/184
        buff = bulkRead(0x86, 0x0200)
        sn = struct.unpack('<H', buff[7:9])[0]
        print 'Read S/N: %s' % (sn,)
        # NOTE:: req max 512 but got 35
        validate_read("\x08\x3A\x00\x90\x32\x00\x00\x2A\x86\x01\x95\x3C\x36\x90\x00\x20"
                  "\x00\x01\x00\xD6\x05\x01\x00\x72\x24\x22\x39\x00\x00\x00\x00\xBF"
                  "\x1D\x20\x00", buff, "packet 183/184")
    
    
    

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

