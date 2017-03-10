'''
SHP380AB contains a DS1993L-F5 iButton
Use BusPirate to read out data
Pinout here
https://siliconpr0n.org/nuc/doku.php?id=eberline:start

'''

import argparse
import fdpexpect
import serial
import struct
import time

from uvscada.util import hexdump

class BPSPI(object):
    def __init__(self, port="/dev/ttyUSB0", ser=None):
        self.verbose = 0
        if not ser:
            ser = serial.Serial(port,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                rtscts=False,
                dsrdtr=False,
                xonxoff=False,
                timeout=3.0,
                # Blocking writes
                writeTimeout=None)
        self.ser = ser
        self.ser.flushInput()
        self.ser.flushOutput()
        self.e = fdpexpect.fdspawn(self.ser.fileno())
        self.e.timeout = 1.0
        self.rst_sync()
        self.owire()
        self.ps_on()
        self.pu_on()
    
    def rst_sync(self):
        self.ser.flushInput()
        self.ser.flushOutput()
        # Reset
        self.snd('#')
        time.sleep(0.1)
        self.e.expect_exact('HiZ>')
        #self.snd('?')
        #self.e.expect_exact('HiZ>')
    
    def snd(self, cmd, *args):
        self.ser.write(cmd + '\n')
        self.ser.flush()
    
    def owire(self):
        '''
        HiZ>m
        1. HiZ
        2. 1-WIRE
        3. UART
        4. I2C
        5. SPI
        6. 2WIRE
        7. 3WIRE
        8. LCD
        9. DIO
        x. exit(without change)
        
        (1)>2
        1WIRE routines (C) 2000 Michael Pearce GNU GPL
        Ready
        1-WIRE>
        '''
        self.snd('m')
        
        # 2. 1-WIRE
        self.e.expect_exact('(1)>')
        self.snd('2')

        self.e.expect_exact('1-WIRE>')

    def ps_on(self):
        '''
        1-WIRE>W
        POWER SUPPLIES ON
        1-WIRE>
        '''
        self.snd('W')
        self.e.expect_exact('Power supplies ON')
        self.e.expect_exact('1-WIRE>')

    def ps_off(self):
        '''
        1-WIRE>w
        POWER SUPPLIES OFF
        1-WIRE>
        '''
        self.snd('W')
        self.e.expect_exact('POWER SUPPLIES OFF')
        self.e.expect_exact('1-WIRE>')

    def pu_on(self):
        '''
        1-WIRE>P
        Pull-up resistors ON
        Warning: no voltage on Vpullup pin
        1-WIRE>
        '''
        self.snd('P')
        self.e.expect_exact('Pull-up resistors ON')
        self.e.expect_exact('1-WIRE>')

    def r_all(self):
        '''
        1-WIRE>{ 0xCC 0xF0 0x00 0x00 r:512
        BUS RESET  OK
        WRITE: 0xCC
        WRITE: 0xF0
        WRITE: 0x00
        WRITE: 0x00
        READ: 0x10 0x00 0x00 ... 0x55 0x55 0x55
        1-WIRE>?
        '''
        self.snd('{ 0xCC 0xF0 0x00 0x00 r:512')
        self.e.expect_exact('BUS RESET  OK')
        self.e.expect_exact('READ: ')
        self.e.expect_exact('1-WIRE>')
        before = self.e.before.strip()
        ret = bytearray([int(x, 0) for x in before.split()])
        return ret

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dump SHP380 iButton using BusPirate')
    parser.add_argument('fn_out', default=None, nargs='?', help='')
    args = parser.parse_args()

    owire = BPSPI()
    rom = owire.r_all()
    
    mn = rom[6:16].replace('\x00', '')
    print 'P/N: %s' % mn
    sn = struct.unpack('>H', rom[3:5])[0]
    print 'S/N: %s' % sn
    
    if args.fn_out:
        open(args.fn_out, 'w').write(rom)
    else:
        print
        hexdump(rom)
