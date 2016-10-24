import argparse
import matplotlib.pyplot as plt
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
    data = []
    print 'Loading'
    for l in f:
        try:
            j = json.loads(l)
        except:
            break
        data.append(j['v'])
    return data

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Help')
    parser.add_argument('fns', nargs='+', help='Files')
    args = parser.parse_args()

    print 'Looping'

    for fn in args.fns:
        print
        print fn
        fn_out = fn.replace('.jl', '.png')
        if fn_out == fn:
            raise Exception()
        data = load_jl(fn)

        limit = 32768
        limit = 25000
        data = filter(lambda x: x < limit, data)

        print 'Plotting (%d samples)' % (len(data),)
        plt.hist(data, bins=range(0, limit, 32))
        plt.savefig(fn_out)
        #plt.show()


