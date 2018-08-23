'''
Python bindings for the minipro tool (TL866)
https://github.com/vdudouyt/minipro/
'''

import subprocess
import os

class Minipro:
    def __init__(self, path='minipro', device=None):
        self.path = path
        self.device = device
        self.verbose = False

    def files(self):
        if self.verbose:
            return subprocess.STDOUT, subprocess.STDOUT
        else:
            return open(os.devnull, 'wb'), open(os.devnull, 'wb')

    def read(self, device=None):
        device = device or self.device
        if device is None:
            raise ValueError("Device required")
        tmpfn = '/tmp/uvminipro.bin'
        stdout, stderr = self.files()
        subprocess.check_call([self.path, '-p', device, '-r', tmpfn], stdout=stdout, stderr=stderr)
        return open(tmpfn, 'r').read()

    def write(self, buff, device=None):
        device = device or self.device
        if device is None:
            raise ValueError("Device required")
        tmpfn = '/tmp/uvminipro.bin'
        open(tmpfn, 'w').write(buff)
        subprocess.check_call([self.path, '-p', device, '-w', tmpfn])
