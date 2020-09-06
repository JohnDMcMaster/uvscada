'''
GPIB adapter
PROLOGIX GPIB-USB CONTROLLER
REV 6.4.1
http://prologix.biz/getfile?attachment_id=2
'''

from uvscada.aserial import ASerial
import serial

class Timeout(Exception):
    pass

class ShortRead(Exception):
    pass

'''
*********************************
GPIB
*********************************

In Controller and Device modes, characters received over USB port are aggregated in an
internal buffer and interpreted when a USB termination character - CR (ASCII 13) or
LF (ASCII 10) - is received. If CR, LF, ESC (ASCII 27), or '+' (ASCII 43) characters are
part of USB data they must be escaped by preceding them with an ESC character. All
un-escaped LF, CR and ESC and '+' characters in USB data are discarded.

Serial port parameters such as baud rate, data bits,
stop bits and flow control do not matter and may be set to any value
'''
class PUGpib:
    def __init__(self, port="/dev/ttyUSB0", ser_timeout=1.0, gpib_timeout=0.9, addr=5, clr=True, eos=0):
        self.port = port
        self.addr = addr
        self.ser = ASerial(port,
                # They claim this parameter is ignored                          
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                rtscts=False,
                dsrdtr=False,
                xonxoff=False,
                timeout=ser_timeout,
                # Blocking writes
                writeTimeout=None)
        self.bin = False
        
        # Clear any previous partial command
        #self.send_str('')
        # Clear any data laying around
        self.ser.flushInput()
        self.ser.flushOutput()

        self.set_addr(addr)
        if clr:
            self.send_str('++clr')
        
        # Will generate a bunch of interrupted errors if you don't set this (default 1)
        self.send_str('++auto 0')
        '''
        ++eos 0    Append CR+LF to instrument commands (appears to be default)
        ++eos 1    Append CR to instrument commands
        ++eos 2    Append LF to instrument commands
        ++eos 3    Do not append anything to instrument commands
        ++eos      Query current EOS state
        '''
        self.send_str('++eos %d' % eos)
        self.send_str('++read_tmo_ms %d' % (gpib_timeout * 1000,))
        
        # Make sure simple queries work
        self.version()
    
    def set_addr(self, addr):
        self.addr = addr
        self.send_str("++addr %d" % (self.addr,))
    
    def interface(self):
        return "GPIB @ %s" % (self.port,)
    
    def bin_mode(self):
        self.bin = True
        # disable cr/lf
        self.send_str("++eos 3")
        #self.send_str("++eot_enable 1")
        # default: 0
        #self.send_str("++eot_char 0")
    
    def snd(self, *args, **kwargs):
        self.send_str(*args, **kwargs)
    
    def send_str(self, s):
        #dbg('Sending "%s"' % (s))
        '''
        With EOT on should not be needed
        for c in '\r\n+\x1b':
            s = s.replace(c, '\x1b' + c)
        '''
        
        '''
        Special care must be taken when sending binary data to instruments. If any of the
        following characters occur in the binary data -- CR (ASCII 13 0x0D), LF (ASCII 10 0x0A), ESC
        (ASCII 27 0x1B), '+' (ASCII 43 0x2B) - they must be escaped by preceding them with an ESC
        character
        '''
        if self.bin:
            for c in '\x1b\x2b\x0d\x0a':
                s = s.replace(c, '\x1b' + c)
        
        self.ser.writea(s + "\n")
        # FIXME: flow control deadlock can get us stuck here
        # need some sort of timeout mechanism
        self.ser.flush()
    
    def rcv(self, *args, **kwargs):
        return self.recv_str(*args, **kwargs)
    
    def recv_str(self, l=1024, empty=False, short=True):
        self.ser.writea('++read eoi\n')
        self.ser.flush()
        
        if self.bin:
            print("read() begin")
            s = self.ser.reada(l)
        else:
            print("readline() begin")
            s = self.ser.readlinea()
        assert type(s) is str, type(s)

        if not s and not empty:
            raise Timeout('Failed recv any bytes')
        if self.bin and short and len(s) != l:
            raise ShortRead()
        if not self.bin:
            s = s.rstrip()
        #print 'DBG: received "%s"' % (s)
        return s
        
    '''
    You can set the GPIB address from the front panel only.
    
    ++read_tmo_ms 3000
    ++addr 5
    *RST
    SYSTEM:VERSION?
    SYSTEM:ERROR?
    ++read eoi
    ++read 10
    
    -410: Query INTERRUPTED
    A command was received which sends data to the output buffer, but the output buffer contained data
    from a previous command (the previous data is not overwritten). The output buffer is cleared when
    power has been turned off, or after a *RST (reset) command has been executed.
    '''
    def snd_rcv(self, *args, **kwargs):
        return self.sendrecv_str(*args, **kwargs)

    def sendrecv_str(self, s, l=1024, empty=False, short=True):
        self.send_str(s)
        return self.recv_str(l=l, empty=empty, short=short)

    def sendrecv_astr(self, s, empty=False):
        '''Send receive adapter string.  No ++read is required'''
        self.send_str(s)
        
        # wait for response line
        s = self.ser.readlinea()
        if not s and not empty:
            raise Timeout('Failed recv')
        s = s.rstrip()
        #print 'received "%s"' % (s)
        return s
    
    def version(self):
        return self.sendrecv_astr('++ver')

    def dump_config(self):
        '''
        Having problem with a few GPIB adapters, reviewing all NVM to see what is different
        
        If enabled, the following configuration parameters are saved whenever they are
        updated - mode, addr, auto, eoi, eos, eot_enable, eot_char and read_tmo_ms.
        '''
        print('versions: %s' % self.version())
        print('versions: %s' % self.sendrecv_astr("++ver"))
        for cmd in  ('mode', 'addr', 'auto', 'eoi', 'eos', 'eot_enable', 'eot_char', 'read_tmo_ms'):
            print('%s: %s' % (cmd, self.sendrecv_astr("++%s" % cmd)))
    
    def local(self):
        self.send_str('++loc')

    '''
    only works as device
    really want below
    def status(self):
        return self.snd_rcv('++status')
    '''
    
    def spoll(self):
        return int(self.snd_rcv('++spoll'))

