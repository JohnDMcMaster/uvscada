#!/usr/bin/env python
# http://linuxcnc.org/docs/html/gcode.html
# Calcs 0.125/2 (0.0625) offsets for cutter
# TODO: coordinate system transform for this?

'''
0.05 depth broke bit due to chatter on entry
0.04 had previously run successfully
Use 0.03 to be conservatrive
does entering from right have more chatter than entering  from left?
right side is sawszall cut and left is bandsaw cut
'''

EM = 0.125

print 'G0 Z0.75'

def comp(pos):
    print '(Comp %0.3f)' % pos
    return '%0.3f' % (pos + EM/2)

def clearP(pos):
    print '(Clear+ %0.3f)' % pos
    return '%0.3f' % (pos + EM/2 + 0.25)

def clearN(pos):
    print '(Clear- %0.3f)' % pos
    return '%0.3f' % (pos - EM/2 - 0.25)

def vright():
    print 'G1 X%s F1' % clearP(7.0)
def vleft():
    print 'G1 X%s F1' % clearN(0.0)
def cut_vert():
    print 'G0 Z -0.030'
    vright()
    print 'G0 Z -0.060'
    vleft()
    print 'G0 Z -0.090'
    vright()
    print 'G0 Z -0.120'
    vleft()

def siz_vert():
    print 'G0 Z -0.125'
    vright()

def fin_vert():
    print 'G0 Z -0.125'
    vright()

# Exact clearance
def clearEP(pos):
    print '(ClearE+ %0.3f)' % pos
    return '%0.3f' % (pos + EM/2)

def clearEN(pos):
    print '(ClearE- %0.3f)' % pos
    return '%0.3f' % (pos - EM/2)

def hdown():
    print '(Down)'
    print 'G1 Y%s F0.5' % clearEP(0.25)
    print 'G1 Y%s F1.0' % clearEP(2.75 - EM)
    print 'G1 Y%s F0.5' % clearEP(2.75)
def hup():
    print '(Up)'
    print 'G1 Y%s F0.5' % clearEN(2.75)
    print 'G1 Y%s F1.0' % clearEN(0.25 + EM)
    print 'G1 Y%s F0.5' % clearEN(0.25)

def cut_hor():
    print 'G0 Y%s' % clearEN(0.25)
    print 'G0 Z 0.05'
    print 'G1 Z -0.030 F0.5'
    hdown()
    print 'G1 Z -0.060 F0.5'
    hup()
    print 'G1 Z -0.090 F0.5'
    hdown()
    print 'G1 Z -0.120 F0.5'
    hup()

def siz_hor():
    print 'G0 Y%s' % clearEN(0.25)
    print 'G0 Z 0.05'
    print 'G1 Z -0.125 F0.5'
    hdown()

def fin_hor():
    print 'G0 Y%s' % clearEN(0.25)
    print 'G0 Z 0.05'
    print 'G1 Z -0.125 F0.5'
    hdown()

def zclear():
    print 'G1 Z0.05 F1'
    print 'G0 Z0.75'

def zclearq():
    print 'G0 Z0.75'

def bulk():
    print
    print '(Top)'
    print 'G0 Y0'
    print 'G0 X-0.3 Y%s' % comp(0.125)
    cut_vert()
    zclearq()

    print
    print '(Bottom)'
    print 'G0 X-0.3 Y%s' % comp(2.750)
    cut_vert()
    zclearq()


    print
    print '(Left)'
    print 'G0 X0'
    print 'G0 X%s Y-0.3 ' % comp(0.375)
    cut_hor()
    zclear()

    print
    print '(Right)'
    print 'G0 X%s Y-0.3' % comp(6.500)
    cut_hor()
    zclear()




def sizing():
    print
    print
    print
    print '(Sizing)'

    print
    print '(Top)'
    print 'G0 Y0'
    print 'G0 X-0.3 Y%s' % comp(0.125)
    siz_vert()
    zclearq()

    print
    print '(Bottom)'
    print 'G0 X-0.3 Y%s' % comp(2.750)
    siz_vert()
    zclearq()


    print
    print '(Left)'
    print 'G0 X%s Y-0.3 ' % comp(0.375)
    siz_hor()
    zclear()

    print
    print '(Right)'
    print 'G0 X%s Y-0.3' % comp(6.500)
    siz_hor()
    zclear()






