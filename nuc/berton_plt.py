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
        data.append((j['vin'], j['vout']))

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
    #plt.subplot(221)
    plt.subplots_adjust(right=0.8)
    plt.plot(*zip(*data), label='Real')
    # Ideal
    plt.plot(*zip(*[(xmv/1000., xmv * -1000.0 / 9000) for xmv in xrange(0, 9000, 10)]), label='Ideal')
    #red_patch = mpatches.Patch(color='red', label='Ideal')
    #plt.legend(handles=[red_patch])
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.savefig(fn_out)
    #plt.show()


