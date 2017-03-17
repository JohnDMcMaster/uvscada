'''
Bertan 225-05 5kV @ 5 mA power supply
Voltage control only, but you can define VI limits
Positive or negative polarity via back switch


NOTE: this uses custom protocol
ie not SCAPI or w/e
In particular, this uses GPIB OOB features a lot more

Teardown here: http://www.kerrywong.com/2016/11/20/bertanspellman-225-20r-hv-power-supply-teardown/
'''

from uvscada.plx_usb import PUGpib

import re
import time

'''
3.2
GPIB ADDRESS SWITCH
A unit's address is set using S9 switch
positions A4 through A0. A4 is the most significant
address bit and A0 the least significant bit. Bit A5 of the
address switch will enable or disable the power-on
Service Request.

3.3
GPIB PROTOCOL
The 225 Series implements the following GPIB
functions:
SH1
Source Handshake
AH1
Acceptor Handshake
T5
Basic Talker & Serial Poll L4
Basic Listener
RL1
Remote/Local with Lockout
PPO
No parallel poll response
CO
Not a controller
SR1
Service Request
DC1
Device Clear
DT1
Device Trigger


not getting far
hmm maybe read the status byte





HIGH VOLTAGE ON-OFF
Enables and Disables high voltage. This front panel switch overrides ALL controls in disabling
of the high voltage output.

Can I query if this is tripped?
'''

