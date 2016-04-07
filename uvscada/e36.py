
'''
Dual output E3648A 0-8V / 0-20V 2.5A
http://cp.literature.agilent.com/litweb/pdf/E3646-90001.pdf

'''
import time
import sys
import datetime
import serial

class Timeout(Exception):
    pass

def now():
    return datetime.datetime.utcnow().isoformat()

def dbg(s):
    if 0:
        print 'GPIO %s: %s' % (now(), s)

    
'''
*********************************
Serial
*********************************

Just send commands verbatim
'''
class PUSerial:
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600, timeout=0, verbose=False):
        self.port = port
        self.verbose = verbose
        self.ser = serial.Serial(port,                          
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                rtscts=False,
                dsrdtr=False,
                xonxoff=False,
                timeout=3,
                writeTimeout=0)
        self.ser.flushInput()
        self.ser.flushOutput()
    
    def interface(self):
        return "RS232"
    
    def send_str(self, s):
        if self.verbose:
            print 'DBG: sending "%s"' % (s)
        s += "\n"
        self.ser.write(s)
        self.ser.flush()
    
    def recv_str(self):
        s = self.ser.readline()
        s = s.rstrip()
        if self.verbose:
            print 'DBG: received "%s"' % (s)
        return s
    
    def sendrecv_str(self, s):
        if self.verbose:
            print 'DBG: sending "%s"' % (s)
        # send without sleep
        self.ser.write(s + '\n')
        self.ser.flush()
        
        # wait for response line
        s = self.ser.readline()
        s = s.rstrip()
        if self.verbose:
            print 'DBG: received "%s"' % (s)
        return s

    def version(self):
        return 'N/A'
        

