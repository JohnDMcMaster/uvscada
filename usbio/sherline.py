'''
This file is part of uvscada
Licensed under 2 clause BSD license, see COPYING for details
'''

'''
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

# Sherline driver box
class Axis:
	def __init__(self, name, sherline, step_pin, dir_pin):
		self.name = name
		self.sherline = sherline
		self.usbio = sherline.usbio
		self.step_pin = step_pin
		self.dir_pin = dir_pin
		
		# Active stepping
		self.steps_per_unit = 1
		
		# Set a known output state
		self.do_forward()
		self.usbio.set_gpio(self.step_pin, True)
		
	def inches(self):
		self.unit = Sherline.UNIT_INCH
		
	def mm(self):
		self.UNIT = Sherline.UNIT_MM
		
	def jog(self, units):
		'''Move axis to position as fast as possible'''
		steps = self.get_steps(units)
		self.forward(steps > 0)
		self.step(abs(steps))
	
	def step(self, steps):
		for i in range(steps):
			print 'Step'
			# No idea if one is better before the other
			time.sleep(0.1)
			self.usbio.set_gpio(self.step_pin, True)
			time.sleep(0.1)
			self.usbio.set_gpio(self.step_pin, False)

	def get_steps(self, units):
		return units * self.steps_per_unit
	
	def forward(self, really = True):
		if self.is_forward == really:
			return
		self.do_x_forward(really)
		
	def do_forward(self, really = True):
		self.usbio.set_gpio(self.dir_pin, really)
		self.is_forward = really

class Sherline:
	'''
	This doesn't matter so much since we can wire arbitrarily, but...
	http://www.sherline.com/8760pg.htm
	1 - Input from EMC (may be ignored in other systems)
	2 - X Direction
	3 - X Step
	4 - Y Direction
	5 - Y Step
	6 - Z Direction
	7 - Z Step
	8 - A Direction
	9 - A Step
	10 - NC
	11 - Output to EMC (may be ignored in other systems)
	12 - Output to EMC, XYZ home (may be ignored in other systems)
	13 - NC
	14 - Input from EMC, C1 (may be ignored in other systems)
	15 - NC
	16 - Input from EMC, C2 (may be ignored in other systems)
	17 - NC
	18-25 - Ground
	'''
	PIN_XDIR = 0
	PIN_XSTEP = 1
	PIN_YDIR = 2
	PIN_YSTEP = 3
	PIN_ZDIR = 4
	PIN_ZSTEP = 5
	PIN_ADIR = 6
	PIN_ASTEP = 7
	
	UNIT_INCH = 1
	UNIT_MM = 2
	
	#DIR_FORWARD = 1
	#DIR_REVERSE = 2
	
	def __init__(self):
		self.usbio = USBIO()
		self.x = Axis('X', self, Sherline.PIN_XSTEP, Sherline.PIN_XDIR)
		self.y = Axis('Y', self, Sherline.PIN_YSTEP, Sherline.PIN_YDIR)
		self.z = Axis('Z', self, Sherline.PIN_ZSTEP, Sherline.PIN_ZDIR)
		self.a = Axis('A', self, Sherline.PIN_ASTEP, Sherline.PIN_ADIR)
		
		self.axes = [self.x, self.y, self.z, self.a]
		
		for axis in self.axes:
			axis.do_forward(True)
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
	
	sher = Sherline()
	
	while True:
		print 'Jogging X'
		sher.x.jog(100)
		time.sleep(1)
		
	while True:
		for axis in sher.axes:
			print 'Jogging %s' % axis.name
			axis.jog(100)

