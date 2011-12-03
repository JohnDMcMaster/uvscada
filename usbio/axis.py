import time

class Unit:
	INCH = 1
	MM = 2

'''
A simple axis that is controlled by a step and direction input
Can subclass later if needed to implement other styles
	ex: raw stepper
	
For now units are in um
'''
class Axis:
	def __init__(self, name, mc, step_pin, dir_pin, invert_dir = False):
		self.name = name
		#self.mc = mc
		self.usbio = mc.usbio
		self.step_pin = step_pin
		self.dir_pin = dir_pin
		self.invert_dir = invert_dir
		
		# Active stepping
		self.steps_per_unit = 1
		# NeoSPlan 5X
		# per um
		self.steps_per_unit = 8.510
		
		# Set a known output state
		self.do_forward()
		self.usbio.set_gpio(self.step_pin, True)
		
		self.step_delay_s = 0.001
		self.step_delay_s = None
		
		self.net = 0
		
	def inches(self):
		self.unit = Unit.INCH
		
	def mm(self):
		self.UNIT = Unit.MM
		
	def jog(self, units):
		'''Move axis to position as fast as possible'''
		steps = self.get_steps(units)
		self.step(steps)

	def step(self, steps):
		self.forward(steps > 0)
		self.do_step(abs(steps))
		
		self.net += steps
		print '%s net %f um (%d steps)' % (self.name, self.net / self.steps_per_unit, self.net)	

	def do_step(self, steps):
		for i in range(steps):
			def s():
				if self.step_delay_s:
					time.sleep(self.step_delay_s)
			
			#print 'Step %d / %d' % (i + 1, steps)
			# No idea if one is better before the other
			s()
			self.usbio.set_gpio(self.step_pin, True)
			s()
			self.usbio.set_gpio(self.step_pin, False)

	def get_steps(self, units):
		return int(units * self.steps_per_unit)
	
	def forward(self, really = True):
		if self.is_forward == really:
			return
		self.do_forward(really)
		
	def do_forward(self, is_forward = True):
		to_set = is_forward
		if self.invert_dir:
			to_set = not to_set
		self.usbio.set_gpio(self.dir_pin, to_set)
		self.is_forward = is_forward
		
	def home(self):
		self.step(-self.net)

class DummyAxis(Axis):
	def __init__(self, name = 'dummy'):
		self.steps_per_unit = 1
		self.is_forward = True
		self.net = 0
		self.name = name
	
	def step(self, steps):
		print 'Dummy: stepping %d' % steps
	
	def do_forward(self, really = True):
		pass
	
	
