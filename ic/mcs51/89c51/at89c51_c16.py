'''
AT89C51 firmware read power analysis torture test
'''

import struct

SZ = 4 * 1024
buff = bytearray('\x00' * SZ)

open('at89c51_0.bin', 'w').write(buff)

for i in xrange(0, SZ, 2):
    buff[i:i+2] = struct.pack('>H', i)

open('at89c51_c16.bin', 'w').write(buff)


