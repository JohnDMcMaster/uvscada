from uvscada import k2750
from uvscada import ber225

import time
import json

def run(dmm, ps, f=None, tsleep=1.0):
    print
    print 'Init DMM'
    dmm.volt_dc()

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
    
    '''
    Settle time
    PS settles before DMM
    DMM is much more linear in general though
    Reccomend 1 second settle, especially for large steps
    
    0.4
    PS 0.000 kV out =>    0 V.  DMM:    0 V
    PS 50.000 kV out =>    0 V.  DMM:    0 V
    PS 100.000 kV out =>  100 V.  DMM:  -75 V
    PS 150.000 kV out =>  100 V.  DMM: -131 V
    
    0.5
    PS 0.000 kV out =>    0 V.  DMM:    0 V
    PS 50.000 kV out =>    0 V.  DMM:    0 V
    PS 100.000 kV out =>  100 V.  DMM:  -83 V
    PS 150.000 kV out =>  151 V.  DMM: -142 V

    1.0
    Ready
    PS 0.000 kV out =>    1 V.  DMM:   -1 V
    PS 50.000 kV out =>    1 V.  DMM:  -41 V
    PS 100.000 kV out =>  101 V.  DMM:  -98 V
    PS 150.000 kV out =>  151 V.  DMM: -149 V
    
    0.5
    Ready
    PS 0.000 kV out =>    0 V.  DMM:    0 V
    PS 250.000 kV out =>  251 V.  DMM: -185 V
    '''
    for vset in xrange(0, 1050, 50):
        # TODO: settle time?
        ps.set_volt(vset)
        ps.apply()
        time.sleep(tsleep)
        ps_vmeas, _ps_imeas = ps.t0()
        dmm_vmeas = dmm.volt_dc()
        print 'PS % 5d out => % 5d V.  DMM: % 5d V' % (vset, ps_vmeas, dmm_vmeas)
        if f:
            j = {'type': 'meas', 'vset': vset, 'ps_vmeas': ps_vmeas, 'dmm_vmeas': dmm_vmeas, 'tsleep': tsleep}
            f.write(json.dumps(j) + '\n')
            f.flush()

    # HV off
    ps.set_volt(0)
    ps.apply()
    ps.off()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Sweep Berton supply control response')
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
        ps.off()
