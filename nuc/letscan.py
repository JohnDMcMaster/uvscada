#!/usr/bin/env python

'''
Use a Sherline 2000 CNC Z axis to scan a LND alpha window GM tube
Use Gamma Spectacular to acquire data through sound port
Allows gathering CPM vs distnace which is basically LET curve

Currently only doing pulses, but in the future should do spectra
'''
from uvscada.cnc_hal import lcnc_ar

import sys
import time
import alsaaudio
import csv
import struct
import argparse

PRINT_QUICK = 10
STEP_T = 120.0
ZMAX = 5.0

class ALSASrc(object):
    def __init__(self):
        card = 'default'

        self.pcm = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK, card)

        nchans = 2
        self.pcm.setchannels(nchans)
        self.pcm.setrate(44100)
        self.pcm.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self.sample_bytes = 2 * nchans
        self.unpacker = struct.Struct('<' + ('h' * nchans))

        self.pcm.setperiodsize(160)
    
        self.buffn = 0

    def gen(self):
        while True:
            # Read data from device
            l, data = self.pcm.read()
          
            if not l:
                continue
            self.buffn += 1
                
            for i in xrange(0, len(data), self.sample_bytes):
                samples = self.unpacker.unpack(data[i:i+self.sample_bytes])
                #print [buffn, samplen, samples]
                sample = samples[-1]
                
                yield sample

class Pulser(object):
    def __init__(self):
        self.pulsing = False
        self.pulses = 0
        self.pulsesl = 0

        # Recognize a pulse at 75% saturation
        self.phi = int(32767 * 0.75)
        # Pulse ends if we cross 25% saturation
        # (note: goes very (saturates) negative after pulse)
        self.plo = int(32767 * 0.25)

    def next(self, sample):
        if self.pulsing:
            if sample <= self.plo:
                self.pulsing = False
        else:
            if sample >= self.phi:
                self.pulsing = True
                self.pulses += 1
    def last(self):
        ret = self.pulses - self.pulsesl
        self.pulsesl = self.pulses
        return ret

def cap(hal, csv_fn):
    print 'Configuring ALSA'
    asrc = ALSASrc()
    
    print 'looping'
    samplen = 0
    tlast = time.time()
    pulser = Pulser()
    tstart = time.time()
    agen = asrc.gen()
    
    smin = float('+inf')
    smax = float('-inf')
    sminl = float('+inf')
    smaxl = float('-inf')

    def mvz(z):
        hal.mv_abs({'z': z}, limit=False)

    def gen_exp():
        yield 0.000
        
        itr = 0
        zil = 0
        while True:
            z = 0.001 * (1.2 ** itr)
            if z > ZMAX:
                break
            
            # skip if less than backlash
            if z < 0.002:
                itr += 1
                continue
            
            '''
            zi = int(z * 1000)
            if zi == zil:
                itr += 1
                continue
            '''
            
            yield z
            itr += 1
    
    def gen_lin():
        return [x / 1000. for x in xrange(0, int(ZMAX * 1000), int(0.2 * 1000))]

    fd = open(csv_fn, 'w')
    cw = csv.writer(fd)
    cw.writerow(['t', 'dt', 'z', 'n', 'pulses'])
    stepn = 0

    #for z in gen_exp():
    for z in gen_lin():
        print
        stepn += 1
        print 'Pos %0.4f, n %d' % (z, stepn)
        # Move into position
        mvz(z)
        
        # Now collect pulses for a minute
        t0 = time.time()
        pulses_t0 = pulser.pulses
        pulser.last()
        tlast = time.time()
        
        while True:
            sample = agen.next()
            pulser.next(sample)
            samplen += 1

            smin = int(min(smin, sample))
            smax = int(max(smax, sample))
            sminl = int(min(sminl, sample))
            smaxl = int(max(smaxl, sample))

            if time.time() - tlast > PRINT_QUICK:
                tlast = time.time()
                print 'Min: %d (%d), max: %d (%d), pulses: %d (%d)' % (smin, sminl, smax, smaxl, pulser.pulses, pulser.last())
                sminl = float('+inf')
                smaxl = float('-inf')
            
            t1 = time.time()
            dt = t1 - t0
            if dt > STEP_T:
                pulses = pulser.pulses - pulses_t0
                row = ['%0.1f' % t0, '%0.1f' % dt , '%0.4f' % z, stepn, pulses]
                cw.writerow(row)
                fd.flush()
                print row
                break

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('fn', nargs='?', default='out.csv', help='csv out')
    args = parser.parse_args()


    hal = None
    try:
        print 'Initializing HAL'
        hal = lcnc_ar.LcncPyHalAr(host='cnc', username='mcmaster', dry=False, log=None)
        #hal._cmd('G91 G1 Z0.01 F1')
        cap(hal, args.fn)
        #print hal.limit()
        #hal.mv_abs({'z': 0}, limit=False)
    finally:
        print 'Shutting down hal'
        if hal:
            hal.ar_stop()

