import struct

'''
Datasheet says 2K (word?) => 4 KB
First 0x1000 (4096) retain code so seems correct
TODO: try programmer upper addresses more and see if anything else sticks other than id and config



IMPORTANT: 
*** !!! The parts you are attempting to program may have LP,XT,HS, or RC suffixes at the device marking.
This indicates that the part is manufactured/tested with preset Oscillator settings.
If that is the case, please make sure you select the same Oscillator setting
in the DEVICE-CONFIGURE menu before programming the part !!!
*** User IDs are the 4 Least Significant Bits of locations 1000h, 1002h, 1004h and 1006h in the buffer.
*** The Configuration Settings (including Code Protect bits) are stored at buffer addresses 1FFEh & 1FFFh.
*** Parts are verified at High and Low voltages depending on Oscillator settings. See Microchip specification for details.
'''

prefix = 'pic16c57'

if 1:
    buff = bytearray('\xFF' * 0x2000)
    size = 4096
    
    def w12(addr, w):
        w1 = w & 0x0FFF
        if w1 != w:
            raise Exception("Data overflow")
        buff[addr:addr+2] = struct.pack('<H', w1)
    
    for i in xrange(0, size, 2):
        w12(i, i)
    '''
    *** The Configuration Settings (including Code Protect bits) are stored at buffer addresses 1FFEh & 1FFFh.
    
    Bit 11-4 "read as 0" => write as 0  
    3: CP
        0 = Code protection on
    2: WD
        0 = WDT disabled
    1-0: FOSC1:FOSC0: Oscillator selection bits
        00 = LP oscillator
        01 = XT oscillator
        10 = HS oscillator
        11 = RC oscillator    
    Readback as 0xFFF9
    conflicts with datasheet saying should be read back as 0
    '''
    for osc_s, osc_v in (('lp', 0), ('xt', 1), ('hs', 2), ('rc' 3)):
        # CP off
        w12(0x1FFE, 0x8 | osc_v)

        w12(0x1000, 0x012)
        w12(0x1002, 0x345)
        w12(0x1004, 0x678)
        w12(0x1006, 0x9AB)

        open('%s_cnt16_%s.bin' % (prefix, osc_s), 'w').write(buff)

if 0:
    buff = bytearray('\xFF' * 0x2000)
    size = 4096
    
    def w12(addr, w):
        w1 = w & 0x0FFF
        if w1 != w:
            raise Exception("Data overflow")
        buff[addr:addr+2] = struct.pack('<H', w1)
    
    for i in xrange(0, size, 2):
        w12(i, i ^ 0xFFF)
    w12(0x1FFE, 0x001)
    
    open('%s_test2.bin' % (prefix,), 'w').write(buff)

if 0:
    #size = 0x200
    size = 2048

    f = open('%s_%04xh_ff.bin' % (prefix, size), 'w')
    for i in xrange(size):
        f.write('\xFF')

    f = open('%s_%04xh_00.bin' % (prefix, size), 'w')
    for i in xrange(size):
        f.write('\x00')

    f = open('%s_%04xh_c16.bin' % (prefix, size), 'w')
    for i in xrange(0, size, 2):
        f.write(struct.pack('<H', i))

    '''
    *** User IDs are the 4 Least Significant Bits of locations 1000h, 1002h, 1004h and 1006h in the buffer.
    *** The Configuration Settings (including Code Protect bits) are stored at buffer addresses 1FFEh & 1FFFh.
    '''
    f = open('%s_%04xh_c16_cp.bin' % (prefix, size), 'w')
    size = 2*4096
    for i in xrange(0, size, 2):
        if i == 0x1FFE:
            f.write(struct.pack('<H', 0x000))
        else:   
            f.write(struct.pack('<H', i))

