#!/usr/bin/env python

from uvscada.dylos.dc1100 import DC1100Pro
import sys
import time

dev = '/dev/ttyUSB0'
log_file = None
if len(sys.argv) > 1:
	dev = sys.argv[1]
if len(sys.argv) > 2:
	log_file = sys.argv[2]

f = None
if log_file:
	print 'Logging to %s' % log_file
	f = open(log_file, 'w')

d = DC1100Pro(dev)

print 'Waiting for data...'
while True:
	m = d.wait_meas()
	print 'T: %s, L: %d (%d CFM), S: %d (%d CFM), Q: %s' % (time.strftime('%F %T'), m.small, m.small_cfm(), m.large, m.large_cfm(), d.quality_str())
	if f:
		f.write('%s,%d,%d' % (time.time(), m.small, m.large))
		# Its a while before we write data again
		f.flush()
		
