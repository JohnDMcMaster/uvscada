'''
Design for and tested against NWR ezlaze but I imagine should work for other stuff as well
In part because I'm actually basing this off of the QuickLaze manual:
https://siliconpr0n.org/media/nwr/quicklaze/quicklaze-50st.pdf
The manual title implies quicklaze but its littered with ezlaze info
The main differences appears to be that quicklaze has a higher duty cycle (hence its name)

General notes:
-Switch operation
    L: emitted when switch START is entered from REMOTE
    R: emitted when switch REMOTE is entered from START
    I assume that switch is not operated
-CR+LF termination
-; Toggles between Program Mode and Menu Mode.
-Power bug
    Use @1 to turn on
    press OFF button
    System turns off
    Querying @ returns as on but system is off
    
    Note: reinforcing power does do the right thing and turn it on

Program ModE:
"x", "xx", "xxx" or "xxxx" where "x" is a positive integer or a character followed by "Enter".
The first digit specifies the Control Function. The number(s) following the first digit specifies
the value for the Control Function. except Function Number ";" (change modes), "P" (initiates
Program Mode) and "7" (Pulse Laser) where Enter is not required. For Function Numbers 1, 2
and 3 the characters "," "." "<" and ">" may also follow the Function Number.


ESC 
Aborts Function command 
or stops a laser burst. 
Displays the letter "E" after the
Function Number e.g. 2E or 7E.

P 
Initiates Program Mode 
Y


Start up menu:

;
                New Wave Research    -    Laser Control Menu
                --------------------------------------------
                Function           Laser            Function
                 Number           Function           Value  
                --------          --------          --------
                                  Laser OFF
                  @   -   Laser On/Off


@ - Turn Laser On/Off (Off=0, On=1) = 1
                New Wave Research    -    Laser Control Menu
                --------------------------------------------
                Function           Laser            Function
                 Number           Function           Value
                --------          --------          --------
                                  Laser  ON
                  1   -   Attenuator Setting         -  255
                  2   -   X Marker Setting           -  255
                  3   -   Y Marker Setting           -  255
                  4   -   Energy Setting             -  Hi
                  5   -   Single Pulse or Cont       -  Pul
                  6   -   Spot Marker Setting        -  Off
                  7   -   Pulse Laser
                  8   -   Wavelength Select          -  GRN
                  9   -   Number of Shots in Burst   -  1
                  A   -   Pulse Rate (Hz)            -  5
                  B   -   Filter Number Select       -  2
                  Q   -   Q-Switch On/Off            -  On
                  W   -   Warm Up Pulse Number       -  0
                  @   -   Laser On/Off


'''

import serial
import time
import pexpect.fdpexpect
import fdpexpect

class EzLaze(object):
    def __init__(self, port="/dev/ttyUSB0", ser_timeout=1.0):
        self.verbose = 0
        self.ser = serial.Serial(port,
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
        self.ser.flushInput()
        self.ser.flushOutput()
        self.mode = None
        self.e = fdpexpect.fdspawn(self.ser.fileno())
        # ESC to abort anything in progress
        self.send('\x1b')
        self.mode_prog()

    def expect(self, s, timeout=3.0):
        return self.e.expect(s, timeout=timeout)

    def send(self, cmd, *args):
        self.ser.write(cmd)
        self.ser.flush()
    
    def mode_prog(self):
        self.send('P')
        self.expect('Y')
        self.mode = 'prog'
    
    def mode_menu(self):
        # P can canonically be used to get to program mode
        # but there is no equivilent for menu mode
        # Switch to program mode and then toggle to arrive at menu mode
        self.mode_prog()
        self.send(';')
        self.expect('Laser Control Menu')
        self.mode = 'menu'
        # Eat any remaining menu data
        # Assume that if no data for 0.1 sec we are idle
        timeout_orig = self.ser.timeout
        try:
            self.ser.timeout = 0.1
            while True:
                s = self.ser.read()
                if len(s) == 0:
                    break
        finally:
            self.ser.timeout = timeout_orig

    '''
    @0Y0
        @0 => Y0
    @1Y1
        @1 => Y1
    @N1
        @ => N1
    '''
    def cmd(self, cmd, *args):
        cmd = str(cmd)
        if len(cmd) != 1:
            raise ValueError('Invalid cmd %s' % cmd)
        if self.mode != 'prog':
            raise Exception("Only program mode supported")
        # TOOD: I think 2 is supported
        # find reference to how these are sent
        if len(args) > 1:
            raise Exception('cmd must take no more than 1 arg')
        self.ser.write(cmd + ''.join([str(arg) for arg in args]) + "\r\n")
        self.ser.flush()
        # command should be echoed.  Ignore
        self.expect('Y')
        self.expect('\n')
        if self.verbose:
            print 'cmd %s: before %s' % (cmd, self.e.before.strip())
    
    def query(self, cmd):
        cmd = str(cmd)
        if len(cmd) != 1:
            raise ValueError('Invalid cmd %s' % cmd)
        if self.mode != 'prog':
            raise Exception("Only program mode supported")
        self.ser.write(cmd + "\r\n")
        self.ser.flush()
        self.expect('N')
        self.expect('\n')
        response = self.e.before.strip()
        if self.verbose:
            print 'query %s: before %s' % (cmd, response)
        return int(response)

    # @   -   Laser On/Off
    def on(self):
        self.cmd('@', 1)
    
    def off(self):
        self.cmd('@', 0)
    
    def is_on(self):
        # WARNING: see bug note at top
        return self.query('@')

    # 1   -   Attenuator Setting         -  255

    
    '''
    On my unit
    x begins to open around 23
    y begins to open around 29
    Also theres a fair amount of backlash
    Hmm still not square
    adjusted visually at w=8
    '''
    def shut_square(self, w):
        self.shut(x=1, y=1)
        self.shut(x=(w + 16), y=(w + 29))
    
    def shut_open(self):
        self.shut(xy=255)
        
    def shut_close(self):
        self.shut(xy=1)

    # 2   -   X Marker Setting           -  255
    # 3   -   Y Marker Setting           -  255
    def shut(self, xy=None, x=None, y=None):
        if xy is not None:
            x = xy
            y = xy

        # Seems that some delay is required for it to reliably take the next command
        # although it does seem to do some queuing
        # shutter also takes some time to move
        # (not fully accounted for here)
        
        if x is not None:
            if not 1 <= x <= 255:
                raise ValueError("Require 1 <= x=%d <= 255" % x)
            self.cmd('2', x)
            time.sleep(0.1)
        
        if y is not None:
            if not 1 <= y <= 255:
                raise ValueError("Require 1 <= y=%d <= 255" % y)
            self.cmd('3', y)
            time.sleep(0.1)
    
    # 4   -   Energy Setting             -  Hi
    # 5   -   Single Pulse or Cont       -  Pul
    # 6   -   Spot Marker Setting        -  Off
    
    # 7   -   Pulse Laser
    '''
    WARNING: will silently drop pulses if needs to cool down
    '''
    def pulse(self, n=1):
        for i in xrange(n):
            self.cmd('7')
            if i == n - 1:
                break
            # TODO: what is this limit?
            # can we get better closed loop control?
            # why is burst mode allowed to shoot faster?
            time.sleep(1)
    
    # 8   -   Wavelength Select          -  GRN
    # 9   -   Number of Shots in Burst   -  1
    # A   -   Pulse Rate (Hz)            -  5
    # B   -   Filter Number Select       -  2
    # Q   -   Q-Switch On/Off            -  On
    # W   -   Warm Up Pulse Number       -  0

