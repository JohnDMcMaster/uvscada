"""
For both K2700 and K2750
But I had a K2750 first
"""

from pymeasure.instruments.keithley import Keithley2700
from pymeasure.adapters import PrologixAdapter

import re
import time
import glob

# -1.25629986E-02VDC,+2319.404SECS,+10155RDNG#
# -3.47094010E-06VDC,+4854.721SECS,+20115RDNG#
volt_dc_re = re.compile("(.*)VDC,(.*)SECS,(.*)RDNG#")
# -4.15096054E-07ADC,+5064.727SECS,+22239RDNG#
curr_dc_re = re.compile("(.*)ADC,(.*)SECS,(.*)RDNG#")
# +9.9E37,+201975.327SECS,+1846855RDNG#
# +6.97856784E-01OHM,+201938.582SECS,+1846490RDNG#
res_re = re.compile("(.*),(.*)SECS,(.*)RDNG#")

class K2700(object):
    def __init__(self, port=None, clr=True, ident=True):
        if port is None:
            devices = glob.glob("/dev/serial/by-id/usb-Prologix_Prologix_GPIB-USB_Controller_*")
            assert len(devices), "No GPIB found"
            port = devices[0]

        self.adapter = PrologixAdapter(port)
        self.instrument = Keithley2700(self.adapter.gpib(5))
        self.func = None
        self.vendor = None
        self.model = None
        self.sn = None
        if ident:
            vendor, model = self.ident()
            # print("ident init", vendor, model)
            if (vendor, model) != ('KEITHLEY INSTRUMENTS INC.', 'MODEL 2750') and (vendor, model) != ('KEITHLEY INSTRUMENTS INC.', 'MODEL 2700'):
                raise ValueError('Bad instrument: %s, %s' % (vendor, model))

    def ident(self):
        # just vendor, model
        return self.ident_ex()[0:2]
        
    def ident_ex(self):
        '''
        Returns the manufacturer, model number, serial
        number, and firmware revision levels of the
        unit.
        ['KEITHLEY INSTRUMENTS INC.', 'MODEL 2750', '0967413', 'A07  /A01']
        '''
        tmp = self.instrument.ask("*IDN?")
        # print("ident debug", tmp)
        ret = tmp.split(',')
        self.vendor = ret[0]
        self.model = ret[1]
        sn = ret[2]
        fw = ret[3]
        return (self.vendor, self.model, sn, fw)

    def card_sn(self):
        return self.gpib.ask("SYSTem:CARD1:SNUMber?")

    def tim_int(self):
        '''Query timer interval'''
        return float(self.instrument.ask('TRIGger:TIMer?'))

    def local(self):
        '''Go to local mode'''
        # Error -113
        self.instrument.ask('GTL')

    def set_beep(self, en):
        '''
        You can disable the beeper for limits and continuity tests. However, when limits or CONT
        is again selected, the beeper will automatically enable.
        '''
        if en:
            self.instrument.ask("SYSTEM:BEEPER OFF")
        else:
            self.instrument.ask("SYSTEM:BEEPER ON")

    def error(self):
        '''Get next error from queue'''
        return self.instrument.ask("SYSTEM:ERROR?").strip()

    def errors(self):
        ret = []
        while True:
            e = self.error()
            if e == '0,"No error"':
                return ret
            ret.append(e)
        return ret
    
    def volt_dc_ex(self):
        if self.func != 'VOLT:DC':
            self.instrument.ask(":FUNC 'VOLT:DC'")
            time.sleep(0.20)
            self.func = 'VOLT:DC'

        raw = self.instrument.ask(":DATA?")
        m = volt_dc_re.match(raw)
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
            self.instrument.ask(":FUNC 'CURR:DC'")
            # Seems to take at least 0.1 sec
            # had problems with 0.15
            time.sleep(0.20)
            self.func = 'CURR:DC'

        raw = self.instrument.ask(":DATA?")
        m = curr_dc_re.match(raw)
        if not m:
            raise Exception("Bad reading: %s" % (raw,))
        adc = float(m.group(1))
        secs = float(m.group(2))
        rdngn = float(m.group(3))
        return {"ADC": adc, "SECS": secs, "RDNG#": rdngn}

    def curr_dc(self):
        return self.curr_dc_ex()["ADC"]

    def set_func(self, mode, lazy=True):
        if lazy and self.func == mode:
            return
        self.instrument.ask(":FUNC '%s'" % (mode,))
        # Seems to take at least 0.1 sec
        # had problems with 0.15
        time.sleep(0.20)
        self.func = mode

    def func_res(self, lazy=True):
        self.set_func("RES", lazy=lazy)

    def res_ex(self):
        self.set_func("RES")

        raw = self.instrument.ask(":DATA?")
        m = res_re.match(raw)
        if not m:
            raise Exception("Bad reading: %s" % (raw,))
        adc = m.group(1)
        if adc.find('OHM') >= 0:
            adc = float(adc.replace('OHM', ''))
        else:
            adc = float('inf')
        # consistently got this, not sure why
        # restarting unit fixed it
        # +9.9E37,+45775778+9.9E37SECS,+45775991RDNG#
        # print(raw)
        secs = float(m.group(2))
        rdngn = float(m.group(3))
        return {"ADC": adc, "SECS": secs, "RDNG#": rdngn}

    def res(self):
        return self.res_ex()["ADC"]

K2750 = K2700
