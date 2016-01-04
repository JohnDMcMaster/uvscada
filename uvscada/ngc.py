'''
http://linuxcnc.org/docs/html/gcode.html'''

import sys
from os import path

cnc = None
class CNC(object):
    def __init__(self, em=1./8, rpm=None, fr=2.0, fr_z=1.0):
        self.em = em
        
        # Z rising to clear part ("chaining")
        # Slow withdrawl in material
        self.clear_zps = 0.050
        # After material clear
        self.clear_zp = 0.100
        
        # Depth to go all the way through the part
        self.clear_zn_u = -0.020
        
        # Distance between finishing pass contours
        self.finish_u = 0.005
        
        # Main feedrate (xy)
        self.fr = fr
        # Plunge feedrate
        self.fr_z = fr_z
        
        self.rpm = rpm
        self.verbose = True
        
        # Name output .ngc same as the generating python file
        # Could support multiple files by adding an open function if needed
        m_fn = path.abspath(sys.modules['__main__'].__file__)
        ngc_fn = m_fn.replace('.py', '.ngc')
        if ngc_fn.find('.ngc') < 0:
            raise Exception("Failed to replace extension")
        # Output file
        self.f = open(ngc_fn, 'w')
        
def init(*args, **kwargs):
    global cnc
    
    cnc = CNC(*args, **kwargs)
    start()

def line(s=''):
    cnc.f.write(s + '\n')
    if cnc.verbose:
        print s

def start():
    line('(Endmill: %0.4f)' % cnc.em)
    line('G90')
    clear_zq()
    line('M3 S%0.1f' % cnc.rpm)

def g0(x, y):
    line('G0 X%0.3f Y%0.3f' % (x, y))

def clear_z():
    line('G1 Z%0.3f F%0.3f' % (cnc.clear_zps, cnc.fr_z))
    line('G0 Z%0.3f' % cnc.clear_zp)

def clear_zq():
    line('G0 Z%0.3f' % cnc.clear_zp)

def clear_zn():
    line('G0 Z%0.3f' % cnc.clear_zps)
    line('G1 Z%0.3f F%0.3f' % (cnc.clear_zn_u, cnc.fr_z))

# Exact clearance
def clear_ep(pos):
    line('(ClearE+ %0.3f)' % pos)
    return '%0.3f' % (pos + cnc.em/2)

def clear_en(pos):
    line('(ClearE- %0.3f)' % pos)
    return '%0.3f' % (pos - cnc.em/2)

# Delta clearance
def clear_dp(pos):
    line('(Clear+ %0.3f)' % pos)
    return '%0.3f' % (pos + cnc.em/2 + 0.25)

def clear_dn(pos):
    line('(Clear- %0.3f)' % pos)
    return '%0.3f' % (pos - cnc.em/2 - 0.25)

def xy(x, y):
    line('G1 X%0.3f Y%0.3f F%0.3f' % (x, y, cnc.fr))

def xy_g0(x, y):
    line('G0 X%0.3f Y%0.3f' % (x, y))

# Cut rectangle with upper left coordinate given
# Cutter centered on rectangle
def rect_slot_ul(x, y, w, h, com=True):
    if com:
        line()
        line('(rect_slot X%0.3f Y%0.3f W%0.3f H%0.3f)' % (x, y, w, h))
    xy_g0(x, y)
    clear_zn()
    xy(x + w, y + 0)
    xy(x + w, y + h)
    xy(x + 0, y + h)
    xy(x + 0, y + 0)
    clear_zq()
    
# Cut rectangle, compensating to cut inside of it
# Endmill is assumed to be square
def rect_in_ul(x, y, w, h, finishes=1):
    line()
    line('(rect_in_ul X%0.3f Y%0.3f W%0.3f H%0.3f)' % (x, y, w, h))
    # Roughing pass
    if finishes:
        if finishes != 1:
            raise Exception("FIXME")
        rect_slot_ul(x + cnc.em/2 + cnc.finish_u, y + cnc.em/2 + cnc.finish_u, w - cnc.em - cnc.finish_u, h - cnc.em - cnc.finish_u, com=False)
    # Finishing pass
    rect_slot_ul(x + cnc.em/2, y + cnc.em/2, w - cnc.em, h - cnc.em, com=False)

'''
G2: clockwise arc
G3: counterclockwise arc
''' 
def circ_cent_slot(x, y, r, cw=False, com=True, clear=True):
    if com:
        line()
        line('(circ_cent_slot X%0.3f Y%0.3f R%0.3f)' % (x, y, r))
    # Arbitrarily start at left
    xy_g0(x - r - cnc.em, y)
    clear_zn()
    line('G3 I%0.3f F%0.3f' % (r, cnc.fr))
    clear_zq()

# Cut circle centered at x, y 
# Leaves a hole the size of r
def circ_cent_in(x, y, r):
    line()
    line('(circ_cent_in X%0.3f Y%0.3f R%0.3f)' % (x, y, r))
    raise Exception("FIXME")

# Cut circle centered at x, y 
# Leaves a cylinder the size of r
def circ_cent_out(x, y, r, finishes=1):
    line()
    line('(circ_cent_out X%0.3f Y%0.3f R%0.3f)' % (x, y, r))
    # Roughing pass
    if finishes:
        if finishes != 1:
            raise Exception("FIXME")
        circ_cent_slot(x, y, r - cnc.em - cnc.finish_u, cw=True, com=False)
    circ_cent_slot(x, y, r - cnc.em, cw=False, com=False)

def end():
    line()
    # Make sure don't crash
    clear_zq()
    line('G0 X0 Y0')
    line('M30')

cnc = CNC()
