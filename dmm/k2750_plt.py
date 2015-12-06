import argparse
import csv
import matplotlib.pyplot as plt
import sys
from scipy import stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot result')
    parser.add_argument('fin', nargs='?', default='out.csv', help='Input csv')
    parser.add_argument('fout', nargs='?', default='out.png', help='Output plot')
    args = parser.parse_args()

    fr = open(args.fin, "r")
    fr.readline()
    cr = csv.reader(fr)

    ts = []
    currs = []
    for l in cr:
        ts.append(float(l[0]))
        currs.append(float(l[2]))
    
    ts = [x - ts[0] for x in ts]
    
    plt.plot(ts, currs)
    plt.xlabel('Time')
    plt.ylabel('Current')
    plt.savefig(args.fout)

