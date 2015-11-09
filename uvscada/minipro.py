'''
Python bindings for the minipro tool (TL866)
https://github.com/vdudouyt/minipro/
'''

import subprocess

class Minipro:
    def __init__(self, path='minipro', device=None):
        self.path = path
        self.device = device
        
    def read(self, device=None):
        device = device or self.device
        if device is None:
            raise ValueError("Device required")
        tmpfn = '/tmp/uvminipro.bin'
        subprocess.check_call([self.path, '-p', device, '-r', tmpfn])
        return open(tmpfn, 'r').read()

    def write(self, buff, device=None):
        device = device or self.device
        if device is None:
            raise ValueError("Device required")
        tmpfn = '/tmp/uvminipro.bin'
        open(tmpfn, 'w').write(buff)
        subprocess.check_call([self.path, '-p', device, '-w', tmpfn])
