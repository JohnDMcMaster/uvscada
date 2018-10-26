import struct

'''
The built-in PROM read-prohibition function has the following two modes:
1. Built-in PROM read-prohibition mode (valid in mode 3
2. Expansion prohibition mode (valid in modes 1 and 2)

To set the read prohibition mode, write FCH to address 4000H in the
PROM mode, and the built-in PROM (addresses OOOOOH-03FFFH) read in
mode 3 is prohibited. In this case, if the built-in PROM is accessed external-
ly, FFH is read irrespective of the internal data.

To set the expansion prohibition mode, write FCH to address 5000H in the PROM
mode. The HD647180X will be fixed in mode 0 (single-chip mode) regardless of the
setting of MPo and MP1. Accordingly, the expanded mode (modes 1 and 2) cannot
be used.

Functions 1 and 2 can be used independently.

Note: The read prohibit function can prevent illegal software access from the out-
side by using the above functions 1 and 2. However, no countermeasures are
taken against illegal hardware access such as probing inside the chip or
irradiating the chip with a spot beam.
'''

SZ = 32 * 1024

f = open('hd_c16.bin', 'w')
for i in xrange(0, SZ, 2):
    f.write(struct.pack('>H', i))

f = open('hd_c16_half.bin', 'w')
for i in xrange(0, SZ/2, 2):
    f.write(struct.pack('>H', i))
for i in xrange(SZ/2):
    f.write('\xFF')

f = open('hd_c16_2x.bin', 'w')
for j in xrange(2):
    for i in xrange(0, SZ/2, 2):
        f.write(struct.pack('>H', i))


if 1:
    buff = bytearray('\xFF' * SZ)
    buff = bytearray(open('/tmp/4/1_soldered.bin', 'r').read())
    def w16(addr, w):
        buff[addr:addr+2] = struct.pack('<H', w)
    
    # expansion prohibition mode
    w16(0x5000, 0xFC)
    # read prohibition mode
    w16(0x4000, 0xFC)
    open('preprog.bin', 'w').write(buff)
