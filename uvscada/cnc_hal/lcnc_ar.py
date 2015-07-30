'''
Linux CNC auto RPC
'''

from lcnc import LcncPyHal
from uvscada.lcnc.client import LCNCRPC, PORT
from uvscada import paramiko_util

import os
import paramiko
import select
import sys
import threading

class LcncPyHalAr(LcncPyHal):
    def __init__(self, host, log=None, dry=False):
        print 'Creating SSH connection'
        self.ssh = paramiko.SSHClient()
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
        self.ssh.connect(hostname=host, port=22, username='machinekit', key_filename=None,
                       look_for_keys=True, password=None)
        
        self.running = True
        
        print 'Copying remote agent'
        remote_tmp = '/tmp/lcnc_ar'
        sftp = self.ssh.open_sftp()
        #sftp.rmdir(remote_tmp)
        # TODO: will probably throw exception if it exists
        try:
            sftp.mkdir(remote_tmp)
        except IOError:
            print "Temp directory already exists"
        # Copy over remote agent
        src = os.path.join(os.path.dirname(__file__), '..', 'lcnc', 'server.py')
        dst = os.path.join(remote_tmp, 'server.py')
        sftp.put(src, dst)
        
        print 'Launching remote agent'
        self.stdin, self.stdout, self.stderr = self.ssh.exec_command('python %s' % dst) 
        self.thread_server = threading.Thread(target=self.run_server)
        
        print 'Creating SSH tunnel'
        self.thread_tunnel = threading.Thread(target=self.run_tunnel)
        
        import time
        time.sleep(100000)
        
        print 'Creating CNC client'
        linuxcnc = LCNCRPC('localhost')
        LcncPyHal.__init__(self, linuxcnc=linuxcnc, log=log, dry=dry)
    
    def __del__(self):
        self.running = False
    
    def run_server(self):
        fds = {
            self.stdout.fileno(): self.stdout,
            self.stderr.fileno(): self.stderr,
        }
        
        while self.running:
            [rdy_r, _rdy_w, _rdy_x] = select.select([fds.keys(), [], []])
            for fd in rdy_r:
                # TODO: consider log file instead
                sys.stdout.write(fds[fd].read())
                sys.stdout.flush()

    def run_tunnel(self):
        paramiko_util.forward_tunnel(local_port=PORT, remote_host='localhost', remote_port=PORT, transport=self.ssh.get_transport())
