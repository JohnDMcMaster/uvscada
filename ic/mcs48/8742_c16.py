import struct

SZ = 0x800
f = open('8742_c16.bin', 'w')

for i in xrange(0, SZ, 2):
    f.write(struct.pack('>H', i))

