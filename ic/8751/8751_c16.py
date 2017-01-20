import struct

SZ = 4 * 1024
f = open('8751_c16.bin', 'w')

for i in xrange(0, SZ, 2):
    f.write(struct.pack('>H', i))

