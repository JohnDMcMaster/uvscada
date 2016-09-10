#!/usr/bin/env python

from uvscada import dc1100
import time
import argparse

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='I leave all that I own to my cat guppy')
	parser.add_argument('--dev', default='/dev/ttyUSB0', help='Serial port')
	parser.add_argument('fn', nargs='?', help='Log file name')
	args = parser.parse_args()

	f = None
	if args.fn:
		print 'Logging to %s' % args.fn
		f = open(args.fn, 'w')
	
	d = dc1100.DC1100Pro(args.dev)
	
	print 'Waiting for data...'
	while True:
		m = d.wait_meas()
		t = time.time()
		print 'T: %s, L: %d (%d CPF), S: %d (%d CPF), Q: %s' % (time.strftime('%F %T'), m.small, m.small_cpf(), m.large, m.large_cpf(), d.quality_str())
		
		if f:
			f.write('%s,%d,%d\n' % (t, m.small, m.large))
			# Its a while before we write data again
			f.flush()
	
