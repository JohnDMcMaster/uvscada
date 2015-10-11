import libusb1
import binascii

from util import hexdump

def usb_wraps(dev):
    # Shorten stack traces to simplify errors
    def bulkRead(endpoint, length, timeout=None):
        if timeout is None:
            timeout = 1000
        return dev.bulkRead(endpoint, length, timeout=timeout)

    def bulkWrite(endpoint, data, timeout=None):
        if timeout is None:
            timeout = 1000
        dev.bulkWrite(endpoint, data, timeout=timeout)
    
    def controlRead(request_type, request, value, index, length,
                    timeout=None):
        if timeout is None:
            timeout = 1000
        return dev.controlRead(request_type, request, value, index, length,
                    timeout=timeout)

    def controlWrite(request_type, request, value, index, data,
                     timeout=None):
        if timeout is None:
            timeout = 1000
        dev.controlWrite(request_type, request, value, index, data,
                     timeout=timeout)
    
    return bulkRead, bulkWrite, controlRead, controlWrite

def validate_read(expected, actual, msg):
    if expected != actual:
        print 'Failed %s' % msg
        print '  Expected; %s' % binascii.hexlify(expected,)
        print '  Actual:   %s' % binascii.hexlify(actual,)

def validate_read_e(expected, actual, msg):
    if expected != actual:
        print 'Failed %s' % msg
        print '  Expected; %s' % binascii.hexlify(expected,)
        print '  Actual:   %s' % binascii.hexlify(actual,)
        raise Exception('failed validate: %s' % msg)

def validate_read_h(expected, actual, msg):
    if expected != actual:
        print 'Failed %s' % msg
        print '  Expected; %s' % binascii.hexlify(expected,)
        hexdump(expected, indent='    ')
        print '  Actual:   %s' % binascii.hexlify(actual,)
        hexdump(actual, indent='    ')

def validate_read_he(expected, actual, msg):
    if expected != actual:
        print 'Failed %s' % msg
        print '  Expected; %s' % binascii.hexlify(expected,)
        hexdump(expected, indent='    ')
        print '  Actual:   %s' % binascii.hexlify(actual,)
        hexdump(actual, indent='    ')
        raise Exception('failed validate: %s' % msg)

def validate_readv_he(expecteds, actual, msg):
    if actual not in expecteds:
        print 'Failed %s' % msg
        for expected in expecteds:
            print '  Expected; %s' % binascii.hexlify(expected,)
            hexdump(expected, indent='    ')
        print '  Actual:   %s' % binascii.hexlify(actual,)
        hexdump(actual, indent='    ')
        raise Exception('failed validate: %s' % msg)
