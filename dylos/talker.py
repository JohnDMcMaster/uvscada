#!/usr/bin/env python

try:
	import pyttsx
	talker = True
except:
	talker = False

from uvscada.dylos.dc1100 import *
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

if talker:
	talker = pyttsx.init()
	rate = talker.getProperty('rate')
	talker.setProperty('rate', rate-75)

if talker:
	talker.say('Dylos DC eleven hundred Pro online')
	talker.runAndWait()

def say_cleanroom():
	global d
	global talker

	talker.say('0 point 5 half micro meter per cubic foot count is %d' % d.last_meas.small)
	talker.runAndWait()
	time.sleep(2)
	if d.last_meas.small <= 10000:
		talker.say('Class 10000 cleanroom okay')
	else:
		talker.say('Class 10000 failure')
	talker.runAndWait()

print 'Waiting for data...'
n_in_state = None
n_not_in_state = 0
# Require 3 measurements to consider a state change valid
state_hysteresis = 3
# Don't report any real warnings until we think we have some reasonable stability
startup_wait = 3
quality_state = None
last_meas = None
while True:
	m = d.wait_meas()
	print 'T: %s, L: %d (%d CPF), S: %d (%d CPF), Q: %s' % (time.strftime('%F %T'), m.small, m.small_cpf(), m.large, m.large_cpf(), d.quality_str())
	
	'''
	Don't say anything until the first few readings so that we know we are stable
	'''
	if talker:
		this_quality = d.meas_quality(m)
		
		'''
		If there is ever a sudden change sound an alarm
		'''
		if last_meas != None and not startup_wait:
			per_change = 100.0 * (m.small - last_meas.small) / last_meas.small
			'''
			My data shows anything over 25% change is pretty rare
			Generally things don't even reach 10%
			'''
			if per_change >= 100:
				msg = 'Warning . . critical increase in contamination levels'
			elif per_change >= 50:
				msg = 'Warning . . large contamination spike'
			elif per_change >= 25:
				msg = 'Warning . . contamination spike'
			elif per_change >= 10:
				msg =  'Warning . . noticible contamination increase'
			else:
				msg = None
			if msg:
				if 0:
					#talker.say('%s . . repeat . . %s' % (msg, msg))
					talker.say(msg)
					talker.runAndWait()
				else:
					talker.say(msg)
					talker.runAndWait()
					time.sleep(3)
					talker.say('Repeat')
					talker.runAndWait()
					time.sleep(1)
					talker.say(msg)
					talker.runAndWait()
				

		if quality_state == None:
			n_in_state = 1
			n_not_in_state = 0
		elif quality_state == this_quaility:
			n_in_state += 1
		else:
			n_not_in_state += 1
			# State change?
			if n_not_in_state >= state_hysteresis:
				# Don't get picky with this number since I'm not really using it yet
				n_in_state = 1
				n_not_in_state = 0
				if this_quality < quality_state:
					talker.say('Warning air quality has dropped to level %s' % Measurement.quality_str(this_quality))
				else:
					talker.say('Air quality is now at level %s' % Measurement.quality_str(this_quality))
				talker.runAndWait()
				quality_state = this_quality
				say_cleanroom()
	if f:
		f.write('%s,%d,%d\n' % (time.time(), m.small, m.large))
		# Its a while before we write data again
		f.flush()


	if startup_wait:
		startup_wait -= 1
		if startup_wait == 0 and talker:		
			talker.say('System has started with air quality %s' % Measurement.quality_str(d.meas_quality(d.last_meas)))
			talker.runAndWait()
			say_cleanroom()
	last_meas = d.last_meas

