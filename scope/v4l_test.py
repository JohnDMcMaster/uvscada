'''
sudo pip install v4l2

See the ``linux/videodev2.h`` header file for details.  Currently the
bindings are up to date with the 2.6.34 kernel headers.

0
touptek
USB Camera (0547:6801)
'''

import v4l2
import fcntl
import errno

vd = open('/dev/video0', 'rw')
cp = v4l2.v4l2_capability()
print fcntl.ioctl(vd, v4l2.VIDIOC_QUERYCAP, cp)
print cp.driver
print cp.card
#print dir(cp)

'''
http://linuxtv.org/downloads/v4l-dvb-apis/control.html
'''

# http://stackoverflow.com/questions/13981933/v4l2-fcntl-ioctl-vidioc-s-parm-for-setting-fps-and-resolution-of-camera-capture

# Example 1.8. Enumerating all user controls
def ex_1_8_enum_ctrls():
    print
    print
    print
    print 'ex_1_8_enum_ctrls()'
    queryctrl = v4l2.v4l2_queryctrl()
    querymenu = v4l2.v4l2_querymenu()
    print dir(querymenu)
    print querymenu.id

    def enumerate_menu():
        print "  Menu items:"
        querymenu.id = queryctrl.id
        for querymenu.index in xrange(queryctrl.minimum, queryctrl.maximum + 1):
            if 0 == fcntl.ioctl(vd, v4l2.VIDIOC_QUERYCAP, querymenu):
                print "  %s" % querymenu.name

    for queryctrl.id in xrange(v4l2.V4L2_CID_BASE, v4l2.V4L2_CID_LASTP1):
        break
        print 'loop: %d' % queryctrl.id
        if 0 == fcntl.ioctl(vd, v4l2.VIDIOC_QUERYCTRL, queryctrl):
            if queryctrl.flags & v4l2.V4L2_CTRL_FLAG_DISABLED:
                continue

            print "Control %s" % queryctrl.name

            if queryctrl.type == v4l2.V4L2_CTRL_TYPE_MENU:
                enumerate_menu()
        else:
            #if errno == EINVAL:
            #    continue;

            #perror("VIDIOC_QUERYCTRL");
            print "VIDIOC_QUERYCTRL"
            sys.exit(1)
    
    queryctrl.id = v4l2.V4L2_CID_PRIVATE_BASE
    while True:
        if 0 != fcntl.ioctl(vd, v4l2.VIDIOC_QUERYCTRL, queryctrl):
            # how to check this?
            #if (errno == EINVAL)
            #    break;

            # perror("VIDIOC_QUERYCTRL");
            print "VIDIOC_QUERYCTRL"
            sys.exit(1)
        
        if not (queryctrl.flags & v4l2.V4L2_CTRL_FLAG_DISABLED):
            print "Control %s" % queryctrl.name

            if queryctrl.type == v4l2.V4L2_CTRL_TYPE_MENU:
                enumerate_menu()
        queryctrl.id += 1
    
# ex_1_8_enum_ctrls()

# http://nullege.com/codes/show/src%40v%404%40v4l2-0.2%40tests.py/276/v4l2.VIDIOC_QUERYCAP/python

def valid_string(string):
    for char in string:
        if (ord(char) < 32 or 126 < ord(char)):
            return False
    return True

def get_device_inputs(fd):
    index = 0
    while True:
        input_ = v4l2.v4l2_input(index)
        try:
            fcntl.ioctl(fd, v4l2.VIDIOC_ENUMINPUT, input_)
        except IOError, e:
            assert e.errno == errno.EINVAL
            break
        yield input_
        index += 1

def get_device_outputs(fd):
    index = 0
    while True:
        output = v4l2.v4l2_output(index)
        try:
            fcntl.ioctl(fd, v4l2.VIDIOC_ENUMOUTPUT, output)
        except IOError, e:
            assert e.errno == errno.EINVAL
            break
        yield output
        index += 1

def foreach_device_input(fd, func):
    original_index = v4l2.c_int()
    fcntl.ioctl(fd, v4l2.VIDIOC_G_INPUT, original_index)
  
    for input_ in get_device_inputs(fd):
        if input_.index != original_index.value:
            try:
                fcntl.ioctl(fd, v4l2.VIDIOC_S_INPUT, v4l2.c_int(input_.index))
            except IOError, e:
                if e.errno == errno.EBUSY:
                    continue
                else:
                    raise
        func(fd, input_)
  
    try:
        fcntl.ioctl(fd, v4l2.VIDIOC_S_INPUT, original_index)
    except IOError, e:
        if not (e.errno == errno.EBUSY):
            raise

