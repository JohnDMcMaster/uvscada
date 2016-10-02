#from uvscada import gp307
import argparse
import sys
import serial
import time
from PyQt4.QtCore import *
from PyQt4.QtGui import QColor
from PyQt4 import Qt
import PyQt4.QtCore as QtCore
import PyQt4.Qwt5 as Qwt
from PyQt4.Qwt5.anynumpy import *
from PyQt4.QtGui import *
import sys

from PyQt4 import QtCore, QtGui

import Queue
import threading
import traceback
import signal
import os
import datetime

class MinXScaleEngine(Qwt.QwtLinearScaleEngine):
    def __init__(self, min_x):
        Qwt.QwtLinearScaleEngine.__init__(self)
        
        self.min_x = min_x
        
    def divideScale(self, x1, x2, maxMajSteps, maxMinSteps, stepSize):
        if x2-x1 < self.min_x:
            x2 = x1 + self.min_x
            stepSize = float(self.min_x) / maxMinSteps
            
        scale = Qwt.QwtLinearScaleEngine.divideScale(self, x1, x2, maxMajSteps, maxMinSteps, stepSize)
        
        return scale
    
class Curve(Qwt.QwtPlotCurve):
    def __init__(self, name, max_points):
        Qwt.QwtPlotCurve.__init__(self, name)
        
        self.x_data = zeros(0, Float)
        self.y_data = zeros(0, Float)
        
        self.max_points = max_points
        
    def addPoint(self, nx, ny):
        if len(self.x_data) < self.max_points:
            self.x_data.resize(len(self.x_data)+1)
            self.x_data[-1] = nx
            
            self.y_data.resize(len(self.y_data)+1)
            self.y_data[-1] = ny
        else:                    
            self.x_data = concatenate((self.x_data[1:], self.x_data[:1]), 1)
            self.x_data[-1] = nx
            
            self.y_data = concatenate((self.y_data[1:], self.y_data[:1]), 1)
            self.y_data[-1] = ny
            
        self.setData(self.x_data, self.y_data)
        
        # Update attached plot
        self.plot().replot()

    def clearLog(self):
        self.x_data = zeros(0, Float)
        self.y_data = zeros(0, Float)

        self.plot().replot()

# total_seconds was added in 2.7 and we have people mostly using 2.6
def td2sec(td):
    return float((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6)) / 10**6

class PlotCurve(Curve):
    def __init__(self, name, origin_fun,scale=1.0,offset=0.0,max_points=100):
        Curve.__init__(self, name, max_points)
        self.origin_fun = origin_fun
        self.scale = scale
        self.offset = offset
        
    def addData(self, t, value):    
        print 't', t
        print 'v', value
        x = t - self.origin_fun(t)
        self.addPoint(x, value*self.scale + self.offset)

class DataPlot(Qwt.QwtPlot):
    def __init__(self, *args):
        Qwt.QwtPlot.__init__(self, *args)
        
        self.setCanvasBackground(Qt.Qt.white)
        self.alignScales()
        
        self.curves = []
        self.curve_names = dict()
        
        self.insertLegend(Qwt.QwtLegend(), Qwt.QwtPlot.RightLegend)
        
        self.setAxisScaleEngine(self.xBottom, MinXScaleEngine(20))

        self.xLabel("Time (seconds)")
        self.yLabel("Values")
        
        self.firstTime = None
        
    def xLabel(self, label):
        self.setAxisTitle(Qwt.QwtPlot.xBottom, label)
    
    def yLabel(self, label):
        self.setAxisTitle(Qwt.QwtPlot.yLeft, label)
        
    def getOriginTime(self, time):
        if not self.firstTime:
            self.firstTime = time
        return self.firstTime
    
    def addDataCurve(self, name, register, color=Qt.Qt.blue,scale=1.0,offset=0.0,max_points=100):
        data = PlotCurve(name, self.getOriginTime,scale,offset,max_points)
        data.setPen(Qt.QPen(color))
        self.addCurve(data)
        self.curve_names[name] = data
        register(data.addData)
            
    def addCurve(self, curve):
        idx = len(self.curves)
        
        self.curves.append(curve)
        curve.attach(self)
        
        return idx        

    def alignScales(self):
        self.canvas().setFrameStyle(Qt.QFrame.Box | Qt.QFrame.Plain)
        self.canvas().setLineWidth(1)
        for i in range(Qwt.QwtPlot.axisCnt):
            scaleWidget = self.axisWidget(i)
            if scaleWidget:
                scaleWidget.setMargin(0)
            scaleDraw = self.axisScaleDraw(i)
            if scaleDraw:
                scaleDraw.enableComponent(
                    Qwt.QwtAbstractScaleDraw.Backbone, False)

    def clearLog( self ):
        self.alignScales()
                
        self.setAxisScaleEngine(self.xBottom, MinXScaleEngine(20))
        
        self.firstTime = None

        for curve in self.curves:
            curve.clearLog()






