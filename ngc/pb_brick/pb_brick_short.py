#!/usr/bin/env python
# http://linuxcnc.org/docs/html/gcode.html

'''
0.375" endmill
Piece about 2.8" and needs to be cut to 2.5"
Endmill center 0.25" left of metal start
Endmill edge touching y metal start
Cut 0.15" off of each side
'''
EM = 3.0/8

def left():
    print 'G1 X0.000 F1'
xr = 1.25 + 2 * 0.25
def right():
    print 'G1 X%0.3f F1' % (xr,)

def zup():
    print 'G0 Z1.5'

def top():
    print
    print '(top)'
    zup()
    print 'G0 X0 Y0'
    print 'G0 Z0'

    print
    print 'G0 Y0.010'
    right()
    print 'G0 Y0.055'
    left()
    print 'G0 Y0.100'
    right()
    print 'G0 Y0.145'
    left()
    print '(finish)'
    print 'G0 Y0.150'
    right()

def btm():
    print
    print '(btm)'
    zup()
    start = 2.5 + 0.375 + 2 * 0.15 - 0.01
    assert start == 3.165
    print 'G0 X%0.3f Y3.165' % xr
    print 'G0 Z0'
    print
    
    print 'G0 Y3.165'
    left()
    print 'G0 Y3.120'
    right()
    print 'G0 Y3.075'
    left()
    print 'G0 Y3.030'
    right()
    print '(finish)'
    print 'G0 Y3.020'
    # 2.5 + 0.375 + 0.15 = 3.025
    print 'G0 Y3.025'
    left()
top()
btm()
    


print
#zclear()
zup()
print 'G0 X0 Y0'
print 'M30'

# hmm ended up with 2.537
# brick mold is perfect though
# where is the 0.037 coming from?
# tried to do backlash compensation
# tried re-milling other side (ie if slipped)
# Is the endmill worn down?  Really the diameter I think it is?
# easy test: make it plunge more
# didn't help at least on top side
# 2.495 seems like good target
# actual: 
# hmm loose fit now
# next one don't adjust and see how it fits
# vice misalignment?

