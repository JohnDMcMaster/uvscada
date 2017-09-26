# https://github.com/vpelletier/python-libusb1
# Python-ish (classes, exceptions, ...) wrapper around libusb1.py . See docstrings (pydoc recommended) for usage.
import usb1
# Bare ctype wrapper, inspired from library C header file.
import libusb1
import struct
import binascii
from PIL import Image
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import sys

import gxs700_fpga

'''
in many cases index and length are ignored
if you request less it will return a big message anyway, causing an overflow exception

19.5 um pixels

General notes

5328:2010 Dexis Platinum
5328:2020 Gendex small
5328:2030 Gendex large
'''

# Wraps around after 0x2000
EEPROM_SZ = 0x2000
# don't think this is setup correctly
# is there not more?
# where did 0x800 come from?
FLASH_SZ = 0x10000
FLASH_PGS = FLASH_SZ / 0x100

WH_SM = (1040, 1552)
WH_LG = (1344, 1850)

# 16 bit image
SZ_SM = 2 * WH_SM[0] * WH_SM[1]
SZ_LG = 2 * WH_LG[0] * WH_LG[1]

# enum
SIZE_SM = 1
SIZE_LG = 2

def sz_wh(sz):
    if sz == SZ_LG:
        return WH_LG
    elif sz == SZ_SM:
        return WH_SM
    else:
        print SZ_SM, SZ_LG
        raise ValueError("Bad buffer size %s" % sz)

def decode(buff, wh=None):
    '''Given bin return PIL image object'''
    # FIXME: hack to make widthwise so it fits on screen better
    depth = 2
    width, height = wh or sz_wh(len(buff))
    buff = bytearray(buff)

    # no need to reallocate each loop
    img = Image.new("I", (height, width), "White")

    for y in range(height):
        line0 = buff[y * width * depth:(y + 1) * width * depth]
        for x in range(width):
            b0 = line0[2*x + 0]
            b1 = line0[2*x + 1]

            G = (b1 << 8) + b0
            # optional 16-bit pixel truncation to turn into 8-bit PNG
            # G = b1

            # In most x-rays white is the part that blocks the x-rays
            # however, the camera reports brightness (unimpeded x-rays)
            # compliment to give in conventional form per above
            G = 0xFFFF - G

            img.putpixel((y, x), G)
    return img

