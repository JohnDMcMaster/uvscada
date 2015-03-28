'''
USB 2.0 max speed: 480 Mbps => 60 MB/s
frame size: 4972800 bytes ~= 5 MB/s
never going to get faster than 12 frames per second from data bottleneck
integration time and other issues will make it actually take much longer

max is about 1/3 fps
State 2 to state 4
    frame1.cap: 10.547345 - 10.237953 = 0.309392
    frame2.cap: 4.093158 - 3.784668 =   0.30849
state 4 to state 8
    frame1.cap: 12.547843 - 10.547345 = 2.000498 seconds
    frame2.cap: 6.092412 - 4.093158 = 1.999254 seconds
bulk transfer
    not checked
from state 2 to end of bulk
    frame1.cap: 13.221687 - 10.237953 = 2.983734
    frame2.cap: 6.773520 - 3.784668 = 2.988852

Currently this code takes about 4.7 sec to capture an image
(with bulking taking much longer than it should)
we should be able to get it down to at least 3
'''

# https://github.com/vpelletier/python-libusb1
# Python-ish (classes, exceptions, ...) wrapper around libusb1.py . See docstrings (pydoc recommended) for usage.
import usb1
# Bare ctype wrapper, inspired from library C header file.
import libusb1
import binascii
import sys
import argparse
import time
from util import open_dev
import os
import gxs700

def validate_read(expected, actual, msg, ignore_errors=False):
    if expected != actual:
        print 'Failed %s' % msg
        print '  Expected; %s' % binascii.hexlify(expected,)
        print '  Actual:   %s' % binascii.hexlify(actual,)
        if not ignore_errors:
            raise Exception('failed validate: %s' % msg)

def replay_449_768(gxs):
    if gxs.img_wh() != (1344, 1850):
        raise Exception("Unexpected w/h")
    
    '''
    FIXME: fails verification if already ran
    Failed packet 453/454
      Expected; 0000
      Actual:   0001
    '''
    if gxs.fpga_r(0x2002) != 0x0000:
        print "WARNING: bad FPGA read"
    
    if gxs.fpga_rsig() != 0x1234:
        raise Exception("Invalid FPGA signature")
    
    gxs._setup_fpga1()
    
    if gxs.fpga_rsig() != 0x1234:
        raise Exception("Invalid FPGA signature")
    
    gxs._setup_fpga2()
    
    gxs.fpga_w(0x2002, 0x0001)
    v = gxs.fpga_r(0x2002)
    if v != 0x0001:
        raise Exception("Bad FPGA read: 0x%04X" % v)
    
    # XXX: why did the integration time change?
    gxs.int_t_w(0x0064)
    
    '''
    FIXME: fails verification if already ran
      Expected; 01
      Actual:   02
    '''
    if gxs.state() != 1:
        print 'WARNING: unexpected state'
    
    #gxs.img_wh_w(1344, 1850)
    
    gxs.flash_sec_act(0x0000)

