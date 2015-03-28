# https://github.com/vpelletier/python-libusb1
# Python-ish (classes, exceptions, ...) wrapper around libusb1.py . See docstrings (pydoc recommended) for usage.
import usb1
# Bare ctype wrapper, inspired from library C header file.
import libusb1
import struct
import binascii
import Image
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

'''
General notes

5328:2010 Dexis Platinum
5328:2020 Gendex small
5328:2030 Gendex large
'''

FRAME_SZ = 4972800

class GXS700:
    def __init__(self, usbcontext, dev):
        self.usbcontext = usbcontext
        self.dev = dev
        self.timeout = 0
    
    def _controlRead_mem(self, req, max_read, addr, dump_len):
        ret = ''
        i = 0
        while i < dump_len:
            l_this = min(dump_len - i, max_read)
            
            res = self.dev.controlRead(0xC0, 0xB0, req, addr + i, l_this, timeout=self.timeout)
            ret += res
            if len(res) != l_this:
                raise Exception("wanted 0x%04X bytes but got 0x%04X" % (l_this, len(res),))
            i += max_read
        return ret

    def _controlWrite_mem(self, req, max_write, addr, buff):
        i = 0
        while i < len(buff):
            this = buff[i:i+max_write]
            res = self.dev.controlWrite(0x40, 0xB0, req, addr + i, this, timeout=self.timeout)
            if res != len(this):
                raise Exception("wanted 0x%04X bytes but got 0x%04X" % (len(this), res,))
            i += max_write

    def hw_trig_arm(self):
        '''Enable taking picture when x-rays are above threshold'''
        self.dev.controlWrite(0x40, 0xB0, 0x2E, 0, '\x00')

    def hw_trig_disarm(self):
        '''Disable taking picture when x-rays are above threshold'''
        self.dev.controlWrite(0x40, 0xB0, 0x2F, 0, '\x00')

    def eeprom_r(self, addr, n):
        # FIXME: should be 0x0D?
        return self._controlRead_mem(0x0B, 0x80, addr, n)
        
    def eeprom_w(self, addr, buff):
        return self._controlWrite_mem(0x0C, 0x80, addr, buff)
    
    def flash_erase(self, addr):
        '''Erase a flash page'''
        self.dev.controlWrite(0x40, 0xB0, 0x11, addr, chr(addr), timeout=self.timeout)

    def sw_trig(self):
        '''Force taking an image without x-rays'''
        self.dev.controlWrite(0x40, 0xB0, 0x2b, 0, '\x00', timeout=self.timeout)

    def flash_r(self, addr, n):
        '''Read (FPGA?) flash'''
        return self._controlRead_mem(0x10, 0x100, addr, n)

    def flash_w(self, addr, buff):
        '''Write (FPGA?) flash'''
        return self._controlWrite_mem(0x0F, 0x100, addr, buff)
    
    def fpga_r(self, addr):
        '''Read FPGA register'''
        return self.fpga_rv(addr, 1)[0]
    
    def fpga_rv(self, addr, n):
        '''Read multiple consecutive FPGA registers'''
        ret = self.dev.controlRead(0xC0, 0xB0, 0x03, addr, n << 1, timeout=self.timeout)
        if len(ret) != n << 1:
            raise Exception("Didn't get all data")
        return struct.unpack('>' + ('H' * n), ret)

    def fpga_rsig(self):
        '''Read FPGA signature'''
        # 0x1234 expected
        return struct.unpack('>H', self.dev.controlRead(0xC0, 0xB0, 0x04, 0, 2, timeout=self.timeout))[0]
    
    def fpga_w(self, addr, v):
        '''Write an FPGA register'''
        self.fpga_wv(addr, [v])
    
    def fpga_wv(self, addr, vs):
        '''Write multiple consecutive FPGA registers'''
        self.dev.controlWrite(0x40, 0xB0, 0x02, addr,
                struct.pack('>' + ('H' * len(vs)), *vs),
                timeout=self.timeout)
    
    # FIXME: remove/hack
    def fpga_wv2(self, addr, vs):
        self.dev.controlWrite(0x40, 0xB0, 0x02, addr,
                vs,
                timeout=self.timeout)
    
    def trig_param_r(self):
        '''Write trigger parameter'''
        return self.dev.controlRead(0xC0, 0xB0, 0x25, 0, 6, timeout=self.timeout)

    def i2c_r(self, addr, n):
        '''Read I2C bus'''
        return self.dev.controlRead(0xC0, 0xB0, 0x0A, 0, n, timeout=self.timeout)

    def i2c_w(self, addr, buff):
        '''Write I2C bus'''
        self.dev.controlWrite(0x40, 0xB0, 0x0A, 0, buff, timeout=self.timeout)
    
    def tim_running(self):
        '''Get if timing analysis is running'''
        return self.fpga_r(0x2002)

    def rst(self):
        '''Reset the system'''
        # Reset is accomplished by writing a 1 to address 0xE600. 
        #self.mcu_rst(1)
        self.dev.controlWrite(0x40, 0xB0, 0xe600, 0, 1, timeout=self.timeout)
        
        # Start running by writing a 0 to that address. 
        #self.mcu_rst(0)
        self.dev.controlWrite(0x40, 0xB0, 0xe600, 0, 0, timeout=self.timeout)
        
    def mcu_rst(self, rst):
        '''Reset FX2'''
        self.dev.controlWrite(0x40, 0xB0, 0xe600, 0, chr(int(bool(rst))), timeout=self.timeout)

    def mcu_w(self, addr, v):
        '''Write FX2 register'''
        self.mcu_w(addr, [v])
    
    def mcu_wv(self, addr, vs):
        '''Write multiple consecutive FX2 registers'''
        # Revisit if over-simplified
        self.dev.controlWrite(0x40, 0xB0, addr, 0, 
                struct.pack('>' + ('B' * len(vs)), *vs),
                timeout=self.timeout)
    
    def fpga_off(self):
        '''Turn FPGA power off'''
        self.i2c_w(0x82, '\x03\x00')
        self.i2c_w(0x82, '\x01\x0E')
    
    def exp_cal_last(self):
        '''Get last exposure calibration'''
        buff = self.img_ctr_r(0x100)
        return ord(buff[6]) << 16 | ord(buff[5]) << 8 | ord(buff[4])

    def exp_since_manu(self):
        '''Get exposure since manual?'''
        buff = self.img_ctr_r(0x100)
        return ord(buff[2]) << 16 | ord(buff[1]) << 8 | ord(buff[0])

    def exp_ts(self):
        '''Get exposure timestamp as string'''
        return self.eeprom_r(self, 0x20, 0x17)

    def versions(self):
        '''Get versions as strings'''
        # 12 actual bytes...
        buff = bytearray(self.dev.controlRead(0xC0, 0xB0, 0x51, 0, 0x1C, timeout=self.timeout))
        print "MCU:     %s.%s.%s" % (buff[0], buff[1], buff[2] << 8 | buff[3])
        print 'FPGA:    %s.%s.%s' % (buff[4], buff[5], buff[6] << 8 | buff[7])
        print 'FGPA WG: %s.%s.%s' % (buff[8], buff[9], buff[10] << 8 | buff[11])
        
    def img_ctr_r(self, n):
        return self.dev.controlRead(0xC0, 0xB0, 0x40, 0, n, timeout=self.timeout)

    def img_wh(self):
        '''Get image (width, height)'''
        return struct.unpack('>HH', self.dev.controlRead(0xC0, 0xB0, 0x23, 0, 4, timeout=self.timeout))
    
    def img_wh_w(self, w, h):
        '''Set image width, height'''
        self.dev.controlWrite(0x40, 0xB0, 0x22, 0, struct.pack('>HH', w, h), timeout=self.timeout)
    
    def int_t_w(self, t):
        '''Set integration time'''
        self.dev.controlWrite(0x40, 0xB0, 0x2C, 0, struct.pack('>H', t), timeout=self.timeout)

    def int_time(self):
        '''Get integration time units?'''
        return struct.unpack('>HH', self.dev.controlRead(0xC0, 0xB0, 0x2D, 0, 4, timeout=self.timeout))[0]
        
    def img_ctr_rst(self):
        '''Reset image counter'''
        self.dev.controlWrite(0x40, 0xB0, 0x41, 0, '\x00')

    def exp_ts_w(self, ts):
        '''Write exposure timestamp'''
        if len(ts) != 0x17:
            raise Exception('Invalid timestamp')
        self.eeprom_w(0x20, ts)

    def flash_sec_act(self, sec):
        '''Activate flash sector?'''
        self.dev.controlWrite(0x40, 0xB0, 0x0E, sec, '')
    
    def cap_mode_w(self, mode):
        if not mode in (0, 5):
            raise Exception('Invalid mode')
        self.dev.controlWrite(0x40, 0xB0, 0x21, mode, '\x00')
        
    def trig_param_w(self, pix_clust_ctr_thresh, bin_thresh):
        '''Set trigger parameters?'''
        buff = bytearray()
        buff.append((pix_clust_ctr_thresh >> 8) & 0xFF)
        buff.append((pix_clust_ctr_thresh >> 0) & 0xFF)
        buff.append((pix_clust_ctr_thresh >> 8) & 0xFF)
        buff.append((pix_clust_ctr_thresh >> 0) & 0xFF)
        buff.append((pix_clust_ctr_thresh >> 24) & 0xFF)
        buff.append((pix_clust_ctr_thresh >> 16) & 0xFF)
        self.dev.controlWrite(0x40, 0xB0, 0x24, 0, buff)

    def state(self):
        '''Get camera state'''
        '''
        Observed states
        -0x01: no activity
        -0x02: short lived
        -0x04: longer lived than 2
        -0x08: read right before capture
        '''
        return ord(self.dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1))

    def error(self):
        '''Get error code'''
        return ord(self.dev.controlRead(0xC0, 0xB0, 0x0080, 0x0000, 1))

    def _cap_frame_bulk(self):
        '''Take care of the bulk transaction prat of capturing frames'''
        global bulk_start
        
        def async_cb(trans):
            '''
            # shutting down
            if self.:
                trans.close()
                return
            '''
            
            buf = trans.getBuffer()
            all_dat[0] += buf
            
            '''
            It will continue to return data but the data won't be valid
            '''
            if len(buf) == 0x4000 and len(all_dat[0]) < FRAME_SZ:
                trans.submit()
            else:
                remain[0] -= 1
    
        trans_l = []
        all_submit = FRAME_SZ
        i = 0
        while all_submit > 0:
            trans = self.dev.getTransfer()
            this_submit = max(all_submit - 0x4000, all_submit)
            this_submit = min(0x4000, this_submit)
            trans.setBulk(0x82, this_submit, callback=async_cb, user_data=None, timeout=1000)
            trans.submit()
            trans_l.append(trans)
            all_submit -= this_submit
    
        rx = 0
        remain = [len(trans_l)]
        all_dat = ['']
        while remain[0]:
            self.usbcontext.handleEventsTimeout(tv=0.1)
        
        for i in xrange(len(trans_l)):
            trans_l[i].close()
    
        all_dat = all_dat[0]
        return all_dat
    
    def cap_bin(self):
        '''Capture a raw binary frame, waiting for trigger'''
        i = 0
        while True:
            if i % 1000 == 0:
                print 'scan %d' % (i,)
            
            # Generated from packet 861/862
            #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
            #if args.verbose:
            #    print 'r1: %s' % binascii.hexlify(buff)
            #state = ord(buff)
            state = self.state()
            
            '''
            Observed states
            -0x01: no activity
            -0x02: short lived
            -0x04: longer lived than 2
            -0x08: read right before capture
            '''
            if state != 0x01:
                #print 'Non-1 state: 0x%02X' % state
                if state == 0x08:
                    print 'Go go go'
                    break
            
            # Generated from packet 863/864
            #buff = dev.controlRead(0xC0, 0xB0, 0x0080, 0x0000, 1)
            #if args.verbose:
            #    print 'r2: %s' % binascii.hexlify(buff)
            #validate_read("\x00", buff, "packet 863/864")
            if self.error():
                raise Exception('Unexpected error')

            i = i + 1

        
        # Generated from packet 783/784
        #buff = dev.controlRead(0xC0, 0xB0, 0x0040, 0x0000, 128)
        # NOTE:: req max 128 but got 8
        #validate_read("\x8E\x00\x00\x00\x58\x00\x00\x00", buff, "packet 783/784", True)
        print 'Img ctr: %s' % binascii.hexlify(self.img_ctr_r(128))
        
        # Generated from packet 785/786
        #buff = dev.controlRead(0xC0, 0xB0, 0x0040, 0x0000, 128)
        # NOTE:: req max 128 but got 8
        #validate_read("\x8E\x00\x00\x00\x58\x00\x00\x00", buff, "packet 785/786", True)
        print 'Img ctr: %s' % binascii.hexlify(self.img_ctr_r(128))
        
        # Generated from packet 787/788
        #buff = dev.controlRead(0xC0, 0xB0, 0x0080, 0x0000, 1)
        #validate_read("\x00", buff, "packet 787/788")
        e = self.error()
        if e:
            raise Exception('Unexpected error %s' % (e,))
        
        # Generated from packet 789/790
        #buff = self.dev.controlRead(0xC0, 0xB0, 0x0051, 0x0000, 28)
        # NOTE:: req max 28 but got 12
        #validate_read("\x00\x05\x00\x0A\x00\x03\x00\x06\x00\x04\x00\x05", buff, "packet 789/790")
        self.versions()
        
        # Generated from packet 791/792
        #buff = dev.controlRead(0xC0, 0xB0, 0x0004, 0x0000, 2)
        #validate_read("\x12\x34", buff, "packet 791/792")
        if self.fpga_rsig() != 0x1234:
            raise Exception("Invalid FPGA signature")

        return self._cap_frame_bulk()

    def cap_img(self, fn):
        '''Capture a decoded image to filename, waiting for trigger'''
        return self.decode(self.cap_bin())

    @staticmethod
    def decode(buff):
        '''Given bin return PIL image object'''
        height = 1850
        width = 1344
        depth = 2
        
        # no need to reallocate each loop
        img = Image.new("RGB", (width, height), "White")
        
        for y in range(height):
            line0 = buff[y * width * depth:(y + 1) * width * depth]
            for x in range(width):
                b0 = ord(line0[2*x + 0])
                b1 = ord(line0[2*x + 1])
                
                # FIXME: 16 bit pixel truncation to fit into png
                #G = (b1 << 8) + b0
                G = b1
                
                # In most x-rays white is the part that blocks the x-rays
                # however, the camera reports brightness (unimpeded x-rays)
                # compliment to give in conventional form per above
                G = 0xFF - G
                
                img.putpixel((x, y), (G, G, G))
        return img
