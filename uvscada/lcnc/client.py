import xmlrpclib
import time

# X-58 Y-59 => 22617
PORT=22617

class LCNCRPCStat:
    def __init__(self, server):
        self.server = server
        self.poll()

    def poll(self):
        for k, v in self.server.s_poll().iteritems():
            setattr(self, k, v)

class LCNCRPCCommand:
    def __init__(self, server):
        self.server = server
        def func(server, f):
            def wrap(*args, **kwargs):
                return getattr(server, 'c_' + f)(*args, **kwargs)
            return wrap
        for f in ['mdi', 'mode', 'wait_complete', 'state', 'home']:
            setattr(self, f, func(self.server, f))

class LCNCRPC:
    def __init__(self, host='localhost', port=PORT):
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

    