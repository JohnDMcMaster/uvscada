import time
import argparse
import sys

from uvscada.k2750 import K2750

if __name__ == '__main__':    
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--port', default=None, help='GPIB serial port')
    args = parser.parse_args()

    k = K2750(port=args.port)
    print("opened")
    print(k.ident_ex())
    self = k
    # print('Timer interval: %s' % k.tim_int())
    # print("Errors begin: %s" % (k.errors(),))
    
    if 0:
        k.set_beep(1)

    if 0:
        print('Entering local mode')
        k.local()

    if 0:
        print('volt meas')
        # Voltage meas mode
        self.gpib.snd(":FUNC 'VOLT:DC'")
        # Errors end:   ['-213,"Init ignored"']
        self.gpib.snd("INIT")

    # Use when in continuous measurement mode
    if 0:
        print('volt meas')
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
        print(self.gpib.snd_rcv(":DATA?"))
        if 0:
            l = []
            tstart = time.time()
            for _i in range(100):
                l.append(self.gpib.snd_rcv(":DATA?"))
            print(l)
            # 82 per sec
            # Much less than read rate so don't worry about specific trigger
            meast = (time.time() - tstart) / len(l)
            print("Meas/sec: %0.3f" % (1.0/meast,))

    # This is intended to be used when continuous measurements are not being read
    if 0:
        print('volt meas')
        # works but complains
        # Errors end:   ['-213,"Init ignored"']
        '''
        NOTE
        Note that sending INITiate while the instrument is performing
        measurements will cause error -213 (init ignored).

        With continuous initiation disabled (INITiate:CONTinuous OFF), you can use
        the INITiate command to trigger one or more measurements.
        '''
        print(self.gpib.snd_rcv("READ?"))
    
    if 0:
        print('current meas')
        self.gpib.snd(":FUNC 'VOLT:DC'")
        time.sleep(0.2)
        self.gpib.snd(":FUNC 'CURR:DC'")
        # Seems to take at least 0.1 sec
        time.sleep(0.15)
        #print self.gpib.snd_rcv("READ?")
        # -4.15096054E-07ADC,+5064.727SECS,+22239RDNG#
        print(self.gpib.snd_rcv(":DATA?"))

    if 1:
        print('resistance meas')
        k.func_res()
        print('go1')
        print(k.res_ex())
        print('go2')
        print(k.res())

    if 1:
        print("Errors end:   %s" % (k.errors(),))
