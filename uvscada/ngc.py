# http://linuxcnc.org/docs/html/gcode.html

'''
Think I should take more of a matplotlib approach with global module state
'''

class CNC(object):
    def __init__(self, em=1./8):
        self._em = em
        self._clear_zp = 0.100
        self._clear_zps = 0.050
        self._clear_zn = -0.020
        self._fr = 2.0
        self._fr_z = 1.0
        print '(Endmill: %0.4f)' % self._em
    
    def clear_z(self):
        print 'G1 Z%0.3f F%0.3f' % (self._clear_zps, self._fr_z)
        print 'G0 Z%0.3f' % self._clear_zp

    def clear_zq(self):
        print 'G0 Z%0.3f' % self._clear_zp
    
    def clear_zn(self):
        print 'G0 Z%0.3f' % self._clear_zps
        print 'G1 Z%0.3f F%0.3f' % (self._clear_zn, self._fr_z)
    
    # Exact clearance
    def clear_ep(self, pos):
        print '(ClearE+ %0.3f)' % pos
        return '%0.3f' % (pos + self._em/2)

    def clear_en(self, pos):
        print '(ClearE- %0.3f)' % pos
        return '%0.3f' % (pos - self._em/2)

    # Delta clearance
    def clear_dp(self, pos):
        print '(Clear+ %0.3f)' % pos
        return '%0.3f' % (pos + self._em/2 + 0.25)

    def clear_dn(self, pos):
        print '(Clear- %0.3f)' % pos
        return '%0.3f' % (pos - self._em/2 - 0.25)

    def xy(self, x, y):
        print 'G1 X%0.3f Y%0.3f F%0.3f' % (x, y, self._fr)

    def xy_g0(self, x, y):
        print 'G0 X%0.3f Y%0.3f' % (x, y)

    # Cut rectangle with upper left coordinate given
    # Cutter centered on rectangle
    def rect_slot_ul(self, x, y, w, h, com=True):
        if com:
            print
            print '(rect_slot X%0.3f Y%0.3f W%0.3f H%0.3f)' % (x, y, w, h)
        self.xy_g0(x, y)
        self.clear_zn()
        self.xy(x + w, y + 0)
        self.xy(x + w, y + h)
        self.xy(x + 0, y + h)
        self.xy(x + 0, y + 0)
        self.clear_zq()
        
    # Cut rectangle, compensating to cut inside of it
    # Endmill is assumed to be square
    def rect_in_ul(self, x, y, w, h, finishes=1):
        print
        print '(rect_in X%0.3f Y%0.3f W%0.3f H%0.3f)' % (x, y, w, h)
        # Roughing pass
        if finishes:
            if finishes != 1:
                raise Exception("FIXME")
            finish_u = 0.005
            self.rect_slot_ul(x + self._em/2 + finish_u, y + self._em/2 + finish_u, w - self._em - finish_u, h - self._em - finish_u, com=False)
        # Finishing pass
        self.rect_slot_ul(x + self._em/2, y + self._em/2, w - self._em, h - self._em, com=False)

    '''
    G2: clockwise arc
    G3: counterclockwise arc
    ''' 
    def circ_cent_slot(self, x, y, r, cw=False, com=True, clear=True):
        if com:
            print
            print '(circ_cent_slot X%0.3f Y%0.3f R%0.3f)' % (x, y, r)
        # Arbitrarily start at left
        self.xy_g0(x - r - self._em, y)
        self.clear_zn()
        print 'G3 I%0.3f F%0.3f' % (r, self._fr)
        self.clear_zq()

    # Cut circle centered at x, y 
    # Leaves a hole the size of r
    def circ_cent_in(self, x, y, r):
        print
        print '(circ_cent_in X%0.3f Y%0.3f R%0.3f)' % (x, y, r)
        raise Exception("FIXME")

    # Cut circle centered at x, y 
    # Leaves a cylinder the size of r
    def circ_cent_out(self, x, y, r, finishes=1):
        print
        print '(circ_cent_out X%0.3f Y%0.3f R%0.3f)' % (x, y, r)
        # Roughing pass
        if finishes:
            if finishes != 1:
                raise Exception("FIXME")
            finish_u = 0.005
            self.circ_cent_slot(x, y, r - self._em - finish_u, cw=True, com=False)
        self.circ_cent_slot(x, y, r - self._em, cw=False, com=False)
    
    def end(self):
        print
        print 'G0 X0 Y0'
        print 'M30'