def get_device_controls(fd):
    # original enumeration method
    queryctrl = v4l2.v4l2_queryctrl(v4l2.V4L2_CID_BASE)
  
    while queryctrl.id < v4l2.V4L2_CID_LASTP1:
        try:
            fcntl.ioctl(fd, v4l2.VIDIOC_QUERYCTRL, queryctrl)
        except IOError, e:
            # this predefined control is not supported by this device
            assert e.errno == errno.EINVAL
            queryctrl.id += 1
            continue
        yield queryctrl
        queryctrl = v4l2.v4l2_queryctrl(queryctrl.id + 1)
  
    queryctrl.id = v4l2.V4L2_CID_PRIVATE_BASE
    while True:
        try:
            fcntl.ioctl(fd, v4l2.VIDIOC_QUERYCTRL, queryctrl)
        except IOError, e:
            # no more custom controls available on this device
            assert e.errno == errno.EINVAL
            break
        yield queryctrl
        queryctrl = v4l2.v4l2_queryctrl(queryctrl.id + 1)

def get_device_controls_by_class(fd, control_class):
    # enumeration by control class
    queryctrl = v4l2.v4l2_queryctrl(
        control_class | v4l2.V4L2_CTRL_FLAG_NEXT_CTRL)
  
    while True:
        try:
            fcntl.ioctl(fd, v4l2.VIDIOC_QUERYCTRL, queryctrl)
        except IOError, e:
            assert e.errno == errno.EINVAL
            break
        if (v4l2.V4L2_CTRL_ID2CLASS(queryctrl.id) != control_class):
            break
        yield queryctrl
        queryctrl = v4l2.v4l2_queryctrl(
            queryctrl.id | v4l2.V4L2_CTRL_FLAG_NEXT_CTRL)

def test_VIDIOC_QUERYCTRL(fd):
    cap = v4l2.v4l2_capability()
    fcntl.ioctl(fd, v4l2.VIDIOC_QUERYCAP, cap)
  
    def queryctrl_print(queryctrl):
        print 'Control: %s' % queryctrl.name
        print '  Range: %d - %d' % (queryctrl.minimum, queryctrl.maximum)
  
        control = v4l2.v4l2_control(queryctrl.id)
        fcntl.ioctl(fd, v4l2.VIDIOC_G_CTRL, control)    
        print '  Id: %d' % control.id
        print '  Value: %d' % control.value
  
    def test_controls(fd, input_or_output):
        '''
        Control: Red Balance
          Range: 0 - 1023
        Control: Blue Balance
          Range: 0 - 1023
        Control: Exposure
          Range: 0 - 800
        Control: Gain
          Range: 0 - 511
        '''
        print 'enum: original'
        # original enumeration method
        for queryctrl in get_device_controls(fd):
            queryctrl_print(queryctrl)
  
        if 0:
            '''
            Control: User Controls
              Range: 0 - 0
            Control: Red Balance
              Range: 0 - 1023
            Control: Blue Balance
              Range: 0 - 1023
            Control: Exposure
              Range: 0 - 800
            Control: Gain
              Range: 0 - 511
            '''
            print 'enum: class'
            # enumeration by control class
            for class_ in (
                v4l2.V4L2_CTRL_CLASS_USER,
                v4l2.V4L2_CTRL_CLASS_MPEG,
                v4l2.V4L2_CTRL_CLASS_CAMERA):
                for queryctrl in get_device_controls_by_class(fd, class_):
                    queryctrl_print(queryctrl)

    if not cap.capabilities & v4l2.V4L2_CAP_VIDEO_CAPTURE:
        raise Exception("Device doesn't support capture")
  
    print '*' * 80
    print 'Capture'
    foreach_device_input(fd, test_controls)
  
    print '*' * 80
    print 'Output'
    if cap.capabilities & v4l2.V4L2_CAP_VIDEO_OUTPUT:
        foreach_device_output(fd, test_controls)

    print '*' * 80

# test_VIDIOC_QUERYCTRL(vd)

def test_VIDIOC_QUERYCTRL_simp(fd):
    cap = v4l2.v4l2_capability()
    fcntl.ioctl(fd, v4l2.VIDIOC_QUERYCAP, cap)
  
    def test_controls(fd, input_or_output):
        '''
        Control: Red Balance
          Range: 0 - 1023
        Control: Blue Balance
          Range: 0 - 1023
        Control: Exposure
          Range: 0 - 800
        Control: Gain
          Range: 0 - 511
        '''
        print 'enum: original'
        # original enumeration method
        for queryctrl in get_device_controls(fd):
            print 'Control: %s' % queryctrl.name
            print '  Range: %d - %d' % (queryctrl.minimum, queryctrl.maximum)

    if not cap.capabilities & v4l2.V4L2_CAP_VIDEO_CAPTURE:
        raise Exception("Device doesn't support capture")
  
    print '*' * 80
    print 'Capture'
    foreach_device_input(fd, test_controls)
  
    print '*' * 80
#test_VIDIOC_QUERYCTRL_simp(vd)

