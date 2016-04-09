

from uvscada.util import hexdump

import argparse
from collections import OrderedDict
from collections import namedtuple
import struct
import serial
import random

# namedtuple
PCmd = namedtuple('PCmd', 'res0 seq sum res3')
PCMD_FMT = 'BBB6s'

fields = '''\
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
Capacity Rate[1]
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
NOUSE    
NOUSE    
NOUSE    
NOUSE    
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
NOUSE    
NOUSE    
NOUSE    
NOUSE    
NOUSE    
NOUSE    
NOUSE    
NOUSE    
Batt Resistance[2]    
Peak Temperature[2]    
Average Voltage[2]    
NOUSE    
NOUSE    
NOUSE    
NOUSE    
NOUSE    
NOUSE    
NOUSE    
NOUSE    
NOUSE    
NOUSE    
NOUSE    
NOUSE    
NOUSE    
NOUSE    
NOUSE    
NOUSE    
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
NOUSE    
AC Check Flag     
'''

PRply = namedtuple('PRply', '')
PRply_FMT = 'BBB6s'

def parse(buff):
    pos = 0
    ret = {}
    if len(buff) != 18 * 16 + 1:
        print 'Dump'
        hexdump(buff)
        raise ValueError("Bad buffer size")
    ret['seq'] = buff[1]
    pos = 7
    for field in fields.split('\n'):
        ret[field] = struct.unpack('<H', buff[pos:pos+2])[0]
        pos += 2
    # 8 bytes leftover
    #print pos, 18 * 16 + 1
    return ret


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
        self.ser.write(cmd)
        self.ser.flush()
        reply = self.ser.read(18 * 16 + 1)
        return reply
    
    def get(self):
        return parse(self.getb())

