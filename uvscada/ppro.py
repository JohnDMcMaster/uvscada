

from uvscada.util import hexdump

import argparse
from collections import OrderedDict
from collections import namedtuple
import struct
import serial
import random
import crcmod

# Forward CRC-16-CCITT
crcf = crcmod.mkCrcFun(poly=0x11021, initCrc=0x0000, rev=False, xorOut=0x0000)

# namedtuple
PCmd = namedtuple('PCmd', 'res0 seq sum res3')
PCMD_FMT = 'BBB6s'

'''
Volt: mV
Amp: mA
Resistance: mOhm
'''

fields = '''\
res1
res2
Application Version
Product Code
Input Voltage[1]
Operation Mode[1]
Operation Status[1]
Cycle Number[1]
Minute[1]
Second[1]
Motor Minute[1]
Motor Second[1]
Warmer Minute[1]
Warmer Second[1]
Output Voltage[1]
Output Current[1]
Output Capacity[1]
Current Temperature[1]
Batt Cells[1]
Cell Voltage1[1]
Cell Voltage2[1]
Cell Voltage3[1]
Cell Voltage4[1]
Cell Voltage5[1]
Cell Voltage6[1]
Cell Voltage7[1]
Cell Resistance1[1]
Cell Resistance2[1]
Cell Resistance3[1]
Cell Resistance4[1]
Cell Resistance5[1]
Cell Resistance6[1]
Cell Resistance7[1]
Blc Pack Voltage[1]
Blc Avg Voltage[1]
Blc Gap Voltage[1]
Blc Max Voltage[1]
Blc Min Voltage[1]
Blc Cell Max[1]
Blc Cell Min[1]
Blc Dchg Count[1]
Capacity Rate[1]'''
'''
FIXME: hack
Lost sync sometime after
Output Capacity[1]
And before
Batt Resistance[1]
Need to consume 8 more bytes somehow
Cell resistances are 8 bit maybe?
'''
if 1:
    fields += '''
    pad1
    pad2'''

fields += '''
Batt Resistance[1]
Peak Temperature[1]
Average Voltage[1]
Motor Now Program Cycle[1]
Motor Program Run Delay[1]
Motor Current Average1[1]
Motor Current Average2[1]
Motor Current Average3[1]
Motor Current Average4[1]
Motor Current Average5[1]
Motor Current Average6[1]
Motor Current Peak1[1]
Motor Current Peak2[1]
Motor Current Peak3[1]
Motor Current Peak4[1]
Motor Current Peak5[1]
Motor Current Peak6[1]
Input Voltage[2]
Operation Mode[2]
Operation Status[2]
Cycle Number[2]
Minute[2]
Second[2]
NOUSE1
NOUSE2
NOUSE3
NOUSE4
Output Voltage[2]
Output Current[2]
Output Capacity[2]
Current Temperature[2]
Batt Cells[2]
Cell Voltage8[1]
Cell Voltage9[1]
Cell Voltage10[1]
Cell Voltage11[1]
Cell Voltage12[1]
Cell Voltage13[1]
Cell Voltage14[1]
Cell Resistance8[1]
Cell Resistance9[1]
Cell Resistance10[1]
Cell Resistance11[1]
Cell Resistance12[1]
Cell Resistance13[1]
Cell Resistance14[1]
Capacity Rate[2]
NOUSE5
NOUSE6
NOUSE7
NOUSE8
NOUSE9
NOUSE10
NOUSE11
NOUSE12
Batt Resistance[2]
Peak Temperature[2]
Average Voltage[2]
NOUSE13
NOUSE14
NOUSE15
NOUSE16
NOUSE17
NOUSE18
NOUSE19
NOUSE20
NOUSE21
NOUSE22
NOUSE23
NOUSE24
NOUSE25
NOUSE26
NOUSE27
NOUSE28
Cycle Charge Minute[1]
Cycle Charge Second[1]
Cycle Peak Voltage[1]
Cycle Charge Capacity[1]
Cycle Charge Res.[1]
Cycle Discharge Minute[1]
Cycle Discharge Second[1]
Cycle Discharge Capacity[1]
Cycle Average Voltage[1]
Cycle Discharge Resist[1]
Cycle Charge Minute[2]
Cycle Charge Second[2]
Cycle Peak Voltage[2]
Cycle Charge Capacity[2]
Cycle Charge Resistance[2]
Cycle Discharge Minute[2]
Cycle Discharge Second[2]
Cycle Discharge Capacity[2]
Cycle Average Voltage[2]
Cycle Discharge Res.[2]
NOUSE29
PAD1
PAD2
AC Check Flag
crc'''

PRply = namedtuple('PRply', '')
PRply_FMT = 'BBB6s'
PKT_SZ = 18 * 16 + 1

