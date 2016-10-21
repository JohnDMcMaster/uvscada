import struct
import alsaaudio

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

