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




    print 'Loading...'
    crf = open(args.fin, 'r')
    
    for l in crf:
        j = eval(l, {"__builtins__": {}})
        row = j['row']
        col = j['col']
        closed = [x[1] for x in j['close']]
        opened = [x[1] for x in j['open']]
        
        plt.plot(opened)
    plt.savefig('tmp/superlot.png')




    print 'Loading...'
    crf = open(args.fin, 'r')
    
    for l in crf:
        j = eval(l, {"__builtins__": {}})
        row = j['row']
        col = j['col']
        closed = [x[1] for x in j['close']]
        opened = [x[1] for x in j['open']]
        
        plt.clf()
        plt.plot(opened)
        plt.savefig('tmp/r%03d_c%03d.png' % (row, col))

