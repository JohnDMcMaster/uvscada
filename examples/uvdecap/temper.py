'''
Real implementation is in C due to the already extreme load bit banging over SPI introduces
'''

from ctypes import *


class TEMPer:
	libtemper = None
	
	def __init__(self, device = "/dev/ttyUSB0"):
		self.libtemper = cdll.LoadLibrary("../../TEMPer/rev1/libtemper.so")
		self.libtemper._Z11temper_initv()
	
	'''
	LM75 / DS75 sensor
	'''

	def get_internal_temp(self, index = 0):
		return self.libtemper.ReadInternalTemp()


	'''
	Thermocouple
	TH1000 only
	'''
	
	# in deg C
	# returns None if not availible (detatched or wrong device)
	def get_thermocouple_temp(self, index = 0):
		self.libtemper._Z20ReadThermocoupleTempv.restype = c_double
		ret_temp = self.libtemper._Z20ReadThermocoupleTempv()
		print 'raw read therm: ', ret_temp
		return ret_temp

	'''
	EEPROM
	'''
	
	def read_EEPROM(self):
		return self.libtemper.ReadEEPROM(address)
	
	def read_EEPROM_byte(self, address):
		return self.libtemper.ReadEEPROM(address)

	def write_EEPROM_byte(self, address, data):
		return self.libtemper.WriteEEPROM(address, data)	

