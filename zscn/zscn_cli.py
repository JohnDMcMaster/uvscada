from uvscada import zscnc
import cmd

'''
# http://stackoverflow.com/questions/510357/python-read-a-single-character-from-the-user
import sys, tty, termios
def getcnow():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch
'''

class CLI(cmd.Cmd):
    """Simple command processor example."""
    
    def do_rst(self, l):
        z.rst()

    def do_nop(self, l):
        z.nop()

    def do_0(self, chan):
        chani = int(chan)
        print 'Chan %d off' % chani
        z.ch_off(chani)

    def do_1(self, chan):
        chani = int(chan)
        print 'Chan %d on' % chani
        z.ch_on(chani)

    def do_ledoff(self, which):
        print 'LED %s off' % which
        z.led_off(which)

    def do_ledon(self, which):
        print 'LED %s on' % which
        z.led_on(which)

    def do_EOF(self, line):
        return True

if __name__ == '__main__':
    z = zscnc.ZscnSer(device='/dev/ttyACM1')
    print 'Ready'
    cli = CLI()
    cli.z = z
    cli.cmdloop()
