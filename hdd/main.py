'''
This file is part of uvscada
Licensed under 2 clause BSD license, see COPYING for details
'''

'''
smartctl --scan doesn't seem to work very well, it misses my external HDD
Bug of feature?

[mcmaster@gespenst icons]$ hddtemp /dev/sda
WARNING: Drive /dev/sda doesn't seem to have a temperature sensor.
WARNING: This doesn't mean it hasn't got one.
WARNING: If you are sure it has one, please contact me (hddtemp@guzu.net).
WARNING: See --help, --debug and --drivebase options.
/dev/sda: OCZ-AGILITY:  no sensor


[root@gespenst ~]# hddtemp /dev/sdb
/dev/sdb: WDC WD5000BEVT-00A0RT0:  drive supported, but it doesn't have a temperature sensor.

palimsest idicates a temperature though
'''

__author__ = "John McMaster"

import sys
from PyQt4 import QtGui, QtCore
from operator import itemgetter
from execute import Execute
import re
import os
import os.path
from util import print_debug

class Device:
	file_name = None
	temperature = None
	dev_label = None
	value_label = None
	session_high = None
	session_low = None
	
	def temp_str(self):
		raw = get_temperature(self.file_name)
		if raw is None:
			return '%s:     <N/A>' % self.file_name
		else:
			(cur_temp, worst_temp) = raw
			if self.session_high:
				self.session_high = max(cur_temp, self.session_high)
			else:
				self.session_high = cur_temp
			if self.session_low:
				self.session_low = min(cur_temp, self.session_low)
			else:
				self.session_low = cur_temp
			return '%s:     cur: %0.1f, worst ever: %0.1f, low: %0.1f, high: %0.1f' % (self.file_name, cur_temp, worst_temp, self.session_low, self.session_high)

class MainWindow(QtGui.QWidget):
	devices = dict()
	
	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self, parent)

		self.resize(800, 600)
		self.setWindowTitle('UVNet temperature monitor')
		self.setWindowIcon(QtGui.QIcon('icons/uvnet.png'))
		
		self.layout = QtGui.QVBoxLayout()
		#self.layout.setSpacing(1)
		
		exit = QtGui.QAction('Quit', self)
		exit.setShortcut('Ctrl+Q')
		self.connect(exit, QtCore.SIGNAL('triggered()'), QtCore.SLOT('close()'))
		
		self.timer = QtCore.QTimer()
		QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.update)
		self.timer.start(1000);

		'''
		self.menubar = QtGui.QMenuBar(self)
		file = self.menubar.addMenu('&File')
		file.addAction(exit)
		self.layout.setMenuBar(self.menubar)
		'''
		
		self.regen_devices()

		self.setLayout(self.layout)
	
	def get_hdd_device_file_names(self):
		ret = set()
		for dir in os.listdir("/dev"):
			raw = re.match("[hs]d[a-z]", dir)
			if raw:
				ret.add(os.path.join("/dev", raw.group()))
		print_debug(ret)
		return ret

	def regen_devices(self):
		cur_devices = self.get_hdd_device_file_names()
		row = 0
		for device_file_name in sorted(cur_devices):
			cur_devices.add(device_file_name)
			if self.devices and device_file_name in self.devices:
				# old device, update
				device = self.devices[device_file_name]
				#device.value_label.setText(device.temp_str())
				device.value_label.setText(device.temp_str())
				continue
			else:
				# new device
				device = Device()
				print '***added %s' % device_file_name
				device.file_name = device_file_name

				#device.dev_label = QtGui.QLabel(self)
				#device.dev_label.setText(device.file_name)
			
				device.value_label = QtGui.QLabel(self)
				to_set = device.temp_str()
				print to_set
				device.value_label.setText(to_set)
				if True:
					self.layout.addWidget(device.value_label)
				elif True:
					self.layout.addWidget(device.dev_label, row, 0)
					self.layout.addWidget(device.value_label, row, 1)
				else:
					device.layout = QtGui.QHBoxLayout()
					device.layout.addWidget(device.dev_label)
					device.layout.addWidget(device.value_label)
					print 'setting up layout'
					device.widget = QtGui.QWidget(self)
					print 'setting up layout 2'
					device.widget.setLayout(self.layout)
					print 'setting up layout 3'
					# Does not like this
					self.layout.addWidget(device.widget)
					print 'setting up layout done'

				#self.devices.add(device)
				self.devices[device.file_name] = device
				row += 1
				
		# Get rid of removed HDDs
		old_devices = set(self.devices)
		print_debug('cur devices: %s' % cur_devices)
		print_debug('old devices: %s' % old_devices)
		removed_devices = old_devices - cur_devices
		print_debug('removed devices: %s' % removed_devices)
		for device_file_name in removed_devices:
			print '***removed %s' % device_file_name
			device = self.devices[device_file_name]
			if True:
				#self.layout.removeWidget(device.dev_label)
				self.layout.removeWidget(device.value_label)
				device.value_label.setParent(None)
			else:
				self.layout.removeWidget(device.layout)
			del self.devices[device_file_name]

	def __cmp__(self, other):
		print 'cmp'
		return self.file_name.__cmp__(other.file_name)
	
	def update(self):	
		print_debug()
		print_debug('update')
		self.regen_devices()
	
	def __del__(self):
		pass

