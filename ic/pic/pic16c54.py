import struct

'''
Datasheet


BPM
IMPORTANT: 

The parts you are attempting to Program may have LP,XT,HS, or RC suffixes in the device marking.
This indicates that the part is manufactured/tested with preset Oscillator settings.
If this is the case, please make sure you select the same Oscillator setting at Data Pattern address 1FFEh or under Device Configure.

ID locations are stored in the Data Pattern at 400h - 407h.
The Configuration Word is located at Data Pattern addresses 1FFEh & 1FFFh.
Both the IDs and Configuration Word may be set under Device Configure and Data Pattern.
Parts are verified at High and Low voltages depending on Oscillator settings per Microchip specs.
'''

prefix = 'pic16c54'

buff = bytearray('\xFF' * 0x2000)
size = 0x200

def w12(addr, w):
    w1 = w & 0x0FFF
    if w1 != w:
        raise Exception("Data overflow")
    buff[addr:addr+2] = struct.pack('<H', w1)

for i in xrange(0, size, 2):
    w12(i, i)
for osc_s, osc_v in (('lp', 0), ('xt', 1), ('hs', 2), ('rc', 3)):
    # CP off
    w12(0x1FFE, 0x8 | osc_v)

    w12(0x1000, 0x012)
    w12(0x1002, 0x345)
    w12(0x1004, 0x678)
    w12(0x1006, 0x9AB)

    open('%s_cnt16_%s.bin' % (prefix, osc_s), 'w').write(buff)