def cleanup(gxs):
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    if gxs.error():
        raise Exception('Unexpected error')
    
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    if gxs.error():
        raise Exception('Unexpected error')
    
    gxs.eeprom_w(0x0020, "2015/03/19-21:44:43:087")
    
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    if gxs.error():
        raise Exception('Unexpected error')
    
    gxs.int_t_w(0x02BC)
    
    gxs.cap_mode_w(0)

    gxs.hw_trig_arm()
    
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    if gxs.error():
        raise Exception('Unexpected error')
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    gxs.img_wh_w(1344, 1850)
    
    gxs.flash_sec_act(0x0000)
    
    if gxs.img_wh() != (1344, 1850):
        raise Exception("Unexpected w/h")
    
    
    if gxs.state() != 1:
        raise Exception('Unexpected state')

    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    if gxs.error():
        raise Exception('Unexpected error')
    
    if gxs.state() != 1:
        raise Exception('Unexpected state')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('--number', '-n', type=int, default=1, help='number to take')
    args = parser.parse_args()

    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext)
    gxs = gxs700.GXS700(usbcontext, dev)
    
    state = gxs.state()
    print 'Init state: %d' % state
    if state == 0x08:
        print 'Flusing stale capture'
        gxs._cap_frame_bulk()
    elif state != 0x01:
        print 'Not idle, refusing to setup'
        sys.exit(1)

    gxs.img_wh_w(1344, 1850)
    
    gxs.flash_sec_act(0x0000)

        
    replay_449_768(gxs)

    if gxs.img_wh() != (1344, 1850):
        raise Exception("Unexpected w/h")
    
    
    '''
    FIXME: fails verification if already plugged in
    '''
    if gxs.state() != 1:
        print 'WARNING: unexpected state'

    gxs.img_wh_w(1344, 1850)
    
    gxs.flash_sec_act(0x0000)
    
    
    if gxs.img_wh() != (1344, 1850):
        raise Exception("Unexpected w/h")
    
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    gxs.img_wh_w(1344, 1850)
    
    gxs.flash_sec_act(0x0000)


    if gxs.img_wh() != (1344, 1850):
        raise Exception("Unexpected w/h")
    
    
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    gxs.int_t_w(0x02BC)
    
    gxs.cap_mode_w(0)
    
    gxs.hw_trig_arm()
    
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    if gxs.error():
        raise Exception('Unexpected error')
    
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    
    '''
    wonder what this means...
    repeatedly fails verification
    what about other captures?
    
    Failed packet 829/830
      Expected; 8700000051000000
      Actual:   910000005b000000

    Failed packet 829/830
      Expected; 8700000051000000
      Actual:   910000005b000000
  
    frame1.cap
        validate_read("\x8E\x00\x00\x00\x58\x00\x00\x00", buff, "packet 783/784")
    cap1.cap
        validate_read("\x87\x00\x00\x00\x51\x00\x00\x00", buff, "packet 829/830")
    cap2.cap
        validate_read("\x87\x00\x00\x00\x51\x00\x00\x00", buff, "packet 829/830")
    '''
    # Generated from packet 829/830
    buff = dev.controlRead(0xC0, 0xB0, 0x0040, 0x0000, 128)
    # NOTE:: req max 128 but got 8
    # FIXME
    validate_read("\x87\x00\x00\x00\x51\x00\x00\x00", buff, "packet 829/830", True)
    
    # Generated from packet 831/832
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    #validate_read("\x01", buff, "packet 831/832", True)
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    # Generated from packet 833/834
    buff = dev.controlRead(0xC0, 0xB0, 0x0040, 0x0000, 128)
    # NOTE:: req max 128 but got 8
    # FIXME
    validate_read("\x87\x00\x00\x00\x51\x00\x00\x00", buff, "packet 833/834", True)
    
    if gxs.error():
        raise Exception('Unexpected error')
    
    # Generated from packet 837/838
    buff = dev.controlRead(0xC0, 0xB0, 0x0051, 0x0000, 28)
    # NOTE:: req max 28 but got 12
    validate_read("\x00\x05\x00\x0A\x00\x03\x00\x06\x00\x04\x00\x05", buff, "packet 837/838")
    
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    if gxs.error():
        raise Exception('Unexpected error')
    
    gxs.img_wh_w(1344, 1850)
    gxs.flash_sec_act(0x0000)
    if gxs.img_wh() != (1344, 1850):
        raise Exception("Unexpected w/h")

    
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    fn = ''
    
    taken = 0
    imagen = 0
    while os.path.exists('capture_%03d.bin' % imagen):
        imagen += 1
    print 'Taking first image to %s' % ('capture_%03d.bin' % imagen,)
    
    while taken < args.number:
        print
        print
        print
        print 'Requesting next image...'
        imgb = gxs.cap_bin()
        
        fn = 'capture_%03d.bin' % imagen
        print 'Writing %s' % fn
        open(fn, 'w').write(imgb)

        fn = 'capture_%03d.png' % imagen
        print 'Decoding %s' % fn
        img = gxs700.GXS700.decode(imgb)
        print 'Writing %s' % fn
        img.save(fn)

        taken += 1
        imagen += 1

        cleanup(gxs)

