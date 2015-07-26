import usb1
import math
import binascii
import libusb1
import sys
        
'''
int self.dev.controlWrite(usb_dev_handle *dev, int requesttype, int request, int value, int index, char *bytes, int size, int timeout)
def controlWrite(self, request_type, request, value, index, data, timeout=0):
def controlRead(self, request_type, request, value, index, length, timeout=0):
'''
def validate_read(expected, actual, msg):
    if expected != actual:
        print 'Failed %s' % msg
        print '  Expected %s' % binascii.hexlify(expected,)
        print '  Actual:   %s' % binascii.hexlify(actual,)
        raise Exception('failed validate: %s' % msg)

class Tester:
    def __init__(self, rawdev):
        self.rawdev = rawdev
        self.dev = self.rawdev.open()
    
    def dev_init(self):
        def controlRead(request_type, request, value, index, length):
            return self.dev.controlRead(request_type, request, value, index, length, timeout=500)
            
        def controlWrite(requestType, request, value, index, bytes):
            self.dev.controlWrite(requestType, request, value, index, bytes, timeout=500)

        def regw(_value, _index):
            if val_reply(controlRead(0xC0, 0x0B, _value, _index, 1)):
                raise Exception("Failed req(0xC0, 0x%02X, 0x%04X, 0x%04X" % (_request, _value, _index))
                
        def val_reply(reply):
            if (len(reply) != 1):
                raise Exception("Bad reply size %u" % size)
            if ord(reply[0]) != 0x08:
                raise Exception("Bad reply 0x%02X" % ord(reply[0]))
        
        width = 1600
        height = 1200

        # Reference packet numbers are from 01_3264_2448.cap
        
        # Set encryption key of 0x0000 (no encryption)
        val_reply(controlRead(0xC0, 0x16, 0x0000, 0x0000, 2))
        
        # Packets 158/159
        if 0:
            print "Setting alt"
            if libusb_set_interface_alt_setting (g_camera.handle, 0, 1):
                raise Exception("Failed to set alt setting")

        # Next (172-175) does some sort of challenge / response to make sure its not cloned hardware
        # It seems to be optional and I don't care to learn how it works since
        # I want to work with their hardware, not clone it
        # bmRequestType=0x40, bRequest=0x59, wValue=0x0000, wIndex=0, wLength=0x0010
        # bmRequestType=0xC0, bRequest=0x79, wValue=0x0000, wIndex=0, wLength=0x0010
        
        
        # The following transactions are constant (no encryption)
        # Packets 176-183
        controlWrite(0x40, 0x01, 0x0001, 0x000F, '')
        controlWrite(0x40, 0x01, 0x0000, 0x000F, '')
        controlWrite(0x40, 0x01, 0x0001, 0x000F, '')
        validate_read("\xE6\x0D\x00\x00", controlRead(0xC0, 0x20, 0x0000, 0x0000, 4), "packet 182/183")
        
        '''
        184/185 is a large read, possibly EEPROM configuration (ex: bad pixel) data
        Skip it since we don't know what to do with it
        Its partially encrypted
        # bmRequestType=0xC0, bRequest=0x20, wValue=0x0000, wIndex=0, wLength=0x060E
        '''
        
        #Now begins the encrypted packets (186-263)


        # Unknown purpose
        regw(0x0100, 0x0103)
        regw(0x0000, 0x0100)
        regw(0x0100, 0x0104)
        regw(0x0004, 0x0300)
        regw(0x0001, 0x0302)
        regw(0x0008, 0x0308)
        regw(0x0001, 0x030A)
        regw(0x0004, 0x0304)
        regw(0x0040, 0x0306)
        regw(0x0000, 0x0104)
        regw(0x0100, 0x0104)

        # Registers have an unknown purpose
        #} else if (width == 1600) {
        regw(0x009C, 0x0344)
        regw(0x0D19, 0x0348)
        regw(0x0068, 0x0346)
        regw(0x09C5, 0x034A)
        regw(0x06C3, 0x3040)
        
        regw(0x0000, 0x0400)
        regw(0x0010, 0x0404)
        
        
        INDEX_WIDTH        = 0x034C
        INDEX_HEIGHT        = 0x034E
        # regw(0x0CC0, 0x034C)
        regw(width, INDEX_WIDTH)
        # regw(0x0990, 0x034E)
        regw(height, INDEX_HEIGHT)
        
        
        # Unknown purpose
        #} else if (width == 1600) {
        regw(0x0640, 0x300A)
        regw(0x0FA0, 0x300C)
        
        # Unknown purpose
        regw(0x0000, 0x0104)
        regw(0x0301, 0x31AE)
        regw(0x0805, 0x3064)
        regw(0x0071, 0x3170)
        regw(0x10DE, 0x301A)
        regw(0x0000, 0x0100)
        regw(0x0010, 0x0306)
        regw(0x0100, 0x0100)
        
        
        
        exposure_ms = 350
        wValue = 0
        #} else if (width == 1600) {
        wValue = exposure_ms * 3
        # Wonder if theres a good reason for sending it twice
        regw(wValue, 0x3012)
        regw(wValue, 0x3012)
        
        regw(0x0100, 0x0104)
        
        
        # Range 0x1000 (nothing) to 0x11FF (highest)
        GAIN_BASE           = 0x1000
        GAIN_MAX            = 0x01FF
        INDEX_GAIN_GTOP     = 0x3056
        INDEX_GAIN_B        = 0x3058
        INDEX_GAIN_R        = 0x305A
        INDEX_GAIN_GBOT     = 0x305C
        gain = 1.5
        GAIN_BASE           = 0x1000
        GAIN_MAX            = 0x01FF
            
        regw(0x01FF, INDEX_GAIN_GTOP)
        regw(0x1100, INDEX_GAIN_B)
        regw(0x1100, INDEX_GAIN_R)
        regw(0x1100, INDEX_GAIN_GBOT)
        
        
        regw(0x0000, 0x0104)

        # Omitted this by accident, does not work without it
        controlWrite(0x40, 0x01, 0x0003, 0x000F, '')
        
        return 0


    
    def test(self):
        print 'Init start'
        self.dev_init()
        print 'Init passed!'
    
        print 'Running test'
        dev = self.dev

        MT9E001_X_OUTPUT_SIZE = 0x034C
        MT9E001_Y_OUTPUT_SIZE = 0x034E
        
        print
        print
        print
        #print '0x%04X' % 1600
        #print '0x%04X' % 1200
        '''
        
        
        10 / 0x0A
        Reply: ffff08
        read sensor register?
        returns 3 bytes
        sort of reasonable as a read (16 bit + valid bit)
        except that the value is wrong....
        maybe need to issue start/stop bit somehow?
        

        11 / 0x0B
        Reply: 08
        requests to write sensor register

        22 / 0x16
        Reply: 08
        the request used to write the encryption key
        must go to fx2 reg

        23 / 0x17
        Reply: 08
        
        0x41
        0x42
        lots of others pre a0 return 0 but ok
        
        0xA0
        Reply: 73747374
        somewhat repetitive but not entirely
        can read n data, not just 4
        
        9f same responses
        
        
        '''
        if 0:
            for i in xrange(0x9F, 0x100):
                try:
                    buff = self.dev.controlRead(0xC0, i, 0x034C, 0x034C, 16, timeout=500)
                except libusb1.USBError:
                    print '0x%02X: failed' % (i,)
                    continue
                print '0x%02X: reply %s' % (i, binascii.hexlify(buff))
                sys.exit(1)
        
        # def controlRead(self, request_type, request, value, index, length, timeout=0):
        if 0:
            # evidently value is ignored
            
            # Reply: 2c0108
            buff = self.dev.controlRead(0xC0, 10, 0x0000, 0x0000, 4, timeout=500)
            print 'Reply: %s' % binascii.hexlify(buff)
            
            # Reply: ffff08
            buff = self.dev.controlRead(0xC0, 10, 0x0000, 0x034C, 4, timeout=500)
            print 'Reply: %s' % binascii.hexlify(buff)
        
        if 1:
            print
            print
            print
            '''
            all 2c0108
            '''
            for i in xrange(0x10000):
                # Reply: ffff08
                buff = self.dev.controlRead(0xC0, 10, i, 0x0000, 16, timeout=500)
                print '0x%04X: %s' % (i, binascii.hexlify(buff))

        if 0:
            print
            print
            print
            '''
            0x0000: 2c0108
            0x001A: 000008
            All others: ffff08
            '''
            for i in xrange(0x10000):
                # Reply: ffff08
                buff = self.dev.controlRead(0xC0, 10, 0x0000, i, 16, timeout=500)
                print '0x%04X: %s' % (i, binascii.hexlify(buff))

        if 0:
            print
            print
            print
            '''
            all 08
            '''
            for i in xrange(0x10000):
                # Reply: ffff08
                buff = self.dev.controlRead(0xC0, 0x17, 0x0000, i, 16, timeout=500)
                print '0x%04X: %s' % (i, binascii.hexlify(buff))
        
        
        
        
        if 0:
            '''
            obviously reading out memory, address + offset
            not the register but interesting
            the original code reads out 4 bytes from the beginning
            no idea what it does with them
            index has no effect
            
            ffff vector table? no 8051 02 ljmp, whats sjmp?
            sample dump:
            0x0000 reply: e60d000032210d0000425a6839314159
            0x0010 reply: 265359613a2efa0002c2ffffffffffff
            0x0020 reply: ffffffffffffffffffffffffffffffff
            0x0030 reply: ffffffffffffffffffffffff60087f00
            0x0040 reply: 07d07bea55ef92aad6c6b46cbacdb4ea
            0x0050 reply: 632a7a68c8f50c81a130027a9a301a09
            0x0060 reply: a69919a4698268c4c8c9e9326d4c13d1
            0x0070 reply: 321a18118d4d1ea64f4020c134c464c0
            0x0080 reply: 40c264c194d0da0344f204f26899a8c4
            0x0090 reply: c0329a32643a9e8d01a4d3d4cd34c86a
            0x00A0 reply: 3268d3d09e43411a7a8f287a8d1994d0
            0x00B0 reply: c98011a7a4d327a8d1a604699069b51e
            0x00C0 reply: 14c4d3d344f28f519814c4f51ea7a8f4
            0x00D0 reply: 8d3d099a8c868613464c099a46d01323
            0x00E0 reply: 403d40ca9fa0993053d326113023d4da
            0x00F0 reply: 86351e9a8d34c9a3c2351a69e84c68d2
            '''
            print
            print
            print
            # validate_read("\xE6\x0D\x00\x00", controlRead(0xC0, 0x20, 0x0000, 0x0000, 4), "packet 182/183")
            for i in xrange(0, 0x10000, 16):
                buff = self.dev.controlRead(0xC0, 0x20, i, 0x0000, 16, timeout=500)
                print '0x%04X reply: %s' % (i, binascii.hexlify(buff))
            print
            print

        if 0:
            # 	pr_devel("reg_w bReq=0x0B, bReqT=0xC0, wVal=0x%04X, wInd=0x%04X",
            # def controlRead(self, request_type, request, value, index, length, timeout=0):
            buff = dev.controlRead(0xC0, 0x0B, 1600, MT9E001_X_OUTPUT_SIZE, 100)
            print 'Reply: %s' % binascii.hexlify(buff)
            
            print 'Packet replay complete'
        

if __name__ == "__main__":
    usbcontext = usb1.USBContext()
    for _i, dev in enumerate(usbcontext.getDeviceList(skip_on_error=True)):
        vid = dev.getVendorID()
        pid = dev.getProductID()
        if vid == 0x0547 and pid == 0x6801:
            print 'Found device'
            print 'Bus %03i Device %03i: ID %04x:%04x' % (
                dev.getBusNumber(),
                dev.getDeviceAddress(),
                vid,
                pid)
            t = Tester(dev)
    t.test()