def finish():
    print
    print
    print
    print '(Finish)'

    print
    print '(Top)'
    print 'G0 Y0'
    print 'G0 X-0.3 Y%s' % comp(0.125)
    fin_vert()
    zclearq()

    print
    print '(Bottom)'
    print 'G0 X-0.3 Y%s' % comp(2.750)
    fin_vert()
    zclearq()


    print
    print '(Left)'
    print 'G0 X0'
    print 'G0 X%s Y-0.3 ' % comp(0.375)
    fin_hor()
    zclear()

    print
    print '(Right)'
    print 'G0 X%s Y-0.3' % comp(6.500)
    fin_hor()
    zclear()

def slotv1():
    global EM
    EM = 0.188
    
    print
    print
    print
    print '(Slot)'
    print '(0.188 endmill)'
    # All the way through + some clearance
    print 'G0 X%s Y%s' % (clearEP(0.500), clearEP(1.250))
    print 'G0 Z0.05'
    
    def down():
        print 'G1 Y%s F1' % (clearEN(1.750))
    def up():
        print 'G1 Y%s F1' % (clearEP(1.250))
    
    z = 0.0
    for i in xrange(999):
        if z <= -0.255:
            break
        z -= 0.03
        print 'G1 Z%0.3f F0.1' % z
        if i % 2 == 0:
            down()
        else:
            up()
        

    zclear()

    EM = 0.125

def slotv2():
    global EM
    EM = 0.188
    
    raise Exception("FIXME: cuts into slideway")
    print
    print
    print
    print '(Slot)'
    print '(0.188 endmill)'
    # All the way through + some clearance
    print 'G0 X%s Y%s' % (clearEP(0.375), clearEP(1.250))
    print 'G0 Z0.05'
    
    # 498:eliminate thin wall forming
    def down():
        print 'G1 X%s Y%s F1' % (clearEP(0.498), clearEP(1.250))
        print 'G1     Y%s F1' % (                clearEN(1.750))
        print 'G1 X%s Y%s F1' % (clearEP(0.375), clearEN(1.750))
    def up():
        print 'G1 X%s Y%s F1' % (clearEP(0.498), clearEN(1.750))
        print 'G1     Y%s F1' % (                clearEP(1.250))
        print 'G1 X%s Y%s F1' % (clearEP(0.375), clearEP(1.250))
    
    z = 0.0
    for i in xrange(999):
        if z <= -0.255:
            break
        z -= 0.03
        print 'G1 Z%0.3f F0.1' % z
        if i % 2 == 0:
            down()
        else:
            up()
        

    zclear()

    EM = 0.125

def drill_prep():
    def plunge():
        print 'G0 Z0.05'
        print 'G1 Z-0.125 F0.1'

    print
    print
    print
    print '(Drill prep)'
    print '(0.125 endmill)'

    print 'G0 X%s Y%s' % (comp(0.375 + 0.018), clearEN(0.25 + 0.018))
    plunge()
    zclear()
    
    print 'G0 X%s Y%s' % (comp(0.375 + 0.018), clearEP(2.750 - 0.018))
    plunge()
    zclear()

def drill():
    def peck():
        print '(hand drill)'

    print
    print
    print
    print '(Drill)'
    print '(#56 => 0.0465)'

    print 'G0 X0.500 Y0.250'
    peck()
    zclear()
    
    print 'G0 X0.500 Y2.750'
    peck()
    zclear()


def short():
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

    def top():
        print
        print '(top)'
        print 'G0 Z1.5'
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
        print 'G0 Z1.5'
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
    #top()
    btm()
    

#bulk()
#finish()
#sizing()
#slotv2()
#drill_prep()
#drill()
short()

print
#zclear()
print 'G0 X0 Y0'
print 'M30'


