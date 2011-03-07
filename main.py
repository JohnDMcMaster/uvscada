'''
UVNet temperature monitor (uvtemp)
Copyright (C) 2011 John McMaster
GUI
'''

'''
[mcmaster@gespenst icons]$ hddtemp /dev/sda
WARNING: Drive /dev/sda doesn't seem to have a temperature sensor.
WARNING: This doesn't mean it hasn't got one.
WARNING: If you are sure it has one, please contact me (hddtemp@guzu.net).
WARNING: See --help, --debug and --drivebase options.
/dev/sda: OCZ-AGILITY:  no sensor


[root@gespenst ~]# hddtemp /dev/sdb
/dev/sdb: WDC WD5000BEVT-00A0RT0:  drive supported, but it doesn't have a temperature sensor.

palimsest idicates a temperature though


[root@gespenst ~]# smartctl --all /dev/sdb
...
SMART Attributes Data Structure revision number: 16
Vendor Specific SMART Attributes with Thresholds:
ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE
  1 Raw_Read_Error_Rate     0x002f   200   200   051    Pre-fail  Always       -       0
  3 Spin_Up_Time            0x0027   188   180   021    Pre-fail  Always       -       1566
  4 Start_Stop_Count        0x0032   100   100   000    Old_age   Always       -       129
  5 Reallocated_Sector_Ct   0x0033   200   200   140    Pre-fail  Always       -       0
  7 Seek_Error_Rate         0x002e   100   253   000    Old_age   Always       -       0
  9 Power_On_Hours          0x0032   099   099   000    Old_age   Always       -       863
 10 Spin_Retry_Count        0x0032   100   100   051    Old_age   Always       -       0
 11 Calibration_Retry_Count 0x0032   100   100   000    Old_age   Always       -       0
 12 Power_Cycle_Count       0x0032   100   100   000    Old_age   Always       -       124
192 Power-Off_Retract_Count 0x0032   200   200   000    Old_age   Always       -       103
193 Load_Cycle_Count        0x0032   180   180   000    Old_age   Always       -       62042
194 Temperature_Celsius     0x0022   118   097   000    Old_age   Always       -       29
196 Reallocated_Event_Count 0x0032   200   200   000    Old_age   Always       -       0
197 Current_Pending_Sector  0x0032   200   200   000    Old_age   Always       -       0
198 Offline_Uncorrectable   0x0030   100   253   000    Old_age   Offline      -       0
199 UDMA_CRC_Error_Count    0x0032   200   200   000    Old_age   Always       -       0
200 Multi_Zone_Error_Rate   0x0008   100   253   051    Old_age   Offline      -       0
...
'''

__author__ = "John McMaster"

import sys
from PIL import Image, ImageQt
from PyQt4 import QtGui, QtCore
from operator import itemgetter

class MainWindow(QtGui.QWidget):
    
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.resize(400, 400)
        self.setWindowTitle('UVNet temperature monitor')
        self.setWindowIcon(QtGui.QIcon('icons/uvnet.png'))
        
        grid = QtGui.QGridLayout()
        grid.setSpacing(4)
        
        exit = QtGui.QAction('Quit', self)
        exit.setShortcut('Ctrl+Q')
        self.connect(exit, QtCore.SIGNAL('triggered()'), QtCore.SLOT('close()'))
        
        '''
        self.menubar = QtGui.QMenuBar(self)
        file = self.menubar.addMenu('&File')
        file.addAction(exit)
        grid.setMenuBar(self.menubar)
        '''

        self.lblFile = QtGui.QLabel(self)
        self.lblFile.setText("/dev/sda:")
        self.lblFileName = QtGui.QLabel(self)
        self.lblFileName.setText("value")
        grid.addWidget(self.lblFile,0,0)
        grid.addWidget(self.lblFileName,0,1)

        self.setLayout(grid)
        
    def __del__(self):
        pass

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()

    rc = app.exec_()
    # Destroy early so modules don't get unloaded
    app = None
    main = None
    sys.exit(rc)

