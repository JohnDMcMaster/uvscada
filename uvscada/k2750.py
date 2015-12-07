from uvscada.plx_usb import PUGpib

import re
import time

class K2750(object):
    def __init__(self, port='/dev/ttyUSB0', clr=True):
        self.gpib = PUGpib(port=port, addr=16, clr=clr, eos=3, ser_timeout=1.0, gpib_timeout=0.9)
        self.func = None
        self.volt_dc_re = None
        self.curr_dc_re = None

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
    
    def volt_dc_ex(self):
        if self.func != 'VOLT:DC':
            self.gpib.snd(":FUNC 'VOLT:DC'")
            time.sleep(0.20)
            self.func = 'VOLT:DC'
        if self.volt_dc_re is None:
            # -1.25629986E-02VDC,+2319.404SECS,+10155RDNG#
            # -3.47094010E-06VDC,+4854.721SECS,+20115RDNG#
            self.volt_dc_re = re.compile("(.*)VDC,(.*)SECS,(.*)RDNG#")

        raw = self.gpib.snd_rcv(":DATA?")
        m = self.volt_dc_re.match(raw)
        if not m:
            raise Exception("Bad reading: %s" % (raw,))
        vdc = float(m.group(1))
        secs = float(m.group(2))
        rdng = float(m.group(3))
        return {"VDC": vdc, "SECS": secs, "RDNG#": rdng}

    def volt_dc(self):
        return self.volt_dc_ex()["VDC"]

    def curr_dc_ex(self):
        if self.func != 'CURR:DC':
            self.gpib.snd(":FUNC 'CURR:DC'")
            # Seems to take at least 0.1 sec
            # had problems with 0.15
            time.sleep(0.20)
            self.func = 'CURR:DC'
        if self.curr_dc_re is None:
            # -4.15096054E-07ADC,+5064.727SECS,+22239RDNG#
            self.curr_dc_re = re.compile("(.*)ADC,(.*)SECS,(.*)RDNG#")

        raw = self.gpib.snd_rcv(":DATA?")
        m = self.curr_dc_re.match(raw)
        if not m:
            raise Exception("Bad reading: %s" % (raw,))
        adc = float(m.group(1))
        secs = float(m.group(2))
        rdngn = float(m.group(3))
        return {"ADC": adc, "SECS": secs, "RDNG#": rdngn}

    def curr_dc(self):
        return self.curr_dc_ex()["ADC"]

