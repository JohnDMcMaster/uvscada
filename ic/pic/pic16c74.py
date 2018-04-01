import struct

'''
Datasheet
4K words
74A adds brown out reset protection
"The separate instruction and data buses of the Harvard
architecture allow a 14-bit wide instruction word with
the separate 8-bit wide data."

14.1 Configuration Bits
The user will note that address 2007h is beyond the
user program memory space. In fact, it belongs to the
special test/configuration memory space (2000h -
3FFFh), which can be accessed only during program-
ming.


BPM
IMPORTANT: The ID locations are addressed in the buffer at 0x4000 - 0x4007.
The Configuration word is located at buffer address 0x400E.  Both the ID and
Configuration word may be set from the CONFIGURE menu or from the above
mentioned addresses in your data file.  Any reserved or Code Protect bit locations
are treated as don't-cares in the buffer.  If Code Protection is
desired, use DEVICE/OPTIONS/'Secure After Programming' to enable.  Reserved
bits are set in the programming algorithm and cannot be changed.
'''

prefix = 'pic16c74'

# Tried adding config word but BP got angry
buff = bytearray('\xFF' * 0x4008)
sizew = 0x2000

def w14(addr, w):
    w1 = w & 0x3FFF
    if w1 != w:
        raise Exception("Data overflow")
    buff[addr:addr+2] = struct.pack('<H', w1)

for i in xrange(0, sizew, 2):
    w14(i, i)

# Dummy ID bytes
w14(0x4000, 0x0012)
w14(0x4002, 0x0123)
w14(0x4004, 0x0234)
w14(0x4006, 0x0345)

open('%s_cnt16s.bin' % (prefix,), 'w').write(buff)