'''
class MagTab(simple_tab.SimpleTab):
    def __init__(self, register, parent=None):

        simple_tab.SimpleTab.__init__(self, register,
            'AB', mag_tree, lambda id_, item: 'ENG_MAG_%c_%s' % (id_, item[1]),
            parent)

    def setupLayout(self, register, types, tree, key_gen):
        vlayout = QVBoxLayout()

        for dev in self.devs:
            plot = DataPlot()
            for axis in self.axes:
                plot.addDataCurve('ENG_MAG_%s_%s_MEAS' % (dev, axis),
                                 axis, register,
                                 {'X': Qt.red,
                                  'Y': Qt.blue,
                                  'Z': Qt.green}[axis])
            plot.resize(300, 300)
            plot.yLabel('Field (m Gauss)')
            vlayout.addWidget(plot)

        hlayout = QHBoxLayout()
        hlayout.addLayout(simple_tab.SimpleTab.setupLayout(self,
                                                           register,
                                                           types,
                                                           tree,
                                                           key_gen))
        hlayout.addLayout(vlayout)
        return hlayout
'''


class DataThread(QThread):
    def __init__(self, ser):
        QThread.__init__(self)
        self.running = threading.Event()
        self.ser = ser
    
    def run(self):
        self.running.set()
        while self.running.is_set():
            l = self.ser.readline().strip()
            t = time.time()
            if not l:
                continue
            print 'THREAD: %0.3f,%s' % (t, l)
            self.emit(SIGNAL('data'), (t, l))
    
    def stop(self):
        self.running.clear()

class Grapher(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)

        self.ser = serial.Serial('/dev/ttyUSB0',
                baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_TWO,
                timeout=0.1, xonxoff=False, rtscts=False, writeTimeout=None, dsrdtr=False,
                interCharTimeout=None)
        self.ser.flushOutput()
        self.ser.flushInput()
        self.dt = DataThread(self.ser)
        self.connect(self.dt, SIGNAL('data'), self.data_rx)
        
        hlayout = QHBoxLayout()
        self.plot = DataPlot()
        hlayout.addWidget(self.plot)
        
        self.data_cb = []
        def register(cb):
            self.data_cb.append(cb)
        self.plot.addDataCurve('Pressure', register, max_points=12)
        self.data_rx((time.time(), '9.90E+09,2.00E+00,9.90E+09'))

        self.dt.start()

        w = QWidget()
        w.setLayout(hlayout)
        self.setCentralWidget(w)
        self.show()


    def data_rx(self, data):
        (t, l) = data
        print 'APP: %0.3f,%s' % (t, l)
        # 9.90E+09,2.00E+00,9.90E+09
        pressure = l.split(',')[1]
        # 2.00E+00
        pressure = float(pressure)
        #tdt = datetime.datetime.fromtimestamp(int(t))
        print 't', t
        #print 'tdt', tdt
        for cb in self.data_cb:
            cb(t, pressure)

def excepthook(excType, excValue, tracebackobj):
    print '%s: %s' % (excType, excValue)
    traceback.print_tb(tracebackobj)
    os._exit(1)

if __name__ == "__main__":
    sys.excepthook = excepthook
    # Exit on ^C instead of ignoring
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = QtGui.QApplication(sys.argv)
    win = Grapher()
    win.show()
    sys.exit(app.exec_())