def test_VIDIOC_S_CTRL(fd):
    cap = v4l2.v4l2_capability()
    fcntl.ioctl(fd, v4l2.VIDIOC_QUERYCAP, cap)
  
    def test_set_control(fd, input_or_output):
        for queryctrl in get_device_controls(fd):
            if queryctrl.flags & v4l2.V4L2_CTRL_FLAG_DISABLED:
                continue

            print 'Ctrl: %s' % queryctrl.name
            original_control = v4l2.v4l2_control(queryctrl.id)
            fcntl.ioctl(fd, v4l2.VIDIOC_G_CTRL, original_control)
  
            print '  Set: defalut'
            control = v4l2.v4l2_control(queryctrl.id, queryctrl.default)
            fcntl.ioctl(fd, v4l2.VIDIOC_S_CTRL, control)
            
            print '  Set: min'
            control.value = queryctrl.minimum + queryctrl.step
            fcntl.ioctl(fd, v4l2.VIDIOC_S_CTRL, control)
  
            control.value = queryctrl.minimum - queryctrl.step
            try:
                fcntl.ioctl(fd, v4l2.VIDIOC_S_CTRL, control)
            except IOError, e:
                assert e.errno in (
                    errno.ERANGE, errno.EINVAL, errno.EIO)
            control.value = queryctrl.maximum + queryctrl.step
            try:
                fcntl.ioctl(fd, v4l2.VIDIOC_S_CTRL, control)
            except IOError, e:
                assert e.errno in (
                    errno.ERANGE, errno.EINVAL, errno.EIO)
            if queryctrl.step > 1:
                control.value = queryctrl.default + queryctrl.step - 1
                try:
                    fcntl.ioctl(fd, v4l2.VIDIOC_S_CTRL, control)
                except IOError, e:
                    assert e.errno == errno.ERANGE
  
            fcntl.ioctl(fd, v4l2.VIDIOC_S_CTRL, original_control)
  
    # general test
    foreach_device_input(fd, test_set_control)
  
    # test for each input devices
    if cap.capabilities & v4l2.V4L2_CAP_VIDEO_CAPTURE:
        foreach_device_input(fd, test_set_control)
  
    # test for each output devices
    if cap.capabilities & v4l2.V4L2_CAP_VIDEO_OUTPUT:
        foreach_device_output(fd, test_set_control)
# test_VIDIOC_S_CTRL(vd)



# Return name of all controls
def ctrls(fd):
    cap = v4l2.v4l2_capability()
    fcntl.ioctl(fd, v4l2.VIDIOC_QUERYCAP, cap)
  
    ret = []
    def test_set_control(fd, input_or_output):
        for queryctrl in get_device_controls(fd):
            if queryctrl.flags & v4l2.V4L2_CTRL_FLAG_DISABLED:
                continue
            ret.append(queryctrl.name)
    foreach_device_input(fd, test_set_control)
    return ret

def ctrl_get(fd, name):
    cap = v4l2.v4l2_capability()
    fcntl.ioctl(fd, v4l2.VIDIOC_QUERYCAP, cap)
  
    ret = []
    def test_set_control(fd, input_or_output):
        for queryctrl in get_device_controls(fd):
            if queryctrl.flags & v4l2.V4L2_CTRL_FLAG_DISABLED:
                continue

            if queryctrl.name != name:
                continue
            
            control = v4l2.v4l2_control(queryctrl.id)
            fcntl.ioctl(fd, v4l2.VIDIOC_G_CTRL, control)
            ret.append(control.value)
  
    # general test
    foreach_device_input(fd, test_set_control)
    
    if len(ret) == 0:
        raise ValueError("Failed to find control")
    return ret[0]

def ctrl_set(fd, name, value):
    cap = v4l2.v4l2_capability()
    fcntl.ioctl(fd, v4l2.VIDIOC_QUERYCAP, cap)
  
    def test_set_control(fd, input_or_output):
        for queryctrl in get_device_controls(fd):
            if queryctrl.flags & v4l2.V4L2_CTRL_FLAG_DISABLED:
                continue

            #print 'Ctrl: %s' % queryctrl.name
            if queryctrl.name != name:
                continue
            
            if value < queryctrl.minimum or value > queryctrl.maximum:
                raise ValueError("Require %d <= %d <= %d" % (queryctrl.minimum, value, queryctrl.maximum))
  
            control = v4l2.v4l2_control(queryctrl.id, value)
            fcntl.ioctl(fd, v4l2.VIDIOC_S_CTRL, control)
  
    foreach_device_input(fd, test_set_control)
  
'''
    Control: Red Balance
      Range: 0 - 1023
    Control: Blue Balance
      Range: 0 - 1023
    Control: Gain
      Range: 0 - 511
    Control: Exposure
      Range: 0 - 800
'''
print 'Setting stuff'
ctrl_set(vd, 'Red Balance', 512)
ctrl_set(vd, 'Blue Balance', 512)
ctrl_set(vd, 'Gain', 256)

print 'Controls'
for ctrl in ctrls(vd):
    print '  %s: %d' % (ctrl, ctrl_get(vd, ctrl))

print 'Done'

