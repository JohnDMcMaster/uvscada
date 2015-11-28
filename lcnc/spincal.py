'''
Manually with PyVCP
S   ~RPM
0   2.3
5   80
10  200
20  440
40  1040
60  1630
80  2220
100 2820
'''

import linuxcnc
import subprocess
import time
import csv
import datetime

stat = linuxcnc.stat()
command = linuxcnc.command()
stat.poll()

def gets(s):
    return float(subprocess.check_output(["halcmd", "gets", s]))

def rps_meas():
    return gets("spindle-fb-filtered-abs-rps")

def rpm_meas():
    return rps_meas() * 60.

fw = open("spincal.csv", "w")
cw = csv.writer(fw)
cw.writerow(("t", "tstr", "pwm", "rpm"))
for pwm in xrange(101):
    print
    print 'PWM: %d' % pwm
    command.mdi("M3 S%d" % pwm)
    time.sleep(4)
    # Noisy
    # Take a bunch and average
    rpms = []
    last = None
    for _i in xrange(16):
        '''
        while True:
            rpm = rpm_meas()
            if rpm != last:
                print rpm
                rpms.append(rpm)
                last = rpm
        '''
        time.sleep(0.2)
        rpm = rpm_meas()
        rpms.append(rpm)
        
    print "RPMs: %s" % (rpms,)
    rpm = sum(rpms) / len(rpms)
    print "RPM: %0.3f" % (rpm,)
    cw.writerow(("%0.3f" % time.time(), datetime.datetime.utcnow(), pwm, "%0.3f" % rpm))
    fw.flush()

command.mdi("M3 S0")

