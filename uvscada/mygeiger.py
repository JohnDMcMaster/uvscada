import serial
import sys
import time

class MyGeiger(object):
    def __init__(self, port='/dev/ttyUSB0'):
        self.ser = serial.Serial(port,
                # Because 9600 would have been too easy to guess
                baudrate=2400,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                rtscts=False,
                dsrdtr=False,
                xonxoff=False,
                timeout=0,
                # Blocking writes
                writeTimeout=None)
        self.ser.flushInput()
        self.ser.flushOutput()
        self.buff = bytearray()
        # consume any partial data coming in
        self.sync()

    def flush(self):
        self.ser.flushInput()
        self.buff = bytearray()
    
    def sync(self):
        # Wait a bit to see if in middle of transaction
        #  1000 * 8 * 8 / 2400 = 27 ms for a large transaction (if saturate UART)
        for i in xrange(2):
            self.buff += self.ser.read()
            pos = self.buff.find('\x0d')
            if pos >= 0:
                cpms = self.buff[0:pos]
                del self.buff[0:pos + 1]
                return
            time.sleep(0.03)

    def cpm(self, block=True):
        # One reading every 5.5 seconds or so
        while True:
            self.buff += self.ser.read()
            pos = self.buff.find('\x0d')
            if pos >= 0:
                cpms = self.buff[0:pos]
                del self.buff[0:pos + 1]
                return int(cpms)
            if not block:
                return None
            time.sleep(0.1)

