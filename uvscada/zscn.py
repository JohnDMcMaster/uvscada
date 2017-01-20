import serial
import sys
import time
import struct
import binascii

# 0.6 had some issues still
# Do this right
DWELL = 1.0

CMD_0 =     0x00
CMD_1 =     0x80

CMD_LED_G = 0xFA & 0x7F
CMD_LED_O = 0xFB & 0x7F
CMD_LED_R = 0xFC & 0x7F
CMD_LED_B = 0xFD & 0x7F
CMD_RST =   0xFE
CMD_NOP =   0xFF

led_s2i = {
    'g': CMD_LED_G,
    'o': CMD_LED_O,
    'r': CMD_LED_R,
    'b': CMD_LED_B,
}

def floats(f):
    if f == float('inf'):
        return 'inf'
    else:
        if f < 1e3:
            return '% 9.3f' % (f,)
        elif f < 1e6:
            return '% 9.3fk' % (f / 1e3,)
        else:
            return '% 9.3fM' % (f / 1e6,)

class Timeout(Exception):
    pass

class ZscnSer:
    # wtf is acm
    def __init__(self, device=None, debug=False):
        self.serial = None
        self.debug = debug
        self.wait_ack = True
        
        self.seq = 0
        if device is None:
            for s in ("/dev/ttyACM1",):
                try:
                    self.try_open(s)
                    print 'Opened %s okay' % s
                    break
                except IOError:
                    print 'Failed to open %s' % s
                    continue
            if self.serial is None:
                raise IOError("Failed to find a suitable device")
        else:
            self.try_open(device)
        
        # Clear old data
        if self.debug:
            print 'Flushing %d chars' % self.serial.inWaiting()
        self.serial.flushInput()
        
        # Send and make sure we get an ack
        self.packet_write(CMD_NOP)
        '''
        if int(time.time()) % 2:
            self.packet_write(CMD_1 | CMD_LED_B, wait_ack=False)
            self.packet_write(CMD_1 | CMD_LED_R, wait_ack=False)
        else:
            self.packet_write(CMD_0 | CMD_LED_B, wait_ack=False)
            self.packet_write(CMD_0 | CMD_LED_R, wait_ack=False)
        '''
        '''
        while True:
            self.packet_write(CMD_0 | CMD_LED_R, wait_ack=False)
            time.sleep(1)
            self.packet_write(CMD_1 | CMD_LED_R, wait_ack=False)
            time.sleep(1)
        '''

    def try_open(self, device):
        self.device = device
        self.serial = serial.Serial(port=self.device, baudrate=38400, timeout=1, writeTimeout=1)    
        if self.serial is None:
            raise IOError('Can not connect to serial')

    def rst(self):
        self.packet_write(CMD_RST)

    def nop(self):
        self.packet_write(CMD_NOP)

    def led(self, which, state):
        if state:
            self.led_on(which)
        else:
            self.led_off(which)

    def led_off(self, which):
        self.packet_write(0x00 | led_s2i[which])

    def led_on(self, which):
        self.packet_write(0x80 | led_s2i[which])

    def ch_off(self, ch):
        self.packet_write(0x00 | ch)

    def ch_on(self, ch):
        self.packet_write(0x80 | ch)
        
    def packet_write(self, cmd, wait_ack=True, retries=3):
        packet_out = chr(cmd)
        #print 'out: %s' % binascii.hexlify(packet_out)
        for retry in xrange(retries):
            try:
                self.serial.flushInput()
                self.serial.write(packet_out)
                self.serial.flush()
                
                if self.wait_ack:
                    if self.packet_read() == packet_out:
                        return
            except Timeout:
                print 'WARNING: retry %s timed out' % retry
                continue
        raise Timeout('Failed to write packet after %d retries' % retries)
        
    def packet_read(self):
        c = self.serial.read(1)
        if not c:
            raise Timeout('Failed to read serial port')
        #print 'In: %s' % binascii.hexlify(c)
        return c

def scan(z, k, pack='dip40', pins=None, verbose=True, dwell=DWELL):
    m = {}
    
    if pack == 'dip40':
        npins = 40
    elif pack == 'sdip64':
        npins = 64
    else:
        raise Exception("Not supported")
    
    if pins is None:
        pins = xrange(1, npins + 1, 1)

    g = 0
    z.led('o', 1)
    z.led('r', 0)
    try:
        for pin in pins:
            ch = pin - 1
            z.led('g', g)
            g = not g
            z.ch_on(ch)
            time.sleep(dwell)
            res = k.res()
            if verbose:
                print '% 3u: %s' % (pin, floats(res))
            z.ch_off(ch)
            m[pin] = res
    except:
        z.led('r', 1)
        raise
    
    time.sleep(dwell)
    res = k.res()
    if verbose:
        print 'End: %s' % (floats(res),)
    if res != float('inf'):
        raise Exception("Expected inf, got %s" % floats(res))

    z.led('o', 0)
    z.led('g', 1)
    return m

def rst_verify(z, k, dwell=DWELL, verbose=True):
    z.rst()

    if 1:
        print 'All off'
        for i in xrange(64):
            z.ch_off(i)

    time.sleep(dwell)
    res = k.res()
    if verbose:
        print 'Reset: %s' % (floats(res),)
    if res != float('inf'):
        raise Exception("Expected inf, got %s" % floats(res))
