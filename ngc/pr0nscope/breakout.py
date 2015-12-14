#!/usr/bin/env python
# http://linuxcnc.org/docs/html/gcode.html
# hole locations

def gen(name, points):
    print
    print '(%s)' % name
    for x, y in points:
        print 'G0 X%0.3f Y%0.3f' % (x - x0, y)
        # no z...lost the cable

chassis = []
for x in (0.760, 10.760):
    for y in (1.000, 3.000):
        chassis.append((x, y))

bbb = [
    (4.460, 0.625),
    (4.460, 2.525),
    (7.060, 0.750),
    (7.060, 2.400),
    ]

db25l = []
for x in (0.630, 5.380):
    for y in (4.087, 5.387):
        db25l.append((x, y))
db25r = [(x + 6.140 - 0.630, y) for x, y in db25l]

print '(Generating)'
print 'G20'

if 1:
    x0 = 0.0
    #gen('bbb', bbb)
    gen('db25l', db25l)
    gen('chassis', chassis)
if 0:
    x0 = 6.0
    gen('db25r', db25r)
    #gen('chassis', chassis)

if 0:
    x0 = 6.0
    gen('chassis', chassis)

print
print 'M3'

'''
(db25l)
G0 X0.630 Y4.087
G0 X0.630 Y5.387
G0 X5.380 Y4.087
G0 X5.380 Y5.387
'''

