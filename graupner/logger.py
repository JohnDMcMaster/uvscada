from uvscada.util import hexdump
from uvscada.ppro import PPro, parse, ppprint

import argparse
import binascii
import datetime
import json
import os
import time
import traceback

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Log Graupner Polaron Pro data')
    parser.add_argument('--port', default='/dev/ttyUSB0', help='Serial port')
    parser.add_argument('outf', default='log.jl', nargs='?', help='output file')
    args = parser.parse_args()
    
    pp = PPro(port=args.port)
    itr = 0
    fj = open(args.outf, 'w')
    while True:
        try:
            retb = pp.getb()
        except Exception as e:
            print 'WARNING: failure'
            traceback.print_exc()
            continue

        fj.write(json.dumps({'t': time.time(), 'i': itr, 'data': binascii.hexlify(retb)}) + '\n')
        fj.flush()

        try:
            retd = parse(retb)
        except Exception as e:
            print 'WARNING: failure'
            traceback.print_exc()
            continue
        
        #ppprint(retd)
        print '%s: I: % 4dmV, OM: % 6s, OS: % 6s, CN: % 6s, O: % 4dmV @ % 4dmA' % (
                datetime.datetime.now().isoformat(),
                retd['Input Voltage[1]'],
                retd['Operation Mode[1]'], retd['Operation Status[1]'], retd['Cycle Number[1]'],
                retd['Output Voltage[1]'], retd['Output Current[1]'])
        time.sleep(1)
        itr += 1
