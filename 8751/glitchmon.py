from uvscada.minipro import Minipro
from uvscada.util import hexdump, add_bool_arg
import os
import sys
import md5
import binascii
import subprocess
import time
import argparse

def mprint(dat):
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

def diff(l, r):
    l = bytearray(l)
    r = bytearray(r)
    ret = bytearray()
    
    if len(l) != len(r):
        raise ValueError()
    for i in xrange(len(l)):
        ret.append((l[i] - r[i]) % 0x100)
    return str(ret)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='I leave all that I own to my cat guppy')
    args = parser.parse_args()

    m = Minipro(device='87C51')
    baseline = m.read()
    
    frame = 0
    while True:
        this = m.read()
        d = diff(baseline, this)
        os.system('clear')
        print frame
        mprint(d)
        frame += 1
