
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
    def __init__(self, port="/dev/ttyS0", baudrate=9600, timeout=0):
        self.port = port
        self.ser = serial.Serial(port,                          
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                rtscts=False,
                dsrdtr=False,
                xonxoff=False,
                timeout=0,
                writeTimeout=0)
    
    def interface(self):
        return "RS232"
    
    def send_str(self, s):
        print 'DBG: sending "%s"' % (s)
        s += "\n"
        self.ser.write(s)
        self.ser.flush()
    
    def recv_str(self):
        s = self.ser.readline(3)
        s = s.rstrip()
        print 'DBG: received "%s"' % (s)
        return s
    
    def sendrecv_str(self, s):
        # send without sleep
        self.ser.write(s + '\n')
        self.ser.flush()
        
        # wait for response line
        s = self.ser.readline(3)
        s = s.rstrip()
        #print 'received "%s"' % (s)
        return s

    def version(self):
        return 'N/A'
        

'''
outp: 1 or 2
Device tracks which is currently enabled
By default commands act on the last selected output
Option argument to per-output commands can switch output if not already selected
'''
class PS:
    def __init__(self, io, verbose=False):
        self.verbose = verbose
        self.vendor = None
        self.model = None

        # Active rail for commands, unknown at init
        self.outp = None
        self.io = io
        # Make sure simple queries work
        self.version()

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

    def off(self):
        '''Turn off both outputs'''
        self.io.send_str("OUTPUT OFF")
    
    def on(self):
        '''Turn on both outputs'''
        self.io.send_str("OUTPUT ON")
    
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
            self.ser.write("*OPC?\012")
            self.ser.flush()
            rx = self.ser.readline(100).rstrip()
            print "got ",rx
            if(rx == "1"):
                break
    
    def apply(self, voltage, current):
        '''Set both voltage and current at once?'''
        self.ser.write("APPL %s,%s" % (voltage, current))


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

    def reset(self):
        '''Reset the device entirely'''
        self.sersend_str("SYSTEM:BEEPER")

    def clear(self):
        '''Clear error queue'''
        self.io.send_str("SYSTEM:BEEPER")

    def get_error(self):
        '''Get next error from queue'''
        return self.io.sendrecv_str("SYSTEM:ERROR?")

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

if __name__ == '__main__':
    import argparse
    import random
    from plx_usb import PUGpib

    parser = argparse.ArgumentParser(description='Write a flash device to death, recording health as we go')
    parser.add_argument('--buffer', action='store_true', help='Unless set will use unbuffered I/O')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('ps', help='Device to act on')
    parser.add_argument('action', help='One of: on, off, beep, text')
    args = parser.parse_args()
    action = args.action.upper()

    io = PUGpib(args.ps)
    ps = PS(io=io, verbose=args.verbose)
    if action == 'OFF':
        print 'Turning off'
        ps.off()
    elif action == 'ON':
        print 'Turning on'
        ps.on()
    elif action == 'BEEP':
        print 'The machine that goes beep!'
        ps.beep()
    elif action == 'TEXT':
        print 'Sending diabolical message'
        msgs = ['MAYONAIS LO', ('turbo-', 'encabulator', 'online')]
        msgs = ['MAYONAIS LO', 'MELTDWN NOW']
        msg = random.sample(msgs, 1)[0]
        for i in xrange(3):
            if type(msg) == tuple:
                for m in msg:
                    ps.text(msg)
                    time.sleep(0.5)
            else:
                ps.text(msg)
                time.sleep(0.5)
            ps.text('')
            time.sleep(0.5)
        ps.text(msg)
    elif action == 'GPIB':
        io.dump_config()
    else:
        print 'invalid action %s' % action

