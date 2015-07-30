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
