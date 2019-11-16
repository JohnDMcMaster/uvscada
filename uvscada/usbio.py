'''
This file is part of uvscada
Licensed under 2 clause BSD license, see COPYING for details
'''

'''
IO Pin           Function
IO_08           IO8/Relay2  
IO7                IO_07
IO_09              IO9/Relay1    
IO6/Counter0    IO_06               
IO_0A           IOA/ADC4          
IO_05              IO5/ADC3                
IO_0B           IOB/ADC5          
IO_04              IO4/ADC2
IO_0C           IOC/ADC6
IO_03             IO3/ADC1
IO_0D           IO_02
IOD/ADC7        IO2/ADC0
IO_0E           IO_01
IOE/PWM0        IO1/RX0
IO_0F           IO_00
IOF/PWM1        IO0/TX0
'''

import serial
import sys
import time

VERSION = 0.0

class Timeout(Exception):
    pass

def dbg(s):
    pass

class USBIO:
    # wtf is acm
    def __init__(self, device=None, debug=False):
        self.serial = None
        self.debug = debug
        if device is None:
            # Only one board left and I only use it under Linux
            # just hard code the ID to avoid confusing with other devices
            # for s in ("/dev/ttyUSB0", "/dev/ttyACM0", "/dev/ttyS5", "COM12"):
            for s in ("/dev/serial/by-id/usb-Microchip_Technology_Inc._CDC_RS-232_Emulation_Demo-if00",):
                try:
                    self.try_open(s)
                    dbg('Opened %s okay' % s)
                    break
                except IOError:
                    dbg('Failed to open %s' % s)
                    continue
            if self.serial is None:
                raise IOError("Failed to find a suitable device")
        else:
            self.try_open(device)
        
        # Clear old data
        if self.debug:
            dbg('Flushing %d chars' % self.serial.inWaiting())
        self.serial.flushInput()

    def try_open(self, device):
        self.device = device
        self.serial = serial.Serial(port=self.device, baudrate=9600, timeout=1, writeTimeout=1)    
        if self.serial is None:
            raise IOError('Can not connect to serial')
        
    '''
    Read the version of the USB_IO device firmware.
    ~ver~            ...............send to USB_IO
    ~VER:3.8~       ...............Receive from USB_IO
    16 Digital Input/Output Ports: IO0~IOF
    ~out0=1~ ..................send to USB_IO (IO0=`1`)
    ~OK~           ..................Receive from USB_IO
    ~outA=0~ ..................Send to USB_IO (IOA=`0`)
    ~OK~           ..................Receive from USB_IO
    ~osta9~ .......................Read the state of OUT_09
    ~OUTES9=1~        ............Receive from USB_IO (OUT_09 state)
    ~osta2~ .......................Read the state of OUT_02
    ~OUTES2=0~        ............Receive from USB_IO (OUT_02 state)
    ~in6~         ..................Send to USB_IO
    ~in6=0~       ..................Receive from USB_IO (IO6=`0`)
    ~inA~         ..................Send to USB_IO
    ~inA=1~       ..................Receive from USB_IO (IOA=`1`)
    '''
    
    
    
    def recv(self):
        # Sync until first ~
        if self.debug:
            print('USBIO DEBUG: recv: waiting for opening ~')
        for _i in range(3):
            c = self.serial.read(1)
            if self.debug:
                print('USBIO DEBUG: recv open wait: got "%s", wait: %d' % (c, self.serial.inWaiting()))
            if c == b'~':
                break
        else:
            raise Timeout('Timed out waiting for opening ~')
        
        if self.debug:
            print('USBIO DEBUG: recv: waiting for closing ~')
        # Read until ~
        ret = b''
        for _i in range(60):
            c = self.serial.read(1)
            if c == b'~':
                break
            ret += c
        else:
            raise Timeout('Timed out waiting for closing ~')
        
        if self.debug:
            print('USBIO DEBUG: recv: returning: "%s"' % (ret,))
        return ret
        
    def send(self, bytes_out):
        out = '~' + bytes_out + '~'
        if self.debug:
            print('USBIO DEBUG: sending: %s' % (out,))
            if self.serial.inWaiting():
                raise Exception('At send %d chars waiting' % self.serial.inWaiting())
        self.serial.write(out.encode('ascii'))
        # if it doesn't get written we will not get a reply
        self.serial.flush()
        # Always expect a reply
        ret = self.recv()
        
        if self.debug:
            res = self.serial.read()
            if len(res):
                raise Exception('Orphaned: %s' % res)
        return ret
        
    def version(self):
        return self.send("ver")

    def set_gpio(self, index, is_on):
        '''index valid 0-15'''
        is_on = 1 if is_on else 0
        #self.serial.flush()
        reply = self.send("out%X=%d" % (index, is_on))
        if reply != b"OK":
            raise Exception("Expected OK but got %s" % (reply,)) 

    def get_gpio(self, index):
        reply = self.send("in%X" % (index,))
        # ~OUTES9=1~
        #print(reply)
        reply_pin, val = reply.split('=')
        if val not in b"01":
            raise Exception("Expected 01 but got %s" % (val,)) 
        return bool(int(val))

    def set_relay(self, relay_id, is_on):
        if relay_id == 1:
            self.set_gpio(9, is_on)
        elif relay_id == 2:
            self.set_gpio(8, is_on)
        else:
            raise Exception("bad relay id")

    def get_16(self):
        """Return all 16 GPIO states as 16 bit integer"""
        ret = 0
        for i in range(16):
            if self.get_gpio(i):
                ret |= 1 << i
        return ret

