import usbio
from axis import DummyAxis
from axis import Axis
import Queue
import threading


# no real interfaces really defined yet...
class Controller:
    def __init__(self):
        self.x = None
        self.y = None
        self.z = None
        self.axes = []

    def build_axes(self):
        self.axes = []
        if self.x:
            self.axes.append(self.x)
        if self.y:
            self.axes.append(self.y)
        if self.z:
            self.axes.append(self.z)

    def inches(self):
        for axis in self.axes:
            axis.inches()
        
    def mm(self):
        for axis in self.axes:
            axis.mm()

    def um(self):
        for axis in self.axes:
            axis.um()
        
    def home(self):
        for axis in self.axes:
            axis.home()
        
    def off(self):
        pass
    
    def on(self):
        pass


class MockController(Controller):
    def __init__(self):
        print Controller
        Controller.__init__(self)
        self.x = DummyAxis('X')
        self.y = DummyAxis('Y')
        self.axes = [self.x, self.y]


