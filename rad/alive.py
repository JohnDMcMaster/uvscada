#!/usr/bin/env python
## This is an example of a simple sound capture script.
##
## The script opens an ALSA pcm forsound capture. Set
## various attributes of the capture, and reads in a loop,
## writing the data to standard out.
##
## To test it out do the following:
## python recordtest.py out.raw # talk to the microphone
## aplay -r 8000 -f S16_LE -c 1 out.raw


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

    fd = open(args.fn, 'w')
    cw = csv.writer(fd)
    cw.writerow(['buffn', 'samplen', 'sample'])
    
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
    inp.setchannels(1)
    inp.setrate(44100)
    inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
    unpacker = struct.Struct('<h')

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
    while True:
        # Read data from device
        l, data = inp.read()
      
        if not l:
            continue
            
        #f.write(data)
        #time.sleep(.001)
        # 16 bit little endian samples
        for i in xrange(0, len(data), 2):
            sample = unpacker.unpack(data[i:i+2])[0]
            #print [buffn, samplen, sample]
            cw.writerow([buffn, samplen, sample])
            
            smin = int(min(smin, sample))
            smax = int(max(smax, sample))
            sminl = int(min(sminl, sample))
            smaxl = int(max(smaxl, sample))
            
            if time.time() - tlast > 1.0:
                tlast = time.time()
                print 'Min: %d (%d), max: %d (%d)' % (smin, sminl, smax, smaxl)
                sminl = float('+inf')
                smaxl = float('-inf')
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
