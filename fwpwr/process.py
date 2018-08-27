import numpy as np
import matplotlib.pyplot as plt

def load_csv(fn, traces, tn):
    print('Loading %s' % fn)
    with open(fn) as f:
        f.readline()
        f.readline()
        f.readline()
        for li, l in enumerate(f):
            # -0.99999341,0.02362205,0.07874016
            parts = l.strip().split(',')
            current = float(parts[1])
            traces[li][tn] = current
        print('Loaded %u lines' % (li + 1,))

def load_traces():
    nt = 8
    ns = 390629

    traces = np.zeros((ns, nt * 2))
    datas = np.zeros(nt * 2)

    print('Loading csvs')
    tn = 0
    for i in xrange(nt):
        load_csv('2018-07-18_01_pat1/%u.csv' % i, traces, tn)
        datas[tn] = 0
        tn += 1

        load_csv('2018-07-18_02_pat1i/%u.csv' % i, traces, tn)
        datas[tn] = 1
        tn += 1

    return traces, datas

def pearson(traces, datas):
    ns = len(traces)
    #ns = ns / 10

    corrs = np.zeros(ns)
    for sn in xrange(ns):
        samples = traces[sn]
        out = np.corrcoef([datas, samples])
        corr = out[0, 1]
        if 0:
            print sn
            print '  ', corr
            print '  ', samples
            print '  ', datas
        corrs[sn] = corr

    return corrs

def plot(corrs):
    plt.clf()
    plt.plot(corrs)
    plt.gca().set_title('Pearson correlation')
    plt.gca().set_xlabel('Sample')
    plt.gca().set_ylabel('Correlation')
    plt.savefig('out.png')
    plt.show()

def run():
    traces, datas = load_traces()
    corrs = pearson(traces, datas)
    plot(corrs)

run()
