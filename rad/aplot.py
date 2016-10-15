import argparse
import csv
import matplotlib.pyplot as plt
import sys
from scipy import stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot spincal.py result')
    parser.add_argument('fin', nargs='?', default='out.csv', help='Input csv')
    parser.add_argument('fout', nargs='?', default=None, help='Output plot')
    args = parser.parse_args()

    fout = args.fin.replace('.csv', '.png')
    if fout == args.fin:
        raise Exception()
    
    fr = open(args.fin, "r")
    fr.readline()
    cr = csv.reader(fr)

    samples = []
    for l in cr:
        # [buffn, samplen, sample]
        samples.append(int(l[2]))
    
    #plt.plot(samples[0:200])
    plt.plot(samples)
    plt.xlabel('N')
    plt.ylabel('DN')
    plt.savefig(fout)
    plt.show()

    '''
    slope, intercept, r_value, p_value, std_err = stats.linregress(pwms, rpms)
    print 'RPM = %0.3f PWM + %0.3f' % (slope, intercept)
    print 'R: %f' % r_value
    print 'P: %f' % p_value
    print 'Std err: %f' % std_err
    print '*' * 80
    print "% 8s% 8s" %      ("PWM",             "RPM")
    print "% 8.1f% 8.1f" %  (-intercept/slope,  0)
    print "% 8.1f% 8.1f" %  (100,               slope * 100 + intercept)
    '''
