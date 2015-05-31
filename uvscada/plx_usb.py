'''
GPIB adapter
PROLOGIX GPIB-USB CONTROLLER
REV 6.4.1
http://prologix.biz/getfile?attachment_id=2
'''

import serial
        

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
    def __init__(self, port="/dev/ttyS0", timeout=3, addr=5):
        self.port = port
        self.addr = addr
        self.ser = serial.Serial(port,
                # They claim this parameter is ignored                          
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                rtscts=False,
                dsrdtr=False,
                xonxoff=False,
                timeout=timeout,
                # Blocking writes
                writeTimeout=None)
        
        
        # Clear any previous partial command
        self.send_str('')
        # Clear any data laying around
        self.ser.flushInput()
        self.ser.flush()
        
        self.send_str('++clr')
        # ++addr 5\n"
        self.send_str("++addr %d" % (self.addr,))
        
        # Will generate a bunch of interrupted errors if you don't set this (default 1)
        self.send_str('++auto 0')
        '''
        ++eos 0    Append CR+LF to instrument commands (appears to be default)
        ++eos 1    Append CR to instrument commands
        ++eos 2    Append LF to instrument commands
        ++eos 3    Do not append anything to instrument commands
        ++eos      Query current EOS state
        '''
        self.send_str('++eos 0')
        self.send_str('++read_tmo_ms 3000')
        
        # Make sure simple queries work
        self.version()
    
    def set_addr(self, addr):
        self.send_astr
    
    def interface(self):
        return "GPIB"
    
    def send_str(self, s):
        dbg('Sending "%s"' % (s))
        s += '\n'
        '''
        With EOT on should not be needed
        for c in '\r\n+\x1b':
            s = s.replace(c, '\x1b' + c)
        '''
        self.ser.write(s)
        # FIXME: flow control deadlock can get us stuck here
        # need some sort of timeout mechanism
        self.ser.flush()
    
    def recv_str(self):
        self.ser.write('++read eoi\n')
        self.ser.flush()
        
        s = self.ser.readline(100)
        if not s:
            raise Timeout('Failed recv')
        s = s.rstrip()
        print 'DBG: received "%s"' % (s)
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
    def sendrecv_str(self, s):
        self.send_str(s)
        self.send_str('++read eoi')
        
        # wait for response line
        s = self.ser.readline()
        if not s:
            raise Timeout('Failed recv')
        s = s.rstrip()
        #print 'received "%s"' % (s)
        return s

    def sendrecv_astr(self, s):
        '''Send receive adapter string.  No ++read is required'''
        self.send_str(s)
        
        # wait for response line
        s = self.ser.readline()
        if not s:
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
        print 'versions: %s' % self.version()
        print 'versions: %s' % self.sendrecv_astr("++ver")
        for cmd in  ('mode', 'addr', 'auto', 'eoi', 'eos', 'eot_enable', 'eot_char', 'read_tmo_ms'):
            print '%s: %s' % (cmd, self.sendrecv_astr("++%s" % cmd))
    
    def local(self):
        self.send_str('++loc')

