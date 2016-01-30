from uvscada.ngc import *

cnc = init(
        em=0.0472, # 1.2 mm
        fr=0.15,
        fr_z=0.05,
        rpm=600,
        verbose=True)

D = 0.277
cnc.clear_zn_u = -0.06

line('(Machine centered on window)')
# Full speed (2800 RPM)
# Really should be running 15k w/ air spindle
line('S100')
clear_zq()

d = D - cnc.em
r = d / 2

line()

line('(Points:)')
g0(r, 0)
g0(0, r)
g0(-r, 0)
g0(0, -r)

line()

# G2/G3
# X/Y: end point (G90/G91 influenced)
# I/J: center relative to current position

line('(Move to bottom)')
line('G0 X0 Y%0.3f' % (r,))
clear_zn()
line('(Right side, arc bottom to top)')
line('G2 X0 Y%0.3f I0 J%0.3f F%0.3F' % (-r, -r, cnc.fr))
if 0:
    clear_z()

    line()
    line('(Pause)')
    line('M0')
    line()

    clear_zn()
line('(Left side, arc top to botom)')
line('G2 X0 Y%0.3f I0 J%0.3f F%0.3F' % (r, r, cnc.fr))
clear_z()
line('G0 Z2')

end()

