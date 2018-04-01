import struct

'''
High-Performance 8-Bit CMOS EPROM/ROM Microcontroller

IMPORTANT: 
Programming the Microcontroller Configuration bits to PROCTECTED
Mode will cause the device to fail verify.  This is because Protected mode
encrypts the programmed data.  Microchip does not recommend code protecting
windowed devices.  This may inhibit the device from being able to be reprogramed.
To change your configuration bit setting, please select Device/Configure.
The Configuration word is located at buffer address 0x1FC00-0x1FC01.
The Configuration word may be set from the CONFIGURE menu or from the above
mentioned addresses in your data file.

0x2000 bytes => 8K
4K EPROM

readback is some sort of XOR inversion
BP detects it is secured
'''

prefix = 'pic17c43'

buff = bytearray('\xFF' * 0x2000)
size = 4096

def w12(addr, w):
    w1 = w & 0x0FFF
    if w1 != w:
        raise Exception("Data overflow")
    buff[addr:addr+2] = struct.pack('<H', w1)

def w16(addr, w):
    w1 = w & 0xFFFF
    if w1 != w:
        raise Exception("Data overflow")
    buff[addr:addr+2] = struct.pack('<H', w1)

for i in xrange(0, size, 2):
    w16(i, i)

'''
for osc_s, osc_v in (('lp', 0), ('xt', 1), ('hs', 2), ('rc', 3)):
    # CP off
    w12(0x1FFE, 0x8 | osc_v)

    w12(0x1000, 0x012)
    w12(0x1002, 0x345)
    w12(0x1004, 0x678)
    w12(0x1006, 0x9AB)

    open('%s_cnt16_%s.bin' % (prefix, osc_s), 'w').write(buff)
'''
open('%s_cnt16.bin' % (prefix,), 'w').write(buff)

