from hal import Hal, format_t

import time

# Camera always local
class LcncHal(Hal):
    def __init__(self, rsh, log=None, dry=False):
        Hal.__init__(self, log, dry)

    def sleep(self, sec, why):
        self.log('Sleep %s' % (format_t(sec), why), 3)
        self.rt_sleep += sec

    def cmd(self, cmd):
        if self.dry:
            self.log(cmd)
        else:
            self._cmd(cmd)
            
    def _cmd(self, cmd):
        raise Exception("Required")
   
    def mv_abs(self, pos):
        # Unlike DIY controllers, all axes can be moved concurrently
        # Don't waste time moving them individually
        self.cmd('G90 G0' + ' '.join(['%c%0.3f' % (k.upper(), v) for k, v in pos.iteritems()]))
        
    def mv_rel(self, delta):
        # Unlike DIY controllers, all axes can be moved concurrently
        # Don't waste time moving them individually
        self.cmd('G91 G0' + ' '.join(['%c%0.3f' % (k.upper(), v) for k, v in delta.iteritems()]))

# http://linuxcnc.org/docs/html/common/python-interface.html
# LinuxCNC python connection
# Currently the rpc version emulates stat and command channels
# making these identical for the time being
class LcncPyHal(LcncHal):
    def __init__(self, linuxcnc, log=None, dry=False):
        LcncHal.__init__(self, log, dry)
        
        self.ax_c2i = {'x': 0, 'y': 1}
        self.ax_i2c = {0: 'x', 1: 'y'}
        
        self.linuxcnc = linuxcnc
        self.stat = self.linuxcnc.stat()
        self.command = self.linuxcnc.command()

        self.command.state(self.linuxcnc.STATE_ON)
        self.stat.poll()
        print 'Enabled: %s' % self.stat.enabled
        
        # prevent "can't do that (EMC_AXIS_HOME:123) in MDI mode"
        # You must home all axes, not just those used
        for axisi in xrange(self.stat.axes):
            self._home(axisi=axisi)
        
        # Home puts into MODE_MANUAL
        self.command.mode(self.linuxcnc.MODE_MDI)
        self.stat.poll()
        print 'Enabled: %s' % self.stat.enabled
    
    def home(self, axes):
        for axis in axes:
            self._home(axis)
    
    def _home(self, axisc=None, axisi=None):
        if axisi is None:
            axisi = self.ax_c2i[axisc]
        
        self.command.mode(self.linuxcnc.MODE_MANUAL)
        print 'Home: check axis %d' % axisi
        self.stat.poll()
        print 'Enabled: %s' % self.stat.enabled
        axis = self.stat.axis[axisi]
        #print axis
        if axis['homed']:
            print '  Already homed'
            return
        # prevent "homing already in progress"
        if not axis['homing']:
            tstart = time.time()
            self.command.home(axisi)
        print '  Waiting for home...'
        while axis['homing']:
            self.stat.poll()
            time.sleep(0.1)
        print '  homed after %0.1f' % (time.time() - tstart,)
    
    def ok_for_mdi(self):
        self.stat.poll()
        return not self.stat.estop and self.stat.enabled and self.stat.homed and self.stat.interp_state == self.linuxcnc.INTERP_IDLE
        
    def wait_mdi_idle(self):
        while not self.ok_for_mdi():
            # TODO: notify self.progress
            #print self.stat.estop, self.stat.enabled, self.stat.homed, self.stat.interp_state, self.linuxcnc.INTERP_IDLE
            print 'Pos: commanded %d actual %s' % (self.stat.axis[0]['input'], self.stat.axis[0]['output'])
            time.sleep(0.1)
        
    def _cmd(self, cmd):
        print
        print
        print cmd
        print 'waiting mdi idle (entry)'
        self.wait_mdi_idle()
        print 'executing command'
        self.command.mdi(cmd)            
        print 'waiting mdi idle (exit)'
        self.wait_mdi_idle()
        print 'command done'

    def forever(self, axes, run, progress):
        while run.is_set():
            # Axes may be updated
            # Copy it so that don't crash if its updated during an iteration
            for axis, sign in dict(axes).iteritems():
                self.mv_rel({axis: sign * 1})
                progress(self.pos())
            time.sleep(0.1)

    # FIXME
    # Trim down HAL so that reported axes is correct
    def axes(self):
        return self.ax_c2i.keys()

    def pos(self):
        ret = {}
        for axis in self.axes():
            ret[axis] = self.stat.axis[ord(axis) - ord('x')]['output']
        return ret

# LinuxCNC remote connection
class LcncRshHal(LcncHal):
    def __init__(self, rsh, log=None, dry=False):
        LcncHal.__init__(self, log, dry)
        self.rsh = rsh
        
    def _cmd(self, cmd):
        # Waits for completion before returning
        self.rsh.mdi(cmd, timeout=0)            
