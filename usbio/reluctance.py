'''
Raw DIN pinout step order
	2
		#2
	4
		#3
	1
		#1
	5
		#4
3 is ground


IO Pin   		Function
IO_08   		IO8/Relay2  
IO7        		IO_07
IO_09  			IO9/Relay1    
IO6/Counter0    IO_06               
IO_0A   		IOA/ADC4          
IO_05  			IO5/ADC3                
IO_0B   		IOB/ADC5          
IO_04  			IO4/ADC2
IO_0C   		IOC/ADC6
IO_03 			IO3/ADC1
IO_0D           IO_02
IOD/ADC7        IO2/ADC0
IO_0E           IO_01
IOE/PWM0        IO1/RX0
IO_0F           IO_00
IOF/PWM1        IO0/TX0
'''

import serial
import sys
import time
from usbio import USBIO

VERSION = 0.0

if True:
	# Reluctance driver box
	class Axis:
		def __init__(self, name, reluctance, pins):
			self.name = name
			self.reluctance = reluctance
			self.usbio = reluctance.usbio
			self.pins = pins
		
			# Active stepping
			self.steps_per_unit = 1
		
			# Step into the first index
			self.index = -1
			# Will not be enforced, make sure its off
			self.usbio.set_gpio(self.pins[2], False)
			# Should be set high soon but avoid having three on at once
			self.usbio.set_gpio(self.pins[1], False)
			# The old high pin will be assumed to have already been set
			#self.usbio.set_gpio(self.pins[0], True)
			self.step(0)
		
		def set_pole(self, index):
			index2 = (index + 1) % 4
		
			old1 = (index + 2) % 4
			old2 = (index + 3) % 4
		
			# TODO: move this to one command
			self.usbio.set_gpio(self.pins[old2], False)
			self.usbio.set_gpio(self.pins[old1], False)
			self.usbio.set_gpio(self.pins[index2], True)
			print 'Activate %d index %d' % (self.pins[index2], index2)
		
		def inches(self):
			self.unit = Reluctance.UNIT_INCH
		
		def mm(self):
			self.UNIT = Reluctance.UNIT_MM
		
		def jog(self, units):
			'''Move axis to position as fast as possible'''
			steps = self.get_steps(units)
			self.step(abs(steps))
	
		def step(self, steps):
			for i in range(steps):
				print 'Step'
				self.index += 1
				self.set_pole(self.index)	
				# No idea if one is better before the other
				time.sleep(1)

		def get_steps(self, units):
			return units * self.steps_per_unit
			
else:
	class Axis:
		def __init__(self, name, reluctance, pins):
			self.name = name
			self.reluctance = reluctance
			self.usbio = reluctance.usbio
			self.pins = pins
		
			# Active stepping
			self.steps_per_unit = 1
		
			# Step into the first index
			self.index = -1
			# Will not be enforced, make sure its off
			self.usbio.set_gpio(self.pins[2], False)
			# Should be set high soon but avoid having three on at once
			self.usbio.set_gpio(self.pins[1], False)
			# The old high pin will be assumed to have already been set
			#self.usbio.set_gpio(self.pins[0], True)
			self.step(0)
		
		def set_pole(self, index):
			index2 = (index + 1) % 4
		
			old1 = (index + 2) % 4
			old2 = (index + 3) % 4
		
			# TODO: move this to one command
			self.usbio.set_gpio(self.pins[old2], False)
			self.usbio.set_gpio(self.pins[index2], True)

		
		def inches(self):
			self.unit = Reluctance.UNIT_INCH
		
		def mm(self):
			self.UNIT = Reluctance.UNIT_MM
		
		def jog(self, units):
			'''Move axis to position as fast as possible'''
			steps = self.get_steps(units)
			self.step(abs(steps))
	
		def step(self, steps):
			for i in range(steps):
				print 'Step'
				self.index += 1
				self.set_pole(self.index)	
				# No idea if one is better before the other
				time.sleep(1)

		def get_steps(self, units):
			return units * self.steps_per_unit

			
			
