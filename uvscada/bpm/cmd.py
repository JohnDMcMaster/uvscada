from uvscada.usb import usb_wraps
from uvscada.usb import validate_read, validate_readv
from uvscada.bpm.bp1410_fw import load_fx2
from uvscada.bpm import bp1410_fw_sn
from uvscada.util import hexdump, str2hex
from uvscada.wps7 import WPS7

from cmd import *

import binascii
import struct
from collections import namedtuple
import libusb1
import time

# prefix: some have 0x18...why?
def bulk86(dev, target=None, donef=None, truncate=False, prefix=0x08):
    bulkRead, _bulkWrite, _controlRead, _controlWrite = usb_wraps(dev)
    
    if donef is None:
        # FIXME: to debug an unknown prefix protocol mode
        if prefix is None:
            def donef(buff):
                return False
        elif target is None:
            def donef(buff):
                return len(buff) > 0
        else:
            def donef(buff):
                return len(buff) >= target
    
    '''
    A suffix of 1 indicates that another buffer is coming
    However, a buffer can be split into multiple packets
    Is this an FX2-parallel distinction?
    Don't think we care at this level

    Ex: need to read 4096 bytes
    Max buffer packet size is 512 bytes
    but for some reason only uses up to 256 bytes of real data
    + 3 framing bytes and 0 fills the rest to form 512 byte transfer
    So to transfer the data 
    '''
    def nxt_buff():
        p = bulkRead(0x86, 0x0200)
        #print str2hex(p)
        if prefix is not None and ord(p[0]) != prefix:
            raise Exception("prefix: wanted 0x%02X, got 0x%02X" % (prefix, ord(p[0])))
        suffix_this = ord(p[-1])
        size = ord(p[-2])
        if size != len(p) - 3:
            if truncate and size < len(p) - 3:
                return p[1:1 + size], suffix_this
            else:
                print 'Truncate: %s' % truncate
                print size, len(p) - 3, len(p)
                hexdump(p)
                raise Exception("Bad length (enable truncation?)")
        return p[1:-2], suffix_this

    buff = ''
    while not donef(buff):
        if 0 and buff:
            print 'NOTE: split packet.  Have %d / %d bytes' % (len(buff), target)
            hexdump(buff)
        try:
            # Ignore suffix continue until we have a reason to care
            buff_this, _suffix_this = nxt_buff()
            buff += buff_this
        # FIXME: temp
        except libusb1.USBError:
            if prefix is None:
                return buff
            raise
    #print 'Done w/ buff len %d' % len(buff)
    if target and len(buff) > target:
        raise Exception('Buffer grew too big')
    return buff

# FIXME: with target set small but not truncate will happily truncate
# FIXME: suffix 1 means continue read.  Make higher level func
def bulk2(dev, cmd, target=None, donef=None, truncate=False, prefix=0x08):
    _bulkRead, bulkWrite, _controlRead, _controlWrite = usb_wraps(dev)
    
    bulkWrite(0x02, cmd)
    return bulk86(dev, target=target, donef=donef, truncate=truncate, prefix=prefix)


def sn_read(dev):
    # Generated from packet 118/119
    buff = bulk2(dev, "\x0E\x00", target=0x20)
    validate_read(
            "\x3A\x00\x90\x32\xA7\x02\x2A\x86\x01\x95\x3C\x36\x90\x00\x1F"
            "\x00\x01\x00\xD6\x05\x01\x00\x72\x24\x22\x39\x00\x00\x00\x00\x27"
            "\x1F",
            buff, "packet 120/121")
    sn = buff[6:8]
    print 'S/N: %s' % binascii.hexlify(sn)

SM1_FMT = '<H12s18s'
SM1 = namedtuple('sm', ('unk0', 'name', 'unk12'))

def sm_read(dev):
    buff = bulk2(dev, "\x0E\x02", target=0x20, truncate=True)
    validate_readv((
              "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
              "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
              "\xFF",
              
              # Socket module
              # 00000000  11 00 53 4D 34 38 44 00  00 00 00 00 00 00 5D F4  |..SM48D.......].|
              # 00000010  39 FF 00 00 00 00 00 00  00 00 00 00 00 00 62 6C  |9.............bl|
              "\x11\x00\x53\x4D\x34\x38\x44\x00\x00\x00\x00\x00\x00\x00\x5D\xF4" \
              "\x39\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x62\x6C",
              ),
              buff, "packet 136/137")
    # Don't throw exception on no SM for now?)
    # since it will break other code
    if buff == '\xFF' * 32:
        return None
    
    return SM1(*struct.unpack(SM1_FMT, buff))

