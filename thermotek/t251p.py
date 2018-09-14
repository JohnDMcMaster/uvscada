'''
WARNING: this code doesn't seem to work
For some reason I never get a WD response

Thermotek T251P can also be branded as a Silicon Thermal CH250
'''

import serial
import binascii
import datetime
import time

'''
comm error status - Single ASCII byte that indicates any error in the last command received.
The errors are as follows:
No Error
-
30h (0)
Checksum Error
-
31h
(1)
Bad Command
-
32h (2)
Out of Bound Qualifier
33h (3)
'''
err_i2s = {
    '0': 'NONE',        # No Error
    '1': 'CHECKSUM',    # Checksum Error
    '2': 'BAD_CMD',     # Bad Command
    '3': 'OOB',         # Out of Bound Qualifier
    }

XON = '\x11'
XOFF = '\x13'
SOC = '.'
CR = '\x0D'

class BadPacket(Exception):
    pass

def calc_checksum(buff):
    '''Calculate checksum, returned in expected ASCII format'''
    return '%02X' % (sum(bytearray(buff)) & 0xFF)

def cmd_encode(cmd_code, opts='', soc='\x2E', checksum=None, cr='\x0D'):
    '''
    2.1 Command Format
    The command issued by the PC will be in the following format:
    soc
    command code
    n optional qualifiers checksum
    Where
    soc -
    cr
    '''
    cmd_code = str(cmd_code)
    assert len(cmd_code) == 1
    tocheck = soc + cmd_code + opts
    if checksum is None:
        # ASCI protcool, so checksum is sent as ASCII
        checksum = calc_checksum(tocheck)
    return tocheck + checksum + cr

def response_decode(buff):
    '''
    2.2
    Response Format
    Every command requires a response of some sort. The general form of the response is:
    sor
    command
    echo
    Where
    sor -
    command echo -
    comm error
    status
    n response
    checksum
    cr
    Start of Response. The command starts with a 23h representing an ASCII
    #. It is one byte in length.
    Echo the last received valid command.
    comm error status - Single ASCII byte that indicates any error in the last command received.
    The errors are as follows:
    No Error
    -
    30h (0)
    Checksum Error
    -
    31h
    (1)
    Bad Command
    -
    32h (2)
    Out of Bound Qualifier
    33h (3)
    n response -
    checksum -
    cr -
    2.3
    data, alarms messages, status conditions as requested by the command
    two ASCII hexadecimal bytes representing the least significant 8 bits of the
    sum of all preceding bytes of the command starting with the sor.
    ASCII carriage return 0Dh
    '''
    if buff is None:
        raise ValueError("packet buff is None")
    sor = buff[0]
    if sor != '\x23':
        raise BadPacket("Bad sor")
    cr = buff[-1]
    if cr != '\x0D':
        raise BadPacket("Bad cr")
    checksum_got = buff[-2]
    checksum_calc = calc_checksum(buff[0:-2])
    if checksum_got != checksum_calc:
        raise BadPacket("Bad checksum")

    last_cmd = buff[1]
    err = err_i2s[int(buff[2])]
    response = buff[3:len(buff) - 2]
    return last_cmd, err, response

