from uvscada import ber225

# spoll before any command sent
def spoll_po(spoll):
    
    '''
    If SRQ = 1, pole A5 of the GPIB address was set for
    "SRQ" at "power-on".
    '''
    print 'SQR: %d' % bool(spoll & 0x40)
    
    '''
    0: pass
    1: RAM fail
    2: ROM fail
    3: AD fail
    '''
    ec = spoll & 0x0F
    print 'Self test error code: %d' % ec
    
def spoll_norm(spoll):
    print 'SQR: %d' % bool(spoll & 0x40)
    print 'Invalid cmd: %d' % bool(spoll & 0x20)
    print 'Shutdown z: %d' % bool(spoll & 0x10)
    print 'Auto trip: %d' % bool(spoll & 0x08)
    print 'OV: %d' % bool(spoll & 0x04)
    print 'OC: %d' % bool(spoll & 0x02)
    print '0: %d' % bool(spoll & 0x01)

def spoll():
    spoll = b.gpib.spoll()
    print '0x%02X' % spoll
    if spoll & 0x80:
        print 'spoll: power on'
        spoll_po(spoll)
    else:
        print 'spoll: norm'
        spoll_norm(spoll)
    
    print

b = ber225.Ber225()
gpib = b.gpib
#spoll()

# Why does this take so long?
print 'Check model'
#polarity, model, fw = b.m()
polarity, model, fw = b.model()
b.chk_ok()
print 'PS: %s w/ FW %s, polarity %s' % (model, fw, polarity)

if 1:
    b.chk_ok()
    b.set_volt(40)
    b.chk_ok()

    b.chk_ok()
    b.la(0.005)
    b.chk_ok()
    
    b.chk_ok()
    b.g()
    b.chk_ok()

if 0:
    b.chk_ok()
    b.z()
    b.chk_ok()

if 1:
    b.chk_ok()
    b.r()
    b.chk_ok()

for i in xrange(1):
    v, a = b.t0()
    print '%0.3f kV @ %0.3fmA' % (v / 1000., a * 1000.)

