from uvscada.ngc import *

import math

'''
Need to account for endmill radius to make the die actualy fit

w=0.805, h=0.789
em=0.0413

Actual used w/h: cos(45) * 0.0413 = 0.02920351
Total w/h: 0.0413
Wasted w/h: 0.0413 - 0.0292 = 0.0121
    each corner
Increase by
'''
cnc = init(
        #em=0.0413,
        em=0.0625,
        fr=2.0,
        fr_z=1.0,
        rpm=600,
        verbose=False)
diew = 0.805
dieh = 0.789
theta = math.atan(diew / dieh)
# FIXME: not necessarily ~45
dw = math.cos(theta) * cnc.em/2
fullw = diew + 2 * dw
dh = math.sin(theta) * cnc.em/2
fullh = dieh + 2 * dh

main_r = 1.063

line('(theta: %0.3f rad, %0.1f deg)' % (theta, theta * 180 / math.pi), verbose=True)
line('(die:  %0.3fw x %0.3fh)' % (diew, dieh), verbose=True)
line('(em:  %0.3f)' % (cnc.em), verbose=True)
line('(died: %0.3fw x %0.3fh)' % (dw, dh), verbose=True)
line('(dief: %0.3fw x %0.3fh)' % (fullw, fullh), verbose=True)

# Original diagram
if 0:
    rect_in_ul(x=-0.403, y=-0.864, w=diew, h=dieh, finishes=1)
    rect_in_ul(x=-0.403, y=-0.075, w=diew, h=dieh, finishes=1)
# Centering properly
if 1:
    sep = 0.10
    line('(Die sep: %0.3f)' % (sep,), verbose=True)
    y = fullh/2 + sep/2
    
    # Find corner xy coordinate then calculate dist to center
    # Does not account for edge rounding (ie slightly underestimates)
    rx = fullw/2
    ry = y + fullh/2
    rd = (rx**2 + ry**2)**0.5
    rsep = main_r - rd
    line('(Edge sep: %0.3f)' % (rsep,), verbose=True)
    line('  (rect: %0.3fx %0.3fy)' % (rx, ry), verbose=True)
    if rsep < 0.05:
        raise Exception("DRC fail")
    # 1.063 - 0.962970924
    
    rect_in_cent(x=0.0, y=-y, w=fullw, h=fullh, finishes=1)
    rect_in_cent(x=0.0, y=y, w=fullw, h=fullh, finishes=1)

# Originaly couldn't finish b/c would lift off
# Now waxing down
circ_cent_out(x=0.0, y=0.0, r=main_r, finishes=1)
end()
