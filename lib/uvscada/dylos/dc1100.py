'''
uvscada
Copyright 2012 John McMaster <JohnDMcMaster@gmail.com>
Licensed under the terms of the LGPL V3 or later, see COPYING for details
'''

'''
I suspect all DC1100 units have the PC interface internally and just aren't brought outside
Not sure how hard that is to do yourself though

Also the manual hints that there is no internal difference between the pro and regular units
The only difference is the calibration
'''

import serial
#import uvscada.serial
import re

'''
Small particles are displayed on the left
Large particles are didplayed on the right

Regular
	Small: Detection limit of 1 micron (um)
	Large: ~5 um
Pro
	Small: 0.5 um
	Large: 2.5 um
Values are scaled to represent concentration of particles in 0.01 cubic foot of sampled air

Since this object only reports density it doesn't matter what these actual size values are
'''

class Measurement:
	# Qualities
	VERY_POOR = 1
	POOR = 2
	FAIR = 3
	GOOD = 4
	VERY_GOOD = 5
	EXCELLENT = 6
	
	@staticmethod
	def quality_str(q):
		vals = 	['VERY_POOR', 'POOR','FAIR','GOOD','VERY_GOOD','EXCELLENT']
		for v in vals:
			if q == eval('Measurement.' + v):
				return v
		return None
		
	def __init__(self, small, large):
		self.small = small
		self.large = large
	
	def small_cpf(self):
		return self.small * self.cpf_conversion()
	
	def large_cpf(self):
		return self.large * self.cpf_conversion()
		
	def cpf_conversion(self):
		# Convert particles / (0.01 ft**3) to particles / ft**3
		return 1 / 0.01
	
	def small_cpm(self):
		return self.small * self.cpm_conversion()
	
	def large_cpm(self):
		return self.large * self.cpm_conversion()
		
	def cpm_conversion(self):
		# Convert particles / (0.01 ft**3) to particles / m**3
		return 1 / (0.01 * ((12.0 * 25.4 / 1000.0)**3))
	
	def valid(self):
		# Some arbitrary high limits to detect a bad data parse
		if self.small > 100000 or self.small < 0:
			return False
		if self.large > 100000 or self.large < 0:
			return False
		# I'm not sure if this is actually true
		return self.small > self.large
	
	@staticmethod
	def parse(s):
		# Reading should be 
		# 1231,422
		parsed = re.match('([0-9]+)[,]([0-9]+)', s)
		if not parsed:
			return None
		return Measurement(int(parsed.group(1)), int(parsed.group(2)))
	
class DC1100:
	def __init__(self, device):
		#if device is None:
		#	device = uvscada.serial.get_device()
		self.device = device
		self.serial = serial.Serial(self.device, 9600, timeout=1)
		self.last_meas = None
		
	# Don't return until a measurement is availible
	def wait_meas(self, require_valid = False):
		while True:
			m = self.meas()
			if m and ((not require_valid) or m.valid()):
				return m
	
	# One Measurement per minute
	def meas(self):
		# Read until newline
		s = ''
		while True:
			c = self.serial.read()
			if c == '\n':
				break
			s += c
		self.last_meas = Measurement.parse(s)
		return self.last_meas

	def quality(self):
		'''
		manual page 12 definition
		Although manual does not say these are small particle counts the back of the unit does
		'''
		if self.last_meas == None:
			return None
		return self.meas_quality(self.last_meas)

	def quality_str(self):
		return Measurement.quality_str(self.quality())
		
	def meas_quality(self, meas):
		'''
		manual page 12 definition
		Although manual does not say these are small particle counts the back of the unit does
		'''
		small = meas.small
		if small >= 1000:
			return Measurement.VERY_POOR
		elif small >= 350:
			return Measurement.POOR
		elif small >= 100:
			return Measurement.FAIR
		elif small >= 50:
			return Measurement.GOOD
		elif small >= 25:
			return Measurement.VERY_GOOD
		elif small >= 0:
			return Measurement.EXCELLENT
		else:
			raise Exception('Malformed measurement')
	
class DC1100Pro(DC1100):
	def __init__(self, dev):
		DC1100.__init__(self, dev)
		
	def meas_quality(self, meas):
		small = meas.small
		if small >= 3000:
			return Measurement.VERY_POOR
		elif small >= 1050:
			return Measurement.POOR
		elif small >= 300:
			return Measurement.FAIR
		elif small >= 150:
			return Measurement.GOOD
		elif small >= 75:
			return Measurement.VERY_GOOD
		elif small >= 0:
			return Measurement.EXCELLENT
		else:
			raise Exception('Malformed measurement')