def sm_info0(dev):
    # Generated from packet 3/4
    gpio_readi(dev)
    
    # Generated from packet 7/8
    gpio_readi(dev)

    # Generated from packet 11/12
    sm_info22(dev)
    
    # Generated from packet 15/16
    sm_info24(dev)
    
    # Generated from packet 19/20
    sm_read(dev)

def sm_info1(dev):
    sm_info0(dev)
    
    # Generated from packet 23/24
    cmd_49(dev)
    
    # Generated from packet 27/28
    sm = sm_read(dev)
    print 'Name: %s' % sm.name

# Possibly I2C traffic
# Addresses are inclusive
def periph_r(dev, periph, start, end):
    if not (0 <= start <= 0x40):
        raise Exception("Bad start")
    if not (0 <= start <= 0x40):
        raise Exception("Bad end")
    words = end - start + 1
    if words < 0:
        raise Exception("Bad start-end")
    '''
    Example commands
    bulk2(dev, "\x22\x02\x22\x00\x23\x00\x06
        read SM 22:23
    
    I fuzzed to find periph 1, no real example commands but this seems to work
        bulk2(dev, "\x22\x01\x00\x00\x7F\x00\x06
    '''
    return bulk2(dev, "\x22" + chr(periph) + chr(start) + "\x00" + chr(end) + "\x00\x06",
                target=(words*2),
                truncate=True)

# Teach adapter (ex: TA84VLV_FX4) EEPROM
def ta_r(dev, start, end):
    return periph_r(dev, 0x01, start, end)

# Read socket module (ex: SM84) EEPROM
def sm_r(dev, start, end):
    return periph_r(dev, 0x02, start, end)

def periph_dump(dev):
    print 'Peripheral memory'
    hexdump(ta_r(dev, 0x00, 0x3F), label="TA", indent='  ')
    hexdump(sm_r(dev, 0x00, 0x3F), label="SM", indent='  ')
    import sys; sys.exit(1)

def sm_insert(dev):
    buff = sm_r(dev, 0x10, 0x1F)
    hexdump(buff, label="sm_insert", indent='  ')
    SM2_FMT = '<HHHH24s'
    SM2 = namedtuple('sm', ('ins_all', 'unk1', 'ins_last', 'unk2', 'res'))
    sm = SM2(*struct.unpack(SM2_FMT, buff))
    # Auto increments during some operation
    print '  Insertions (all): %d' % sm.ins_all
    print '  Insertions (since last): %d' % sm.ins_last
    
    return sm

def sm_info10(dev):
    # Generated from packet 35/36
    buff = sm_r(dev, 0x10, 0x13)
    '''
    something caused fields to update
      Expected; 8
        "\x32\x01\x00\x00\x93\x00\x00\x00"
        00000000  32 01 00 00 93 00 00 00                           |2.......        |
      Actual; 8
        "\x3A\x01\x00\x00\x9B\x00\x00\x00"
        00000000  3A 01 00 00 9B 00 00 00                           |:.......        |
    '''
    hexdump(buff, label="sm_info10", indent='  ')
    SM3_FMT = '<HHHH'
    SM3 = namedtuple('sm3', ('ins_all', 'unk1', 'ins_last', 'unk2'))
    sm = SM3(*struct.unpack(SM3_FMT, buff))
    print '  Insertions (all): %d' % sm.ins_all
    print '  Insertions (since last): %d' % sm.ins_last

def sm_info22(dev):
    # Generated from packet 11/12
    buff = sm_r(dev, 0x22, 0x23)
    validate_read("\xAA\x55\x33\xA2", buff, "packet 13/14")

def sm_info24(dev):
    # Generated from packet 15/16
    buff = sm_r(dev, 0x24, 0x25)
    validate_read("\x01\x00\x00\x00", buff, "packet 17/18")