class Reluctance:
	'''
	CCW sequence
		1
		3
		2
		4
		
	Blue 1
		To 4
	Green 2
		To 3
	White 3
		To 5, 6
	Red 4
		To 1
	Black 5
		To 2
		
		
		
	4 / 2
	2 / 1
	5 / 3
	1 / 0
	'''
	UNIT_INCH = 1
	UNIT_MM = 2
	
	def __init__(self):
		self.usbio = USBIO()
		
		if True:
			p = [2, 1, 3, 0]
			def s():
				time.sleep(1)
			# Half stepping
			while True:
				print 'round'
				self.usbio.set_gpio(p[0], True)
				s()
				self.usbio.set_gpio(p[3], False)
				s()
				self.usbio.set_gpio(p[1], True)
				s()
				self.usbio.set_gpio(p[0], False)
				s()
				self.usbio.set_gpio(p[2], True)
				s()
				self.usbio.set_gpio(p[1], False)
				s()
				self.usbio.set_gpio(p[3], True)
				s()
				self.usbio.set_gpio(p[2], False)
				s()
			# standard algorithm
			while True:
				print 'round'
				self.usbio.set_gpio(p[3], False)
				self.usbio.set_gpio(p[0], True)
				s()
				self.usbio.set_gpio(p[0], False)
				self.usbio.set_gpio(p[1], True)
				s()
				self.usbio.set_gpio(p[1], False)
				self.usbio.set_gpio(p[2], True)
				s()
				self.usbio.set_gpio(p[2], False)
				self.usbio.set_gpio(p[3], True)
				s()
		
		#self.x = Axis('X', self, [0, 1, 2, 3])
		# This is what I was expecting to do it...hmm
		#self.x = Axis('X', self, [2, 1, 3, 0])
		# maybe pin numbers are reversed
		#self.x = Axis('X', self, [0, 3, 1, 2])
		
		#self.x = Axis('X', self, [0, 0, 0, 0])

	
		if False:
			# barely twitches
			#self.x = Axis('X', self, [0, 0, 1, 1])
		
			# moves
			#self.x = Axis('X', self, [0, 0, 2, 2])
			# moves well
			self.x = Axis('X', self, [0, 0, 3, 3])
		
		if False:
			# moves well
			self.x = Axis('X', self, [3, 3, 0, 0])
			# barely twitches
			self.x = Axis('X', self, [3, 3, 1, 1])
			self.x = Axis('X', self, [3, 3, 2, 2])
		
		if False:
			# !!!!! No engagement
			self.x = Axis('X', self, [2, 2, 1, 1])
			# twiches
			#self.x = Axis('X', self, [2, 2, 0, 0])
			#self.x = Axis('X', self, [2, 2, 3, 3])
			
		if True:
			# logical order looking at breadboard
			#self.x = Axis('X', self, [2, 3, 1, 4])
			# bur reversed wiring because of breakout board order
			# all that should mean is that it would run in reverse though
			#self.x = Axis('X', self, [3, 0, 2, 1])
			self.x = Axis('X', self, [2, 1, 3, 0])
			
		self.axes = [self.x]
		self.inches()
		
	def inches(self):
		for axis in self.axes:
			axis.inches()
		
	def mm(self):
		for axis in self.axes:
			axis.mm()
				
def str2bool(arg_value):
	arg_value = arg_value.lower()
	if arg_value == "false" or arg_value == "0" or arg_value == "no" or arg_value == "off":
		return False
	else:
		return True

def help():
	print 'usbio version %s' % VERSION
	print 'Copyright 2011 John McMaster <JohnDMcMaster@gmail.com>'
	print 'Usage:'
	print 'usbio [options] [<port> <state>]'
	print 'Options:'
	print '--help: this message'

if __name__ == "__main__":
	port = None
	state = True
	raw_index = 0
	
	for arg_index in range (1, len(sys.argv)):
		arg = sys.argv[arg_index]
		arg_key = None
		arg_value = None
		if arg.find("--") == 0:
			arg_value_bool = True
			if arg.find("=") > 0:
				arg_key = arg.split("=")[0][2:]
				arg_value = arg.split("=")[1]
				arg_value_bool = str2bool(arg_value)
			else:
				arg_key = arg[2:]
				
			if arg_key == "help":
				help()
				sys.exit(0)
			elif arg_key == "port":
				port = arg_value
			elif arg_key == "state":
				state = arg_value_bool
			else:
				log('Unrecognized argument: %s' % arg)
				help()
				sys.exit(1)
		else:
			arg_bool = str2bool(arg)

			if arg == "false" or arg == "0" or arg == "no":
				arg_bool = False

			raw_index += 1
			if raw_index == 1:
				port = arg
			elif raw_index == 2:
				state = arg_bool
	
	if True:
		u = USBIO()
		def s():
			time.sleep(0.1)
			pass
		while True:
			u.set_gpio(0, True)
			s()
			u.set_gpio(0, False)
			s()
		sys.exit(1)
	
	sher = Reluctance()
	
	while True:
		print 'Jogging X'
		sher.x.jog(100)
		#time.sleep(1)
		
	while True:
		for axis in sher.axes:
			print 'Jogging %s' % axis.name
			axis.jog(100)

