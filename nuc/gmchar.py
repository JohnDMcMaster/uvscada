from uvscada import k2750
from uvscada import e36
from uvscada import plx_usb

import time
import json

def run(dmm, ps, f=None):
    print
    print 'Init DMM'
    dmm.curr_dc()

    print
    print 'Init PS'
    # Turn down HV
    ps.off()
    ps.set_volt(0.0, outp=2)
    # Turn on HV supply (if not already on)
    ps.set_volt(24, outp=1)
    time.sleep(0.5)
    ps.on()
    print 'Stabalizing...'
    time.sleep(3.0)
    
    print
    print 'Ready'
    
    '''
    450 V IIRC is recommended operating
    '''
    for mvin in xrange(0, 6000, 100):
        vin = mvin / 1000.0
        ps.set_volt(vin, outp=2)
        time.sleep(0.6)
        # Average measurements for a few seconds
        tstart = time.time()
        imeas = []
        while True:
            imeas.append(dmm.curr_dc())
            dt = time.time() - tstart
            if dt >= 10.0:
                break
        iavg = sum(imeas) / len(imeas)
        
        vout = vin * 1000.0 / 9.0
        print '%0.3f V ctrl => %0.1f V out => %d meas giving %0.3f uA' % (vin, vout, len(imeas), 1e6 * iavg)
        if f:
            j = {'vctrl': vin, 'v': vout, 'iavg': iavg}
            f.write(json.dumps(j) + '\n')
            f.flush()

    # HV off
    ps.set_volt(0.0, outp=2)

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
        #ps = e36.E36(io=e36.PUSerial(args.ps, verbose=False), verbose=False)
        ps = e36.E36(io=plx_usb.PUGpib(args.ps), verbose=False)
        ps_vendor, ps_model, ps_sn, _ps_fw = ps.ident_ex()
        print 'PS: %s, %s, S/N %s' % (ps_vendor, ps_model, ps_sn)
        
    f = None
    if args.fn:
        f = open(args.fn, 'w')
        j = {'type': 'setup', 'dmm': dmm.ident_ex(), 'ps': ps.ident_ex()}
        f.write(json.dumps(j) + '\n')

    try:
        run(dmm, ps, f)
    finally:
        ps.off()
        ps.local()
        #dmm.local()