'''
outp: 1 or 2
Device tracks which is currently enabled
By default commands act on the last selected output
Option argument to per-output commands can switch output if not already selected
'''
class E36:
    def __init__(self, io, verbose=False):
        self.verbose = verbose
        self.vendor = None
        self.model = None

        # Active rail for commands, unknown at init
        self.outp = None
        self.io = io
        # Make sure simple queries work
        if not self.version():
            raise Exception("Failed init")

    '''
    *********************************8
    MISC
    *********************************8
    '''
    
    def version(self):
        return self.io.sendrecv_str("SYSTEM:VERSION?")
    
    def ident(self):
        '''
        PS ident: ['HEWLETT-PACKARD', 'E3632A', '0', '1.1-5.0-1.0']
        '''
        ret = self.io.sendrecv_str("*IDN?").split(',')
        self.vendor = ret[0]
        self.model = ret[1]
        return (self.vendor, self.model)

    def remote(self):
        '''Put into remote mode?  Required before running any commands'''
        self.io.send_str("SYSTEM:REMOTE")

    def local(self):
        '''Put into local mode?  Evidently displays better'''
        #self.io.send_str("SYSTEM:LOCAL")        # to make display updates in real time
        # for some reason you need to issue the GPIB instead of the device local command
        self.io.local()

    def off(self, tsleep=0.2):
        '''Turn off both outputs'''
        self.io.send_str("OUTPUT OFF")
        # Copied from on.  Needed?
        time.sleep(tsleep)
    
    def on(self, tsleep=0.2):
        '''Turn on both outputs'''
        self.io.send_str("OUTPUT ON")
        # 0.1 causes error, 0.15 fine
        time.sleep(tsleep)
    
    def set_outp(self, outp):
        '''Force selecting given rail'''
        if not outp in (1, 2):
            raise Exception('Bad outp %s' % (outp,))
        # FIXME: hack
        if self.model == 'E3632A':
            return
        self.io.send_str("INSTRUMENT:SELECT OUTP%d" % outp)
        self.outp = outp
    
    def disp_vi(self, outp=None):
        '''display actual currents on front panel'''   
        # FIXME: hack
        if self.model == 'E3632A':
            return
        if outp is not None and outp != self.outp:
            self.set_outp(outp)
        self.io.send_str("DISP:MODE VI")
    
    def wait_ready(self):
        '''
        Generally, it is best to use the "Operation Complete" bit (bit
        0) in the Standard Event register to signal when a command
        sequence is completed. This bit is set in the register after an
        *OPC command has been executed. If you send *OPC after a
        command which loads a message in the power supply's
        output buffer (query data), you can use the "Operation
        Complete" bit to determine when the message is available.
        However, if too many messages are generated before the
        *OPC command executes (sequentially), the output buffer
        will overload and the power supply will stop processing
        commands.
        '''
        while True:
            print "sending *OPC?"
            self.io.send_str("*OPC?\012")
            self.ser.flush()
            rx = self.ser.readline(100).rstrip()
            print "got ",rx
            if(rx == "1"):
                break
    
    def apply(self, voltage, current):
        '''Set both voltage and current at once?'''
        self.io.send_str("APPL %s,%s" % (voltage, current))


    '''
    Errors are retrieved in the first- in- first- out (FIFO) order.
    The first error returned is the first error that was stored.
    Errors are cleared as you read them. When you have read all
    errors from the queue, the ERROR annunciator turns off and
    the errors are cleared. The power supply beeps once each
    time an error is generated.
    If more than 20 errors have occurred, the last error stored
    in the queue (the most recent error) is replaced with
    - 350, "Queue overflow". No additional errors are stored until
    you remove errors from the queue. If no errors have
    occurred when you read the error queue, the power supply
    responds with +0, "No error" over the remote interface or NO
    ERRORS from the front panel.
    The error queue is cleared by the *CLS (clear status)
    command or when power is cycled. The errors are also
    cleared when you read the queue.
    The *RST (reset) command does not clear the error queue.
    '''
    def beep(self):
        '''Call this to annoying your labmates'''
        self.io.send_str("SYSTEM:BEEPER")

    def text(self, s):
        '''Call this to put creepy messages directly on the display'''
        if len(s) > 11:
            raise Exception('string too long')
        self.io.send_str("DISPLAY:TEXT \"%s\"" % (s,))

    def text_clr(self):
        self.io.send_str("DISPlay:TEXT:CLEar")

    def rst(self, tsleep=1.0):
        '''Reset the device except for errors'''
        self.io.send_str("*RST")
        # Device locks up for a bit
        time.sleep(tsleep)

    def clr(self):
        '''Clear error queue'''
        self.io.send_str("*CLS")

    def get_err(self):
        '''Get next error from queue'''
        return self.io.sendrecv_str("SYST:ERR?")

    '''
    *********************************8
    CURRENT
    *********************************8
    '''
    
    def curr(self, outp=None):
        '''Get current reading'''
        return float(self.io.sendrecv_str("MEAS:CURR?"))

    def curr_max(self, outp=None):
        '''Get current setpoint as set by set_curr'''
        return float(self.io.sendrecv_str("CURR?"))

    def set_curr(self, current, outp=None):
        '''Set current limit on given output'''
        if outp is not None and outp != self.outp:
            self.set_outp(outp)
        self.io.send_str("CURR %3.3f" % current)

    '''
    *********************************8
    VOLTAGE
    *********************************8
    '''
    
    # 0.185 s over serial
    def volt(self, outp=None):
        '''Get voltage reading'''
        if outp is not None and outp != self.outp:
            self.set_outp(outp)
        return float(self.io.sendrecv_str("MEAS:VOLT?"))
    
    def volt_max(self, outp=None):
        '''Get voltage setpoint'''
        if outp is not None and outp != self.outp:
            self.set_outp(outp)
        return float(self.io.sendrecv_str("VOLT?"))

    def set_volt(self, volt, outp=None):
        '''Set voltage limit on given output'''
        if outp is not None and outp != self.outp:
            self.set_outp(outp)
        self.io.send_str("VOLT %3.3f" % (volt,))
    
    def set_ovp(self, volt, outp=None):
        '''Set over voltage protection limit on given output'''
        if outp is not None and outp != self.outp:
            self.set_outp(outp)
        self.io.send_str("VOLTAGE:PROT %3.3f" % (volt,))

    def ovp_enb(self, outp=None):
        '''Enable over voltage protection'''
        if outp is not None and outp != self.outp:
            self.set_outp(outp)
        self.io.send_str("VOLTAGE:PROT:STATE ON")
    
    def ovp_dis(self, outp=None):
        '''Disable over voltage protection'''
        if outp is not None and outp != self.outp:
            self.set_outp(outp)
        self.io.send_str("VOLTAGE:PROT:STATE OFF")
    
    def ovp_clr(self, outp=None):
        '''Clear voltage protect fault?'''
        if outp is not None and outp != self.outp:
            self.set_outp(outp)
        self.io.send_str("VOLTAGE:PROT:CLEAR")

def print_errors(ps):
    print 'Errors:'
    errors = []
    while True:
        s = ps.get_err()
        if s == '+0,"No error"':
            break
        errors.append(s)
    if errors:
        for error in errors:
            print '  %s' % error
    else:
        print '  None'
