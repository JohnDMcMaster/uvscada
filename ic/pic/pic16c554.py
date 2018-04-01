import struct

'''
IMPORTANT: The ID locations are addressed in the buffer at 0x4000 - 0x4007.
The Configuration word is located at buffer address 0x400E.  Both the ID and
Configuration word may be set from the CONFIGURE menu or from the above
mentioned addresses in your data file.  Any reserved or Code Protect bit locations
are treated as don't-cares in the buffer.  If Code Protection is
desired, use DEVICE/OPTIONS/'Secure After Programming' to enable.  Reserved
bits are set in the programming algorithm and cannot be changed.
'''

prefix = 'pic16c554'
buff = bytearray('\xFF' * 0x4010)
words = 512

def w14(addr, w):
    w1 = w & 0x3FFF
    if w1 != w:
        raise Exception("Data overflow")
    buff[addr:addr+2] = struct.pack('<H', w1)

def w16(addr, w):
    buff[addr:addr+2] = struct.pack('<H', w)

for i in xrange(words):
    w14(2 * i, i)

# ID bytes
# Shifted address because overflowed 14 bit 
w14(0x4000, 0x0400)
w14(0x4002, 0x0402)
w14(0x4004, 0x0404)
w14(0x4006, 0x0406)

open('%s_cnt16s.bin' % (prefix,), 'w').write(buff)
