from uvscada import gxs700_util
from uvscada import util

import argparse
import binascii
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Dump device data')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    util.add_bool_arg(parser, '--eeprom', default=False, help='')
    util.add_bool_arg(parser, '--flash', default=False, help='')
    parser.add_argument('din', nargs='?', default='dump', help='File in')
    args = parser.parse_args()

    usbcontext, dev, gxs = gxs700_util.ez_open_ex()
    
    if args.eeprom or args.eeprom_all:
        print 'Writing EEPROM'
        eeprom_w = open(os.path.join(args.din, 'eeprom.bin'), 'r').read()
        gxs.eeprom_w(0x0000, eeprom_w[0:0x2000/1])
        
        print 'Reading back to verify'
        eeprom_r = gxs.eeprom_r()
        if eeprom_w != eeprom_r:
            raise Exception("Failed to update EEPROM")
        print 'Update OK!'


    '''
    if args.flash:
        print 'Writing flash'
        flash = open(os.path.join(args.din, 'flash.bin'), 'r').read()
        gxs.flash_w(flash)
    '''