class Ber225(object):
    def __init__(self, port='/dev/ttyUSB0', addr=0):
        # clr turns off power
        self.gpib = PUGpib(port=port, addr=addr, clr=False, eos=3, ser_timeout=0.4, gpib_timeout=0.9)
        #self.chk_ok()

    def la(self, a):
        '''
        Program amps limit
        '''
        if a < 0 or a > 0.005:
            raise ValueError("Bad current %f" % a)
        s = 'L%0.4fM' % (a / 1000.)
        print s
        self.gpib.snd(s)

    def set_volt(self, v):
        '''
        Program volts
        
        A "K" indicates a kilovolt limit and an
        "M" or "U" indicates a milliamp or microamp limit,
        respectively. The syntax is:

        "L{numeric string}K"
        Kilovolt Limit (All models)
        
        "L{numeric string}M"
        Milliamp Limit (All models except 30kV & 50kV))
        
        "L{numeric string}U"
        Microamp Limit (Models 225- 30R & 225-50R only)



        3.4.1
        PROGRAMMING THE HIGH VOLTAGE
        OUTPUT ("P")
        "P {numeric string}K"
        
        Px.xxxxK (For 1kV, 3kV and 5kV models)

        3.4.1.1 PROGRAMMING THE OUTPUT VOLTAGE AS A PERCENTAGE
        "P (numeric string) %K"
        

        The actual high voltage output will not change to a
        newly programmed value after a program command has
        been issued until the unit also receives a device trigger
        bus command or the "G" command string (see sections
        3.3.4 and 3.4.3).
        
        '''
        if v < 0 or v > 5000:
            raise ValueError("Bad voltage %f" % v)
        self.gpib.snd('P%0.4fK' % (v / 1000.))

    # as percent
    #def pp(self, vp):
    #    pass

    def g(self):
        '''
        3.4.3
        ENTERING THE CURRENT
        PROGRAMMING & LIMIT VALUES ("G")


        When timing is not important, the "G" may be appended
        to the programming or limit command as shown below:
        Pxx.xxxKG
        Lx.xxxxMG
        '''
        self.gpib.snd('G')
    apply = g

    def z(self):
        '''
        3.4.4
        SHUTTING THE HIGH VOLTAGE
        OUTPUT OFF ("Z")
        The user may turn off the high voltage output without
        affecting the currently active programmed value. The
        syntax is:
        "Z" the single ASCII character
        This has the same effect as executing the device clear
        bus command
        '''
        self.gpib.snd('Z')
    off = z

    def r(self):
        '''
        3.4.5
        RESTORING THE HIGH VOLTAGE
        OUTPUT ("R")
        The high voltage output may be turned back on to the
        currently active programming value after having been
        shut off by a user command "Z" or by a trip due to
        overload. The sytax is:
        "R" the single ASCII character
        The high voltage output will return to the value that was
        programmed before the shut down. If the output was
        turned off by an overload trip, the cause of the overload
        should be corrected before trying to restore the output
        voltage or the trip will occur again.
        '''
        self.gpib.snd('R')


    def t0(self):
        '''
        3.4.8
        TRIGGERING METER READINGS OF
        THE OUTPUT ("T")
        Each unit has the capability to perform meter readings of its output voltage and current. The user may trigger a
        reading of the output voltage, the output current or both. The syntax is:
        "T {numeric}"
        Where {numeric} is the single ASCII character for 0, 1 or 2 and:
        T0: Triggers a measurement of the output voltage and current
        T1:  Triggers a measurement of the output current only
        After receiving one of the "T" commands, the unit will return a character string containing output status (Normal,
        Tripped or Shutdown) and voltage and/or current readings. The numerical formats are those used to enter
        voltage and current values.
        Below are the "T" commands with some typical strings that are returned to the GPIB controlled in response:
        T0
        "N Vxx.xxxK Ix.xxxxM"
        Note: These strings are, or are not, followed
        T1
        "S Vx.xxxxK"
        by Line Terminators CR/LF depending
        T2
        "T Ixxx.xxU"
        upon the chosen setting of switch S9,
        Position A6 (see section 3.2)
        A leading "N" in the string means that the output is on.
        A leading "S" means that the output was shut down by
        the user with a "Z" command or a device clear bus
        command. A leading "T" means that the output was
        tripped due to an overload detection. Also:
        "V" in the string means voltage
        "I" in the string means current
        "K" in the string means kilovolts
        "M" in the string means milliamps
        "U" in the string means microamps
        
        T0 N Vxx.xxxK Ix.xxxxM
        T1 S Vx.xxxxK
        T2 T Ixxx.xxU

        N V0.0349K I0.0009M
        T V0.0006K I0.0007M
        '''
        s = self.gpib.snd_rcv('T0')
        # N V0.0349K I0.0009M
        m = re.match(r'N V(.*)K I(.*)M', s)
        if m:
            # raw in kV, mA
            # convert to V, A
            return (1000 * float(m.group(1)), float(m.group(2)) / 1000.)

        # T V0.0006K I0.0007M
        m = re.match(r'T V(.*)K I(.*)M', s)
        if m:
            return (1000 * float(m.group(1)), float(m.group(2)) / 1000.)
            
        raise Exception(s)

    def m(self):
        # sometimes the first one freezes
        # why?
        # ah yeah something to do with spoll
        '''
        After receiving the "M" command, the unit will return a
        character string with its model number, output polarity
        setting and software revision.
        
        In the returned string, the "+225.03 re0.8" would denote
        a positive high voltage output from 0 to +3kV and the
        use of revision 0.8 software.
        
        Mine:
        M: +225.05 RE0.8

        "+225.0.5" 225-0.5R set to positive output polarity
        "-225.30" 225-30R set to negative polarity
        '''
        #print 'M: %s' % self.gpib.snd_rcv('M')
        #b.gpib.snd('M')
        #print 'M: %s' % b.gpib.ser.readline()
        s = self.gpib.snd_rcv('M')
        # +225.05 RE0.8
        m = re.match(r'(.)(.*) (.*)', s)
        if not m:
            raise Exception(s)
        polarity = m.group(1)
        model = m.group(2)
        fw = m.group(3)
        return (polarity, model, fw)
    model = m

    def chk_ok(self):
        spoll = self.gpib.spoll()
        # No commands issued yet
        if spoll & 0x80:
            return
        
        if spoll & 0x20:
            raise Exception('spoll 0x%02x: invalid command' % spoll)
        if spoll & 0x08:
            raise Exception('spoll 0x%02x: tripped' % spoll)
        if spoll & 0x04:
            raise Exception('spoll 0x%02x: OV' % spoll)
        if spoll & 0x02:
            raise Exception('spoll 0x%02x: OC' % spoll)

