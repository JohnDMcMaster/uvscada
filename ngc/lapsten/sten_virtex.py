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

diew = 0.805
dieh = 0.789
theta = math.atan(diew / dieh)
# FIXME: not necessarily ~45
fullw = diew + 2 * math.cos(theta) * cnc.em
fullh = dieh + 2 * math.cos(theta) * cnc.em

init(
        em=0.0413,
        fr=2.0,
        fr_z=1.0,
        rpm=600)
line('(theta: %0.3f rad, %0.1f deg)' % (theta, theta * 180 / math.pi))
rect_in_ul(x=-0.403, y=-0.864, w=fullw, h=fullh, finishes=1)
rect_in_ul(x=-0.403, y=-0.075, w=fullw, h=fullh, finishes=1)
# Originaly couldn't finish b/c would lift off
# Now waxing down
circ_cent_out(x=0.0, y=0.0, r=1.063, finishes=1)
end()
