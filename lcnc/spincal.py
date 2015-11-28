#!/usr/bin/env python
'''
You must have spindle "RPM" setup such that 0 => stopped and 100 => 100% drive
'''
import argparse
import csv
import datetime
import linuxcnc
import subprocess
import time

def gets(s):
    return float(subprocess.check_output(["halcmd", "gets", s]))

def rps_meas():
    return gets("spindle-fb-filtered-abs-rps")

def rpm_meas():
    return rps_meas() * 60.

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Characterize spindle PWM to RPM')
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('out', nargs='?', default='spincal.csv', help='Output csv')
    args = parser.parse_args()

    if os.path.exists(args.out) and not args.overwrite:
        raise Exception("Refusing to overwrite")

    command = linuxcnc.command()

    try:
        fw = open(args.out, "w")
        cw = csv.writer(fw)
        cw.writerow(("t", "tstr", "pwm", "rpm"))
        for pwm in xrange(101):
            print
            print 'PWM: %d' % pwm
            command.mdi("M3 S%d" % pwm)
            time.sleep(3)
            # Noisy
            # Take a bunch and average
            rpms = []
            last = None
            for _i in xrange(16):
                time.sleep(0.2)
                rpm = rpm_meas()
                rpms.append(rpm)
                
            print "RPMs: %s" % (rpms,)
            rpm = sum(rpms) / len(rpms)
            print "RPM: %0.3f" % (rpm,)
            cw.writerow(("%0.3f" % time.time(), datetime.datetime.utcnow(), pwm, "%0.3f" % rpm))
            fw.flush()
    finally:
        print 'Shutting down spindle'
        command.mdi("M3 S0")

