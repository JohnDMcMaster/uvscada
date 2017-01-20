import serial

class BK879B:
    def __init__(self, port='/dev/ttyUSB0'):
        self.ser = serial.Serial(port,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                rtscts=False,
                dsrdtr=False,
                xonxoff=False,
                timeout=1.0,
                # Blocking writes
                writeTimeout=None)
        self.ser.flushOutput()
        self.ser.flushInput()
        model = self.idn()[0]
        if model != '879B LCR Meter':
            raise Exception("Bad model: %s" % model)
    
    def auto_gen(self):
        '''
        +8.82304e-15,+0.00000e+00,N
        <Primary measured data, Secondly measured
        data, Tolerance Result > + <CR> <LF>
        '''
        while True:
            l = self.ser.readline().strip()
            m1, m2, tol = l.split(',')
            yield float(m1), float(m2), tol
    
    def snd(self, s):
        self.ser.write(s + '\n')
        self.ser.flush()
    
    def sndrcv(self, s):
        self.ser.write(s + '\n')
        self.ser.flush()
        l = self.ser.readline().strip()
        return l.split(',')
    
    def idn(self):
        '''Identify instrument'''
        # 879B LCR Meter,VER2.1.1102,SN127D15472
        model, ver, sn = self.sndrcv('*IDN?')
        return model, ver.replace('VER', ''), sn.replace('SN', '')
    
    def llo(self):
        '''
        Local Lockout. This means that all front panel
        buttons, including the "USB" key is not available.
        '''
        self.snd('*LLO')
    
    def gtl(self):
        '''
        Go to local. Puts the meter into the local state,
        clearing the remote state and front panel lockout.
        '''
        self.snd('*GTL')

    def func_set(self, func, sleep=True):
        '''
        FUNCtion:impa < L | C | R | Z >
        (Z for model 879B only)
        '''
        if not func in 'LCRZ':
            raise ValueError("Invalid function %s" % func)
        self.snd('FUNC:impa %c' % func)
        if sleep:
            # 40 ms was unreliable
            time.sleep(0.05)
        
    def func(self):
        '''
        Description: Query primary parameter
        Response: Return L, C, R, Z (879B
        only),NULL
        '''
        return self.sndrcv('FUNC:impa?')

    def fetch(self):
        '''
        Returns the primary, secondary
        display value and tolerance
        compared result of device's output buffer.
        Response: Return <NR3, NR3, NR1> format string
        '''
        l = self.sndrcv('FETCh?')
        print l
        m1, m2, tol = l
        return float(m1), float(m2), tol


import time

bk = BK879B()
print bk.idn()
if 0:
    for m in bk.auto_gen():
        print m
if 1:
    bk.func_set('C')
    while True:
        print '%0.1f: %0.5g' % (time.time(), bk.fetch()[0])
