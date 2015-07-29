import time
from imager import Imager

def format_t(dt):
    s = dt % 60
    m = int(dt / 60 % 60)
    hr = int(dt / 60 / 60)
    return '%02d:%02d:%02d' % (hr, m, s)

'''
Planner hardware abstraction layer (HAL)
At this time there is no need for unit conversions
Operate in whatever the native system is

Hal is not thread safe with exception of the following:
-stop
-estop
(since it needs to be able to interrupt an active operation)
'''
class Hal(object):
    def __init__(self, log, dry):
        self.dry = dry
        if log is None:
            def log(msg=''):
                print msg
        self.log = log
        # seconds to wait before snapping picture
        self.t_settle = 4.0
        
        # Overwrite to get updates while moving
        # (if supported)
        self.progress = lambda pos: None

    def axes(self):
        '''Return supported axes'''
        raise Exception("Required")

    def home(self, axes):
        '''Set current position to 0.0'''
        raise Exception("Required")
        
    def ret0(self):
        '''Return to origin'''
        self.mv_abs(dict([(k, 0.0) for k in self.axes]))

    def mv_abs(self, pos):
        '''Absolute move to positions specified by pos dict'''
        raise Exception("Required")

    def mv_rel(self, delta):
        '''Relative move to positions specified by delta dict'''
        raise Exception("Required")
    
    '''
    In modern systems the first is almost always used
    The second is supported for now while porting legacy code
    '''
    def img_get(self):
        '''Take a picture and return a PIL image'''
        raise Exception("Required")
    def img_take(self):
        '''Take a picture and save it to internal.  File name is generated automatically'''
        raise Exception("Unsupported")

    def pos(self):
        '''Return current position for all axes'''
        raise Exception("Required")

    def on(self):
        '''Call at start of MDI phase, before planner starts'''
        pass

    def off(self):
        '''Call at program exit / user request to completely shut down machine.  Motors can lose position'''
        pass

    def begin(self):
        '''Call at start of active planer use'''
        raise Exception("Required")
    
    def end(self):
        '''Called after machine is no longer in planer use.  Motors must maintain position for MDI'''
        raise Exception("Required")

    def stop(self):
        '''Stop motion as soon as convenient.  Motors must maintain position'''
        pass

    def estop(self):
        '''Stop motion ASAP.  Motors are not required to maintain position'''
        pass

    def unestop(self):
        '''Allow system to move again after estop'''
        pass

    def meta(self):
        '''Supplementary info to add to run log'''
        return {}

    def forever_pos(self):
        raise Exception("Not supported")

    def forever_neg(self):
        raise Exception("Not supported")

    def settle(self):
        '''Check last move time and wait if its not safe to take picture'''
        if self.dry:
            self.sleep(self.t_settle, 'settle')
        else:
            sleept = self.t_settle + self.mv_lastt - time.time()
            if sleept > 0.0:
                self.sleep(sleept, 'settle')

'''
Has no actual hardware associated with it
'''
class MockHal(Hal):
    def __init__(self, axes='xy', log=None, dry=False):
        Hal.__init__(self, log, dry)

        self._axes = list(axes)
        self._pos = {}
        # Assume starting at 0.0 until causes problems
        for axis in self._axes:
            self._pos[axis] = 0.0

    def _log(self, msg):
        if self.dry:
            self.log('Mock-dry: ' + msg)
        else:
            self.log('Mock: ' + msg)

    def axes(self):
        return self._axes
        
    def take_picture(self, file_name):
        self._log('taking picture to %s' % file_name)

    def mv_abs(self, pos):
        for axis, apos in pos.iteritems():
            self._pos[axis] = apos
        self._log('absolute move to ' + ' '.join(['%c%0.3f' % (k.upper(), v) for k, v in pos.iteritems()]))

    def mv_rel(self, delta):
        for axis, adelta in delta.iteritems():
            self._pos[axis] += adelta
        self._log('relative move to ' + ' '.join(['%c%0.3f' % (k.upper(), v) for k, v in delta.iteritems()]))

    def pos(self):
        return self._pos
    
    def settle(self):
        # No hardware to let settle
        pass

'''
Legacy uvscada.mc adapter
'''
class MCHal(Hal):
    def __init__(self, mc, log=None, dry=False):
        Hal.__init__(self, log, dry)
        self.mc = mc

    def sleep(self, sec, why):
        self.log('Sleep %s' % (format_t(sec), why), 3)
        self.rt_sleep += sec

    def reset_camera(self):
        # original needed focus button released
        #self.line('M9')
        # suspect I don't need anything here
        pass

    def mv_abs(self, pos):
        # Only one axis can be moved at a time
        for axis, apos in pos.iteritems():
            if self.dry:
                self._pos[axis] = apos
            else:
                self.mc.axes[axis].mv_abs(apos)
                self.mv_lastt = time.time()
        
    def mv_rel(self, delta):
        # Only one axis can be moved at a time
        for axis, adelta in delta.iteritems():
            if self.dry:
                self._pos[axis] += adelta
            else:
                self.mc.axes[axis].mv_rel(adelta)
                self.mv_lastt = time.time()

    '''
    def meta(self):
        ret = {}
        
        # FIXME: time estimator
        # It didn't really work so I didn't bother porting it over during cleanup
        self.rt_move = 0.0
        self.rt_settle = 0.0
        self.rt_sleep = 0.0

        rt_tot = self.rt_move + self.rt_settle + self.rt_sleep
        if self.rconfig.dry:
            rt_k = 'rt_est'
        else:
            rt_k = 'rt'
        ret[rt_k] = {
                    'total':    rt_tot,
                    'move':     self.rt_move,
                    'settle':   self.rt_settle,
                    'sleep':    self.rt_sleep,
                    }
        
        return ret
        '''

