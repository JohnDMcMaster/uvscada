import time
import argparse
import sys
from uvscada.plx_usb import PUGpib

class K2750(object):
    def __init__(self, port='/dev/ttyUSB0', clr=True):
        self.gpib = PUGpib(port=port, addr=16, clr=clr, eos=3, ser_timeout=1.0, gpib_timeout=0.9)

    def tim_int(self):
        '''Query timer interval'''
        return float(self.gpib.snd_rcv('TRIGger:TIMer?'))

    def local(self):
        '''Go to local mode'''
        # Error -113
        self.gpib.snd('GTL')

    def set_beep(self, en):
        '''
        You can disable the beeper for limits and continuity tests. However, when limits or CONT
        is again selected, the beeper will automatically enable.
        '''
        if en:
            self.gpib.snd("SYSTEM:BEEPER OFF")
        else:
            self.gpib.snd("SYSTEM:BEEPER ON")

    def error(self):
        '''Get next error from queue'''
        return self.gpib.snd_rcv("SYSTEM:ERROR?")

    def errors(self):
        ret = []
        while True:
            e = self.error()
            if e == '0,"No error"':
                return ret
            ret.append(e)
        
if __name__ == '__main__':    
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--port', default='/dev/ttyUSB0', help='GPIB serial port')
    args = parser.parse_args()

    k = K2750(port=args.port)
    self = k
    print 'Timer interval: %s' % k.tim_int()
    print "Errors begin: %s" % (k.errors(),)
        
    if 0:
        k.set_beep(1)

    if 0:
        print 'Entering local mode'
        k.local()

    if 0:
        print 'volt meas'
        # Voltage meas mode
        self.gpib.snd(":FUNC 'VOLT:DC'")
        # Errors end:   ['-213,"Init ignored"']
        self.gpib.snd("INIT")

    # Use when in continuous measurement mode
    if 0:
        print 'volt meas'
        # make sure its in cont mode
        # can query this to avoid the long delay?
        # self.gpib.snd("SYST:PRES")
        # Requires at least 1.1 sec delay
        # time.sleep(1.2)
        
        # DC voltage
        self.gpib.snd(":FUNC 'VOLT:DC'")
        # -1.25629986E-02VDC,+2319.404SECS,+10155RDNG#
        # -3.47094010E-06VDC,+4854.721SECS,+20115RDNG#
        # value, time since start?, sample since start?
        print self.gpib.snd_rcv(":DATA?")
        if 0:
            l = []
            tstart = time.time()
            for _i in xrange(100):
                l.append(self.gpib.snd_rcv(":DATA?"))
            print l
            # 82 per sec
            # Much less than read rate so don't worry about specific trigger
            meast = (time.time() - tstart) / len(l)
            print "Meas/sec: %0.3f" % (1.0/meast,)

    # This is intended to be used when continuous measurements are not being read
    if 0:
        print 'volt meas'
        # works but complains
        # Errors end:   ['-213,"Init ignored"']
        '''
        NOTE
        Note that sending INITiate while the instrument is performing
        measurements will cause error -213 (init ignored).

        With continuous initiation disabled (INITiate:CONTinuous OFF), you can use
        the INITiate command to trigger one or more measurements.
        '''
        print self.gpib.snd_rcv("READ?")
    
    if 1:
        print 'current meas'
        self.gpib.snd(":FUNC 'VOLT:DC'")
        time.sleep(0.2)
        self.gpib.snd(":FUNC 'CURR:DC'")
        # Seems to take at least 0.1 sec
        time.sleep(0.15)
        #print self.gpib.snd_rcv("READ?")
        # -4.15096054E-07ADC,+5064.727SECS,+22239RDNG#
        print self.gpib.snd_rcv(":DATA?")

    print "Errors end:   %s" % (k.errors(),)
