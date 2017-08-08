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

    def _init(self):
        #self.rst()

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

        if self.img_wh() != self.WH:
            raise Exception("Unexpected w/h")

        v = self.fpga_r(0x2002)
        if v != 0x0000 and self.verbose:
            print "WARNING: bad FPGA read: 0x%04X" % v

        v = self.fpga_rsig()
        if v != 0x1234:
            raise Exception("Invalid FPGA signature: 0x%04X" % v)

        self._setup_fpga1()

        v = self.fpga_rsig()
        if v != 0x1234:
            raise Exception("Invalid FPGA signature: 0x%04X" % v)

        self._setup_fpga2()

        self.fpga_w(0x2002, 0x0001)
        v = self.fpga_r(0x2002)
        if v != 0x0001:
            raise Exception("Bad FPGA read: 0x%04X" % v)

        # XXX: why did the integration time change?
        self.int_t_w(0x0064)

        if self.state() != 1:
            print 'WARNING: unexpected state'

        self.set_act_sec(0x0000)

        v = self.img_wh()
        if v != self.WH:

            raise Exception("Unexpected w/h: %s" % (v,))

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


        v = self.img_wh()
        if v != self.WH:
            raise Exception("Unexpected w/h: %s" % (v,))


        v = self.state()
        if v != 1:
            print 'WARNING: unexpected state %s' % (v,)

        self.int_t_w(0x02BC)

        self.cap_mode_w(0)

    def _cap_frame_bulk(self):
        '''Take care of the bulk transaction prat of capturing frames'''
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

    def _cap_bin(self, scan_cb=lambda itr: None):
        '''Capture a raw binary frame, waiting for trigger'''
        self.wait_trig_cb()

        i = 0
        while True:
            scan_cb(i)
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
                    #print 'Go go go'
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

    def _setup_fpga1(self):
        self.fpga_wv2(0x0400, "\x00\x00\x60\x00\x00\x00")
        self.fpga_wv2(0x0404, "\x00\xE5\xC0\x00\x00\x00")
        self.fpga_wv2(0x0408, "\x00\xF7\x20\x00\x00\x01")
        self.fpga_wv2(0x040C, "\x00\xE5\x80\x00\x00\x01")
        self.fpga_wv2(0x0410, "\x00\xF7\xE0\x00\x00\x01")
        self.fpga_wv2(0x0414, "\x00\xE5\xA0\x00\x00\x02")
        self.fpga_wv2(0x0418, "\x00\xC5\x20\x00\x00\x04")
        self.fpga_wv2(0x041C, "\x00\x05\x38\x00\x00\x04")
        self.fpga_wv2(0x0420, "\x00\x04\x98\x00\x00\x04")
        self.fpga_wv2(0x0424, "\x00\x00\xF8\x02\x00\x0C")
        self.fpga_wv2(0x0428, "\x08\x00\x3F\x00\x00\x00")
        self.fpga_wv2(0x042C, "\x08\x00\x42\x04\x00\x00")
        self.fpga_wv2(0x0430, "\x08\x04\x4B\x04\x00\x00")
        self.fpga_wv2(0x0434, "\x08\x06\x54\x04\x00\x00")
        self.fpga_wv2(0x0438, "\x08\x04\x5D\x04\x00\x00")
        self.fpga_wv2(0x043C, "\x08\x06\x66\x04\x00\x00")
        self.fpga_wv2(0x0440, "\x08\x04\x6F\x04\x00\x00")
        self.fpga_wv2(0x0444, "\x08\x00\x72\x04\x00\x00")
        self.fpga_wv2(0x0448, "\x08\x01\x78\x04\x00\x00")
        self.fpga_wv2(0x044C, "\x08\x03\x7E\x04\x00\x00")
        self.fpga_wv2(0x0450, "\x08\x01\x84\x04\x00\x00")
        self.fpga_wv2(0x0454, "\x08\xC3\x8A\x04\x00\x00")
        self.fpga_wv2(0x0458, "\x08\xC1\x90\x04\x00\x00")
        self.fpga_wv2(0x045C, "\x08\xC0\x96\x04\x00\x00")
        self.fpga_wv2(0x0460, "\x08\xC2\x9C\x04\x00\x00")
        self.fpga_wv2(0x0464, "\x08\xC0\xA2\x04\x00\x08")
        self.fpga_wv2(0x0468, "\x08\x42\x06\x04\x00\x00")
        self.fpga_wv2(0x046C, "\x08\x00\x0C\x04\x00\x00")
        self.fpga_wv2(0x0470, "\x08\x82\x12\x04\x00\x00")
        self.fpga_wv2(0x0474, "\x08\x00\x18\x04\x00\x08")
        self.fpga_wv2(0x0478, "\x0F\x42\x18\x04\x00\x00")
        self.fpga_wv2(0x047C, "\x0F\x02\x22\x04\x00\x00")
        self.fpga_wv2(0x0480, "\x0E\x02\x6A\x04\x00\x00")
        self.fpga_wv2(0x0484, "\x0A\x02\x6F\x04\x00\x00")
        self.fpga_wv2(0x0488, "\x0A\x82\x87\x04\x00\x00")
        self.fpga_wv2(0x048C, "\x0A\x02\xFF\x04\x00\x00")
        self.fpga_wv2(0x0490, "\x08\x02\x04\x04\x00\x09")
        self.fpga_wv2(0x0494, "\x08\x20\x09\x04\x00\x00")
        self.fpga_wv2(0x0498, "\x08\x30\x12\x04\x00\x00")
        self.fpga_wv2(0x049C, "\x08\x20\x1B\x04\x00\x00")
        self.fpga_wv2(0x04A0, "\x08\x30\x24\x04\x00\x00")
        self.fpga_wv2(0x04A4, "\x08\x20\x2D\x04\x00\x00")
        self.fpga_wv2(0x04A8, "\x08\x00\x36\x04\x00\x00")
        self.fpga_wv2(0x04AC, "\x08\x0A\x3F\x04\x00\x00")
        self.fpga_wv2(0x04B0, "\x08\x1A\x48\x04\x00\x00")
        self.fpga_wv2(0x04B4, "\x08\x0A\x51\x04\x00\x00")
        self.fpga_wv2(0x04B8, "\x08\x1A\x5A\x04\x00\x00")
        self.fpga_wv2(0x04BC, "\x08\x0A\x63\x04\x00\x00")
        self.fpga_wv2(0x04C0, "\x08\x00\x64\x04\x00\x00")
        self.fpga_wv2(0x04C4, "\x08\x10\x6C\x04\x00\x08")
        self.fpga_wv2(0x04C8, "\x08\x10\x04\x0C\x00\x00")
        self.fpga_wv2(0x04CC, "\x08\x00\x08\x0C\x00\x00")
        self.fpga_wv2(0x04D0, "\x08\x10\x0C\x0C\x00\x00")
        self.fpga_wv2(0x04D4, "\x08\x00\x10\x0C\x00\x08")
        self.fpga_wv2(0x04D8, "\x08\x10\x09\x1C\x00\x00")
        self.fpga_wv2(0x04DC, "\x08\x00\x12\x1C\x00\x00")
        self.fpga_wv2(0x04E0, "\x08\x10\x1B\x1C\x00\x00")
        self.fpga_wv2(0x04E4, "\x08\x00\x1C\x1C\x00\x00")
        self.fpga_wv2(0x04E8, "\x08\x00\x24\x1D\x00\x08")
        self.fpga_wv2(0x04EC, "\x08\x22\x3C\x00\x00\x00")
        self.fpga_wv2(0x04F0, "\x08\x32\x78\x00\x00\x00")
        self.fpga_wv2(0x04F4, "\x08\x22\xB4\x00\x00\x00")
        self.fpga_wv2(0x04F8, "\x08\x32\xF0\x00\x00\x00")
        self.fpga_wv2(0x04FC, "\x08\x22\x2C\x00\x00\x01")
        self.fpga_wv2(0x0500, "\x08\x02\x35\x00\x00\x01")
        self.fpga_wv2(0x0504, "\x08\x0A\x3E\x00\x00\x01")
        self.fpga_wv2(0x0508, "\x08\x1A\x47\x00\x00\x01")
        self.fpga_wv2(0x050C, "\x08\x0A\x4C\x00\x00\x01")
        self.fpga_wv2(0x0510, "\x08\x1A\x50\x00\x00\x01")
        self.fpga_wv2(0x0514, "\x08\x0A\x59\x00\x00\x01")
        self.fpga_wv2(0x0518, "\x08\x02\x5E\x00\x00\x01")
        self.fpga_wv2(0x051C, "\x08\x12\x66\x00\x00\x01")
        self.fpga_wv2(0x0520, "\x08\x02\x67\x00\x00\x01")
        self.fpga_wv2(0x0524, "\x08\x02\x6F\x01\x00\x09")
        self.fpga_wv2(0x0528, "\x08\x00\x08\x0C\x00\x00")
        self.fpga_wv2(0x052C, "\x08\x00\x10\x04\x00\x00")
        self.fpga_wv2(0x0530, "\x08\x00\x18\x00\x00\x08")
        self.fpga_wv2(0x0534, "\x08\x10\x09\x00\x00\x00")
        self.fpga_wv2(0x0538, "\x08\x00\x12\x00\x00\x00")
        self.fpga_wv2(0x053C, "\x08\x10\x1B\x00\x00\x00")
        self.fpga_wv2(0x0540, "\x08\x00\x1C\x00\x00\x00")
        self.fpga_wv2(0x0544, "\x08\x00\x24\x01\x00\x08")
        self.fpga_wv2(0x0548, "\x08\x10\x09\x1C\x00\x00")
        self.fpga_wv2(0x054C, "\x08\x00\x12\x1C\x00\x00")
        self.fpga_wv2(0x0550, "\x08\x10\x1B\x1C\x00\x00")
        self.fpga_wv2(0x0554, "\x08\x00\x1C\x1C\x00\x00")
        self.fpga_wv2(0x0558, "\x08\x00\x24\x1D\x00\x08")
        self.fpga_wv2(0x055C, "\x08\xC2\x06\x00\x00\x00")
        self.fpga_wv2(0x0560, "\x08\xC0\x0C\x00\x00\x00")
        self.fpga_wv2(0x0564, "\x08\xC2\x12\x00\x00\x00")
        self.fpga_wv2(0x0568, "\x08\xC0\x18\x00\x00\x08")
        self.fpga_wv2(0x056C, "\x08\x45\x09\x80\x00\x00")
        self.fpga_wv2(0x0570, "\x08\xC5\x36\x80\x00\x00")
        self.fpga_wv2(0x0574, "\x08\x45\x3F\x80\x00\x00")
        self.fpga_wv2(0x0578, "\x08\x04\x48\x80\x00\x00")
        self.fpga_wv2(0x057C, "\x08\x00\x51\x80\x00\x08")
        self.fpga_wv2(0x0580, "\x08\x00\x04\x80\x00\x08")
        self.fpga_wv2(0x0584, "\x09\x24\x60\x00\x00\x00")
        self.fpga_wv2(0x0588, "\x09\x36\xC0\x00\x00\x00")
        self.fpga_wv2(0x058C, "\x09\x24\x20\x00\x00\x01")
        self.fpga_wv2(0x0590, "\x09\x36\x80\x00\x00\x01")
        self.fpga_wv2(0x0594, "\x09\x24\x40\x00\x00\x02")
        self.fpga_wv2(0x0598, "\x09\x00\xA0\x00\x00\x02")
        self.fpga_wv2(0x059C, "\x09\x01\x00\x00\x00\x03")
        self.fpga_wv2(0x05A0, "\x09\x03\x60\x00\x00\x03")
        self.fpga_wv2(0x05A4, "\x09\x01\xC0\x00\x00\x03")
        self.fpga_wv2(0x05A8, "\x09\x03\x20\x00\x00\x04")
        self.fpga_wv2(0x05AC, "\x09\x01\x80\x00\x00\x04")
        self.fpga_wv2(0x05B0, "\x09\x00\x40\x00\x00\x0D")
        self.fpga_wv2(0x05B4, "\x0F\x42\x18\x00\x00\x00")
        self.fpga_wv2(0x05B8, "\x0F\x02\x22\x00\x00\x00")
        self.fpga_wv2(0x05BC, "\x0E\x02\x6A\x00\x00\x00")
        self.fpga_wv2(0x05C0, "\x0A\x00\x6F\x00\x00\x00")
        self.fpga_wv2(0x05C4, "\x0A\x80\x87\x00\x00\x00")
        self.fpga_wv2(0x05C8, "\x0A\x00\xFF\x00\x00\x00")
        self.fpga_wv2(0x05CC, "\x08\x00\x04\x00\x00\x09")

    def _setup_fpga2(self):
        self.fpga_wv2(0x1000, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        self.fpga_wv2(0x1008, "\x00\x02\x00\x00\x00\x00\x90\x00\x00\x00")
        self.fpga_wv2(0x1010, "\x00\x03\x00\x00\x00\x00\x90\x00\x00\x0A")
        self.fpga_wv2(0x1018, "\x04\x03\xCC\x00\x00\x00\x90\x00\x00\x1A")
        self.fpga_wv2(0x1020, "\x00\x05\x00\x00\x00\x00\x90\x00\x00\x1E")
        self.fpga_wv2(0x1028, "\x00\x06\x00\x00\x00\x00\x00\x00\x00\x25")
        self.fpga_wv2(0x1030, "\x07\x06\x63\x00\x00\x00\x00\x00\x00\x32")
        self.fpga_wv2(0x1038, "\x08\x07\x20\x00\x00\x00\x00\x00\x00\x36")
        self.fpga_wv2(0x1040, "\x09\x08\xF5\x13\xFF\xF0\x00\x00\x00\x32")
        self.fpga_wv2(0x1048, "\x0A\x09\x20\x00\x00\x00\x00\x00\x00\x36")
        self.fpga_wv2(0x1050, "\x0B\x0A\xF5\x13\xFF\xF0\x00\x00\x00\x32")
        self.fpga_wv2(0x1058, "\x0C\x0B\x20\x00\x00\x00\x00\x00\x00\x36")
        self.fpga_wv2(0x1060, "\x0D\x0C\xF5\x13\xFF\xF0\x00\x00\x00\x32")
        self.fpga_wv2(0x1068, "\x0E\x0D\x20\x00\x00\x00\x00\x00\x00\x36")
        self.fpga_wv2(0x1070, "\x0F\x0E\xF5\x13\xFF\xF0\x00\x00\x00\x32")
        self.fpga_wv2(0x1078, "\x10\x0F\x20\x00\x00\x00\x00\x00\x00\x36")
        self.fpga_wv2(0x1080, "\x11\x10\x0A\x13\xFF\xF0\x00\x00\x00\x32")
        self.fpga_wv2(0x1088, "\x03\x11\x0A\x12\x00\x70\x00\x00\x00\x32")
        self.fpga_wv2(0x1090, "\x02\x12\xDC\x13\xFF\xF0\x90\x00\x00\x1A")
        self.fpga_wv2(0x1098, "\x00\x14\x00\x00\x00\x00\x90\x00\x00\x5B")
        self.fpga_wv2(0x10A0, "\x15\x14\xFF\x00\x00\x0F\x00\x00\x00\x60")
        self.fpga_wv2(0x10A8, "\x00\x16\x00\x00\x00\x00\x90\x00\x00\x61")
        self.fpga_wv2(0x10B0, "\x00\x17\x00\x00\x00\x00\x90\x00\x00\x6D")
        self.fpga_wv2(0x10B8, "\x00\x18\x00\x00\x00\x00\x00\x00\x00\x3B")
        self.fpga_wv2(0x10C0, "\x16\x18\x3E\x01\x73\x95\x00\x00\x00\x4D")
        self.fpga_wv2(0x10C8, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        self.fpga_wv2(0x10D0, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        self.fpga_wv2(0x10D8, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        self.fpga_wv2(0x10E0, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        self.fpga_wv2(0x10E8, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        self.fpga_wv2(0x10F0, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        self.fpga_wv2(0x10F8, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")

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

        if self.img_wh() != self.WH:
            raise Exception("Unexpected w/h")

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
        if self.img_wh() != self.WH:
            raise Exception("Unexpected w/h")

        if self.state() != 1:
            raise Exception('Unexpected state')

