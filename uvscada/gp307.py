'''
GP307 ion gauge
(with RS-232 option)
'''

import serial

# like on the display
def fmt(f):
    return '%1.1E' % f

class GP307(object):
    def __init__(self, port="/dev/ttyUSB0", ser_timeout=10.0):
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
        self.flush()
    
    def flush(self):
        '''
        measurements every 5 seconds
        9600 baud 
        1200 bytes / sec => 0.83 * 9/8 = 0.93 ms/char
        27 char message
        min transmit time: 27 * 0.93 = 25 ms
        should ideally flush for that in case we start in the middle of a message
        probably not that efficient..wait at least double
        '''

        timeout = self.ser.timeout
        try:
            self.ser.timeout = 0.1
            while True:
                l = self.ser.readline()
                # finished command in progress => flushed
                if not l:
                    return
                # a finished command => done
                if l[-1] == '\n':
                    return
        finally:
            self.ser.timeout = timeout
                

    def get(self):
        '''Return ion gauge, TC A, TC B.  Up to 5 seconds on healthy system'''
        # 9.90E+09,6.10E-02,9.90E+09
        l = self.ser.readline().strip()
        #print l
        ig, a, b = l.split(',')
        return float(ig), float(a), float(b)
