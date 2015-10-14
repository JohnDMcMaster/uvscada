import libusb1
import binascii

from util import hexdump, str2hex

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

do_exception = True
do_hexdump = True
do_str2hex = True

def validate_read(expected, actual, msg):
    validate_readv([expected], actual, msg)

def validate_readv(expecteds, actual, msg):
    if type(actual) is int:
        return validate_readiv(expecteds, actual, msg)
    
    if actual not in expecteds:
        print 'Failed %s' % msg
        for expected in expecteds:
            if do_str2hex:
                print '  Expected; %d' % (len(expected),)
                print str2hex(expected, prefix='    ')
            else:
                print '  Expected:   %d %s' % (len(expected), binascii.hexlify(expected))
            if do_hexdump:
                hexdump(expected, indent='    ')
        if do_str2hex:
            print '  Actual; %d' % (len(actual),)
            print str2hex(actual, prefix='    ')
        else:
            print '  Actual:   %d %s' % (len(actual), binascii.hexlify(actual))
        if do_hexdump:
            hexdump(actual, indent='    ')
        if do_exception:
            raise Exception('failed validate: %s' % msg)

def validate_readiv(expecteds, actual, msg):
    if actual not in expecteds:
        print 'Failed %s' % msg
        for expected in expecteds:
            print '  Expected; %d 0x%04X' % (expected, expected)
        print '  Actual; %d 0x%04X' % (actual, actual)
        if do_exception:
            raise Exception('failed validate: %s' % msg)
