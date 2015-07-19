'''
http://wiki.linuxcnc.org/cgi-bin/wiki.pl?Emcrsh

hello EMC x 1.0
set enable EMCTOO
set verbose on
set machine on
set home 0
set home 1
set home 2
set home 3
set home 4
set home 5
set mode mdi


hello EMC x 1.0
set enable EMCTOO
set verbose on
set machine on
set mode mdi
'''

import pexpect.fdpexpect
import telnetlib
import sys
import datetime

from uvscada.lcnc.rsh import Rsh

class IOTimestamp(object):
    def __init__(self, obj=sys, name='stdout'):
        self.obj = obj
        self.name = name
        
        self.fd = obj.__dict__[name]
        obj.__dict__[name] = self
        self.nl = True

    def __del__(self):
        if self.obj:
            self.obj.__dict__[self.name] = self.fd

    def flush(self):
        self.fd.flush()
       
    def write(self, data):
        parts = data.split('\n')
        for i, part in enumerate(parts):
            if i != 0:
                self.fd.write('\n')
            # If last bit of text is just an empty line don't append date until text is actually written
            if i == len(parts) - 1 and len(part) == 0:
                break
            if self.nl:
                self.fd.write('%s: ' % datetime.datetime.utcnow().isoformat())
            self.fd.write(part)
            # Newline results in n + 1 list elements
            # The last element has no newline
            self.nl = i != (len(parts) - 1)

_ts = IOTimestamp()


rsh = Rsh('mk-xray')

# Even though I only have 3 axes looks like 6 need homing?
# also they take a really long time
# why?
if 0:
    print 'Config axes'
    for axis in xrange(3):
        print 'set %d' % axis
        rsh.set_home(axis)

# queing test
for i in xrange(3):
    print 'G0'
    rsh.mdi('G0 X200')

    print 'G0'
    rsh.mdi('G0 X0')