def cmd_01(dev):
    '''
    def donef(buff):
        return len(buff) == 129 or len(buff) == 133
    buff = bulk2(dev, '\x01', donef=donef)
    validate_readv([r01_cold, r01_warm, r01_glitch_154, r01_ps, r01_sm] + r01_glitches, buff, "packet 68/69 (warm/cold)")
    '''

    r01_cold = ("\x80\xA4\x06\x02\x00\x22\x00\x43\x00\xC0\x03\x00\x08\xF8\x19"
              "\x00\x00\x30\x00\x80\x00\x00\x00\x00\x00\xC0\x00\x00\x00\x09\x00"
              "\x08\x00\xFF\x00\xE0\x14\x00\x00\xE8\x14\x00\x00\x84\x1C\x00\x00"
              "\xEC\x14\x00\x00\xD0\x19\xFF\xFF\xC0\x19\xFF\xFF\x00\x00\xF0\x3C"
              "\xFF\xFF\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00"
              "\x00\x00\x56\x10\x00\x00\x88\x1B\x00\x00\x6C\x1B\x00\x00\x00\x00"
              "\x00\x00\x64\x1B\x00\x00\x66\x1B\x00\x00\x68\x1B\x00\x00\x44\x1C"
              "\x00\x00\x70\x1B\x00\x00\x30\x11\x00\x00\x34\x11\x00\x00\x74\x1B"
              "\x00\x00")
    r01_warm = ("\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24"
              "\x00\x00\x30\x00\x83\x00\x30\x01\x09\x00\xC0\x00\x00\x00\x09\x00"
              "\x08\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00"
              "\xD0\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55"
              "\x01\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00"
              "\x00\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00"
              "\x01\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46"
              "\x00\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11"
              "\x00\x00\xC0\x1E\x00\x00")
    # warm glitched initially on 154/155
    # after that stuck on 68/69
    # Not sure what it means though
    # Otherwise its a warm startup
    r01_glitch_154 = (
              "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24"
              # Differences here
              "\x00\x00\x30\x00\x80\x00\x00\x00\x09\x00\xC0\x00\x00\x00\x09\x00"
              "\x08\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00"
              "\xD0\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55"
              "\x01\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00"
              "\x00\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00"
              "\x01\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46"
              "\x00\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11"
              "\x00\x00\xC0\x1E\x00\x00")
    
    # rarer responses
    r01_glitches = [
        binascii.unhexlify("84a406020026004300c0030008102400003000820010010900c000000009000800ff00c41e0000cc1e0000b4460000d01e0000c01e0100b01e01000000305501000000000002008001d00102000100000056100000a025000084250000000001007c2500007e2500008025000074460000381100003c1100004011000044110000c01e0000"),
        binascii.unhexlify('84a406020026004300c0030008102400003000830030010900c000000009000800ff00c41e0000cc1e0000b4460000d01e0000c01e0100b01e01000000305501000000000002008001c00102000100000056100000a025000084250000000001007c2500007e2500008025000074460000381100003c1100004011000044110000c01e0000'),
        ]
    
    r01_ps = \
         "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24\x00" \
        "\x00\x30\x00\x84\x00\x50\x01\x09\x00\xC0\x00\x00\x00\x09\x00\x08" \
        "\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00\xD0" \
        "\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55\x01" \
        "\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00\x00" \
        "\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00\x01" \
        "\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46\x00" \
        "\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11\x00" \
        "\x00\xC0\x1E\x00\x00"
    
    r01_sm = \
        "\x80\xA4\x06\x02\x00\x22\x00\x43\x00\xC0\x03\x00\x08\xF8\x19\x00" \
        "\x00\x30\x00\x80\x00\x00\x00\x00\x00\xC0\x00\x00\x00\x09\x00\x08" \
        "\x00\xFF\x00\xE0\x14\x00\x00\xE8\x14\x00\x00\x84\x1C\x00\x00\xEC" \
        "\x14\x00\x00\xD0\x19\xFF\xFF\xC0\x19\xFF\xFF\x00\x00\xF0\x3C\xFF" \
        "\xFF\x00\x00\x00\x00\x02\x00\x80\x01\xE0\x01\x02\x00\x01\x00\x00" \
        "\x00\x56\x10\x00\x00\x88\x1B\x00\x00\x6C\x1B\x00\x00\x00\x00\x00" \
        "\x00\x64\x1B\x00\x00\x66\x1B\x00\x00\x68\x1B\x00\x00\x44\x1C\x00" \
        "\x00\x70\x1B\x00\x00\x30\x11\x00\x00\x34\x11\x00\x00\x74\x1B\x00" \
        "\x00"
    
    
    
    def donef(buff):
        return len(buff) == 129 or len(buff) == 133

    buff = bulk2(dev, '\x01',
            #target=133)
            donef=donef)
    print 'cmd_01 len: %d' % len(buff)
    validate_readv((
            "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24"
            "\x00\x00\x30\x00\x80\x00\x00\x00\x00\x00\xC0\x00\x00\x00\x09\x00"
            "\x08\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00"
            "\xD0\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55"
            "\x01\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00"
            "\x00\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00"
            "\x01\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46"
            "\x00\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11"
            "\x00\x00\xC0\x1E\x00\x00",
    
            "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24\x00" \
            "\x00\x30\x00\x80\x00\x00\x00\x00\x00\xC0\x00\x00\x00\x09\x00\x08" \
            "\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00\xD0" \
            "\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55\x01" \
            "\x00\x00\x00\x00\x00\x02\x00\x80\x01\xC0\x01\x02\x00\x01\x00\x00" \
            "\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00\x01" \
            "\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46\x00" \
            "\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11\x00" \
            "\x00\xC0\x1E\x00\x00",

              "\x80\xA4\x06\x02\x00\x22\x00\x43\x00\xC0\x03\x00\x08\xF8\x19"
              "\x00\x00\x30\x00\x80\x00\x00\x00\x00\x00\xC0\x00\x00\x00\x09\x00"
              "\x08\x00\xFF\x00\xE0\x14\x00\x00\xE8\x14\x00\x00\x84\x1C\x00\x00"
              "\xEC\x14\x00\x00\xD0\x19\xFF\xFF\xC0\x19\xFF\xFF\x00\x00\xF0\x3C"
              "\xFF\xFF\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00"
              "\x00\x00\x56\x10\x00\x00\x88\x1B\x00\x00\x6C\x1B\x00\x00\x00\x00"
              "\x00\x00\x64\x1B\x00\x00\x66\x1B\x00\x00\x68\x1B\x00\x00\x44\x1C"
              "\x00\x00\x70\x1B\x00\x00\x30\x11\x00\x00\x34\x11\x00\x00\x74\x1B"
              "\x00\x00",

            "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24\x00" \
            "\x00\x30\x00\x98\x00\xD0\x76\x09\x00\xC0\x00\x00\x00\x09\x00\x08" \
            "\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00\xD0" \
            "\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55\x01" \
            "\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00\x00" \
            "\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00\x01" \
            "\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46\x00" \
            "\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11\x00" \
            "\x00\xC0\x1E\x00\x00",






              "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24"
              "\x00\x00\x30\x00\x80\x00\x00\x00\x00\x00\xC0\x00\x00\x00\x09\x00"
              "\x08\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00"
              "\xD0\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55"
              "\x01\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00"
              "\x00\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00"
              "\x01\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46"
              "\x00\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11"
              "\x00\x00\xC0\x1E\x00\x00",
              
              # warm
              "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24"
              "\x00\x00\x30\x00\x83\x00\x30\x01\x09\x00\xC0\x00\x00\x00\x09\x00"
              "\x08\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00"
              "\xD0\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55"
              "\x01\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00"
              "\x00\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00"
              "\x01\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46"
              "\x00\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11"
              "\x00\x00\xC0\x1E\x00\x00",
              
              # glitch recover
              "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24"
              "\x00\x00\x30\x00\x83\x00\x30\x01\x09\x00\xC0\x00\x00\x00\x09\x00"
              "\x08\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00"
              "\xD0\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55"
              "\x01\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00"
              "\x00\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00"
              "\x01\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46"
              "\x00\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11"
              "\x00\x00\xC0\x1E\x00\x00",
              
              # after ps
            "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24\x00" \
            "\x00\x30\x00\x84\x00\x50\x01\x09\x00\xC0\x00\x00\x00\x09\x00\x08" \
            "\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00\xD0" \
            "\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55\x01" \
            "\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00\x00" \
            "\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00\x01" \
            "\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46\x00" \
            "\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11\x00" \
            "\x00\xC0\x1E\x00\x00",



            "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24\x00" \
            "\x00\x30\x00\x92\x00\xA0\x63\x09\x00\xC0\x00\x00\x00\x09\x00\x08" \
            "\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00\xD0" \
            "\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55\x01" \
            "\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00\x00" \
            "\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00\x01" \
            "\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46\x00" \
            "\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11\x00" \
            "\x00\xC0\x1E\x00\x00",
    
            "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24\x00" \
            "\x00\x30\x00\x83\x00\x30\x01\x09\x00\xC0\x00\x00\x00\x09\x00\x08" \
            "\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00\xD0" \
            "\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55\x01" \
            "\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00\x00" \
            "\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00\x01" \
            "\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46\x00" \
            "\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11\x00" \
            "\x00\xC0\x1E\x00\x00",




            r01_cold,
            r01_warm,
            r01_glitch_154,
            r01_sm,
            r01_ps,
            r01_glitches[0],
            r01_glitches[1],
            ), buff, "packet 116/117")
    return buff

