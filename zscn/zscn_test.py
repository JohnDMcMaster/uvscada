from uvscada import zscn
from uvscada.k2750 import K2750
from uvscada.zscn import floats

import time

if __name__ == '__main__':
    k = K2750(port='/dev/ttyUSB0')
    z = zscn.ZscnSer(device='/dev/ttyACM1')
    
    print 'Ready'
    z.rst()
    print 'Reset'
    z.led('g', 1)

    
    while 0:
        i = 0
        
        print
        
        z.led('b', 0)
        time.sleep(1)
        print '0 % 2u: %0.1f' % (i, k.res())

        z.led('b', 1)
        time.sleep(1)
        print '1 % 2u: %0.1f' % (i, k.res())

    while 0:
        i = 0
        
        print
        
        z.ch_off(0)
        time.sleep(1)
        print '0 % 2u: %0.1f' % (i, k.res())

        z.ch_on(0)
        time.sleep(1)
        print '1 % 2u: %0.1f' % (i, k.res())

    while 1:
        i = 0
        
        print
        
        z.ch_off(32)
        time.sleep(0.5)
        print '0 % 2u: %0.1f' % (i, k.res())

        z.ch_on(32)
        time.sleep(0.5)
        print '1 % 2u: %0.1f' % (i, k.res())

    while 0:
        i = 0
        
        print
        
        z.ch_off(32)
        z.ch_off(33)
        z.ch_off(34)
        time.sleep(0.5)
        print '0 % 2u: %0.1f' % (i, k.res())

        z.ch_on(32)
        z.ch_on(33)
        z.ch_on(34)
        time.sleep(0.5)
        print '1 % 2u: %0.1f' % (i, k.res())

    if 0:
        print 'All off'
        for i in xrange(64):
            z.ch_off(i)

    if 0:
        z.led('o', 1)
        for i in xrange(20):
            z.ch_on(i)
            time.sleep(0.6)
            print '% 3u: %s' % (i, floats(k.res()))
            z.ch_off(i)
        z.led('o', 0)
    
    #zscn.scan_dip(z, k, npins=40, verbose=True)
    #zscn.scan_dip(z, k, npins=40, pins=xrange(30, 41, 1), verbose=True)
