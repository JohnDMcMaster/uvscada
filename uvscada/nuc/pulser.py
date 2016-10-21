import time

'''
Simple audio analyzer that looks for pulses
'''
class Pulser(object):
    def __init__(self):
        self.pulsing = False

        # Recognize a pulse at 75% saturation
        self.phi = int(32767 * 0.75)
        # Pulse ends if we cross 25% saturation
        # (note: goes very (saturates) negative after pulse)
        self.plo = int(32767 * 0.25)

    def next(self, sample):
        was_pulsing = self.pulsing
        if self.pulsing:
            if sample <= self.plo:
                self.pulsing = False
        else:
            if sample >= self.phi:
                self.pulsing = True
                self.pulses += 1
        # Finished pulse?
        return was_pulsing and not self.pulsing

class PulserStat(object):
    def __init__(self, tprint=5.0):
        self.tprint = tprint
        self.rst()
    
    def rst(self):
        self.smin = float('+inf')
        self.smax = float('-inf')
        
        self.sminl = float('+inf')
        self.smaxl = float('-inf')
        
        self.samples = 0
        self.samplesl = 0
        
        self.pulses = 0
        self.pulsesl = 0
        
        self.tlast = time.time()

    def rstl(self):
        self.sminl = float('+inf')
        self.smaxl = float('-inf')
        self.pulsesl = 0
        self.samplesl = 0
        self.tlast = time.time()
        
    def next(self, sample, pulse):
        self.smin = int(min(self.smin, sample))
        self.smax = int(max(self.smax, sample))
        self.sminl = int(min(self.sminl, sample))
        self.smaxl = int(max(self.smaxl, sample))
        
        self.samples += 1
        self.samplesl += 1
        if pulse:
            self.pulses += 1
            self.pulsesl += 1

        if self.tprint and time.time() - self.tlast > self.tprint:
            self.tlast = time.time()
            print 'Min: %d (%d), max: %d (%d), pulses: %d (%d)' % (self.smin, self.sminl, self.smax, self.smaxl, self.pulses, self.pulsesl)
            self.rstl()

'''
Pulse height analyzer
Identifies pulses
'''
class PHA(object):
    def __init__(self, phi, plo):
        self.pulsing = False
        self.pulses = 0
        self.pulsesl = 0

        # Recognize a pulse at 75% saturation
        self.phi = phi
        # Pulse ends if we cross 25% saturation
        # (note: goes very (saturates) negative after pulse)
        self.plo = plo
        self.buff = []

    def next(self, sample):
        '''Returns height on finished pulse, None otherwise'''
        if self.pulsing:
            self.buff.append(sample)
            if sample <= self.plo:
                self.pulsing = False
                return max(self.buff)
        else:
            if sample >= self.phi:
                self.pulsing = True
                self.buff = [sample]
                self.pulses += 1
        return None
    
    def last(self):
        ret = self.pulses - self.pulsesl
        self.pulsesl = self.pulses
        return ret
