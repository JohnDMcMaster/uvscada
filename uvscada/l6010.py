'''
LeCroy 6010 GPIB to CAMAC adapter
using ProLogix USB-GPIB adapter

general notes:
-Case insensitive?
-generally poor error detection when sending bad commands...it will do *something*
    try to detect errors before sending
    often will truncate, modulo arith, etc


a   00000000  41 20 30                                          |A 0             |
b   00000000  42 49 4E 20 6D 69 6E 2F  6D 61 78                 |BIN min/max     |
c   none
e   none
f   00000000  46 20 30                                          |F 0             |
i   00000000  49 4E 48 49 42 49 54 20  30                       |INHIBIT 0       |
l   00000000  4C 20 31 36                                       |L 16            |
n   00000000  4E 20 31 38                                       |N 18            |
q   00000000  51 20 31                                          |Q 1             |
r   00000000  52 20 30                                          |R 0             |
u   
    00000000  55 73 69 6E 67 20 73 6C  6F 74 20 31 3B 20 75 6E  |Using slot 1; un|
    00000010  72 65 63 5F 30 31                                 |rec_01          |
v   none
w   00000000  57 20 30                                          |W 0             |
x   00000000  58 20 31                                          |X 1             |
z   none
'''

from plx_usb import PUGpib

import sys

def propget(func):
    locals = sys._getframe(1).f_locals
    name = func.__name__
    prop = locals.get(name)
    if not isinstance(prop, property):
        prop = property(func, doc=func.__doc__)
    else:
        doc = prop.__doc__ or func.__doc__
        prop = property(func, prop.fset, prop.fdel, doc)
    return prop

def propset(func):
    locals = sys._getframe(1).f_locals
    name = func.__name__
    prop = locals.get(name)
    if not isinstance(prop, property):
        prop = property(None, func, doc=func.__doc__)
    else:
        doc = prop.__doc__ or func.__doc__
        prop = property(prop.fget, func, prop.fdel, doc)
    return prop

def propdel(func):
    locals = sys._getframe(1).f_locals
    name = func.__name__
    prop = locals.get(name)
    if not isinstance(prop, property):
        prop = property(None, None, func, doc=func.__doc__)
    else:
        prop = property(prop.fget, prop.fset, func, prop.__doc__)
    return prop

class L6010(object):
    def __init__(self, port='/dev/ttyUSB0'):
        self.gpib = PUGpib(port=port, addr=1, clr=True, eos=3, ser_timeout=1.0, gpib_timeout=0.9)
    
    '''
    Dataway: address
    '''
    @propget
    def a(self):
        # 00000000  41 20 31                                          |A 1             |
        ret = self.gpib.snd_rcv('A')
        return int(ret.split()[1])

    @propset
    def a(self, value):
        if value < 0 or value > 15:
            raise ValueError(value)
        self.gpib.snd('A %d' % value)


    @propget
    def b(self):
        # 00000000  42 49 4E 20 6F 66 66                              |BIN off         |
        # 00000000  42 49 4E 20 6D 69 6E 2F  6D 61 78                 |BIN min/max     |
        ret = self.gpib.snd_rcv('B')
        return int(ret.split()[1])

    @propset
    def b(self, value):
        # anything other than m turns it off
        self.gpib.snd('B %c' % ('m' if value else '0',))

    def c(self):
        self.gpib.snd('C')

    def e(self):
        self.gpib.snd('E')

    '''
    Dataway: function code
    '''
    @propget
    def f(self):
        ret = self.gpib.snd_rcv('F')
        return int(ret.split()[1])

    @propset
    def f(self, value):
        if value < 0 or value > 31:
            raise ValueError(value)
        self.gpib.snd('F %d' % value)


    '''
    Dataway: inhibit
    '''
    @propget
    def i(self):
        ret = self.gpib.snd_rcv('I')
        return bool(int(ret.split()[1]))

    @propset
    def i(self, value):
        s = 'I %d' % (1 if value else 0,)
        self.gpib.snd(s)

    def i2(self, value):
        s = 'i %d' % (1 if value else 0,)
        self.gpib.snd(s)

    @propget
    def l(self):
        ret = self.gpib.snd_rcv('L')
        return bool(int(ret.split()[1]))

    '''
    Dataway: slot number
    '''
    @propget
    def n(self):
        ret = self.gpib.snd_rcv('N')
        return int(ret.split()[1])

    @propset
    def n(self, value):
        if value < 1 or value > 23:
            raise ValueError(value)
        self.gpib.snd('N %d' % value)

    @propget
    def q(self):
        ret = self.gpib.snd_rcv('Q')
        return bool(int(ret.split()[1]))

    @propget
    def r(self):
        ret = self.gpib.snd_rcv('R')
        return bool(int(ret.split()[1]))

    '''
    rq and rqx seem to do the same thing
    They timeout returning data
    00000000  00 00 00 00                                       |....            |
    
    appears in sample register read code
    '''
    #def rq(self):
    #    self.gpib.snd('RQX')
    
    #cbls = %4 d;
    
    # read block command?
    # rb", n, f, a, count);

    @propget
    def u(self):
        '''
        00000000  55 73 69 6E 67 20 73 6C  6F 74 20 31 3B 20 75 6E  |Using slot 1; un|
        00000010  72 65 63 5F 30 31                                 |rec_01          |
        '''
        ret = self.gpib.snd_rcv('U')
        # TODO: parse out
        return ret
    
    @propset
    def u(self, value):
        '''
        likes 1-21 but will sort of accept some o ther values
        00000000  55 73 69 6E 67 20 73 6C  6F 74 20 32 32 3B 20 69  |Using slot 22; i|
        00000010  6C 6C 65 67 61 6C                                 |llegal          |
        '''
        if value < 1 or value > 21:
            raise ValueError(value)
        self.gpib.snd('U %d' % value)

    def v(self):
        self.gpib.snd('V')

    '''
    Data read/write buffer
    '''
    @propget
    def w(self):
        ret = self.gpib.snd_rcv('W')
        return int(ret.split()[1])

    @propset
    def w(self, value):
        # 32 bit signed
        self.gpib.snd('W %d' % value)

    # query only
    @propget
    def x(self):
        # 00000000  58 20 30                                          |X 0             |
        ret = self.gpib.snd_rcv('X')
        return int(ret.split()[1])

    '''
    generates bus activity
    args ignored?
    results in I being set
    '''
    def z(self):
        self.gpib.snd('Z')

    def camo(n,     # slot number of module
            f,      # funtion code
            a,      # address code
            d):     # data
        self.n = n
        self.f = f
        self.a = a
        self.w = d
        ret = self.gpib.rcv(l=10)
        # Q/X update
        print ret

    def cami(n,     # slot number of module
            f,      # funtion code
            a):     # address code
        self.n = n
        self.f = f
        self.a = a
        # needed?
        self.w = 0
        ret = self.gpib.rcv(l=10)
        # Q/X update, data
        print ret
        return ret