# Original encoding
opr_i2so = {
    0:  '0.Not Operation',
    1:  '1.Charge Mode',
    2:  '2.Discharge Mode',
    3:  '3.Delay Time',
    4:  '4.Charger Too Hot',
    5:  '5.Finish',
    6:  '6.Error',
    7:  '7.LCB ',
    8:  '8.HEAT',
    9:  '9.Motor',
    10: '10.Servo',
    11: '11.Cycle',
}

opr_i2s = {
    0:  'IDLE',
    1:  'CHARGE',
    2:  'DISCHARGE',
    3:  'DELAY',
    4:  'OVERHEAT',
    5:  'DONE',
    6:  'ERROR',
    7:  'LCB ',
    8:  'HEAT',
    9:  'MOTOR',
    10: 'SERVO',
    11: 'CYCLE',
}

stat_i2so = {
    0:  'Automatic Charge',
    1:  'Normal Charge',
    2:  'Linear Charge',
    3:  'Replex Charge',
    4:  'cc-cv Charge',
    5:  'Automatic Discharge',
    6:  'Normal Discharge',
    7:  'Linear Discharge',
    8:  'Delta-peak Finish',
    9:  'Zero Delta-peak Finish',
    10: 'cc-cv Full Finish',
    11: 'Cut-off Discharge Finish',
    12: 'Temperature Finish',
    13: 'Max Capacity Finish',
    14: 'Flat Limited Finish',
    15: 'Time Limited Finish',
    16: 'Tcs Capacity Finish',
}

class CRCBad(ValueError):
    pass

def parsef(f):
    return parse(f.read(PKT_SZ))

def parse(buff, convert=True, crc=True):
    pos = 0
    ret = {}
    ret = OrderedDict()
    if len(buff) != PKT_SZ:
        print 'Dump'
        hexdump(buff)
        raise ValueError("Bad buffer size")
    
    if ord(buff[0]) != 0x00:
        raise ValueError("Bad prefix")
    pos += 1
    
    ret['seq'] = ord(buff[1])
    pos += 1
    ret['seqn'] = ord(buff[2])
    pos += 1
    seqx = ret['seq'] ^ ret['seqn']
    if seqx != 0xFF:
        raise Exception("Unexpected seq 0x%02X w/ seqn 0x%02X => 0x%02X" % (ret['seq'], ret['seqn'], seqx))
    
    for field in fields.split('\n'):
        field = field.strip()
        v = struct.unpack('<H', buff[pos:pos+2])[0]
        if convert:
            if field in ('Operation Mode[1]', 'Operation Mode[2]'):
                v = opr_i2s[v]
            # FIXME: 2 bad
            elif field in ('Operation Status[1]', 'Operation Status[2]'):
            #elif field in ('Operation Status[1]',):
                v = stat_i2so[v]
        ret[field] = v
        pos += 2
    
    # 8 bytes leftover
    #hexdump(buff)
    if pos != PKT_SZ:
        raise Exception('Expected parse %d bytes but got %d' % (PKT_SZ, pos))
    
    if ret['res1'] != 0x0118:
        raise Exception("Unexpected res1: 0x%04X" % ret['res1'])
    if ret['res2'] != 0x0100:
        raise Exception("Unexpected res2: 0x%04X" % ret['res2'])
    
    if crc:
        buffc = buff[3:-2]
        check = crcf(buffc)
        if check != ret['crc']:
            raise CRCBad('CRC fail: given 0x%04X, calc 0x%04X' % (ret['crc'], check))
    
    return ret

def ppprint(d):
    print 'Data'
    #for k in sorted(d.keys()):
    for k in d.keys():
        if k == 'NOUSE':
            continue
        print '  % -32s %s' % (k, d[k])

class PPro(object):
    def __init__(self, port="/dev/ttyUSB0", ser_timeout=1.0):
        self.verbose = 0
        self.ser = serial.Serial(port,
                baudrate=115200,
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
        # FIXME: send dummy command
        self.seq = random.randint(1, 255)
        #self.seq = 0

    def getb(self):
        #  Ex: 00 01 FE 00 00 00 99 90 12
        cmd = struct.pack(PCMD_FMT, 0x00, self.seq, 0xFF - self.seq, '\x00\x00\x00\x99\x90\x12')
        # 0 appears to be invalid
        #print 'seq', self.seq
        #self.seq = (self.seq + 1) % 0x100
        if self.seq == 0xFF:
            self.seq = 1
        else:
            self.seq = self.seq + 1
        self.ser.flushInput()
        self.ser.write(cmd)
        self.ser.flush()
        reply = self.ser.read(18 * 16 + 1)
        return reply

    def get(self):
        return parse(self.getb())

        
