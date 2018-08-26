'''
Erase until the chip reports erased stable for 10% of the lead up time
'''

import eprom_etime
import os
import subprocess
import json
import numpy as np
from uvscada.minipro import Minipro

def run(dout, prog_dev, ethresh=20., interval=3.0, passes=10):
    if not os.path.exists(dout):
        os.mkdir(dout)
    '''
    if '27C16' in prog_dev:
        size = 16 * 1024 / 8
    elif '27C32' in prog_dev:
        size = 32 * 1024 / 8
    elif '27C64' in prog_dev:
        size = 64 * 1024 / 8
    elif '27C128' in prog_dev:
        # 16384
        size = 128 * 1024 / 8
    elif '27C256' in prog_dev:
        size = 256 * 1024 / 8
    else:
        assert 0, prog_dev
    '''
    prog = Minipro(device=prog_dev)
    size = len(prog.read())

    subprocess.check_call('python patgen.py --size %u %s/0s.bin' % (size, dout), shell=True)
    dts = []
    dt_halfs = []
    for passn in xrange(passes):
        fnout = '%s/iter_%02u.jl' % (dout, passn)
        print('')
        print('Writing to %s' % fnout)
        print('Writing')
        subprocess.check_call("minipro -p '%s' -w %s/0s.bin" % (prog_dev, dout), shell=True)
        print('Wrote')
        dt, dt_half = eprom_etime.run(fnout, prog_dev=prog_dev, ethresh=ethresh, interval=interval)
        dts.append(dt)
        dt_halfs.append(dt_half)

        print('')
        tavg = 1.0 * sum(dts) / len(dts)
        stdev = np.std(dts)
        thalf_avg = 1.0 * sum(dt_halfs) / len(dt_halfs)
        thalf_stdev = np.std(dt_halfs)
        print('%s @ %u passes' % (prog_dev, passn))
        print('  120%% erase avg: %0.1f sec, stdev: %0.1f sec' % (tavg, stdev))
        for dt in dts:
            print("    %0.1f" % dt)
        print('  50%% erase avg: %0.1f sec, stdev: %0.1f sec' % (thalf_avg, thalf_stdev))
        for dt in dt_halfs:
            print("    %0.1f" % dt)

        fnout = '%s/sweep.jl' % (dout,)
        with open(fnout, 'w') as fout:
            j = {'tavg': tavg}
            fout.write(json.dumps(j) + '\n')

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--prog-device', required=True, help='')
    parser.add_argument('--passes', type=int, default=10, help='')
    parser.add_argument('dout', help='')
    args = parser.parse_args()

    run(args.dout, args.prog_device, passes=args.passes)
