from usbio.usbio import USBIO
import time

print 'Creating device'
u = USBIO('/dev/ttyACM0', debug=True)

for i in xrange(16):
    print 'Version: %s' % (u.version(),)

print
print 'Done'