class GXS700:
    '''
    Size 1: small
    Size 2: large
    '''
    def __init__(self, usbcontext=None, dev=None, verbose=False, init=True, size=2):
        self.verbose = verbose
        self.usbcontext = usbcontext
        self.dev = dev
        self.timeout = 0
        self.wait_trig_cb = lambda: None
        self.set_size(size)
        if init:
            self._init()

    def set_size(self, size):
        self.size = size
        self.WH = {
            1: WH_SM,
            2: WH_LG,
        }[size]
        # 16 bit image
        # LG: 4972800
        self.FRAME_SZ = 2 * self.WH[0] * self.WH[1]

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

    def eeprom_r(self, addr=0, n=EEPROM_SZ):
        # FIXME: should be 0x0D?
        # 0x0B seems to work as well
        # self.dev.controlRead(0xC0, 0xB0, req, addr + i, l_this, timeout=self.timeout)
        if addr + n > EEPROM_SZ:
            raise ValueError("Address out of range: 0x%04X > 0x%04X" % (addr + n, EEPROM_SZ))
        return self._controlRead_mem(0x0B, 0x80, addr, n)

    def eeprom_w(self, addr, buff):
        if addr + len(buff) > EEPROM_SZ:
            raise ValueError("Address out of range: 0x%04X > 0x%04X" % (addr + len(buff), EEPROM_SZ))
        return self._controlWrite_mem(0x0C, 0x20, addr, buff)

    '''
    Note that R/W address is in bytes except erase which specifies a 256 byte page offset
    '''

    def flash_r(self, addr=0, n=FLASH_SZ):
        '''Read (FPGA?) flash'''
        if addr + n > FLASH_SZ:
            raise ValueError("Address out of range: 0x%04X > 0x%04X" % (addr + n, FLASH_SZ))
        return self._controlRead_mem(0x10, 0x100, addr, n)

    def flash_erase(self, page):
        '''Erase a flash page'''
        if page > FLASH_PGS:
            raise ValueError("Page out of range: 0x%02X > 0x%02X" % (page, FLASH_PGS))
        self.dev.controlWrite(0x40, 0xB0, 0x11, page, chr(page), timeout=self.timeout)

    def flash_erase_all(self, verbose=True):

        for page in xrange(FLASH_PGS):
            self.flash_erase(page)
            if verbose:
                sys.stdout.write('.')
                sys.stdout.flush()
        if verbose:
            print

    def flash_w(self, addr, buff):
        '''Write (FPGA?) flash'''
        #if addr + len(buff) > FLASH_SZ:
        #    raise ValueError("Address out of range: 0x%04X > 0x%04X" % (addr + len(buff), EEPROM_PGS))
        self._controlWrite_mem(0x0F, 0x100, addr, buff)
        #self._controlWrite_mem(0x0F, 0x10, addr, buff)

    def fpga_r(self, addr):
        '''Read FPGA register'''
        return self.fpga_rv(addr, 1)[0]

    def fpga_rv(self, addr, n):
        '''Read multiple consecutive FPGA registers'''
        ret = self.dev.controlRead(0xC0, 0xB0, 0x03, addr, n << 1, timeout=self.timeout)
        if len(ret) != n << 1:
            raise Exception("Didn't get all data")
        return struct.unpack('>' + ('H' * n), ret)

    def fpga_rsig(self, decode=True):
        '''Read FPGA signature'''
        '''
        index (0) is ignored
        size is ignored
        '''
        # 0x1234 expected
        buff = self.dev.controlRead(0xC0, 0xB0, 0x04, 0, 2, timeout=self.timeout)
        if not decode:
            return buff
        return struct.unpack('>H', buff)[0]

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
        '''Read trigger parameter'''
        # index, len ignored
        return self.dev.controlRead(0xC0, 0xB0, 0x25, 0, 6, timeout=self.timeout)

    def i2c_r(self, addr, n):
        '''Read I2C bus'''
        return self.dev.controlRead(0xC0, 0xB0, 0x0A, addr, n, timeout=self.timeout)

    def i2c_w(self, addr, buff):
        '''Write I2C bus'''
        self.dev.controlWrite(0x40, 0xB0, 0x0A, addr, buff, timeout=self.timeout)

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

    # FIXME: unclear if these are right
    def mcu_w(self, addr, v):
        '''Write FX2 register'''
        self.mcu_wv(addr, [v])

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
        return self.eeprom_r(0x20, 0x17)

    def versions(self, decode=True):
        # index, length ignored
        buff = self.dev.controlRead(0xC0, 0xB0, 0x51, 0, 0x1C, timeout=self.timeout)
        if not decode:
            return buff
        buff = bytearray(buff)
        print "MCU:     %s.%s.%s" % (buff[0], buff[1], buff[2] << 8 | buff[3])
        print 'FPGA:    %s.%s.%s' % (buff[4], buff[5], buff[6] << 8 | buff[7])
        print 'FGPA WG: %s.%s.%s' % (buff[8], buff[9], buff[10] << 8 | buff[11])

    def img_ctr_r(self, n=8):
        # think n is ignored
        return self.dev.controlRead(0xC0, 0xB0, 0x40, 0, n, timeout=self.timeout)

    '''
    w/h: 1, 1 at boot
    how to inteligently set?
    GXS700-lg: 1344w x 1850h
        0x540 x 0x73a
    but I'm told Windows app captures a different size

    calibration files also come in unexpected resolutions:
    .flf:      1346w x 1700h
    .dfm:      1352w x 1700h
    '''

    def img_wh(self):
        '''Get image (width, height)'''
        # length, index ignored
        return struct.unpack('>HH', self.dev.controlRead(0xC0, 0xB0, 0x23, 0, 4, timeout=self.timeout))

    def img_wh_w(self, w, h):
        '''Set image width, height'''
        self.dev.controlWrite(0x40, 0xB0, 0x22, 0, struct.pack('>HH', w, h), timeout=self.timeout)

    def int_t_w(self, t):
        '''Set integration time'''
        self.dev.controlWrite(0x40, 0xB0, 0x2C, 0, struct.pack('>H', t), timeout=self.timeout)

    def int_time(self):
        '''Get integration time (in ms?)'''
        buff = self.dev.controlRead(0xC0, 0xB0, 0x2D, 0, 4, timeout=self.timeout)
        return struct.unpack('>H', buff)[0]

    def img_ctr_rst(self):
        '''Reset image counter'''
        self.dev.controlWrite(0x40, 0xB0, 0x41, 0, '\x00')

    def exp_ts_w(self, ts):
        '''Write exposure timestamp'''
        if len(ts) != 0x17:
            raise Exception('Invalid timestamp')
        self.eeprom_w(0x20, ts)

    def set_act_sec(self, sec):
        '''Activate flash sector?'''
        self.dev.controlWrite(0x40, 0xB0, 0x0E, sec, '')

    def cap_mode_w(self, mode):
        if not mode in (0, 5):
            raise Exception('Invalid mode')
        self.dev.controlWrite(0x40, 0xB0, 0x21, mode, '\x00')

    def trig_param_w(self, pix_clust_ctr_thresh, bin_thresh):
        '''Set trigger parameters?'''
        # FIXME: looks like I messed something up here
        # bin_thresh is unused
        buff = bytearray()
        buff.append((pix_clust_ctr_thresh >> 8) & 0xFF)
        buff.append((pix_clust_ctr_thresh >> 0) & 0xFF)
        buff.append((bin_thresh >> 8) & 0xFF)
        buff.append((bin_thresh >> 0) & 0xFF)
        buff.append((bin_thresh >> 24) & 0xFF)
        buff.append((bin_thresh >> 16) & 0xFF)
        self.dev.controlWrite(0x40, 0xB0, 0x24, 0, buff)

    def sw_trig(self):
        '''Force taking an image without x-rays.  Takes a few seconds'''
        self.dev.controlWrite(0x40, 0xB0, 0x2b, 0, '\x00', timeout=self.timeout)

    def state(self):
        '''Get camera state'''
        '''
        Observed states
        -0x01: no activity
        -0x02: short lived
        -0x04: longer lived than 2
        -0x08: read right before capture

        index, length ignored
        '''
        return ord(self.dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1))

    def error(self):
        '''Get error code'''
        # index, len ignored
        return ord(self.dev.controlRead(0xC0, 0xB0, 0x0080, 0x0000, 1))

    '''
    ***************************************************************************
    High level functionality
    ***************************************************************************
    '''

    def chk_wh(self):
        v = self.img_wh()
        if v != self.WH:
            if 1:
                print 'got wh', v
                return
            raise Exception("Unexpected w/h: %s" % (v,))

    def _init(self):
        #self.rst()

        '''
        already config 1
        if self.size == 1:
            print 'set config'
            print 'before: %s' % self.dev.getConfiguration()
            self.dev.setConfiguration(1)
            print 'after: %s' % self.dev.getConfiguration()
        '''

        # If a capture was still in progress init will have problems without this
        self.hw_trig_disarm()

        state = self.state()
        print 'Init state: %d' % state
        if state == 0x08:
            print 'Flusing stale capture'
            self._cap_frame_bulk()
        elif state != 0x01:
            raise Exception('Not idle, refusing to setup')

        # small vs large: how to correctly set?
        # (32769, 1)
        #print self.img_wh()
        self.img_wh_w(*self.WH)

        self.set_act_sec(0x0000)

        self.chk_wh()

        v = self.fpga_r(0x2002)
        if v != 0x0000 and self.verbose:
            print "WARNING: bad FPGA read: 0x%04X" % v

        v = self.fpga_rsig()
        if v != 0x1234:
            raise Exception("Invalid FPGA signature: 0x%04X" % v)

        #{1: gxs700_fpga.setup_fpga1_sm,
        {1: gxs700_fpga.setup_fpga1_sm,
         2: gxs700_fpga.setup_fpga1_lg}[self.size](self)

        v = self.fpga_rsig()
        if v != 0x1234:
            raise Exception("Invalid FPGA signature: 0x%04X" % v)

        #{1: gxs700_fpga.setup_fpga2_sm,
        {1: gxs700_fpga.setup_fpga2_sm,
         2: gxs700_fpga.setup_fpga2_lg}[self.size](self)

        self.fpga_w(0x2002, 0x0001)
        v = self.fpga_r(0x2002)
        if v != 0x0001:
            raise Exception("Bad FPGA read: 0x%04X" % v)
        
        if self.size == 1:
            self.fpga_rv(0x2002, 1)

        # XXX: why did the integration time change?
        self.int_t_w(0x0064)

        if self.state() != 1:
            print 'WARNING: unexpected state'

        self.set_act_sec(0x0000)

        self.chk_wh()

        v = self.state()
        if v != 1:
            print 'WARNING: unexpected state %s' % (v,)

        self.img_wh_w(*self.WH)

        self.set_act_sec(0x0000)


        v = self.img_wh()
        if v != self.WH:
            raise Exception("Unexpected w/h: %s" % (v,))

        v = self.state()
        if v != 1:
            print 'WARNING: unexpected state %s' % (v,)

        self.img_wh_w(*self.WH)

        self.set_act_sec(0x0000)


        self.chk_wh()


        v = self.state()
        if v != 1:
            print 'WARNING: unexpected state %s' % (v,)

        # This may depend on cal files
        self.int_t_w(0x02BC)
        self.cap_mode_w(0)
        #self.hw_trig_arm()

    def _cap_frame_bulk(self):
        '''
        Take care of the bulk transaction prat of capturing frames
        Large sensor only
        '''
        '''
        0x4000
        (2 * 1040 * 1552) % 0x4000 = 512
        (2 * 1344 * 1850) % 0x4000 = 8448

        It will continue to return data but the data won't be valid
        So take just enough data
        '''

        all_dat = ['']
        def async_cb(trans):
            buf = trans.getBuffer()
            all_dat[0] += buf
            if len(all_dat[0]) < self.FRAME_SZ:
                trans.submit()
            else:
                remain[0] -= 1

        trans_l = []
        remain = [0]
        for _i in xrange(32):
            trans = self.dev.getTransfer()
            trans.setBulk(0x82, 0x4000, callback=async_cb, user_data=None, timeout=1000)
            trans.submit()
            trans_l.append(trans)
            remain[0] += 1

        while remain[0]:
            self.usbcontext.handleEventsTimeout(tv=0.1)

        for trans in trans_l:
            trans.close()

        all_dat = str(all_dat[0][0:self.FRAME_SZ])
        if len(all_dat) != self.FRAME_SZ:
            raise Exception("Unexpected buffer size")
        return all_dat
    
    def _cap_frame_inter(self):
        '''
        Small sensor only
        '''

        # Required for setAlt
        self.dev.claimInterface(0)
        # Packet 10620
        self.dev.setInterfaceAltSetting(0, 1)
        all_dat = self.dev.interruptRead(2, self.FRAME_SZ, timeout=5000)
        # Packet 12961
        self.dev.setInterfaceAltSetting(0, 0)

        all_dat = str(all_dat[0:self.FRAME_SZ])
        if len(all_dat) != self.FRAME_SZ:
            raise Exception("Unexpected buffer size")
        return all_dat

    def _cap_bin(self, scan_cb=lambda itr: None):
        '''Capture a raw binary frame, waiting for trigger'''
        self.wait_trig_cb()

        state_last = self.state()
        i = 0
        while True:
            scan_cb(i)
            if i % 1000 == 0:
                print 'scan %d (state %s)' % (i, state_last)

            # Generated from packet 861/862
            #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
            #if args.verbose:
            #    print 'r1: %s' % binascii.hexlify(buff)
            #state = ord(buff)
            state = self.state()
            if state != state_last:
                print 'scan %d (new state %s)' % (i, state_last)

            '''
            Observed states
            -0x01: no activity
            -0x02: short lived
            -0x04: longer lived than 2
            -0x08: read right before capture
            
            Note: small sensor doesn't go through 8
            '''
            if state != 0x01:
                # Large
                if self.size == SIZE_LG and state == 0x08:
                    print 'Go go go 8'
                    break
                # Small
                elif self.size == SIZE_SM and state == 0x04:
                    print 'Go go go 4'
                    break
                # Intermediate states
                # Ex: 2 during acq
                else:
                    # raise Exception('Unexpected state: 0x%02X' % state)
                    pass


            # Generated from packet 863/864
            #buff = dev.controlRead(0xC0, 0xB0, 0x0080, 0x0000, 1)
            #if args.verbose:
            #    print 'r2: %s' % binascii.hexlify(buff)
            #validate_read("\x00", buff, "packet 863/864")
            if self.error():
                raise Exception('Unexpected error')

            i = i + 1
            state_last = state


        # Generated from packet 783/784
        #buff = dev.controlRead(0xC0, 0xB0, 0x0040, 0x0000, 128)
        # NOTE:: req max 128 but got 8
        #validate_read("\x8E\x00\x00\x00\x58\x00\x00\x00", buff, "packet 783/784", True)
        #print 'Img ctr: %s' % binascii.hexlify(self.img_ctr_r(128))

        # Generated from packet 785/786
        #buff = dev.controlRead(0xC0, 0xB0, 0x0040, 0x0000, 128)
        # NOTE:: req max 128 but got 8
        #validate_read("\x8E\x00\x00\x00\x58\x00\x00\x00", buff, "packet 785/786", True)
        #print 'Img ctr: %s' % binascii.hexlify(self.img_ctr_r(128))

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
        #self.versions()

        # Generated from packet 791/792
        #buff = dev.controlRead(0xC0, 0xB0, 0x0004, 0x0000, 2)
        #validate_read("\x12\x34", buff, "packet 791/792")
        if self.fpga_rsig() != 0x1234:
            raise Exception("Invalid FPGA signature")

        if self.size == SIZE_SM:
            return self._cap_frame_inter()
        else:
            return self._cap_frame_bulk()

    def cap_binv(self, n, cap_cb, loop_cb=lambda: None, scan_cb=lambda itr: None):
        self._cap_setup()

        taken = 0
        while taken < n:
            imgb = self._cap_bin(scan_cb=scan_cb)
            rc = cap_cb(imgb)
            # hack: consider doing something else
            if rc:
                n += 1
            taken += 1
            self.cap_cleanup()
            loop_cb()

        self.hw_trig_disarm()

    def cap_bin(self):
        ret = []
        def cb(buff):
            ret.append(buff)
        self.cap_binv(1, cb)
        return ret[0]

    def cap_img(self):
        '''Capture a decoded image to filename, waiting for trigger'''
        return self.decode(self.cap_bin())

    @staticmethod
    def decode_sm(buff):
        pass

    @staticmethod
    def decode(buff):
        return decode(buff)

    def cap_cleanup(self):
        if self.state() != 1:
            raise Exception('Unexpected state')

        if self.error():
            raise Exception('Unexpected error')

        if self.state() != 1:
            raise Exception('Unexpected state')

        if self.error():
            raise Exception('Unexpected error')

        self.eeprom_w(0x0020, "2015/03/19-21:44:43:087")

        if self.state() != 1:
            raise Exception('Unexpected state')

        if self.error():
            raise Exception('Unexpected error')

        self.int_t_w(0x02BC)
        self.cap_mode_w(0)
        self.hw_trig_arm()

        if self.state() != 1:
            raise Exception('Unexpected state')

        if self.error():
            raise Exception('Unexpected error')
        if self.state() != 1:
            raise Exception('Unexpected state')

        if self.state() != 1:
            raise Exception('Unexpected state')

        self.img_wh_w(*self.WH)

        self.set_act_sec(0x0000)

        self.chk_wh()

        if self.state() != 1:
            raise Exception('Unexpected state')

        if self.error():
            raise Exception('Unexpected error')

        if self.state() != 1:
            raise Exception('Unexpected state')

    def _cap_setup(self):
        '''Setup done right before taking an image'''

        self.hw_trig_arm()

        if self.state() != 1:
            raise Exception('Unexpected state')

        if self.error():
            raise Exception('Unexpected error')

        if self.state() != 1:
            raise Exception('Unexpected state')

        #print 'Img ctr: %s' % binascii.hexlify(self.img_ctr_r(128))

        if self.state() != 1:
            raise Exception('Unexpected state')

        #print 'Img ctr: %s' % binascii.hexlify(self.img_ctr_r(128))

        if self.error():
            raise Exception('Unexpected error')

        #self.versions()

        if self.state() != 1:
            raise Exception('Unexpected state')
        if self.error():
            raise Exception('Unexpected error')

        self.img_wh_w(*self.WH)
        self.set_act_sec(0x0000)
        self.chk_wh()

        if self.state() != 1:
            raise Exception('Unexpected state')

