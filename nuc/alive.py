#!/usr/bin/env python

'''
Bad noise capture on wrong channel
Faulty grounding on mono stereo conversion?
guess its leaking over
Would a mono cable help?

[2, 342, (5296,)]
[2, 343, (20147,)]
[2, 344, (32766,)]
[2, 345, (25280,)]
[2, 346, (-1,)]
[2, 347, (27513,)]
[2, 348, (32766,)]
[2, 349, (780,)]
[2, 350, (-1,)]
[2, 351, (19609,)]
[2, 352, (19012,)]

[0, 117, (6407,)]
[0, 118, (6417,)]
[0, 119, (6417,)]
[0, 120, (6369,)]
[0, 121, (6369,)]
[0, 122, (6377,)]
[0, 123, (6354,)]





streo

[7, 1065, (21, -14)]
[7, 1066, (25, -9)]
[7, 1067, (58, 24)]
[7, 1068, (61, 25)]
[7, 1069, (26, -6)]
[7, 1070, (-629, -661)]
[7, 1071, (-1307, -1342)]
[7, 1072, (-1017, -1052)]
[7, 1073, (-690, -724)]
[7, 1074, (-366, -401)]
[7, 1075, (-149, -186)]
[7, 1076, (-16, -52)]
[7, 1077, (28, -6)]


[1, 287, (-73, -737)]
[1, 288, (265, 990)]
[1, 289, (976, -304)]
[1, 290, (32767, 32767)]
[1, 291, (32767, 32767)]
[1, 292, (-32768, 32767)]
[1, 293, (-32768, 32767)]
[1, 294, (32767, 32767)]
[1, 295, (30462, 32767)]
[1, 296, (-32768, 32767)]
[1, 297, (-32768, 32767)]
[1, 298, (30126, 10640)]
[1, 299, (16194, 9155)]
[1, 300, (15401, 3203)]
[1, 301, (10049, 1262)]


'''



'''
https://larsimmisch.github.io/pyalsaaudio/index.html


$ aplay -l
**** List of PLAYBACK Hardware Devices ****
card 0: PCH [HDA Intel PCH], device 0: CX20590 Analog [CX20590 Analog]
  Subdevices: 1/1
  Subdevice #0: subdevice #0


In [3]: alsaaudio.cards()
Out[3]: [u'PCH', u'NVidia', u'Set', u'ThinkPadEC']

In [4]: alsaaudio.mixers()
Out[4]: 
[u'Master',
 u'Headphone',
 u'Speaker',
 u'PCM',
 u'Mic Boost',
 u'Beep',
 u'Capture',
 u'Auto-Mute Mode',
 u'Digital',
 u'Internal Mic Boost']
 
 
$ aplay -l 
**** List of PLAYBACK Hardware Devices ****
card 0: PCH [HDA Intel PCH], device 0: CX20590 Analog [CX20590 Analog]
  Subdevices: 0/1
  Subdevice #0: subdevice #0
card 1: NVidia [HDA NVidia], device 3: HDMI 0 [HDMI 0]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
card 1: NVidia [HDA NVidia], device 7: HDMI 0 [HDMI 0]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
card 1: NVidia [HDA NVidia], device 8: HDMI 0 [HDMI 0]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
card 1: NVidia [HDA NVidia], device 9: HDMI 0 [HDMI 0]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
card 2: Set [C-Media USB Headphone Set], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0


'''

import sys
import time
import alsaaudio
import csv
import struct
import argparse

def cap():
    limit_n = args.number
    limit_t = args.time
    
    # Recognize a pulse at 75% saturation
    phi = int(32767 * 0.75)
    # Pulse ends if we cross 25% saturation
    # (note: goes very (saturates) negative after pulse)
    plo = int(32767 * 0.25)

    fd = open(args.fn, 'w')
    cw = csv.writer(fd)
    cw.writerow(['buffn', 'samplen', 'samplel', 'sampler'])
    
    card = 'default'
    # alsaaudio.ALSAAudioError: Device or resource busy
    #card = 'hw:2,0'
    # busy...
    #card = 'sysdefault:CARD=Set'
    
    # .asoundrc
    # http://www.alsa-project.org/main/index.php/Asoundrc
    #card = 'hw:0,0'

    # Open the device in nonblocking capture mode. The last argument could
    # just as well have been zero for blocking mode. Then we could have
    # left out the sleep call in the bottom of the loop
    inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK, card)

    # Set attributes: Mono, 44100 Hz, 16 bit little endian samples
    nchans = 2
    inp.setchannels(nchans)
    inp.setrate(44100)
    inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
    sample_bytes = 2 * nchans
    unpacker = struct.Struct('<' + ('h' * nchans))

    # The period size controls the internal number of frames per period.
    # The significance of this parameter is documented in the ALSA api.
    # For our purposes, it is suficcient to know that reads from the device
    # will return this many frames. Each frame being 2 bytes long.
    # This means that the reads below will return either 320 bytes of data
    # or 0 bytes of data. The latter is possible because we are in nonblocking
    # mode.

    inp.setperiodsize(160)
    
    print 'looping'
    buffn = 0
    samplen = 0
    tlast = time.time()
    smin = float('+inf')
    smax = float('-inf')
    sminl = float('+inf')
    smaxl = float('-inf')
    tstart = time.time()
    pulsing = False
    pulses = 0
    pulsesl = 0
    while True:
        # Read data from device
        l, data = inp.read()
      
        if not l:
            continue
            
        #f.write(data)
        #time.sleep(.001)
        # 16 bit little endian samples
        for i in xrange(0, len(data), sample_bytes):
            samples = unpacker.unpack(data[i:i+sample_bytes])
            print [buffn, samplen, samples]
            cw.writerow([buffn, samplen] + list(samples))
            sample = samples[-1]

            if pulsing:
                if sample <= plo:
                    pulsing = False
            else:
                if sample >= phi:
                    pulsing = True
                    pulses += 1

            smin = int(min(smin, sample))
            smax = int(max(smax, sample))
            sminl = int(min(sminl, sample))
            smaxl = int(max(smaxl, sample))
            
            if time.time() - tlast > 1.0:
                tlast = time.time()
                print 'Min: %d (%d), max: %d (%d), pulses: %d (%d)' % (smin, sminl, smax, smaxl, pulses, pulses - pulsesl)
                sminl = float('+inf')
                smaxl = float('-inf')
                pulsesl = pulses
            samplen += 1
            fd.flush()
            if limit_n and samplen >= limit_n:
                return

        if limit_t and time.time() - tstart > limit_t:
            return
        buffn += 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('--number', '-n', type=int, default=0, help='number to take')
    parser.add_argument('--time', '-t', type=int, default=0, help='number to take')
    parser.add_argument('fn', nargs='?', default='out.csv', help='csv out')
    args = parser.parse_args()
    
    cap()