def str2bool(arg_value):
    arg_value = arg_value.lower()
    if arg_value == "false" or arg_value == "0" or arg_value == "no" or arg_value == "off":
        return False
    else:
        return True

def help():
    print('usbio version %s' % VERSION)
    print('Copyright 2011 John McMaster <JohnDMcMaster@gmail.com>')
    print('Usage:')
    print('usbio [options] [<port> <state>]')
    print('Options:')
    print('--help: this message')

if __name__ == "__main__":
    port = None
    state = True
    raw_index = 0
    
    for arg_index in range (1, len(sys.argv)):
        arg = sys.argv[arg_index]
        arg_key = None
        arg_value = None
        if arg.find("--") == 0:
            arg_value_bool = True
            if arg.find("=") > 0:
                arg_key = arg.split("=")[0][2:]
                arg_value = arg.split("=")[1]
                arg_value_bool = str2bool(arg_value)
            else:
                arg_key = arg[2:]
                
            if arg_key == "help":
                help()
                sys.exit(0)
            elif arg_key == "port":
                port = arg_value
            elif arg_key == "state":
                state = arg_value_bool
            else:
                log('Unrecognized argument: %s' % arg)
                help()
                sys.exit(1)
        else:
            arg_bool = str2bool(arg)

            if arg == "false" or arg == "0" or arg == "no":
                arg_bool = False

            raw_index += 1
            if raw_index == 1:
                port = arg
            elif raw_index == 2:
                state = arg_bool
    
    usbio = USBIO()
    
    i = 0
    import time
    
    for i in range(20):
        usbio.set_gpio(0, True)
        usbio.set_gpio(0, False)    
        
    sys.exit(1)
    
    while True:
        i += 1
        print(i)
        usbio.set_gpio(0, True)
        usbio.set_gpio(0, False)
        #time.sleep(0.05)
    
    if port is None:
        print('port must be specified')
        help()
        sys.exit(1)
    
    port = port.upper()
    if port == "RELAY1":
        usbio.set_relay(1, state)
    elif port == "RELAY2":
        usbio.set_relay(2, state)
    else:
        print('bad port: %s' % port)
        help()
        sys.exit(1)