# cmd_01: some sort of big status read
# happens once during startup and a few times during programming write/read cycles

def cmd_2(dev, exp, msg='cmd_2'):
    # Generated from packet 188/189
    buff = bulk2(dev, "\x02", target=6, truncate=True)
    validate_read(exp, buff, msg)

def cmd_08(dev, cmd):
    cmdf = "\x08\x01\x57" + cmd + "\x00"
    if len(cmdf) != 5:
        raise Exception("Malfored command")

    buff = bulk2(dev, cmdf, target=0x02, truncate=True)
    validate_read("\x00\x00", buff, "packet W: 359/360, R: 361/362")

# clear => present
GPIO_SM = 0x0001
# Not sure if this actually is GPIO
# but seems like a good guess given that it detects socket module insertion
def gpio_readi(dev):
    buff = bulk2(dev, "\x03", target=2, truncate=True)
    validate_readv((
            "\x31\x00",
            "\x71\x04",
            "\x71\x00",
            
            # SM
            "\x30\x00",
            "\x30\x04",
            ),
            buff, "packet 128/129")
    return struct.unpack('<H', buff)[0]

def cmd_09(dev):
    _bulkRead, bulkWrite, _controlRead, _controlWrite = usb_wraps(dev)
    bulkWrite(0x02, "\x09\x10\x57\x81\x00")

