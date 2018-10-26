'''
AT89C51 firmware read power analysis torture test
'''

import struct

SZ = 4 * 1024
buff = bytearray('\x00' * SZ)

'''
Alternate pattern:
00 00 ff ff ff ff ff
This should hopefully clearly show up when we align traces
Then do an inverted pattern so we can try to diff the two
'''
for i in xrange(SZ):
    state = i % 8
    if state < 2:
        buff[i] = 0x00
    else:
        buff[i] = 0xFF

open('at89c51_pat1.bin', 'w').write(buff)

# invert
for i in xrange(SZ):
    buff[i] ^= 0xFF
open('at89c51_pat1i.bin', 'w').write(buff)

