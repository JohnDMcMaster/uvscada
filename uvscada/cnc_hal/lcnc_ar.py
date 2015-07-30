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
import time
import subprocess

DEVNULL = open(os.devnull, 'wb')

class LcncPyHalAr(LcncPyHal):
    def __init__(self, *args, **kwargs):
        try:
            self._init(*args, **kwargs)
        except:
            print 'Shutting down on init failure'
            self.ar_stop()
            raise
    
    def _init(self, host, log=None, dry=False):
        print 'Creating SSH connection'
        self.ssh = paramiko.SSHClient()
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
        self.ssh.connect(hostname=host, port=22, username='machinekit', key_filename=None,
                       look_for_keys=True, password=None)
        
        self.running = True
        self.tunnel = None
        
        remote_tmp = '/tmp/lcnc_ar'
        dst = os.path.join(remote_tmp, 'server.py')
        
        if 0:
            print 'Copying remote agent'
            sftp = self.ssh.open_sftp()
            #sftp.rmdir(remote_tmp)
            # TODO: will probably throw exception if it exists
            try:
                sftp.mkdir(remote_tmp)
            except IOError:
                print "Temp directory already exists"
            # Copy over remote agent
            src = os.path.join(os.path.dirname(__file__), '..', 'lcnc', 'server.py')
            sftp.put(src, dst)
        
        if 0:
            print 'Launching linuxcnc'
            ini = '/home/machinekit/machinekit/configs/ARM.BeagleBone.CRAMPS/CRAMPS-linuxcncrsh.ini'
            transport = self.ssh.get_transport()
            channel = transport.open_session()
            # http://stackoverflow.com/questions/7734679/paramiko-and-exec-command-killing-remote-process
            # Makes sure process dies when we close connection
            channel.get_pty()
            self.stdin, self.stdout, self.stderr = channel.exec_command('linuxcnc %s' % ini) 
            self.thread_linuxcnc = threading.Thread(target=self.run_linuxcnc)
            self.thread_linuxcnc.start()
            time.sleep(5)
            # Although unused is a good indicator
            # note: if you are using axis gui this will freeze
            # need to poke around and see how we can do better
            self.wait_remote_port(5007)
        
        if 0:
            print 'Launching remote agent'
            transport = self.ssh.get_transport()
            channel = transport.open_session()
            # http://stackoverflow.com/questions/7734679/paramiko-and-exec-command-killing-remote-process
            # Makes sure process dies when we close connection
            channel.get_pty()
            self.stdin, self.stdout, self.stderr = channel.exec_command('python %s' % dst) 
            self.thread_server = threading.Thread(target=self.run_server)
            self.thread_server.start()
            self.wait_remote_port(PORT)
        
        if 1:
            print 'Creating SSH tunnel'
            self.thread_tunnel = threading.Thread(target=self.run_tunnel)
            self.thread_tunnel.start()
            time.sleep(1)
        self.wait_local_port(PORT)
        
        linuxcnc = LCNCRPC('localhost')
        LcncPyHal.__init__(self, linuxcnc=linuxcnc, log=log, dry=dry)
    
    def wait_local_port(self, port):
        print 'Checking local port %d' % port
        while True:
            rc = subprocess.call('exec 6<>/dev/tcp/127.0.0.1/%s' % port, shell=True, stdout=DEVNULL, stderr=DEVNULL, executable='/bin/bash')
            if rc == 0:
                print 'port is open'
                break
    
    def wait_remote_port(self, port):
        print 'Checking remote port %d' % port
        while True:
            channel = self.ssh.transport().open_session()
            # exec 6<>/dev/tcp/127.0.0.1/22617
            channel.exec_command('exec 6<>/dev/tcp/127.0.0.1/%s' % port)
            rc = channel.recv_exit_status()
            print rc
            if rc == 0:
                print 'port is open'
                break
    
    def __del__(self):
        self.ar_stop()
    
    def ar_stop(self):
        print 'shutting down'
        self.running = False
        if self.tunnel:
            # ForwardServer
            self.tunnel.shutdown()
        self.ssh.close()
    
    def run_server(self):
        '''
        # AttributeError: 'ChannelFile' object has no attribute 'fileno'
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
        '''

        import time
        # http://sebastiandahlgren.se/2012/10/11/using-paramiko-to-send-ssh-commands/
        # weird they didn't conform to the file api at all with fds
        while self.running:
            for f in [self.stdout, self.stderr]:
                sys.stdout.write(f.read())
                sys.stdout.flush()
                time.sleep(0.1)
        print 'Server thread exiting'

    def run_tunnel(self):
        '''
        Because we're using xmlrpc it generates a lot of socket connections
        if you leave verbose on you'll get spammed with messages like this
        
        Connected!  Tunnel open ('127.0.0.1', 55469) -> ('192.168.2.55', 22) -> ('127.0.0.1', 22617)
        Tunnel closed from ('127.0.0.1', 55469)
        
        Is this socket deluge okay or should I look into something more connection oriented?
        '''
        
        print 'Preparing tunnel'
        self.tunnel = paramiko_util.forward_tunnel(local_port=PORT, remote_host='127.0.0.1', remote_port=PORT, transport=self.ssh.get_transport())
        print 'Serving tunnel'
        self.tunnel.serve_forever()
        print 'Tunnel thread exiting'
