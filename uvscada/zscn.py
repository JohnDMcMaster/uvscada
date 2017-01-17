import serial
import sys
import time
import struct
import binascii
from collections import namedtuple

class Timeout(Exception):
    pass

class AckException(Exception):
    pass
    
class BadChecksum(Exception):
    pass

# 0xC0 
SLIP_END = chr(192)
# 0xDB
SLIP_ESC = chr(219)

REG_NONE =      0x00
REG_ACK =       0x01
REG_NOP =       0x02

'''
uint8_t checksum;
uint8_t seq;
uint8_t opcode;
uint32_t value;
'''
PACKET_FORMAT = '<BBBi'
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)
Packet = namedtuple('zscnpkt', ('checksum', 'seq', 'opcode', 'value'))

def checksum(data):
    data = str(data)
    return (~(sum([ord(c) for c in data]) % 0x100)) & 0xFF

def slip(bytes):
    ret = SLIP_END
    for b in bytes:
        if b == SLIP_END:
            # If a data byte is the same code as END character, a two byte sequence of
            # ESC and octal 334 (decimal 220) is sent instead.  
            ret += SLIP_ESC + chr(220)
        elif b == SLIP_ESC:
            # If it the same as an ESC character, an two byte sequence of ESC and octal 335 (decimal
            # 221) is sent instead
            ret += SLIP_ESC + chr(221)
        else:
            ret += b
    # When the last byte in the packet has been
    # sent, an END character is then transmitted
    return ret + SLIP_END

def deslip(bytes):
    '''Returns None if slip decoding failed'''
    escape = False
    rx = ''
    i = 0
    
    def slip_dbg(s):
        #print s
        pass

    while i < len(bytes):
        c = chr(bytes[i])
        i += 1
        slip_dbg('')
        slip_dbg('Processing: %02X' % ord(c))

        if escape:
            slip_dbg('Escape followed')
            escape = False
            
            # If a data byte is the same code as END character, a two byte sequence of
            # ESC and octal 334 (decimal 220) is sent instead.  
            if c == chr(220):
                rx += SLIP_END
            # If it the same as an ESC character, an two byte sequence of ESC and octal 335 (decimal
            # 221) is sent instead
            elif c == chr(221):
                rx += SLIP_ESC
            else:
                slip_dbg('Escape invalid')
                del bytes[0:i]
                rx = ''
                i = 0
                continue
        elif c == SLIP_END:
            del bytes[0:i]
            # Not the right size? drop it
            if len(rx) == PACKET_SIZE:
                slip_dbg('Good packet')
                return rx
            slip_dbg('Dropping packet: bad size')
            rx = ''
            i = 0
            continue
        elif c == SLIP_ESC:
            slip_dbg('Escape detected')
            escape = True
        # Ordinary character
        else:
            slip_dbg('Normal char')
            rx += c
    return None

class ZscnSer:
    # wtf is acm
    def __init__(self, device=None, debug=False):
        self.serial = None
        self.debug = debug
        self.wait_ack = True
        
        self.seq = 0
        if device is None:
            for s in ("/dev/ttyACM0",):
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
        self.reg_write(REG_NOP, 0)

    def try_open(self, device):
        self.device = device
        self.serial = serial.Serial(port=self.device, baudrate=38400, timeout=1, writeTimeout=1)    
        if self.serial is None:
            raise IOError('Can not connect to serial')
        
    def reg_write(self, reg, value):
        self.packet_write(0x80 | reg, value)
        
    def reg_read(self, reg, retries=3):
        '''Return 32 bit register value'''
        for i in xrange(retries):
            try:
                self.serial.flushInput()
                self.packet_write(reg, 0)
                
                reply_packet = self.packet_read()
                if reply_packet.opcode != reg:
                    print "WARNING: Replied wrong reg.  Expected 0x%02X but got 0x%02X" % (reg, reply_packet.opcode)
                    # try to flush out
                    time.sleep(0.1)
                    continue
                return reply_packet.value
            except BadChecksum as e:
                if i == retries-1:
                    raise e
                print 'WARNING: bad checksum on read: %s' % (e,)
            except Timeout as e:
                if i == retries-1:
                    raise e
                print 'WARNING: timed out read'
    
    def debug_read(self):
        print 'DEBUG IN: reading'
        buff = self.serial.read(1024)
        print 'DEBUG IN: %s' % buff
        print 'DEBUG IN: %s' % binascii.hexlify(buff)
        buff = self.serial.read(1024)
        print 'DEBUG IN: %s' % buff
        print 'DEBUG IN: %s' % binascii.hexlify(buff)
 
    def packet_write(self, reg, value, retries=3):
        #print 'Packet write reg=0x%02X, value=0x%08X' % (reg, value)
        packet = struct.pack('<BBi', self.seq, reg, value)
        packet = chr(checksum(packet)) + packet
        out = slip(packet)
        self.seq = (self.seq + 1) % 0x100

        print 'DEBUG OUT: %s' % packet
        print 'DEBUG OUT: %s' % binascii.hexlify(packet)

        if self.debug:
            print 'DEBUG zscn: packet: %s, sending: %s' % (binascii.hexlify(packet), binascii.hexlify(out))
            #if self.serial.inWaiting():
            #    raise Exception('At send %d chars waiting' % self.serial.inWaiting())
        for retry in xrange(retries):
            try:
                self.serial.flushInput()
                self.serial.write(out)
                self.serial.flush()
                
                self.debug_read()
                
                if self.wait_ack:
                    try:
                        _ack_packet = self.packet_read()
                    except BadChecksum as e:
                        print 'WARNING: bad rx checksum'
                        continue
                        
                        # poorly assume if we get any response back that the write succeeded
                        # since we are throwing the reply away anyway
                return
            except Timeout:
                print 'WARNING: retry %s timed out' % retry
                continue
        raise Timeout('Failed to write packet after %d retries' % retries)
        
    def packet_read(self):
        # Now read response
        # Go until we either get a packet or serial port times out
        rx = bytearray()
        while True:
            while True:
                c = self.serial.read(1)
                if not c:
                    raise Timeout('Failed to read serial port')
                rx += c
                #print 'Read %s' % binascii.hexlify(rx)
                packet_raw = deslip(rx)
                if packet_raw:
                    break
            #print 'Got packet of length %d' % len(packet_raw)
            packet = Packet(*struct.unpack(PACKET_FORMAT, packet_raw))
            checksum_computed = checksum(packet_raw[1:])
            if packet.checksum != checksum_computed:
                self.serial.flushOutput()
                self.serial.flushInput()
                raise BadChecksum("Expected 0x%02X but got 0x%02X" % (packet.checksum, checksum_computed))
            return packet
        
