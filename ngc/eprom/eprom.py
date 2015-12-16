from uvscada.ngc import CNC

cnc = CNC(em=0.0472)
D = 0.5
cnc._clear_zn = -0.05
cnc._fr = 1.0
cnc._fr_z = 0.2

print '(Machine centered on window)'
print 'G90'
# Full speed (2800 RPM)
print 'S100'

print

d = D - cnc._em
r = d / 2

print '(Move to bottom)'
print 'G0 X0 Y%0.3f' % (r,)
cnc.clear_zn()
print '(Left side, arc bottom to top)'
print 'G2 X0 Y%0.3f I0 J%0.3f' % (-d, -r)
cnc.clear_z()

print
print '(Pause)'
print 'M0'
print

cnc.clear_zn()
print '(Right side, arc top to botom)'
print 'G2 X0 Y%0.3f I0 J%0.3f' % (d, r)
cnc.clear_z()

cnc.end()
