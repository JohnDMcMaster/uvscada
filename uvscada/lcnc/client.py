import xmlrpclib
from xmlrpclib import Binary
import time

class LCNCRPCStat:
    def __init__(self, server):
        self.server = server

    def poll(self):
        for k, v in self.server.poll().iteritems():
            setattr(self, k, v)

class LCNCRPCCommand:
    def __init__(self, server):
        self.server = server
    
    def mdi(self, *args, **kwargs):
        return self.server.mdi(*args, **kwargs)

    def mode(self, *args, **kwargs):
        return self.server.mode(*args, **kwargs)

    def wait_complete(self, *args, **kwargs):
        return self.server.wait_complete(*args, **kwargs)

class LCNCRPC:
    # X-58 Y-59 => 22617
    def __init__(self, host='localhost', port=22617):
        self.server = xmlrpclib.ServerProxy('http://%s:%d' % (host, port), allow_none=True)
        for k, v in self.server.constants().iteritems():
            setattr(self, k, v)

    def stat(self):
        return LCNCRPCStat(self.server)
    
    def command(self):
        return LCNCRPCCommand(self.server)

'''
Remotely spawns the server and creates ssh tunnels
'''
class SshLCNCRPC(LCNCRPC):
    def __init__(self, host):
        raise Exception("FIXME")

if __name__ == '__main__':
    lcncrpc = LCNCRPC()
    
    s = lcncrpc.stat()
    c = lcncrpc.command()
    
    def ok_for_mdi():
        s.poll()
        return not s.estop and s.enabled and s.homed and (s.interp_state == lcncrpc.INTERP_IDLE)
    
    if ok_for_mdi():
        c.mode(lcncrpc.MODE_MDI)
        c.wait_complete() # wait until mode switch executed
        c.mdi("G0 X5")
        time.sleep(1)
        c.mdi("G0 X0")

    