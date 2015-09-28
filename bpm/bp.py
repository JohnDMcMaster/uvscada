# https://github.com/vpelletier/python-libusb1
# Python-ish (classes, exceptions, ...) wrapper around libusb1.py . See docstrings (pydoc recommended) for usage.
import usb1
# Bare ctype wrapper, inspired from library C header file.
import libusb1
import struct
import binascii
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class BP:
    def __init__(self, usbcontext, dev, verbose=False, init=True):
        self.verbose = verbose
        self.usbcontext = usbcontext
        self.dev = dev
        self.timeout = 0

    def _controlRead_mem(self, req, max_read, addr, dump_len):
        ret = ''
        i = 0
        while i < dump_len:
            l_this = min(dump_len - i, max_read)
            
            res = self.dev.controlRead(0xC0, 0xB0, req, addr + i, l_this, timeout=self.timeout)
            ret += res
            if len(res) != l_this:
                raise Exception("wanted 0x%04X bytes but got 0x%04X" % (l_this, len(res),))
            i += max_read
        return ret

    def _controlWrite_mem(self, req, max_write, addr, buff):
        i = 0
        while i < len(buff):
            this = buff[i:i+max_write]
            res = self.dev.controlWrite(0x40, 0xB0, req, addr + i, this, timeout=self.timeout)
            if res != len(this):
                raise Exception("wanted 0x%04X bytes but got 0x%04X" % (len(this), res,))
            i += max_write

    def eeprom_r(self, addr, n):
        # FIXME: should be 0x0D?
        return self._controlRead_mem(0x0B, 0x80, addr, n)
        
    def eeprom_w(self, addr, buff):
        return self._controlWrite_mem(0x0C, 0x80, addr, buff)
    
    def i2c_r(self, addr, n):
        '''Read I2C bus'''
        return self.dev.controlRead(0xC0, 0xB0, 0x0A, addr, n, timeout=self.timeout)

    def i2c_w(self, addr, buff):
        '''Write I2C bus'''
        self.dev.controlWrite(0x40, 0xB0, 0x0A, addr, buff, timeout=self.timeout)
    
    def rst(self):
        '''Reset the system'''
        # Reset is accomplished by writing a 1 to address 0xE600. 
        #self.mcu_rst(1)
        self.dev.controlWrite(0x40, 0xB0, 0xe600, 0, "\x01", timeout=self.timeout)
        
        # Start running by writing a 0 to that address. 
        #self.mcu_rst(0)
        self.dev.controlWrite(0x40, 0xB0, 0xe600, 0, "\x00", timeout=self.timeout)
        
    def mcu_rst(self, rst):
        '''Reset FX2'''
        self.dev.controlWrite(0x40, 0xB0, 0xe600, 0, chr(int(bool(rst))), timeout=self.timeout)