class GCodeHalImager(Imager):
    def __init__(self, hal):
        self.hal = hal
        
    def take(self):
        # Focus (coolant mist)
        self.hal._line('M7')
        self.hal._dwell(2)
        
        # Snap picture (coolant flood)
        self.hal._line('M8')
        self.hal._dwell(3)
        
        # Release shutter (coolant off)
        self.hal._line('M9')

'''
http://linuxcnc.org/docs/html/gcode/gcode.html

Static gcode generator using coolant hack
Not to be confused LCncHal which uses MDI g-code in real time

M7 (coolant on): tied to focus / half press pin
M8 (coolant flood): tied to snap picture
    M7 must be depressed first
M9 (coolant off): release focus / picture
'''
class GCodeHal(Hal):
    def __init__(self, axes='xy', log=None, dry=False):
        Hal.__init__(self, log, dry)
        self._axes = list(axes)
        
        self._pos = {}
        # Assume starting at 0.0 until causes problems
        for axis in self._axes:
            self._pos[axis] = 0.0
        self._buff = bytearray()

    def imager(self):
        return GCodeHalImager(self)
    
    def mv_abs(self, pos):
        for axis, apos in pos.iteritems():
            self._pos[axis] = apos
        self._line('G90 G0' + ' '.join(['%c%0.3f' % (k.upper(), v) for k, v in pos.iteritems()]))

    def mv_rel(self, pos):
        for axis, delta in pos.iteritems():
            self._pos[axis] += delta
        self._line('G91 G0' + ' '.join(['%c%0.3f' % (k.upper(), v) for k, v in pos.iteritems()]))

    def comment(self, s=''):
        if len(s) == 0:
            self._line()
        else:
            self._line('(%s)' % s)

    def _line(self, s=''):
        #self.log(s)
        self._buff += s + '\n'

    def begin(self):
        pass
    
    def end(self):
        self._line()
        self._line('(Done!)')
        self._line('M2')

    def _dwell(self, seconds):
        self._line('G4 P%0.3f' % (seconds,))

    def get(self):
        return str(self._buff)

# Camera always local
class LcncHal(Hal):
    def __init__(self, rsh, log=None, dry=False):
        Hal.__init__(self, log, dry)

    def sleep(self, sec, why):
        self.log('Sleep %s' % (format_t(sec), why), 3)
        self.rt_sleep += sec

    def cmd(self, cmd):
        raise Exception("Required")
   
    def do_cmd(self, cmd):
        if self.dry:
            self.log(cmd)
        else:
            self.cmd(cmd)
            
    def mv_abs(self, pos):
        # Unlike DIY controllers, all axes can be moved concurrently
        # Don't waste time moving them individually
        self.cmd_('G90 G0' + ' '.join(['%c%0.3f' % (k.upper(), v) for k, v in pos.iteritems()]))
        
    def mv_rel(self, delta):
        # Unlike DIY controllers, all axes can be moved concurrently
        # Don't waste time moving them individually
        self.cmd('G91 G0' + ' '.join(['%c%0.3f' % (k.upper(), v) for k, v in delta.iteritems()]))

# LinuxCNC python connection
# Currently the rpc version emulates stat and command channels
# making these identical for the time being
class LcncPyHal(LcncHal):
    def __init__(self, linuxcnc, log=None, dry=False):
        LcncHal.__init__(self, log, dry)
        self.linuxcnc = linuxcnc
        self.stat = self.linuxcnc.stat()
        self.command = self.linuxcnc.command()
    
    def ok_for_mdi(self):
        self.stat.poll()
        return not self.stat.estop and self.stat.enabled and self.stat.homed and self.stat.interp_state == self.linuxcnc.INTERP_IDLE
        
    def wait_mdi_idle(self):
        while not self.ok_for_mdi():
            # TODO: notify self.progress
            time.sleep(0.1)
        
    def do_cmd(self, cmd):
        self.wait_mdi_idle()
        self.command.mdi(cmd)            
        self.wait_mdi_idle()
    
# LinuxCNC remote connection
class LcncRshHal(LcncHal):
    def __init__(self, rsh, log=None, dry=False):
        LcncHal.__init__(self, log, dry)
        self.rsh = rsh
        
    def do_cmd(self, cmd):
        # Waits for completion before returning
        self.rsh.mdi(cmd, timeout=0)            
