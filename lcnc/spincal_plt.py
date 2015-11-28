import argparse
import csv
import matplotlib.pyplot as plt
import sys
from scipy import stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot spincal.py result')
    parser.add_argument('fin', nargs='?', default='spincal.csv', help='Input csv')
    parser.add_argument('fout', nargs='?', default='spincal.png', help='Output plot')
    args = parser.parse_args()

    fr = open(args.fin, "r")
    fr.readline()
    cr = csv.reader(fr)

    pwms = []
    rpms = []
    for l in cr:
        pwms.append(float(l[2]))
        rpms.append(float(l[3]))
    
    plt.plot(pwms, rpms)
    plt.xlabel('PWM')
    plt.ylabel('RPM')
    plt.savefig(args.fout)

    slope, intercept, r_value, p_value, std_err = stats.linregress(pwms, rpms)
    print 'RPM = %0.3f PWM + %0.3f' % (slope, intercept)
    print 'R: %f' % r_value
    print 'P: %f' % p_value
    print 'Std err: %f' % std_err
    print '*' * 80
    print "% 8s% 8s" %      ("PWM",             "RPM")
    print "% 8.1f% 8.1f" %  (-intercept/slope,  0)
    print "% 8.1f% 8.1f" %  (100,               slope * 100 + intercept)

