import cStringIO
import os
import pycurl
import time

class WPS7Exception(Exception):
    pass

class WPS7:
    def __init__(self, host=None, user=None, pass_=None):
        # WPS7 defaults
        self.host = host or os.getenv('WPS7_HOST', '192.168.0.1')
        self.user = user or os.getenv('WPS7_USER', 'admin')
        self.pass_ = pass_ or os.getenv('WPS7_PASS', '1234')
        self.verbose = 0
    
    def on(self, n):
        self.sw(n, True)
    
    def off(self, n):
        self.sw(n, False)

    def cycle(self, n, t=1.0):
        try:
            l = list(n)
        except TypeError:
            l = [n]
        
        for n in l:
            self.sw(n, False)
        time.sleep(t)
        for n in l:
            self.sw(n, True)
    
    def sw(self, n, on):
        state = 'ON' if on else 'OFF'
        if n < 1 or n > 8:
            raise ValueError("require 1 <= sw %d <= 8" % n)
        
        c = pycurl.Curl()
        url = 'http://%s/outlet?%d=%s' % (self.host, n, state)
        if self.verbose:
            print 'WPS: %s' % url
            print '  u: %s' % self.user
            print '  p: %s' % self.pass_
        c.setopt(c.URL, url)
        fout = cStringIO.StringIO()
        c.setopt(c.WRITEFUNCTION, fout.write)
        c.setopt(pycurl.USERPWD, '%s:%s' % (self.user, self.pass_))
        c.perform()
        c.close()
        
        response = fout.getvalue()
        if 'Login Incorrect' not in response and '<META HTTP-EQUIV="refresh" content="0; URL=/index.htm">' in response:
            return
        if self.verbose:
            print response
        raise WPS7Exception("bad response to %s" % (url,))
