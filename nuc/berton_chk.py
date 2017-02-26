from uvscada import k2750
from uvscada import e36
from uvscada import plx_usb

import time
import json

def run(dmm, ps, f=None):
    print
    print 'Init DMM'
    dmm.volt_dc()

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
    0 - 9V => 0 - 1000V
    Manual indicates you can go a little higher
    should test?
    Good PS should cut off if user goes too high
    
    and so it crashed by 8.5 => -1001.1
    '''
    for mvin in xrange(0, 9100, 100):
        vin = mvin / 1000.0
        ps.set_volt(vin, outp=2)
        '''
        0.5 seems to be where things are nearly stable
        0.6 is a little more conservative

        0.1
        0.000 => -5.2
        0.100 => -4.7
        0.200 => -4.5
        0.300 => -4.5
        0.400 => -30.8
        0.500 => -40.4

        0.3
        0.000 => -10.4
        0.100 => -9.3
        0.200 => -20.5
        0.300 => -28.9
        0.400 => -45.0
        0.500 => -55.6
        
        0.4
        0.000 => -4.9
        0.100 => -6.1
        0.200 => -20.5
        0.300 => -33.9
        0.400 => -45.2
        0.500 => -57.2
        
        0.5
        0.000 => -4.5
        0.100 => -9.3
        0.200 => -22.4
        0.300 => -34.3
        0.400 => -46.2
        0.500 => -57.9
    
        1.0
        0.000 => -3.5
        0.100 => -10.9
        0.200 => -22.7
        0.300 => -34.4
        0.400 => -46.3
        0.500 => -58.0
        '''
        time.sleep(0.6)
        vout = dmm.volt_dc()
        print '%0.3f => %0.1f' % (vin, vout)
        if f:
            j = {'vin': vin, 'vout': vout}
            f.write(json.dumps(j) + '\n')
            f.flush()

    # HV off
    ps.set_volt(0.0, outp=2)

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