class T251P(object):
    def __init__(self, port="/dev/ttyUSB0", ser_timeout=0.10, ser=None):
        self.verbose = True
        if not ser:
            ser = serial.Serial(port,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                rtscts=False,
                dsrdtr=False,
                # sucks..doesn't packetize reads
                #xonxoff=True,
                xonxoff=False,
                timeout=ser_timeout,
                # Blocking writes
                writeTimeout=None)
        self.ser = ser
        #self.ser.flushInput()
        #self.ser.flushOutput()
        #self.flush()
        self.rxbuff = ''
        self.xon = False

    def flush(self):
        timeout = self.ser.timeout
        try:
            self.ser.timeout = 0.1
            while True:
                l = self.ser.readline()
                # finished command in progress => flushed
                if not l:
                    return
                # a finished command => done
                if l[-1] == '\n':
                    return
        finally:
            self.ser.timeout = timeout

    def snd(self, cmd_code, opts):
        encoded = cmd_encode(cmd_code, opts)
        out = XON + encoded + XOFF
        if self.verbose:
            print('TX: %s' % binascii.hexlify(out))
            print("TX ASCII: %s" % encoded[0:-1])
        self.ser.write(out)
        self.ser.flush()

    def recv(self):
        '''
        WD packets are XON without XOFF
        Normal packets are XON + data + XOFF
        '''
        self.rxbuff += self.ser.read(16)
        print('Got %u: %s' % (len(self.rxbuff), binascii.hexlify(self.rxbuff)))
        while True:
            xon_pos = self.rxbuff.find(XON)
            xoff_pos = self.rxbuff.find(XOFF)
            #print(xon_pos, xoff_pos, len(self.rxbuff))
            if xon_pos < 0 and xoff_pos < 0:
                return None
            # Process new xon if its not going to interrupt a valid packet
            if xon_pos >= 0 and (xoff_pos < 0 or xon_pos < xoff_pos):
                self.rxbuff = self.rxbuff[xon_pos + 1:]
                self.xon = True
                if self.verbose:
                    print('rx XON')
                continue
            if xoff_pos >= 0:
                packet = self.rxbuff[0:xoff_pos + 1]
                self.rxbuff = self.rxbuff[xoff_pos + 1:]
                if not self.xon:
                    if self.verbose:
                        print('WARNING: packet missing XON')
                    continue
                else:
                    assert packet[-1] == XOFF
                    return response_decode(packet)

    def cmd(self, cmd_code, opts='', timeout=1.5):
        # watchdog requests may have stacked up
        #self.ser.flushInput()
        self.snd(cmd_code, opts)

        tstart = time.time()
        while True:
            if time.time() - tstart > timeout:
                raise Exception("Timed out waiting for valid reply")

            try:
                recv = self.recv()
            except BadPacket as e:
                if self.verbose:
                    print('WARNING: bad packet %s' % e)
                continue

            # watchdog
            if not recv:
                continue
            last_cmd, err, response = recv
            # ??? shouldn't get this due to flush and such, but just in case
            if last_cmd != cmd_code:
                if self.verbose:
                    print('WARNING: unexpected command result %s' % last_cmd)
                continue
            if err != 'NONE':
                raise Exception("Got error: %s" % err)
            return response

    def mode_select(self, mode):
        modei = {
            'STAND_BY': 0,
            'RUN': 1,
            }[mode]
        self.cmd('G', str(modei))

    def read_memory(self, opt=0):
        # 0. Temp & Max Power Setpoint
        # TODO: decode
        return self.cmd('H', str(opt))

    def read_alarm_state(self):
        '''
        fs : Float Switch
        ha : Hi Alarm
        la : Low Alarm
        sa : Sensor Alarm
        pa : EEPROM Fail
        wa : Watch dog
        '''
        fs, ha, la, sa, pa, wa = self.cmd('H')
        return fs, ha, la, sa, pa, wa

    def serial_watchdog(self):
        ''''
        NOTE: this command is special, used to init comms

        md: mode status
        as: alarm status
        cs: chiller status
        ds: dryer status
        '''
        md, as_, cs, ds = self.cmd('U')
        return md, as_, cs, ds

def monitor_wd(t):
    while True:
        try:
            recv = t.recv()
        except BadPacket as e:
            print('WARNING: bad packet %s' % e)
            continue
        print('%s: recv packet: %s' % (datetime.datetime.utcnow().isoformat(), recv))

def run():
    t = T251P()
    if 0:
        while True:
            d = t.ser.read()
            print(len(d), binascii.hexlify(d))
    
    # verify XON pulse
    if 0:
        d = t.ser.read()
        assert len(d) == 0
    t.serial_watchdog()
    #t.ser.write('\x2e\x47\x30\x41\x35\x0D')
    #monitor_wd(t)
    #t.mode_select('RUN')
    t.mode_select('STAND_BY')
    #print('read_alarm_state', t.read_alarm_state())

def test():
    assert cmd_encode('\x47', '\x30') == '\x2e\x47\x30\x41\x35\x0D'
    print('Test ok')

run()
#test()