# cmd_04

# cmd_08

'''
1 => LED on

LEDs:
-1: fail
-2: active
-4: pass
'''
led_s2i = {
            'fail': 1,
            'active': 2,
            'pass': 4,
            'green': 1,
            'orange': 2,
            'red': 4,
            }
#led_i2s = dict((v, k) for k, v in led_s2i.iteritems())

def cmd_0C_mk():
    return "\x0C\x04"

def led_mask(dev, mask):
    _bulkRead, bulkWrite, _controlRead, _controlWrite = usb_wraps(dev)
    
    mask = led_s2i.get(mask, mask)
    if mask < 0 or mask > 7:
        raise ValueError("Bad mask")
    bulkWrite("0x02, \x0C" + chr(mask), truncate=True)

def led_mask_30(dev, mask):
    mask = led_s2i.get(mask, mask)
    if mask < 0 or mask > 7:
        raise ValueError("Bad mask")
    buff = bulk2(dev, "\x0C" + chr(mask) + "\x30", target=2, truncate=True)
    validate_read(chr(mask) + "\x00", buff, "packet 9/10")    

# cmd_0E repeat with a few different arguments
# one of them reads SM EEPROM
def cmd_0E(dev):
    buff = bulk2(dev, "\x0E\x02", target=0x20, truncate=True)
    # Discarded 480 / 512 bytes => 32 bytes
    validate_read(
        "\x11\x00\x53\x4D\x34\x38\x44\x00\x00\x00\x00\x00\x00\x00\x5D\xF4" \
        "\x39\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x62\x6C"
        , buff, "packet W: 787/788, R: 789/790")

# cmd_10
def cmd_10(dev):
    buff = bulk2(dev, "\x10\x80\x02", target=0x06)
    # Discarded 3 / 9 bytes => 6 bytes
    validate_read("\x80\x00\x00\x00\x09\x00", buff, "packet W: 65/66, R: 67/68")

# cmd_14 repeat

# cmd_1D

def cmd_20_mk():
    '''
    Examples:
    bulkWrite(0x02, "\x20\x01\x00 \x0C\x04")
    bulkWrite(0x02, "\x20\x01\x00 \x50\x7D\x02\x00\x00")
    '''
    return "\x20\x01\x00"

