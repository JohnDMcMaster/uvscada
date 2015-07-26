#!/usr/bin/env python
import sys
bmRequestTypes = {}
bRequests = {}
wValues = {}
wIndexs = {}
if len(sys.argv) < 2:
    fn = '01.txt'
else:
    fn = sys.argv[1]
f = open(fn)
key = int(f.readline().split(',')[1], 0)
print 'key: 0x%04X' % key

for l in f.readlines():
    # n_rw = dev_ctrl_msg(0xC0, 0x0B, 0x62C8, 0x435B, buff, 1);
    #l = l[len('n_rw = dev_ctrl_msg('):]
    #l = l.replace('(', '').replace(');', '')
    (bmRequestType, bRequest, wValue, wIndex) = [int(part, 0) for part in l.split(',')[0:4]]
    
    bmRequestTypes[bmRequestType] = bmRequestTypes.get(bmRequestType, 0) + 1
    bRequests[bRequest] = bRequests.get(bRequest, 0) + 1
    wValues[wValue] = wValues.get(wValue, 0) + 1
    wIndexs[wIndex] = wIndexs.get(wIndex, 0) + 1
    
print
print 'bmRequestType (%u unique)' % len(bmRequestTypes)
for (k, v) in bmRequestTypes.items():
    print '  0x%02X: %u' % (k, v)
    
print
print 'bRequest (%u unique)' % len(bRequests)
for (k, v) in bRequests.items():
    print '  0x%02X: %u' % (k, v)

print
print 'wValue (%u unique)' % len(wValues)
for (k, v) in wValues.items():
    print '  0x%02X: %u' % (k, v)

print
print 'wIndex (%u unique)' % len(wIndexs)
for (k, v) in wIndexs.items():
    print '  0x%02X: %u' % (k, v)

