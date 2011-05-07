#!/usr/bin/python
'''
uvscada decapsulation machine high level control
Copyright 2011 John McMaster <JohnDMcMaster@gmail.com>
Licensed under the terms of the LGPL V3 or later, see COPYING for details
'''

import sys
import temper
import usbio
import time

def log(s):
	print s

class UVDecapMachine:
	# TH1000 thermocouple
	temper = None
	'''
	USB IO V3 digital output
	Used to actuate hotplate
	'''
	usbio = None
	
	def __init__(self):
		self.temper = temper.TEMPer("/dev/ttyUSB0")
		self.usbio = usbio.USBIO("/dev/ttyACM0")
	
	def get_bath_temperature(self):
		temp = self.temper.get_thermocouple_temp()
		print temp
		return temp
	
	def set_hotplate(self, is_on):
		self.usbio.set_relay(2, is_on)
	
	def run(self):
		target_temperature = 30.0
		MODE_IDLE = 'IDLE'
		MODE_HEAT = 'HEAT'
		MODE_COOL = 'COOL'
		MODE_ALARM = 'ALARM'
		
		mode = MODE_IDLE
		alarms = set()
		ALARM_HIGH_TEMP = 'high temperature'
		ALARM_INVALID_STATE = 'invalid state'
		
		last_temperatures = [0] * 5
		# TODO: set to near boiling of sulfuric
		alarm_set_threshold = 30.0
		alarm_clear_threshold = 26.0
		alarm = False
		target_temperature = 27.5
		temperature_hysteresis = 2.5

		while True:
			print 'Mode: ', mode
			try:
				# Shift
				for i in range(1, 5):
					last_temperatures[i] = last_temperatures[i - 1]
				# Renew
				# Note that all processors add up to 100 even if SMP
				last_temperatures[0] = self.get_bath_temperature()
				print last_temperatures
				average_temperature = sum(last_temperatures) / len(last_temperatures)
			
				# Check for now alarm conditions
				if ALARM_HIGH_TEMP not in alarms and average_temperature > alarm_set_threshold:
					print 'HIGH TEMPERATURE ALARM!'
					alarms.add(ALARM_HIGH_TEMP)
			except:
				raise
				print 'Exception: ', sys.exc_info()[0]
				alarms.add(ALARM_INVALID_STATE)
			
			if len(alarms) > 0:
				mode = MODE_ALARM
			
			try:
				print 'average / target: %f / %f' % (average_temperature, target_temperature)
				if mode == MODE_IDLE:
					if average_temperature < target_temperature:
						mode = MODE_HEAT 
					else:
						mode = MODE_COOL
				elif mode == MODE_HEAT:
					self.set_hotplate(True)
					
					if average_temperature > target_temperature + temperature_hysteresis:
						mode = MODE_COOL
				elif mode == MODE_COOL:
					self.set_hotplate(False)
					
					if average_temperature < target_temperature - temperature_hysteresis:
						mode = MODE_HEAT
				elif mode == MODE_ALARM:
					self.set_hotplate(False)
					print 'Alarms:', alarms
				
					self.set_hotplate(False)

					new_alarms = set(alarms)
					for alarm in alarms:
						if alarm == ALARM_HIGH_TEMP:
	 						if average_temperature < alarm_clear_threshold:
								new_alarms.remove(ALARM_HIGH_TEMP)
					alarms = new_alarms
					
					if len(alarms) == 0:
						print 'ALARM CLEAR'
						mode = MODE_IDLE
			except:
				raise
				print 'Exception: ', sys.exc_info()[0]
				alarms.add(ALARM_INVALID_STATE)
			
			time.sleep(1)
		

def help():
	print 'uvdecap version %s' % VERSION
	print 'Copyright 2011 John McMaster <JohnDMcMaster@gmail.com>'
	print 'Usage:'
	print 'uvdecap [options]'
	print 'Options:'
	print '--help: this message'

if __name__ == "__main__":
	for arg_index in range (1, len(sys.argv)):
		arg = sys.argv[arg_index]
		arg_key = None
		arg_value = None
		if arg.find("--") == 0:
			arg_value_bool = True
			if arg.find("=") > 0:
				arg_key = arg.split("=")[0][2:]
				arg_value = arg.split("=")[1]
				if arg_value == "false" or arg_value == "0" or arg_value == "no":
					arg_value_bool = False
			else:
				arg_key = arg[2:]
				
			if arg_key == "help":
				help()
				sys.exit(0)
			else:
				log('Unrecognized argument: %s' % arg)
				help()
				sys.exit(1)
		else:
			help()
			sys.exit(1)

	machine = UVDecapMachine()
	machine.run()
	

