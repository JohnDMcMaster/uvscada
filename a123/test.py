from uvscada.e36 import PUSerial, E36, print_errors

import os
import time
import json

io = PUSerial('/dev/ttyUSB0', verbose=False)
ps = E36(io=io, verbose=False)
#ps.rst()
#ps.clr()

print 'Version: %s' % ps.version()
print_errors(ps)
ps.apply(3.6, 3.0)
ps.disp_vi()
ps.off()
ps.on()
print ps.volt()


log_dir = 'log'
if not os.path.exists(log_dir):
    os.mkdir(log_dir)
fn = 'log/out.jl'
jf = open(fn, 'w')

class Bench(object):
    def __enter__(self):
        self.tstart = time.time()
    
    def __exit__(self, type, value, traceback):
        tend = time.time()
        print 'Delta: %0.3f' % (tend - self.tstart,)

tstart = time.time()
while 1:
    v = ps.volt()
    i = ps.curr()
    
    t = time.time()
    
    print '%0.1f %0.3f V @ %0.3f A' % (t, v, i)
    
    j = {
        'event': 'vi',
        't': t,
        'v': v,
        'i': i,
    }
    jf.write(json.dumps(j) + '\n')
    
    # Charging terminated?
    if i < 0.001:
        print 'Charging terminated'
        jf.write(json.dumps({'event': 'charge_done', 't': t}) + '\n')
        break


