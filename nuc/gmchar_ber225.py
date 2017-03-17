'''
Sweep tube using
-Bertan 225 GPIB high voltage power supply
-Keithley 225 for current measurement
'''

from uvscada import k2750
from uvscada import ber225

import time
import json

def run(dmm, ps, f=None, tlimit=10.0, tsleep=1.0):
    print
    print 'Init DMM'
    dmm.curr_dc()

    print
    print 'Init PS'
    # Turn down HV
    ps.off()
    ps.set_volt(0.0)
    ps.apply()
    print 'Stabalizing...'
    time.sleep(3.0)
    
    print
    print 'Ready'
    
    for vset in xrange(200, 1000, 10):
        ps.set_volt(vset)
        ps.apply()
        time.sleep(tsleep)
        # Average measurements for a few seconds
        tstart = time.time()
        imeas = []
        while True:
            imeas.append(dmm.curr_dc())
            dt = time.time() - tstart
            if dt >= tlimit:
                break
        iavg = sum(imeas) / len(imeas)
        # len(imeas), 1e6 * iavg
        
        ps_vmeas, ps_imeas = ps.t0()
        print 'PS % 5d V out => % 5d V @ %0.3f mA.  DMM: %0.3f mA' % (vset, ps_vmeas, 1000. * ps_imeas, iavg)
        if f:
            j = {'type': 'meas', 'vset': vset, 'ps_vmeas': ps_vmeas, 'ps_imeas': ps_imeas, 'iavg': iavg, 'dt': dt, 'in': len(imeas), 'tsleep': tsleep}
            f.write(json.dumps(j) + '\n')
            f.flush()

    # HV off
    ps.set_volt(0.0)
    ps.apply()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Characterize GM tube voltage response')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('--dmm', default='/dev/serial/by-id/usb-Prologix_Prologix_GPIB-USB_Controller_PXG6VRG6-if00-port0', help='K2750 serial port')
    parser.add_argument('--ps', default='/dev/serial/by-id/usb-Prologix_Prologix_GPIB-USB_Controller_PXGEN79T-if00-port0', help='K2750 serial port')
    parser.add_argument('fn', nargs='?', default='out.csv', help='csv out')
    args = parser.parse_args()

    if 1:
        print
        print 'Connecting DMM'
        dmm = k2750.K2750(args.dmm)
        dmm_vendor, dmm_model, dmm_sn, _dmm_fw = dmm.ident_ex()
        print 'DMM: %s, %s, S/N %s' % (dmm_vendor, dmm_model, dmm_sn)

    if 1:
        print
        print 'Connecting PS'
        ps = ber225.Ber225()
        polarity, model, fw = ps.m()
        print 'PS: %s w/ FW %s, polarity %s' % (model, fw, polarity)        

    f = None
    if args.fn:
        f = open(args.fn, 'w')
        j = {'type': 'setup', 'dmm': dmm.ident_ex(), 'ps': ps.m()}
        f.write(json.dumps(j) + '\n')

    try:
        run(dmm, ps, f)
    finally:
        ps.z()
        #ps.local()
        #dmm.local()
