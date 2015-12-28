from uvscada.ngc import CNC

cnc = CNC(em=0.0472)
D = 0.25
cnc._clear_zn = -0.05
cnc._fr = 0.15
cnc._fr_z = 0.1

print '(Machine centered on window)'
print 'G90'
# Full speed (2800 RPM)
print 'S100'
cnc.clear_zq()

d = D - cnc._em
r = d / 2

print

print '(Points:)'
cnc.g0(r, 0)
cnc.g0(0, r)
cnc.g0(-r, 0)
cnc.g0(0, -r)

print

# G2/G3
# X/Y: end point (G90/G91 influenced)
# I/J: center relative to current position

print '(Move to bottom)'
print 'G0 X0 Y%0.3f' % (r,)
cnc.clear_zn()
print '(Right side, arc bottom to top)'
print 'G2 X0 Y%0.3f I0 J%0.3f F%0.3F' % (-r, -r, cnc._fr)
if 0:
    cnc.clear_z()

    print
    print '(Pause)'
    print 'M0'
    print

    cnc.clear_zn()
print '(Left side, arc top to botom)'
print 'G2 X0 Y%0.3f I0 J%0.3f F%0.3F' % (r, r, cnc._fr)
cnc.clear_z()
print 'G0 Z2'

cnc.end()

