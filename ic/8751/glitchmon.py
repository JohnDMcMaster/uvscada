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

'''
# http://stackoverflow.com/questions/510357/python-read-a-single-character-from-the-user
# hmm don't think this really did anything useful: still have to press enter
def nextc():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
'''

def nextc():
    return sys.stdin.read(1) if select.select([sys.stdin,],[],[],0.0)[0] else None

'''
def nextc():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        s = select.select([sys.stdin,],[],[],0.0)[0]
        print s
        return sys.stdin.read(1) if s else None
        # return sys.stdin.read(1) if select.select([sys.stdin,],[],[],0.0)[0] else None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
'''

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
def buff_print2(dat):
    # 4096 x ?
    rows = 4096 / 256
    cols = 4096 / rows
    for row in xrange(rows):
        for col in xrange(cols):
            #if col > 209:
            #    break
            if col == cols / 2:
                sys.stdout.write('\n')
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

buff_print = buff_print2

def buff_op(l, r, op):
    l = bytearray(l)
    r = bytearray(r)
    ret = bytearray()
    
    if len(l) != len(r):
        raise ValueError()
    for i in xrange(len(l)):
        ret.append(op(l[i], r[i]))
    return str(ret)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='I leave all that I own to my cat guppy')
    args = parser.parse_args()

    m = Minipro(device='87C51')
    baseline = m.read()
    or_buff = None
    
    frame = 0
    while True:
        c = nextc()
        if c == 'q':
            break
        elif c == 'r':
            baseline = m.read()
            or_buff = None
        
        this = m.read()
        if 0:
            out = buff_op(baseline, this, lambda l, r: (l - r) % 0x100)
        if 1:
            d = buff_op(baseline, this, lambda l, r: (l - r) % 0x100)
            if or_buff is None:
                or_buff = d
            else:
                or_buff = buff_op(or_buff, d, lambda l, r: (l + bool(r)) % 0x100)
            out = or_buff
        os.system('clear')
        print frame
        buff_print(out)
        frame += 1
