'''
Erase until the chip reports erased stable for 10% of the lead up time
'''

from uvscada.minipro import Minipro
import json
import datetime
import time
import zlib
import binascii
import md5

def is_erased(fw, prog_dev):
    # for now assume all 1's is erased
    # on some devices like PIC this isn't true due to file 0 padding
    percent = 100.0 * sum(bytearray(fw)) / (len(fw) * 0xFF)
    return percent == 100.0, percent

def run(fnout, prog_dev, ethresh=20., interval=3.0):
    prog = Minipro(device=prog_dev)
    with open(fnout, 'w') as fout:
        j = {'type': 'header', 'prog_dev': prog_dev, 'date': datetime.datetime.utcnow().isoformat(), 'interval': interval, 'ethresh': ethresh}
        fout.write(json.dumps(j) + '\n')

        tstart = time.time()
        tlast = None
        passn = 0
        nerased = 0
        while True:
            if tlast is not None:
                while time.time() - tlast < interval:
                    time.sleep(0.1)
    
            tlast = time.time()
            now = datetime.datetime.utcnow().isoformat()
            passn += 1
            fw = prog.read()
            erased, erase_percent = is_erased(fw, prog_dev)
            if erased:
                nerased += 1
            else:
                nerased = 0
            pcomplete = 100.0 * nerased / passn

            j = {'iter': passn, 'date': now, 'fw': binascii.hexlify(zlib.compress(fw)), 'pcomplete': pcomplete, 'erase_percent': erase_percent, 'erased': erased}
            fout.write(json.dumps(j) + '\n')

            signature = binascii.hexlify(md5.new(fw).digest())[0:8]
            print('%s iter %u: erased %u w/ erase_percent %0.3f%%, sig %s, pcomplete: %0.1f' % (now, passn, erased, erase_percent, signature, pcomplete))
            if pcomplete >= ethresh:
                break
        print('Erased after %0.1f sec' % (tlast - tstart,))

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--prog-device', required=True, help='')
    parser.add_argument('fout', help='')
    args = parser.parse_args()

    run(args.fout, args.prog_device)
