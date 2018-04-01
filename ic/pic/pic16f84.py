import struct

'''
Datasheet
64 bytes of Data EEPROM
14-bit wide instruction words
1024 words of program memory
Register 6-1: PIC16F84A CONFIGURATION WORD
    Single bit


IDs at 0x4000 - 0x4007
config at 0x400E
EEPROM at 0x4200 - 0x427F
'''

prefix = 'pic16f84'
program_words = 1024
program_bytes = 2 * program_words
eeprom_bytes = 64

def w14(addr, w):
    w1 = w & 0x3FFF
    if w1 != w:
        raise Exception("Data overflow")
    buff[addr:addr+2] = struct.pack('<H', w1)

def w16(addr, w):
    buff[addr:addr+2] = struct.pack('<H', w)

def w8(addr, w):
    w1 = w & 0xFFF
    if w1 != w:
        raise Exception("Data overflow")
    buff[addr:addr+2] = struct.pack('<H', w)


# BP
if 1:
    buff = bytearray('\xFF' * 0x4280)
    
    for i in xrange(0, program_bytes, 2):
        w14(i, i)
    
    # hmm BP programs these almost like they are words
    for i in xrange(0, 2 * eeprom_bytes, 2):
        # Other "word" byte fixed at 0
        w8(0x4200 + i, i)
    
    open('%s_bp_cnt16.bin' % (prefix,), 'w').write(buff)


# minipro
if 1:
    buff = bytearray('\xFF' * program_bytes)
    for i in xrange(0, program_bytes, 2):
        w14(i, i)
    open('%s_minipro-code_cnt16.bin' % (prefix,), 'w').write(buff)

    buff = bytearray('\xFF' * eeprom_bytes)
    for i in xrange(0, eeprom_bytes, 1):
        buff[i] = i
    open('%s_minipro-data_cnt16.bin' % (prefix,), 'w').write(buff)

    buff = '''\
user_id0 = 0x3f00
user_id1 = 0x3f01
user_id2 = 0x3f02
user_id3 = 0x3f03
conf_word = 0x3fff'''
    open('%s_minipro-config_ncp.txt' % (prefix,), 'w').write(buff)

    buff = '''\
user_id0 = 0x3f00
user_id1 = 0x3f01
user_id2 = 0x3f02
user_id3 = 0x3f03
conf_word = 0x3fef'''
    open('%s_minipro-config_cp.txt' % (prefix,), 'w').write(buff)

