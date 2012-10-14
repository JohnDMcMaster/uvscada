from ctypes import *
import sys
import atexit
import Image
#import cStringIO
#import StringIO
#import numpy

# To speed up rendering
try:
    import psyco
    psyco.full()
except ImportError:
    pass

width = 1600
height = 1200

# Unfortunately this doesn't load in symbols for libmu800
# Still using LD_PRELOAD...
libusb = CDLL("/usr/lib/libusb-1.0.so.0")

#cdll.LoadLibrary("libmu800.so") 
mu800 = CDLL("libmu800.so")

'''
print 'Trying test'
mu800.mu800_test()

simple_cb_t = CFUNCTYPE(None)
@simple_cb_t
def simple_cb():
    print 'Python got CB'
    sys.stdout.flush()

print 'Py: simple CB test setup'
mu800.mu800_simple_cb_test.argtypes = [simple_cb_t]
mu800.mu800_simple_cb_test.restype = None
print 'Py: simple CB test calling'
mu800.mu800_simple_cb_test(simple_cb)

mu800_image_cb_t = CFUNCTYPE(None, POINTER(c_char), c_int, c_int)
@mu800_image_cb_t
def my_cb(data, width, height):
    print "CB'd"
    print 'Some data: data[0] = %u (%c)' % (ord(data[0]), data[0])
    print 'Width: %u' % width
    print 'Height: %u' % height

print 'Trying CB test'
mu800.mu800_cb_test.argtypes = [mu800_image_cb_t]
mu800.mu800_cb_test.restype = None
mu800.mu800_cb_test(my_cb)
'''

# int mu800_init()
mu800.mu800_init.argtypes = None
mu800.mu800_init.restype = c_int

# int mu800_dev_init(void);
mu800.mu800_dev_init.argtypes = None
mu800.mu800_dev_init.restype = c_int

# void mu800_shutdown()
mu800.mu800_shutdown.argtypes = None
mu800.mu800_shutdown.restype = None

# uint8_t *mu800_image(void);
mu800.mu800_image.argtypes = None
mu800.mu800_image.restype = POINTER(c_char)

# int mu800_resolution(unsigned int width, unsigned int height);
mu800.mu800_resolution.argtypes = [c_int, c_int]
mu800.mu800_resolution.restype = c_int

# void mu800_verbose(bool verbose);
mu800.mu800_verbose.argtypes = [c_bool]
mu800.mu800_verbose.restype = None

# Ready to roll
mu800.mu800_init()

@atexit.register
def shutdown():
    '''Unload the module'''
    print "Py: mu800 unloading"
    mu800.mu800_shutdown()

def verbose(v = True):
    '''Turn on/off verbose operation'''
    mu800.mu800_verbose(v)

def resolution(width_in, height_in):
    global width
    global height
    
    width = width_in
    height = height_in
    mu800.mu800_resolution(width, height)

def raw_image():
    '''Take a single usable image and return it in raw format'''
    # Usable means its not the first two which are black
    mu800.mu800_resolution(width, height)
    # Without this it will be freewheeling...need to frame sync
    if mu800.mu800_dev_init():
        raise Exception('Failed to reinit device')
    # How to assign size info?
    ret = mu800.mu800_image()
    #print ret
    # FIXME: how to set length?
    #print len(ret)
    if ret is None:
        raise Exception('Failed ot take image')
    
    # Add proper length semantics
    class MyLen:
        def __init__(self, buff, l):
            self.buff = buff
            self.l = l
        
        def __len__(self):
            return self.l
        
        def __getitem__(self, index):
            if index >= self.l or index < 0:
                raise Exception('Out of bounds')
            return self.buff[index]

        def __getslice__(self, i, j):
            if i >= self.l or j > self.l or j < i or i < 0:
                raise Exception('i %u / j %u out of bounds %u', i, j, self.l)
            return self.buff[i:j]
                    
    ret2 = MyLen(ret, width * height)
    #ret2 = numpy.frombuffer(ret, width * height)
    #ret2 = cast(ret, POINTER(c_byte * (width * height)))
    #print len(ret2)
    #sys.exit(1)
    return ret2

def decode(raw):
    print 'Decoding %ux%u' % (width, height)
    
    #f = cStringIO.StringIO(raw)
    #f = StringIO.StringIO(raw)
    
    #raw = raw.read(width * height * 2 + width * 0 + 0)
    #raw = raw[width * height * 2 + width * 0 + 0:]
    
    # also try 'L;16B', 'I;16', and 'I;16B'
    #image = Image.fromstring('RGBX', (width, height), raw)
    
    image = None
    # no need to reallocate each loop
    image = Image.new("RGB", (width, height), "Yellow")
    bin = ''
    print
    print 'Rendering frame...'
    pos = 0
    for y in range(0, height, 2):
        # GBGB
        # RGRG
        line0 = raw[pos:pos + width]
        pos += width
        bin += line0
        line1 = raw[pos:pos + width]
        pos += width
        bin += line1
    
        if y % (height / 10) == 0:
            print 'Rendering y = %d / %d...' % (y, height)
    
        '''
        GRGRGR...
        BGBGBG...
        '''
        for x in range(0, width, 2):
            R = 0
            G = ord(line0[x + 0])
            B = 0
            image.putpixel((x + 0, y + 0), (R, G, B))
        for x in range(0, width, 2):
            R = ord(line0[x + 1])
            G = 0
            B = 0
            image.putpixel((x + 1, y + 0), (R, G, B))
        for x in range(0, width, 2):
            R = 0
            G = 0
            B = ord(line1[x + 0])
            image.putpixel((x + 0, y + 1), (R, G, B))
        for x in range(0, width, 2):
            R = 0
            G = ord(line1[x + 1])
            B = 0
            image.putpixel((x + 1, y + 1), (R, G, B))
            
    if 1:
        print 'Saving binary'
        open('image.bin', 'w').write(bin)
    if 1:
        print 'Saving png'
        image.save('image.png')
    if 1:
        print 'Displaying image (%u bytes)' % len(bin)
        image.show()

