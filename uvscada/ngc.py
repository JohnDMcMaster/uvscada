'''
http://linuxcnc.org/docs/html/gcode.html'''

import sys
from os import path

cnc = None
class CNC(object):
    def __init__(self, em=1./8, rpm=None, fr=2.0, fr_z=1.0, verbose=True):
        # Endmill diameter
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
        self.verbose = verbose
        
        # Name output .ngc same as the generating python file
        # Could support multiple files by adding an open function if needed
        m_fn = path.abspath(sys.modules['__main__'].__file__)
        ngc_fn = m_fn.replace('.py', '.ngc')
        if ngc_fn.find('.ngc') < 0:
            raise Exception("Failed to replace extension")
        # Output file
        self.f = open(ngc_fn, 'w')
        
        self.chain = clear_z
        
def init(*args, **kwargs):
    global cnc
    
    cnc = CNC(*args, **kwargs)
    start()
    return cnc

def line(s='', verbose=None):
    if verbose is None:
        verbose = cnc.verbose
    cnc.f.write(s + '\n')
    if verbose:
        print s

def start():
    line('(Endmill: %0.4f)' % cnc.em)
    line('G90')
    clear_zq()
    line('M3 S%0.1f' % cnc.rpm)

def end():
    line()
    # Make sure don't crash
    clear_zq()
    line('G0 X0 Y0')
    line('M30')

def fmt(f):
    return '%+0.3f' % f

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

def g0(x, y):
    line('G0 X%0.3f Y%0.3f' % (x, y))

def g1(x, y):
    line('G1 X%s Y%s F%0.3f' % (fmt(x), fmt(y), cnc.fr))

# Cut rectangle with upper left coordinate given
# Cutter centered on rectangle
def rect_slot_ul(x, y, w, h, com=True, chain=True, leadin='g0'):
    if com:
        line()
        line('(rect_slot_ul X%s Y%s W%s H%s)' % (fmt(x), fmt(y), fmt(w), fmt(h)))
    if leadin == 'g0':
        g0(x, y)
        clear_zn()
    elif leadin == 'g1':
        g1(x, y)
    else:
        raise Exception("Oops")
    g1(x + w, y + 0)
    g1(x + w, y + h)
    g1(x + 0, y + h)
    g1(x + 0, y + 0)
    if chain:
        cnc.chain()
    
# Cut rectangle, compensating to cut inside of it
# Endmill is assumed to be square
def rect_in_ul(x, y, w, h, finishes=1, chain=True, com=True):
    if com:
        line()
        line('(rect_in_ul X%s Y%s W%s H%s)' % (fmt(x), fmt(y), fmt(w), fmt(h)))
    # Roughing pass
    if finishes:
        if finishes != 1:
            raise Exception("FIXME")
        line('(Rough)')
        rect_slot_ul(x + cnc.em/2 + cnc.finish_u, y + cnc.em/2 + cnc.finish_u, w - cnc.em - cnc.finish_u, h - cnc.em - cnc.finish_u, com=False, chain=False)
        # Finishing pass
        line('(Finish)')
        rect_slot_ul(x + cnc.em/2, y + cnc.em/2, w - cnc.em, h - cnc.em, com=False, chain=chain, leadin='g1')
    else:
        # Finishing pass
        rect_slot_ul(x + cnc.em/2, y + cnc.em/2, w - cnc.em, h - cnc.em, com=False, chain=chain)

def rect_in_cent(x, y, w, h, *args, **kwargs):
    x0 = x - w/2
    y0 = y - h/2
    if kwargs.get('com', True):
        line()
        line('(rect_in_cent X%s Y%s W%s H%s)' % (fmt(x), fmt(y), fmt(w), fmt(h)))
    kwargs['com'] = False
    rect_in_ul(x0, y0, w, h, *args, **kwargs)

'''
G2: clockwise arc
G3: counterclockwise arc
''' 
def circ_cent_slot(x, y, r, cw=False, com=True, leadin='g0', chain=True):
    if com:
        line()
        line('(circ_cent_slot X%sf Y%s R%s)' % (fmt(x), fmt(y), fmt(r)))

    # Arbitrarily start at left
    x0 = x - r
    if leadin == 'g0':
        g0(x0, y)
        clear_zn()
    elif leadin == 'g1':
        g1(x0, y)
    else:
        raise Exception("Oops")

    line('G3 I%0.3f F%0.3f' % (r, cnc.fr))
    if chain:
        cnc.chain()

# Cut circle centered at x, y 
# Leaves a hole the size of r
def circ_cent_in(x, y, r):
    line()
    line('(circ_cent_in X%s Y%s R%s)' % (fmt(x), fmt(y), fmt(r)))
    raise Exception("FIXME")

# Cut circle centered at x, y 
# Leaves a cylinder the size of r
def circ_cent_out(x, y, r, finishes=1):
    line()
    line('(circ_cent_out X%s Y%s R%s)' % (fmt(x), fmt(y), fmt(r)))
    # Roughing pass
    if finishes:
        if finishes != 1:
            raise Exception("FIXME")
        line('(Rough)')
        circ_cent_slot(x, y, r + cnc.em + cnc.finish_u, cw=True, com=False, chain=False)
        line('(Finish)')
        circ_cent_slot(x, y, r + cnc.em, cw=False, com=False, leadin='g1')
    else:
        circ_cent_slot(x, y, r + cnc.em, cw=False, com=False)
