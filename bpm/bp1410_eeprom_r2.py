'''
Golden refernece of the hack that gets packet 167 to read correctly
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



    '''

    .text:101D9085                 mov     dword ptr [esp+138h+var_110], 0BEEFh     ; length?
    .text:101D9081                 mov     [esp+138h+var_114], edi                  ; value (eeprom offset)
        starts out as 0
        incremenets by 0x1000
            add     edi, 1000h
    .text:101D9079                 mov     [esp+138h+var_118], 0A2h                 ; request
    .text:101D908D                 mov     [esp+138h+var_11C], 1                    ; index?

    
    '''
    buff = controlRead(request_type=0xC0, request=0xA2, value=0, index=0x1, length=0x1000)
    # can't be bulk, has control parameters
    # don't think its both...could it be?
    #buff = bulkRead(request_type=0x82, request=0xA2, value=0, index=0x1, length=0x1000)
    print 'len buff: %d' % buff
    #print binascii.hexlify(buff,)

