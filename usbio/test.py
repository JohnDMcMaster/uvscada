'''
This file is part of uvscada
Licensed under 2 clause BSD license, see COPYING for details
'''

from usbio.usbio import USBIO
import time

print 'Creating device'
u = USBIO('/dev/ttyACM0', debug=True)

print 'Version: %s' % (u.version(),)

print
print 'Setting 1 relay on'
u.set_relay(1, True)

print
print 'Setting 1 relay off'
u.set_relay(1, False)

print
print 'Done'

print
print 'X forward'
u.set_gpio(1, True)
for i in xrange(16):
    print
    print 'Step X on %d' % i
    u.set_gpio(0, True)
    print
    print 'Step X off %d' % i
    u.set_gpio(0, False)
    time.sleep(0.25)

print
print 'X Reverse'
u.set_gpio(1, False)
for i in xrange(16):
    print
    print 'Step X on'
    u.set_gpio(0, True)
    print
    print 'Step X off'
    u.set_gpio(0, False)
    time.sleep(0.25)

print
print 'Done'

