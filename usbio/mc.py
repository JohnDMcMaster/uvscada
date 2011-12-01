'''
UCN5804

x motor
stuck direection
looking into motor shaft
	CCW

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

alpha is using UCN5804 but waiting for new drivers in mail
'''

import serial
import sys
import time
from usbio import USBIO

VERSION = 0.0

from optparse import OptionParser
from axis import Axis

# Klinger / Micro-controle driver
class MC:
	UNIT_INCH = 1
	UNIT_MM = 2
	
	#DIR_FORWARD = 1
	#DIR_REVERSE = 2
	
	def __init__(self):
		self.usbio = USBIO()
		self.x = Axis('X', self, 2, 3)
		self.y = Axis('Y', self, 0, 1)
		
		self.axes = [self.x, self.y]
		
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
	mc = MC()
	
	'''
	parser = OptionParser()
	parser.add_option("-f", "--file", dest="filename",
		              help="write report to FILE", metavar="FILE")
	parser.add_option("-q", "--quiet",
		              action="store_false", dest="verbose", default=True,
		              help="don't print status messages to stdout")

	(options, args) = parser.parse_args()
	'''
	
	while True:
		def s():
			time.sleep(0.5)
		d = 100
		print 'Jogging X'
		mc.x.jog(d)
		s()
		print 'Jogging Y'
		mc.y.jog(d)
		s()
		print 'Jogging -X'
		mc.x.jog(-d)
		s()
		print 'Jogging -Y'
		mc.y.jog(-d)
		s()
		
	while True:
		for axis in mc.axes:
			print 'Jogging %s' % axis.name
			axis.jog(100)

