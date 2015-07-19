from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpclib import Binary
import linuxcnc

class Server(object):
    def __init__(self, bind='localhost', port=22617, verbose=False):
        self.server = None
        self.bind = bind
        self.port = port
        self.verbose = verbose
        
        self.s = linuxcnc.stat()
        self.c = linuxcnc.command()

    def poll(self):
        self.s.poll()
        ret = {}
        for attr in ['estop', 'enabled', 'homed', 'interp_state']:
            ret[attr] = getattr(self.s, attr)
        return ret

    def constants(self):
        return {
            'MODE_MDI': linuxcnc.MODE_MDI,
            'INTERP_IDLE': linuxcnc.INTERP_IDLE,
            }

    def run(self):
        print 'Starting server'
        self.server = SimpleXMLRPCServer((self.bind, self.port), logRequests=self.verbose, allow_none=True)
        self.server.register_introspection_functions()
        self.server.register_multicall_functions()
        self.server.register_instance(self)
        self.server.register_function(self.c.mode,          "mode")
        self.server.register_function(self.c.wait_complete, "wait_complete")
        self.server.register_function(self.c.mdi,           "mdi")
        print 'Running'
        self.server.serve_forever()

s = Server()
s.run()
