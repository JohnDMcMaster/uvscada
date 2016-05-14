from uvscada.util import hexdump
from uvscada.ppro import PPro, parse

import argparse
import datetime
import json
import os
import time
import traceback

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Log Graupner Polaron Pro data')
    parser.add_argument('--port', default='/dev/ttyUSB0', help='ezlaze serial port')
    args = parser.parse_args()
    
    if os.path.exists('log'):
        raise Exception('Refusing to overwrite')
    os.mkdir('log')
    
    pp = PPro()
    itr = 0
    fj = open(os.path.join('log', 'log.jl'), 'w')
    while True:
        try:
            retb = pp.getb()
        except Exception as e:
            print 'WARNING: failure'
            traceback.print_exc()
            continue

        # 1 day charging => 24 * 60 * 60 =              86400
        # 3 month charging => 3 * 30 * 24 * 60 * 60 = 7776000
        # eh do 6 digit, mostly expect few days max
        with open(os.path.join('log', 'l%06d.bin' % itr), 'w') as f:
            f.write(retb)
        fj.write(json.dumps({'t': time.time(), 'i': itr}) + '\n')
        fj.flush()

        try:
            retd = parse(retb)
        except Exception as e:
            print 'WARNING: failure'
            traceback.print_exc()
            continue
        
        print '%s: I: % 4dmV, OM: %d, OS: %d, CN: %d, O: % 4dmV @ % 4dmA' % (
                datetime.datetime.now().isoformat(),
                retd['Input Voltage[1]'],
                retd['Operation Mode[1]'], retd['Operation Status[1]'], retd['Cycle Number[1]'],
                retd['Output Voltage[1]'], retd['Output Current[1]'])
        time.sleep(1)
        itr += 1
