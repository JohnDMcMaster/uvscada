'''
Timing accurate reset replay leading up to packet 167

biggest lead so far
    @@ -578,6 +577,7 @@
         # NOTE:: req max 4096 but got 3
         validate_read("\x00\x00\x00", buff, "packet 155/156")
         time.sleep(0.002)
    +    # WARNING: complete code -121 (EREMOTEIO)
         # Generated from packet 157/158
         buff = bulkRead(0x86, 0x0200)
         # NOTE:: req max 512 but got 4
    @@ -597,9 +597,10 @@
         # NOTE:: req max 4096 but got 3
         validate_read("\x00\x00\x00", buff, "packet 165/166")
         time.sleep(0.004)
    +    # WARNING: complete code -2 (ENOENT)
         # Generated from packet 167/168
         buff = bulkRead(0x86, 0x0200)
    -    # NOTE:: req max 512 but got 4
    -    validate_read("\x08\x16\x01\x00", buff, "packet 167/168")
    +    # NOTE:: req max 512 but got 0
    +    validate_read("", buff, "packet 167/168")
Why does a timeout cause ENOENT?
To try
    Make the earlier bulk request impossibly short timeout to see what error that generates
        tried but too short, can't race it
    Do another capture, fresh from power on, and verify flow is still the same
    











dmesg output
    # dmesg
    [372465.244124] usb 1-3: reset high-speed USB device number 21 using ehci_hcd
    [372465.548084] usb 1-3: reset high-speed USB device number 21 using ehci_hcd
    [372482.220093] usb 1-3: reset high-speed USB device number 21 using ehci_hcd
    [372483.468072] usb 1-3: reset high-speed USB device number 21 using ehci_hcd
no errors...


As far as I can tell the first one might be okay
due to differnet setting of URB_SHORT_NOT_OK between vmware and libusb
focus on ENOENT which is def an error



ENOENT
    http://libusb.6.n5.nabble.com/ENOENT-error-from-libusb-submit-transfer-td5747.html
    This happens when the endpoint address is wrong. Judging from a comment
    in your code, you are not too clear on which endpoint you should be
    using. You need to include your device descriptors (lsusb -v) for people
    to help you further. 



ENOENT
EREMOTEIO
what caused the first EREMOTEIO?


http://libusb.6.n5.nabble.com/ENOENT-on-read-from-device-td7270.html
    As far as I can see (going by the documentation in the kernel) -2
    (ENOENT) means "specified interface or endpoint does not exist or
    is not enabled". Now there's something in the 'dmesg' output for
    the device that looks a bit suspicious to me but which I am not
    sure if it's relevant: 

http://sourceforge.net/p/libusb/mailman/message/25635949/
    >> I gather that the difficulty is how to tell whether or not a submission
    >> failure represents an error.  The criterion is simple: If the errno
    >> value from the failed submission ioctl is EREMOTEIO then it's not an
    >> error (it's merely a rejection because the transer has already
    >> completed), otherwise it is.



From /usr/src/linux/Documentation/usb/error-codes.txt:
    -EREMOTEIO The data read from the endpoint did not fill the
    specified buffer, and URB_SHORT_NOT_OK was set in
    urb->transfer_flags.

did the windows request not set URB_SHORT_NOT_OK?

where are transfer flags specified?
    struct usbdevfs_urb {
	    unsigned char type;
	    unsigned char endpoint;
	    int status;
	    unsigned int flags;
	    void *buffer;
	    int buffer_length;
	    int actual_length;
	    int start_frame;
	    int number_of_packets;
	    int error_count;
	    unsigned int signr;	/* signal to be sent on completion,
				      or 0 if none should be sent. */
	    void *usercontext;
	    struct usbdevfs_iso_packet_desc iso_frame_desc[0];
    };
    is this the right data structure?
    no urb id...
    


flags
    #define USBDEVFS_URB_SHORT_NOT_OK	0x01
    #define USBDEVFS_URB_ISO_ASAP		0x02
    #define USBDEVFS_URB_BULK_CONTINUATION	0x04
    #define USBDEVFS_URB_NO_FSBR		0x20
    #define USBDEVFS_URB_ZERO_PACKET	0x40
    #define USBDEVFS_URB_NO_INTERRUPT	0x80


packet 158
    tmp.cap: -EREMOTEIO
    

usbrply bp1410_01_startup.cap --range 1:168  --sleep >bp1410_01_startup_tmp.py
usbrply tmp.cap --sleep >tmp.py

usbrply bp1410_18_startup_warm.cap --range 1:168  --sleep >bp1410_18_startup_warm.py
usbrply bp1410_19_startup_warm.cap --range 1:168  --sleep >bp1410_19_startup_warm.py
usbrply bp1410_20_startup_warm.cap --range 1:168  --sleep >bp1410_20_startup_warm.py




diff -u bp1410_01_startup_tmp.py tmp.py


GOAL: get the replay working correctly to get the original sequence
Verify current replays still give same sequence?

detailed packet 01 disassembly
1-4
    linux plug in
5-26
    linux enum 1
        ie linux_rst_seq.cap, a call to dev.resetDevice()
    1-26 identical between all full caps
27-28
    get descriptor not in reset seq
29-50
    linux enum 2
51-72
    fixme
73-94
    linux enum 3
95-96
    get descriptor not in reset seq
97-118
    linux enum 4
119-124
    fixme

125+: normal    
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

def setup(dev):
    # 1-4 linux plug in
    # nothing to do for this

    print 'plugin in begin sleep'
    time.sleep(4.599)
    print 'sleep done'
    
    
    # 5-26
    # linux enum 1
    dev.resetDevice()



    time.sleep(0.054)
    
    
    
    # 27-28 get descriptor not in reset seq
    # Generated from packet 27/28
    buff = dev.controlRead(0x80, 0x06, 0x0100, 0x0000, 64)
    # NOTE:: req max 64 but got 18
    validate_read("\x12\x01\x00\x02\xFF\xFF\xFF\x40\xB9\x14\x01\x00\x00\x00\x01\x02"
              "\x00\x01", buff, "packet 27/28")
    

    time.sleep(0.002)

    # 29-50 linux enum 2
    dev.resetDevice()
    

    time.sleep(0.062)



    # 51-72 fixme
    # Generated from packet 51/52
    buff = controlRead(0x80, 0x06, 0x0100, 0x0000, 18)
    validate_read("\x12\x01\x00\x02\xFF\xFF\xFF\x40\xB9\x14\x01\x00\x00\x00\x01\x02"
              "\x00\x01", buff, "packet 51/52")
    time.sleep(0.001)
    # Generated from packet 53/54
    buff = controlRead(0x80, 0x06, 0x0200, 0x0000, 9)
    validate_read("\x09\x02\x2E\x00\x01\x01\x00\xC0\x00", buff, "packet 53/54")
    # Generated from packet 55/56
    buff = controlRead(0x80, 0x06, 0x0200, 0x0000, 255)
    # NOTE:: req max 255 but got 46
    validate_read("\x09\x02\x2E\x00\x01\x01\x00\xC0\x00\x09\x04\x00\x00\x04\xFF\xFF"
              "\xFF\x00\x07\x05\x02\x02\x40\x00\x00\x07\x05\x04\x02\x40\x00\x00"
              "\x07\x05\x86\x02\x40\x00\x00\x07\x05\x88\x03\x40\x00\x05", buff, "packet 39/40")
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
    time.sleep(0.003)
    # Generated from packet 65/66
    buff = controlRead(0x80, 0x06, 0x0200, 0x0000, 9)
    validate_read("\x09\x02\x2E\x00\x01\x01\x00\xC0\x00", buff, "packet 65/66")
    time.sleep(0.001)
    
    # get descriptor sizes are different for low speed
    # 67 => 113
    # Generated from packet 67/68
    buff = controlRead(0x80, 0x06, 0x0200, 0x0000, 46)
    '''
    validate_read("\x09\x02\x2E\x00\x01\x01\x00\xC0\x00\x09\x04\x00\x00\x04\xFF\xFF"
              "\xFF\x00\x07\x05\x02\x02\x00\x02\x00\x07\x05\x04\x02\x00\x02\x00"
              "\x07\x05\x86\x02\x00\x02\x00\x07\x05\x88\x03\x40\x00\x05", buff, "packet 67/68")
    '''
    validate_read("\x09\x02\x2E\x00\x01\x01\x00\xC0\x00\x09\x04\x00\x00\x04\xFF\xFF"
              "\xFF\x00\x07\x05\x02\x02\x40\x00\x00\x07\x05\x04\x02\x40\x00\x00"
              "\x07\x05\x86\x02\x40\x00\x00\x07\x05\x88\x03\x40\x00\x05", buff, "packet 113/114")
    
    time.sleep(0.001)
    # Generated from packet 69/70
    controlWrite(0x00, 0x09, 0x0001, 0x0000, "")
    time.sleep(0.113)
    # Generated from packet 71/72
    buff = controlRead(0x80, 0x06, 0x0100, 0x0000, 18)
    validate_read("\x12\x01\x00\x02\xFF\xFF\xFF\x40\xB9\x14\x01\x00\x00\x00\x01\x02"
              "\x00\x01", buff, "packet 71/72")
    
    # end windows enum
    
  
  
    print 'windows enum => bpwin sleep'
    time.sleep(12.471)
    print 'sleep done'
    
    
    
    
    # begin bpwin
    
    
    
    # 73-94 linux enum 3
    dev.resetDevice()
    
    # this appeared in one capture but not others
    # unclear where it came from
    time.sleep(1.000)
    
    
    # 95-96 get descriptor not in reset seq
    # Generated from packet 95/96
    buff = controlRead(0x80, 0x06, 0x0100, 0x0000, 64)
    
    
    
    # 97-118 linux enum 4
    dev.resetDevice()
    
    
    time.sleep(0.094)


    
    # 119-124 fixme
    # Generated from packet 119/120
    buff = controlRead(0x80, 0x06, 0x0100, 0x0000, 18)
    validate_read("\x12\x01\x00\x02\xFF\xFF\xFF\x40\xB9\x14\x01\x00\x00\x00\x01\x02"
              "\x00\x01", buff, "packet 119/120")
    time.sleep(0.006)
    # Generated from packet 121/122
    buff = controlRead(0x80, 0x06, 0x0200, 0x0000, 9)
    validate_read("\x09\x02\x2E\x00\x01\x01\x00\xC0\x00", buff, "packet 121/122")
    time.sleep(0.002)
    # Generated from packet 123/124
    controlWrite(0x00, 0x09, 0x0001, 0x0000, "")
    time.sleep(0.004)
    
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
    time.sleep(0.004)
    # Generated from packet 127/128
    # packet 127: clear 0 (ENDPOINT HALT), interface: 0x02
    controlWrite(0x02, 0x01, 0x0000, 0x0002, "")
    time.sleep(0.002)
    
    
    load_fw(dev)
    time.sleep(0.002)
    
    
    
    # Generated from packet 141/142
    # Clear endpoint 0x86
    controlWrite(0x02, 0x01, 0x0000, 0x0086, "")
    time.sleep(0.001)    
    # Generated from packet 143/144
    # Clear endpoint 0x02
    controlWrite(0x02, 0x01, 0x0000, 0x0002, "")
    time.sleep(0.001)
    # Generated from packet 145/146
    # Clear endpoint 0x88
    controlWrite(0x02, 0x01, 0x0000, 0x0088, "")
    time.sleep(0.001)
        
    # Generated from packet 147/148
    # gxs note i2c_read: controlRead(0xC0, 0xB0, 0x0A, addr, n, timeout=self.timeout)
    # close but not quite the same?
    # maybe should try scanning address space
    # tried looping, always returns 000000 regardless of wIndex or wValue
    buff = controlRead(0xC0, 0xB0, 0x0000, 0x0000, 4096)
    # NOTE:: req max 4096 but got 3
    validate_read("\x00\x00\x00", buff, "packet 147/148")
    
    '''
    General pattern in this section:
    -Clear endpoints
    -Control in request.  Takes a while
    -Bulk read
    '''
    
    # Generated from packet 149/150
    # Clear endpoint 0x86
    controlWrite(0x02, 0x01, 0x0000, 0x0086, "")
    time.sleep(0.001)
    # Generated from packet 151/152
    # Clear endpoint 0x02
    controlWrite(0x02, 0x01, 0x0000, 0x0002, "")
    time.sleep(0.001)
    # Generated from packet 153/154
    # Clear endpoint 0x88
    controlWrite(0x02, 0x01, 0x0000, 0x0088, "")
    time.sleep(0.001)
    
    # Generated from packet 155/156
    buff = controlRead(0xC0, 0xB0, 0x0000, 0x0000, 4096)
    # NOTE:: req max 4096 but got 3
    print 'val 155: %s' % binascii.hexlify(buff)
    validate_read("\x00\x00\x00", buff, "packet 155/156")
    time.sleep(0.002)

    # Generated from packet 157/158
    # xxx: when is the earliest we can do this?
    # tried to race this to see how error code would differ
    #buff = bulkRead(0x86, 0x0200, timeout=1)
    buff = bulkRead(0x86, 0x0040)
    # NOTE:: req max 512 but got 4
    print 'val 157: %s' % binascii.hexlify(buff)
    validate_read("\x08\x16\x01\x00", buff, "packet 157/158")
    time.sleep(0.004)
    
    # Generated from packet 159/160
    # Clear endpoint 0x86
    controlWrite(0x02, 0x01, 0x0000, 0x0086, "")
    time.sleep(0.002)
    # Generated from packet 161/162
    # Clear endpoint 0x02
    controlWrite(0x02, 0x01, 0x0000, 0x0002, "")
    time.sleep(0.001)
    # Generated from packet 163/164
    # Clear endpoint 0x88
    controlWrite(0x02, 0x01, 0x0000, 0x0088, "")
    time.sleep(0.001)

    # Generated from packet 165/166
    buff = controlRead(0xC0, 0xB0, 0x0000, 0x0000, 4096)
    print 'val 165: %s' % binascii.hexlify(buff)
    # NOTE:: req max 4096 but got 3
    validate_read("\x00\x00\x00", buff, "packet 165/166")
    time.sleep(0.004)


    '''
    The very first symptom of incorrect reset sequence is this doesn't replay correctly

    oh yeah this is actually a timeout...
    Traceback (most recent call last):
      File "bp1410_rst.py", line 585, in <module>
        replay(dev)
      File "bp1410_rst.py", line 406, in replay
        buff = bulkRead(0x86, 0x0200, timeout=500)
      File "bp1410_rst.py", line 278, in bulkRead
        return dev.bulkRead(endpoint, length, timeout=timeout)
      File "/usr/local/lib/python2.7/dist-packages/usb1.py", line 1174, in bulkRead
        transferred = self._bulkTransfer(endpoint, data, length, timeout)
      File "/usr/local/lib/python2.7/dist-packages/usb1.py", line 1144, in _bulkTransfer
        raise libusb1.USBError(result)
    libusb1.USBError: LIBUSB_ERROR_TIMEOUT [-7]
    '''    
    # freezes
    print 'bulk read 167'
    try:
        # Generated from packet 167/168
        # reference is ***111 us***
        buff = bulkRead(0x86, 0x0040)
    except libusb1.USBError:
        print 'SHIT'
        raise
    print 'val 167: %s' % binascii.hexlify(buff)
    # NOTE:: req max 512 but got 4
    validate_read("\x08\x16\x01\x00", buff, "packet 167/168")
    time.sleep(0.002)
    
    print '!' * 80
    print 'Got through it!'

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
    
    # 1-124
    setup(dev)
    
    # 125+
    replay(dev)

