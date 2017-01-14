'''
Quatech / BNB electronics
'''

import socket
import time
import select

# Raw TCP socket serial port
class BNBRawT(object):
    def __init__(self, host, port=None):
        port = port or 5000
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((host, port))
        self.timeout = 10.0
        self.buff = bytearray()

    def flushInput(self):
        self.buff = bytearray()

    def flushOutput(self):
        pass

    def read(self, n=1):
        if len(self.buff) < n:
            ready = select.select([self.s], [], [], self.timeout)
            if ready[0]:
                self.buff += self.s.recv(16)
        
        ret = self.buff[0:n]
        del self.buff[0:n]
        return str(ret)
    
    def readline(self):
        tstart = time.time()
        l = ''
        while True:
            c = self.read()
            l += c
            if c == '\n':
                return l
            
            if time.time() - tstart > self.timeout:
                return l
    
    def close(self):
        self.s.close()
    
    def __del__(self):
        self.close()