def cmd_20(dev):
    _bulkRead, bulkWrite, controlRead, controlWrite = usb_wraps(dev)
    # No reply
    bulkWrite(0x02, cmd_20_mk())


# cmd_22 peripheral (I2C?) read

# cmd_30: see LED functions

# cmd_3B
def cmd_3B(dev):
    _bulkRead, bulkWrite, _controlRead, _controlWrite = usb_wraps(dev)
    
    bulkWrite(0x02, 
        "\x3B\x0C\x22\x00\xC0\x40\x00\x3B\x0E\x22\x00\xC0\x00\x00\x3B\x1A" \
        "\x22\x00\xC0\x18\x00"
        )

def cmd_41(dev):
    _bulkRead, bulkWrite, _controlRead, _controlWrite = usb_wraps(dev)
    bulkWrite(0x02, "\x41\x00\x00")

# cmd_43... repeat
def cmd_43(dev):
    _bulkRead, bulkWrite, _controlRead, _controlWrite = usb_wraps(dev)
    
    bulkWrite(0x02, "\x43\x19\x10\x00\x00")

# cmd_45
def cmd_45(dev):
    buff = bulk2(dev, "\x45\x01\x00\x00\x31\x00\x06", target=0x64)
    # Discarded 3 / 103 bytes => 100 bytes
    validate_read(
        "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF" \
        "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF" \
        "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF" \
        "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF" \
        "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF" \
        "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF" \
        "\xFF\xFF\xFF\xFF"
        , buff, "packet W: 77/78, R: 79/80")

# Common (GPIO/status?)
# Oddly sometimes this requires truncation and sometimes doesn't
def cmd_49(dev):
    # Generated from packet 156/157
    buff = bulk2(dev, "\x49", target=2, truncate=True)
    validate_read("\x0F\x00", buff, "packet 158/159")

# cmd_4A
def cmd_4A(dev):
    # Generated from packet 123/124
    buff = bulk2(dev, "\x4A\x03\x00\x00\x00", target=0x02)
    # Discarded 3 / 5 bytes => 2 bytes
    validate_read("\x03\x00", buff, "packet W: 123/124, R: 125/126")

def cmd_4C(dev):
    _bulkRead, bulkWrite, _controlRead, _controlWrite = usb_wraps(dev)
    bulkWrite(0x02, "\x4C\x00\x02")
'''

Always
-begin with 0x57
-end with 0x00

Payload size varies
-1
-4

Often returns 0000 but not always
Return size can vary

think these are literlaly a 57 command followed by a 50 command
this hints that I can string (some?) commands together
but it may not be obvious to know where the boundary is
'''

def cmd_50_mk(cmd):
    '''
    Example:
    "\x50\x9F\x09\x00\x00"
    As part of a larger command:
    "\x57\x82\x00 \x50\x1D\x00\x00\x00"
    '''
    ret = "\x50" + cmd + "\x00\x00"
    if len(ret) != 5:
        raise Exception("Malfored command")
    return ret

def cmd_50(dev, cmd):
    _bulkRead, bulkWrite, controlRead, controlWrite = usb_wraps(dev)
    # No reply
    bulkWrite(0x02, cmd_50_mk(cmd))

def cmd_57_mk(cmd):
    return "\x57" + cmd + "\x00"

def cmd_57s(dev, cmds, exp, msg="cmd_57"):
    out = ''.join([cmd_57_mk(c) for c in cmds])
    buff = bulk2(dev, out, target=len(exp), truncate=True)
    validate_read(exp, buff, msg)

def cmd_57_94(dev):
    cmd_57s(dev, '\x94', "\x62",  "cmd_57_94")
    # Seems to get paired with this
    buff = bulk86(dev, target=0x01, truncate=True, prefix=0x18)
    validate_read("\x0B", buff, "packet 545/546")

def cmd_57_50(dev, c57, c50):
    # ex: bulkWrite(0x02, "\x57\x82\x00 \x50\x1D\x00\x00\x00")
    _bulkRead, bulkWrite, controlRead, controlWrite = usb_wraps(dev)
    bulkWrite(0x02, cmd_57_mk(c57) + cmd_50_mk(c50))

# cmd_5A: encountered once

# cmd_66

# cmd_80

# cmd_82

# cmd_A6

# cmd_DB

# cmd_E9
