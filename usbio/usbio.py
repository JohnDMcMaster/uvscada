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
import time

class USBIO:
	device = None
	serial = None
	
	# wtf is acm
	def __init__(self, device = "/dev/ttyACM0"):
		self.device = device
		self.serial = serial.Serial(self.device, 9600, timeout=1)
		#self.serial = open(self.device)
		print self.serial

	'''
	Read the version of the USB_IO device firmware.
	~ver~            ...............send to USB_IO
	~VER:3.8~       ...............Receive from USB_IO
	16 Digital Input/Output Ports: IO0~IOF
	~out0=1~ ..................send to USB_IO (IO0=`1`)
	~OK~           ..................Receive from USB_IO
	~outA=0~ ..................Send to USB_IO (IOA=`0`)
	~OK~           ..................Receive from USB_IO
	~osta9~ .......................Read the state of OUT_09
	~OUTES9=1~        ............Receive from USB_IO (OUT_09 state)
	~osta2~ .......................Read the state of OUT_02
	~OUTES2=0~        ............Receive from USB_IO (OUT_02 state)
	~in6~         ..................Send to USB_IO
	~in6=0~       ..................Receive from USB_IO (IO6=`0`)
	~inA~         ..................Send to USB_IO
	~inA=1~       ..................Receive from USB_IO (IOA=`1`)
	'''
	
	
	
	# Raw
	def send_core(self, bytes_in):
		bytes = '~' + bytes_in + '~'
		print 'Sending: %s' % bytes
		self.serial.write(bytes)
	
	def recv(self):
		# Sync until first ~
		while True:
			c = self.serial.read()
			if c == '~':
				break
		
		# Read until ~
		ret = ''
		while True:
			c = self.serial.read()
			if c == '~':
				break
			ret += c
		
		return ret
		
	def send(self, bytes_out):
		self.send_core(bytes_out)
		reply = self.recv()
		if not reply == "OK":
			raise Exception("EEE!") 
		
	def send_recv(self, bytes_out):
		self.send_core(bytes_out)
		return self.recv()
	
	def get_version(self):
		return self.send_recv("ver")

	def set_gpio(self, index, is_on):
		'''index valid 0-15'''
		# Eliminate none and other corner cases
		if is_on:
			is_on = 1
		else:
			is_on = 0
		
		self.send_core("out%X=%d" % (index, is_on))
	
	def set_relay(self, relay_id, is_on):
		if relay_id == 1:
			self.set_gpio(9, is_on)
		elif relay_id == 2:
			self.set_gpio(8, is_on)
		else:
			raise Exception("bad relay id")


if __name__ == "__main__":
	usbio = USBIO()
	for i in range(0, 30000):
		usbio.set_relay(1, True)
		usbio.set_relay(2, True)
		time.sleep(5)
		usbio.set_relay(1, False)
		usbio.set_relay(2, False)
		time.sleep(5)

