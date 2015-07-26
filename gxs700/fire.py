import pycurl
import time
import os

SW_HV = 1
SW_FIL = 2

def switch(n, on):
     state = 'ON' if on else 'OFF'
     c = pycurl.Curl()
     c.setopt(c.URL, 'http://energon/outlet?%d=%s' % (n, state))
     c.setopt(c.WRITEDATA, open('/dev/null', 'w'))
     c.setopt(pycurl.USERPWD, '%s:%s' % (os.getenv('WPS7_USER', 'admin'), os.getenv('WPS7_PASS', '')))
     c.perform()
     c.close()

print 'Warming filament...'
switch(SW_FIL, 1)
time.sleep(5)

print 'Nuking...'
switch(SW_HV, 1)
time.sleep(3)

print 'Safing...'
switch(SW_HV, 0)

print 'Done'