def get_temperature(device):
	# multiplatform
	return get_temperature_by_smartctl(device)
	return get_temperature_by_hddtemp(device)
	
def get_temperature_by_hddtemp(device):
	"""
	'''
	'''
	command = "hddtemp"
	args = list()
	
	args.append(device)
	
	# go go go
	(rc, output) = Execute.with_output(command, args)
	'''
	'''
	rc_adj = rc / 256
	if not rc == 0:
		print output
		print 'Bad rc: %d (%d)' % (rc_adj, rc)
		return None
	
	print_debug()
	print_debug()
	print_debug(output)
	print_debug()
	print_debug()
	
	'''
	[root@gespenst uvtemp]# hddtemp /dev/sda
	WARNING: Drive /dev/sda doesn't seem to have a temperature sensor.
	WARNING: This doesn't mean it hasn't got one.
	WARNING: If you are sure it has one, please contact me (hddtemp@guzu.net).
	WARNING: See --help, --debug and --drivebase options.
	/dev/sda: OCZ-AGILITY:  no sensor
	[root@gespenst uvtemp]# echo $?
	0


	[root@gespenst uvtemp]# hddtemp /dev/hdf
	/dev/hdf: open: No such file or directory
	
	[root@gespenst uvtemp]# echo $?
	1
	'''
	if output.find('no sensor') >= 0:
		return None
	
	# 194 Temperature_Celsius     0x0022   117   097   000    Old_age   Always       -       30
	re_res = re.search(".*Temperature_Celsius.*", output)
	if re_res is None:
		return None
	line = re_res.group()
	print_debug('line: %s' % repr(line))

	worst_temp = float(line.split()[4])
	print_debug('worst: %s' % worst_temp)
	cur_temp = float(line.split()[9])
	print_debug('cur: %s' % cur_temp)

	return (cur_temp, worst_temp)
	"""
	return None
	
