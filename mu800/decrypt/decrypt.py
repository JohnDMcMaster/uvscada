import sys

if len(sys.argv) < 2:
    fn = '01.txt'
else:
    fn = sys.argv[1]
f = open(fn)

def rleft16(i, n):
    i = i << n
    return (i & 0xFFFF) | (i / 0x10000)

def rright16(i, n):
    return rleft16(i, 16 - n)

key = int(f.readline().split(',')[1], 0)
check = rright16(key, 4)
#check = 0xAC16
print 'key: 0x%04X' % key
print 'check: 0x%04X' % check
#sys.exit(1)

def decrypt16(i):
    return i ^ check

for l in f.readlines():
    # n_rw = dev_ctrl_msg(0xC0, 0x0B, 0x62C8, 0x435B, buff, 1);
    #l = l[len('n_rw = dev_ctrl_msg('):]
    #l = l.replace('(', '').replace(');', '')
    (bmRequestType, bRequest, wValue, wIndex) = [int(part, 0) for part in l.split(',')[0:4]]
    print 'OUT(0x%02X, 0x%02X, 0x%04X, 0x%04X, ...)' % (bmRequestType, bRequest, decrypt16(wValue), decrypt16(wIndex))

