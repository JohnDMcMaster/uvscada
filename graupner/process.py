from uvscada.util import hexdump
from uvscada.ppro import parse, CRCBad

import argparse
import os
import time
import matplotlib.pyplot as plt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze data')
    parser.add_argument('din', default='log', nargs='?', help='log dir')
    args = parser.parse_args()
    
    itr = 0
    datas = []
    print 'Loading...'
    tprint = time.time()
    ver_ref = None
    crc = 0
    while True:
        if 0 and itr > 1000:
            break
        if time.time() - tprint > 5.0:
            print '%d' % itr
            tprint = time.time()
        fn = os.path.join(args.din, 'l%06d.bin' % itr)
        try:
            raw = open(fn).read()
        except IOError:
            break
        try:
            dec = parse(raw, convert=False)
        except CRCBad:
            print 'WARNING: %s bad CRC' % (fn,)
            crc += 1
            itr += 1
            continue
        except Exception:
            print fn
            raise
        
        if 0:
            ver = dec['Application Version']
            if ver_ref is None:
                ver_ref = ver
            elif ver_ref != ver:
                print fn, ver_ref, ver
                raise Exception('Version')
        
        if 0:
            v = dec['Input Voltage[1]']
            if v > 12200 or v < 11800:
                print fn, v
                raise Exception('Input Voltage[1]')

        datas.append(dec)
        itr += 1
    print 'Loaded w/ %d bad CRC' % crc
    if 0:
        print 'Checking'
        for i, v in enumerate([x['Input Voltage[1]'] for x in datas]):
            if v > 12200 or v < 11800:
                print i, v
                raise Exception()
        print 'pass'
    '''
    Is not actaully a sequence number so much as a timer it seems
    Counts down, sometimes stays flat
    '''
    if 0:
        print 'Checking'
        seq_exp = None
        for i, seq in enumerate([x['seq'] for x in datas]):
            if seq_exp is not None:
                if seq_exp != seq:
                    print i, seq_exp, seq
                    #raise Exception()
            if seq == 0xFF:
                seq_exp = 0x01
            else:
                seq_exp = seq + 1
        print 'pass'
    
    if 0:
        plt.clf()
        #plt.gca().get_yaxis().get_major_formatter().set_scientific(False)
        plt.plot([x['Input Voltage[1]'] for x in datas])
        plt.show()
    if 0:
        plt.clf()
        #plt.gca().get_yaxis().get_major_formatter().set_scientific(False)
        plt.plot([x['seq'] for x in datas])
        plt.show()
    if 1:
        for k in datas[0]:
            print k
            plt.clf()
            #plt.gca().get_yaxis().get_major_formatter().set_scientific(False)
            y = [x[k] for x in datas]
            # skip emptyish sets
            if not any(y[0:100]):
                continue
            try:
                plt.plot(y)
            except:
                print y
                raise
            plt.savefig('out/%s.png' % (k,))
