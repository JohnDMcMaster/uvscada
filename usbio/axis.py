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
        self.net = 0
    
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
      
    def forever_neg(self, done):
        '''Decrease until stopped'''
        raise Exception('Required')
          
    def forever_pos(self, done):
        '''Increase until stopped'''
        raise Exception('Required')

