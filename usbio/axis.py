import time

class Unit:
	INCH = 1
	MM = 2

'''
A simple axis that is controlled by a step and direction input
Can subclass later if needed to implement other styles
	ex: raw stepper
'''
class Axis:
	def __init__(self, name, mc, step_pin, dir_pin):
		self.name = name
		#self.mc = mc
		self.usbio = mc.usbio
		self.step_pin = step_pin
		self.dir_pin = dir_pin
		
		# Active stepping
		self.steps_per_unit = 1
		
		# Set a known output state
		self.do_forward()
		self.usbio.set_gpio(self.step_pin, True)
		
	def inches(self):
		self.unit = Unit.INCH
		
	def mm(self):
		self.UNIT = Unit.MM
		
	def jog(self, units):
		'''Move axis to position as fast as possible'''
		steps = self.get_steps(units)
		self.forward(steps > 0)
		self.step(abs(steps))
	
	def step(self, steps):
		for i in range(steps):
			def s():
				time.sleep(0.001)
			
			print 'Step %d / %d' % (i + 1, steps)
			# No idea if one is better before the other
			s()
			self.usbio.set_gpio(self.step_pin, True)
			s()
			self.usbio.set_gpio(self.step_pin, False)

	def get_steps(self, units):
		return units * self.steps_per_unit
	
	def forward(self, really = True):
		if self.is_forward == really:
			return
		self.do_forward(really)
		
	def do_forward(self, really = True):
		self.usbio.set_gpio(self.dir_pin, really)
		self.is_forward = really

