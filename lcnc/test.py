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

print 'opening socket'
telsh = telnetlib.Telnet('mk-xray', 5007, timeout=0.5)
client = pexpect.fdpexpect.fdspawn(telsh)
print 'Ready'


print 'Authenticating'
client.sendline('HELLO EMC x 1.0')
client.expect('HELLO ACK i 1.1')

print 'Configuring'
client.sendline('SET ECHO OFF')
client.sendline('GET ECHO')
client.expect('ECHO OFF')

client.sendline('SET VERBOSE ON')
# Creates these ACK messages to show up in addition to NACK
client.expect('SET VERBOSE ACK')

print 'Setting enable'
client.sendline('SET ENABLE EMCTOO')
client.expect('SET ENABLE ACK')

print 'Setting machine'
client.sendline('SET MACHINE ON')
client.expect('SET MACHINE ACK')

print 'Config axes'
# Even though I only have 3 axes looks like 6 need homing?
# also they take a really long time
# why?
if 0:
    for axis in xrange(3):
        print 'set %d' % axis
        client.sendline('SET HOME %d' % axis)
        print 'expect %d' % axis
        client.expect('SET HOME ACK')

print 'MDI mode'
client.sendline('SET MODE MDI')
client.expect('SET MODE ACK')

# for large commands
# USRMOT: ERROR: invalid command
# but doesn't return error

# queing test
for i in xrange(3):
    print 'G0'
    client.sendline('SET MDI G0 X200')
    client.expect('SET MDI ACK')

    print 'G0'
    client.sendline('SET MDI G0 X0')
    client.expect('SET MDI ACK')

while True:
    client.sendline('GET PROGRAM_STATUS')
    status = client.readline().strip()
    if status == 'PROGRAM_STATUS RUNNING':
        print 'still running'
    elif status == 'PROGRAM_STATUS IDLE':
        print 'done'
        break
    else:
        print 'bad status %s' % status

