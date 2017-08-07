import argparse
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import json

def load_csv(f):
    f = open(f, 'r')
    data = []
    print 'Loading'
    for l in f:
        try:
            j = json.loads(l)
        except:
            break
        data.append(j['v'])
    return data

def load_jl(f):
    f = open(f, 'r')
    # skip metadata
    f.readline()
    data = []
    print 'Loading'
    for l in f:
        try:
            j = json.loads(l)
        except:
            break
        data.append((j['v'], -j['iavg'] * 1e6))

    if 1:
        data2 = []
        for i, d in enumerate(data):
            v, i = d
            if v >= 220:
                data2.append(d)
        data = data2

    # normalize
    if 1:
        imin = min([x[1] for x in data])
        if imin < 0:
            for i, (v, iavg) in enumerate(data):
                data[i] = (v, iavg - imin)
            data = data[1:]
    
    return data

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Help')
    parser.add_argument('fn', help='File')
    args = parser.parse_args()

    print 'Looping'

    fn = args.fn
    print
    print fn
    fn_out = fn.replace('.jl', '.png')
    if fn_out == fn:
        raise Exception()
    data = load_jl(fn)

    # x mv y V
    print 'Plotting (%d samples)' % (len(data),)
    plt.semilogy(*zip(*data))
    #fig = plt.gcf()
    #fig.set_ylim(1e-2, 1e2)
    ax = plt.gca()
    ax.set_ylim(1e-2, 1e2)
    plt.xlabel('Tube voltage')
    plt.ylabel('Tube uA')
    plt.savefig(fn_out)
    #plt.show()


    # average current 500 - 700 v
    meas = []
    for i, d in enumerate(data):
        v, i = d
        if v >= 500 and v <= 700:
            meas.append(i)
    print 'Center average: %0.3f' % (sum(meas) / len(meas),)