def get_temperature_by_smartctl(device):
	'''
	[root@gespenst ~]# smartctl --all /dev/sdb
	...
	SMART Attributes Data Structure revision number: 16
	Vendor Specific SMART Attributes with Thresholds:
	ID# ATTRIBUTE_NAME		  FLAG	 VALUE WORST THRESH TYPE	  UPDATED  WHEN_FAILED RAW_VALUE
	  1 Raw_Read_Error_Rate	 0x002f   200   200   051	Pre-fail  Always	   -	   0
	  3 Spin_Up_Time			0x0027   188   180   021	Pre-fail  Always	   -	   1566
	  4 Start_Stop_Count		0x0032   100   100   000	Old_age   Always	   -	   129
	  5 Reallocated_Sector_Ct   0x0033   200   200   140	Pre-fail  Always	   -	   0
	  7 Seek_Error_Rate		 0x002e   100   253   000	Old_age   Always	   -	   0
	  9 Power_On_Hours		  0x0032   099   099   000	Old_age   Always	   -	   863
	 10 Spin_Retry_Count		0x0032   100   100   051	Old_age   Always	   -	   0
	 11 Calibration_Retry_Count 0x0032   100   100   000	Old_age   Always	   -	   0
	 12 Power_Cycle_Count	   0x0032   100   100   000	Old_age   Always	   -	   124
	192 Power-Off_Retract_Count 0x0032   200   200   000	Old_age   Always	   -	   103
	193 Load_Cycle_Count		0x0032   180   180   000	Old_age   Always	   -	   62042
	194 Temperature_Celsius	 0x0022   118   097   000	Old_age   Always	   -	   29
	196 Reallocated_Event_Count 0x0032   200   200   000	Old_age   Always	   -	   0
	197 Current_Pending_Sector  0x0032   200   200   000	Old_age   Always	   -	   0
	198 Offline_Uncorrectable   0x0030   100   253   000	Old_age   Offline	  -	   0
	199 UDMA_CRC_Error_Count	0x0032   200   200   000	Old_age   Always	   -	   0
	200 Multi_Zone_Error_Rate   0x0008   100   253   051	Old_age   Offline	  -	   0
	..
	'''
	command = "smartctl"
	args = list()
	
	args.append('-a')
	args.append(device)
	
	# go go go
	(rc, output) = Execute.with_output(command, args)
	'''
	[root@gespenst uvtemp]# smartctl /dev/sdf
	smartctl 5.40 2010-10-16 r3189 [i386-redhat-linux-gnu] (local build)
	Copyright (C) 2002-10 by Bruce Allen, http://smartmontools.sourceforge.net

	Smartctl open device: /dev/sdf failed: No such device
	[root@gespenst uvtemp]# echo $?
	2
	'''
	"""
	Too many obsecure conditions
	Try to parse and ignore if the parse fails

	[mcmaster@gespenst uvtemp]$ smartctl /dev/sda
	smartctl 5.40 2010-10-16 r3189 [i386-redhat-linux-gnu] (local build)
	Copyright (C) 2002-10 by Bruce Allen, http://smartmontools.sourceforge.net

	Smartctl open device: /dev/sda failed: Permission denied

	rc_adj = rc / 256
	if rc_adj == 4:
		'''
		...
		smartctl 5.40 2010-10-16 r3189 [i386-redhat-linux-gnu] (local build)
		Copyright (C) 2002-10 by Bruce Allen, http://smartmontools.sourceforge.net

		=== START OF INFORMATION SECTION ===
		Model Family:     Indilinx Barefoot based SSDs
		Device Model:     OCZ-AGILITY
		...
		Warning: device does not support Error Logging
		Warning! SMART ATA Error Log Structure error: invalid SMART checksum.
		SMART Error Log Version: 1
		No Errors Logged

		Warning! SMART Self-Test Log Structure error: invalid SMART checksum.
		SMART Self-test log structure revision number 1
		No self-tests have been logged.  [To run self-tests, use: smartctl -t]


		Device does not support Selective Self Tests/Logging
		
		
		Still had table info though, but not temp
		'''
		return None
	elif not rc == 0:
		print output
		# This happens for a number of reasons, hard to guage
		print 'Bad rc: %d (%d)' % (rc_adj, rc)
		return None
	"""
	if output is None:
		return None
	
	print_debug()
	print_debug()
	print_debug(output)
	print_debug()
	print_debug()
	# 194 Temperature_Celsius     0x0022   117   097   000    Old_age   Always       -       30
	re_res = re.search(".*Temperature_Celsius.*", output)
	if re_res is None:
		return None
	line = re_res.group()
	if line is None:
		return None
	print_debug('line: %s' % repr(line))

	worst_temp = float(line.split()[4])
	print_debug('worst: %s' % worst_temp)
	cur_temp = float(line.split()[9])
	print_debug('cur: %s' % cur_temp)

	return (cur_temp, worst_temp)
	
if __name__ == "__main__":
	if False:
		for dev in get_hdd_devices():
			print 'Fetching %s' % dev
			raw = get_temperature(dev)
			if raw:
				(cur_temp, worst_temp) = raw

		sys.exit(1)
	
	app = QtGui.QApplication(sys.argv)
	main = MainWindow()
	main.show()

	rc = app.exec_()
	# Destroy early so modules don't get unloaded
	app = None
	main = None
	sys.exit(rc)

