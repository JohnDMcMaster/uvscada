import time
import threading

class Unit:
	INCH = 1
	UM = 2

'''
A simple axis that is controlled by a step and direction input
Can subclass later if needed to implement other styles
	ex: raw stepper
	
For now units are in um
Currently assumes stepper control (even for mock), further subclass as needed
'''
class Axis:
	def __init__(self, name):
		self.name = name

		# Active stepping
		self.steps_per_unit = 1
		# NeoSPlan 5X calibration
		# shouldn't change with objective though as its independent of microscope
		# per um
		self.steps_per_unit = 8.510
	
	def __str__(self):
		return self.name
		
	def inches(self):
		self.unit = Unit.INCH
		raise Exception('no')
		
	def um(self):
		self.UNIT = Unit.UM
	
	def get_steps(self, units):
		return int(units * self.steps_per_unit)
	
	def get_mm(self):
		return self.get_um() / 1000.0
	
	def get_um(self):
		return self.net / self.steps_per_unit
		
	def home(self):
		self.set_pos(0.0)
		
	def set_home(self):
		'''Pretend we are at 0 as returned by get_mm() etc, does not move'''
		raise Exception('Required')
		
	def set_pos(self, units):
		'''Go to absolute position as fast as possible'''
		raise Exception('Required')

	def jog(self, units):
		'''Move axis relative to current position as fast as possible'''
		self.step(self.get_steps(units))
	
	def step(self, steps):
		raise Exception("Required")

	def stop(self):
		'''Gracefully stop the system at next interrupt point'''
		self.estop()

	def estop(self):
		'''Halt the system ASAP, possibly losing precision/position'''
		raise Exception('Required')
		
	def unestop(self):
		'''Clear emergency stop, if any'''
		raise Exception('Required')		

class DummyAxis(Axis):
	def __init__(self, name = 'dummy'):
		Axis.__init__(self, name)
		self.steps_per_unit = 1
		self.net = 0
	
	def jog(self, units):
		print 'Dummy axis %s: jogging %s' % (self.name, units)
		
	def step(self, steps):
		print 'Dummy axis %s: stepping %s' % (self.name, steps)

	def set_pos(self, units):
		print 'Dummy axis %s: set_pos %s' % (self.name, units)
	
	def stop(self):
		print 'Dummy axis %s: stop' % (self.name,)

	def estop(self):
		print 'Dummy axis %s: emergency stop' % (self.name,)
	
	def unestop(self):
		print 'Dummy axis %s: clearing emergency stop' % (self.name,)
	
	def set_home(self):
		print 'Dummy axis %s: set home' % (self.name,)

	def home(self):
		print 'Dummy axis %s: home' % (self.name,)
		
class MCAxis(Axis):
	def __init__(self, name, mc, step_pin, dir_pin, invert_dir = False):
		Axis.__init__(self, name)
		#self.mc = mc
		self.usbio = mc.usbio
		if self.usbio.serial is None:
			raise Exception("USBIO missing serial")
		self.step_pin = step_pin
		self.dir_pin = dir_pin
		self.invert_dir = invert_dir
		
		# Set a known output state
		# Unknown state to force set
		self.is_forward = None
		self.forward()
		
		self.usbio.set_gpio(self.step_pin, True)
		
		self.step_delay_s = None
		#self.step_delay_s = 0.001
		#self.step_delay_s = 5
		
		self.net = 0

		self._stop = threading.Event()
		self._estop = threading.Event()
		
	def stop(self):
		self._stop.set()

	def estop(self):
		self._estop.set()
	
	def unestop(self):
		self._estop.clear()
		
	def step(self, steps):
		self.forward(steps > 0)

		for i in range(abs(steps)):
			# Loop runs quick enough that should detect reasonably quickly
			if self._estop.is_set():
				print 'MC axis %s: emergency stop detected!' % (self.name,)
				# Record what we finished since its little work
				self.net += i
				return
			#print 'Step %d / %d' % (i + 1, steps)
			# No idea if one is better before the other
			if self.step_delay_s:
				time.sleep(self.step_delay_s)
			self.usbio.set_gpio(self.step_pin, True)
			if self.step_delay_s:
				time.sleep(self.step_delay_s)
			self.usbio.set_gpio(self.step_pin, False)

		self.net += steps
		print '%s net %f um (%d steps)' % (self.name, self.net / self.steps_per_unit, self.net)	

	def forward(self, is_forward = True):
		if self.is_forward == is_forward:
			return
		to_set = is_forward
		if self.invert_dir:
			to_set = not to_set
		self.usbio.set_gpio(self.dir_pin, to_set)
		self.is_forward = is_forward
	
	# pretend we are at 0
	def set_home(self):
		self.net = 0
	
	def set_pos(self, units):
		'''
		Ex:
		old position is 2 we want 10
		we need to move 10 - 2 = 8
		'''
		self.jog(units - self.get_um())
		
	def home(self):
		self.step(-self.net)
