from uvscada.minipro import Minipro
from uvscada.util import hexdump, add_bool_arg
import os
import sys
import md5
import binascii
import subprocess
import time
import argparse
import tty
import termios
import select
import struct

def nextc():
    return sys.stdin.read(1) if select.select([sys.stdin,],[],[],0.0)[0] else None

def buff_print1(dat):
    # 4096 x ?
    rows = 4096 / 256
    cols = 4096 / rows
    for row in xrange(rows):
        for col in xrange(cols):
            val = ord(dat[row * cols + col])
            bl = val.bit_length()
            if bl <= 0:
                c = ' '
            elif bl <= 3:
                c = '.'
            elif bl <= 6:
                c = ':'
            else:
                c = '='
            sys.stdout.write(c)
        sys.stdout.write('\n')
    sys.stdout.flush()

#buff_print = buff_print2

def hexdump_sys(buff):
    open('/tmp/glitchmon.bin', 'w').write(buff)
    os.system('hexdump -C /tmp/glitchmon.bin')

def buff_op(l, r, op):
    l = str(l)
    r = str(r)
    ret = bytearray()
    
    if len(l) != len(r):
        raise ValueError()
    for i in xrange(0, len(l), 2):
        li = struct.unpack('<H', l[i:i+2])[0]
        ri = struct.unpack('<H', r[i:i+2])[0]
        resi = op(li, ri)
        ret += struct.pack('<H', resi)
    return str(ret)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='I leave all that I own to my cat guppy')
    args = parser.parse_args()

    m = Minipro(device='PIC16C57')
    baseline = m.read()
    or_buff = None
    
    ref = open('pic16c57_test1.bin')
    
    frame = 0
    while True:
        c = nextc()
        if c == 'q':
            break
        elif c == 'r':
            baseline = m.read()
            or_buff = None
        
        this = m.read()
        diff = buff_op(baseline, this, lambda l, r: (l - r) % 0x1000)
        
        '''
        if 1:
            d = buff_op(baseline, this, lambda l, r: (l - r) % 0x1000)
            if or_buff is None:
                or_buff = d
            else:
                or_buff = buff_op(or_buff, d, lambda l, r: (l + bool(r)) % 0x1000)
            out = or_buff
        '''
        
        os.system('clear')
        print frame
        #buff_print(out)
        hexdump_sys(diff)
        frame += 1


