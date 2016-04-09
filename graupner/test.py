from uvscada.util import hexdump
from uvscada.ppro import PPro

import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Use ezlaze with LinuxCNC to carve a bitmap')
    parser.add_argument('--port', default='/dev/ttyUSB0', help='ezlaze serial port')
    args = parser.parse_args()
    
    pp = PPro()
    ret = pp.get()
    print ret
    for f in ('Application Version', 'Product Code', 'Input Voltage[1]', 'Operation Mode[1]', 'Operation Status[1]', 'Cycle Number[1]', 'Minute[1]', 'Second[1]'):
        print f, ret[f]

