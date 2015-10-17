from uvscada.util import str2hex

import re
import sys
import ast
import json
import binascii
import subprocess

from uvscada.bpm.startup import led_i2s
from i87c51_read_fw import p_p2n

prefix = ' ' * 8
indent = ''
def line(s):
    print '%s%s' % (indent, s)
def indentP():
    global indent
    indent += '    '
def indentN():
    global indent
    indent = indent[4:]

# args.big_thresh
big_pkt = {}
def fmt_terse(data, pktn=None):
    if data in p_p2n:
        return 'i87c51_read_fw.%s' % p_p2n[data]
    if pktn and data in big_pkt:
        return 'i87c51_write_fw.%s' % big_pkt[data]
    
    if args.big_thresh and pktn and len(data) > args.big_thresh:
        big_pkt[data] = 'p' + str(pktn)
        return 'i87c51_write_fw.%s' % big_pkt[data]
    
    ret = str2hex(data, prefix=prefix)
    if len(data) > 16:
        ret += '\n%s' % prefix
    return ret

def pkt_strip(p):
    pprefix = ord(p[0])
    '''
    if pprefix != 0x08:
        #raise Exception("Bad prefix")
        line('# WARNING: unexpected prefix')
    '''
    suffix = ord(p[-1])
    if suffix != 0x00:
        if 1:
            line('# WARNING: unexpected suffix: 0x%02X' % suffix)
        else:
            line('"""')
            line('WARNING: bad suffix')
            line(fmt_terse(p))
            line('"""')
        # saw this once and it looked more or less okay
        # raise Exception("Bad suffix")
    size = ord(p[-2])
    # Exact match
    if size == len(p) - 3:
        return (p[1:-2], False, pprefix, suffix)
    # Extra data
    # So far this is always 0 (should verify?)
    elif size < len(p) - 3:
        # TODO: verify 0 padding
        return (p[1:1 + size], True, pprefix, suffix)
    # Not supposed to happen
    else:
        print fmt_terse(p)
        print size
        raise Exception("Bad size")

def dump(fin):
    j = json.load(open(fin))
    pi = 0
    ps = j['data']

    line('# Generated from scrape.py')
    line('from uvscada.bpm.startup import bulk2, bulk86')
    line('import i87c51_read_fw')
    line('')
    
    # remove all comments to make processing easier
    # we'll add our own anyway
    # ps = filter(lambda p: p['type'] != 'comment', ps)
    
    def peekp():
        return nextp()[1]

    def nextp():
        ppi = pi + 1
        while True:
            if ppi >= len(ps):
                raise Exception("Out of packets")
            p = ps[ppi]
            if p['type'] != 'comment':
                return ppi, p
            ppi = ppi + 1
    
    line('def replay(dev):')
    indentP()
    line("bulkRead, bulkWrite, controlRead, controlWrite = usb_wraps(dev)")
    line('')
    
    if 0:
        line("# Generated from packet 61/62")
        line("# ...")
        line("# Generated from packet 71/72")
        line("load_fx2(dev)")
        line()
    
    while pi < len(ps):
        p = ps[pi]
        if p['type'] == 'comment':
            line('# %s' % p['v'])
            pass
        elif p['type'] == 'controlRead':
            '''
            # Generated from packet 6/7
            # None (0xB0)
            buff = controlRead(0xC0, 0xB0, 0x0000, 0x0000, 4096)
            # NOTE:: req max 4096 but got 3
            validate_read("\x00\x00\x00", buff, "packet 6/7")
            '''
            line('buff = controlRead(0x%02X, 0x%02X, 0x%04X, 0x%04X, %d)' % (
                    p['reqt'], p['req'], p['val'], p['ind'], p['len']))
            data = binascii.unhexlify(p['data'])
            line('# Req: %d, got: %d' % (p['len'], len(data)))
            line('validate_read(%s, buff, "packet %s/%s")' % (
                    fmt_terse(data, p['packn'][0]), p['packn'][0], p['packn'][1]))
        elif p['type'] == 'controlWrite':
            '''
            controlWrite(0x40, 0xB2, 0x0000, 0x0000, "")
            '''
            data = binascii.unhexlify(p['data'])
            line('buff = controlWrite(0x%02X, 0x%02X, 0x%04X, 0x%04X, %s)' % (
                    p['reqt'], p['req'], p['val'], p['ind'], str2hex(data, prefix=prefix)))
        elif p['type'] == 'bulkRead':
            if p['endp'] != 0x86:
                raise Exception("Unexpected endpoint")
            if 0:
                line('buff = bulkRead(0x%02X, 0x%04X)' % (p['endp'], p['len']))
                data = binascii.unhexlify(p['data'])
                line('# Req: %d, got: %d' % (p['len'], len(data)))
                line('validate_read(%s, buff, "packet %s/%s")' % (
                        fmt_terse(data, p['packn'][0]), p['packn'][0], p['packn'][1]))
            reply_full = binascii.unhexlify(p['data'])
            reply, truncate, pprefix, suffix = pkt_strip(reply_full)
            truncate_str = ''
            if truncate:
                truncate_str = ', truncate=True'
            pprefix_str = ''
            if pprefix != 0x08:
                pprefix_str = ', prefix=0x%02X' % pprefix
            suffix_str = ''
            if suffix != 0x00:
                suffix_str = ', suffix=0x%02X' % suffix
            line('# Discarded %d / %d bytes => %d bytes' % (len(reply_full) - len(reply), len(reply_full), len(reply)))
            pack_str = 'packet %s/%s' % (
                     p['packn'][0], p['packn'][1])
            line('buff = bulk86(dev, target=0x%02X%s%s%s)' % (len(reply), truncate_str, pprefix_str, suffix_str))
            line('validate_read(%s, buff, "%s")' % (fmt_terse(reply, p['packn'][0]), pack_str))
        elif p['type'] == 'bulkWrite':
            '''
            bulkWrite(0x02, "\x01")
            '''
            # Not all 0x02 have readback
            if p['endp'] != 0x02 or peekp()['type'] != 'bulkRead':
                data = binascii.unhexlify(p['data'])
                line('bulkWrite(0x%02X, %s)' % (p['endp'], fmt_terse(data, p['packn'][0])))
            else:
                p_w = p
                pi, p_r = nextp()
                cmd = binascii.unhexlify(p_w['data'])
                reply_full = binascii.unhexlify(p_r['data'])
                if 0:
                    line("'''")
                    line(fmt_terse(reply_full, p['packn'][0]))
                    line("'''")
                reply, truncate, pprefix, suffix = pkt_strip(reply_full)
                if cmd == "\x03":
                    line('gpio_readi(dev)')
                if len(cmd) == 3 and cmd[0] == "\x0C" and cmd[2] == "\x30":
                    #line('led_mask(dev, 0x%02X)' % ord(cmd[1]))
                    line('led_mask(dev, "%s")' % led_i2s[ord(cmd[1])])
                elif cmd == "\x22\x02\x10\x00\x1F\x00\x06":
                    line('sm_insert(dev)')
                elif cmd == "\x22\x02\x22\x00\x23\x00\x06":
                    if reply != "\xAA\x55\x33\xA2":
                        raise Exception("Unexpected response")
                    line('sm_info4(dev)')
                elif cmd == "\x22\x02\x24\x00\x25\x00\x06":
                    if reply != "\x01\x00\x00\x00":
                        raise Exception("Unexpected response")
                    line('sm_info5(dev)')
                # elif cmd == "":
                #    line('(dev)')
                elif cmd == "\x49":
                    line('cmd_49(dev)')
                else:
                    truncate_str = ''
                    if truncate:
                        truncate_str = ', truncate=True'
                    #if suffix != 0:
                    #    raise Exception("Unexpected")
                    pprefix_str = ''
                    if pprefix != 0x08:
                        pprefix_str = ', prefix=0x%02X' % pprefix
                    suffix_str = ''
                    if suffix != 0x00:
                        suffix_str = ', suffix=0x%02X' % suffix
                    pack_str = 'packet W: %s/%s, R: %s/%s' % (
                            p_w['packn'][0], p_w['packn'][1], p_r['packn'][0], p_r['packn'][1])
                    line('buff = bulk2(dev, %s, target=0x%02X%s%s%s)' % (fmt_terse(cmd, p_w['packn'][0]), len(reply), truncate_str, pprefix_str, suffix_str))
                    line('# Discarded %d / %d bytes => %d bytes' % (len(reply_full) - len(reply), len(reply_full), len(reply)))
                    line('validate_read(%s, buff, "%s")' % (fmt_terse(reply, p_r['packn'][0]), pack_str))
        else:
            raise Exception("Unknown type: %s" % p['type'])
        pi += 1

    indentN()

    print
    for pkt, name in big_pkt.iteritems():
        print '%s = %s' % (name, fmt_terse(pkt))

    print '''
def open_dev(usbcontext=None):
    if usbcontext is None:
        usbcontext = usb1.USBContext()
    
    print 'Scanning for devices...'
    for udev in usbcontext.getDeviceList(skip_on_error=True):
        vid = udev.getVendorID()
        pid = udev.getProductID()
        if (vid, pid) == (0x14b9, 0x0001):
            print
            print
            print 'Found device'
            print 'Bus %03i Device %03i: ID %04x:%04x' % (
                udev.getBusNumber(),
                udev.getDeviceAddress(),
                vid,
                pid)
            return udev.open()
    raise Exception("Failed to find a device")

if __name__ == "__main__":
    import argparse 
    
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    args = parser.parse_args()

    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext)
    dev.claimInterface(0)
    dev.resetDevice()
    replay(dev)
'''

if __name__ == "__main__":
    import argparse 
    
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--usbrply', default='')
    parser.add_argument('fin')
    args = parser.parse_args()
    args.big_thresh = 256

    if args.fin.find('.cap') >= 0:
        fin = '/tmp/scrape.json'
        #print 'Generating json'
        cmd = 'usbrply --packet-numbers --no-setup --comment --fx2 %s -j %s >%s' % (args.usbrply, args.fin, fin)
        #print cmd
        subprocess.check_call(cmd, shell=True)
    else:
        fin = args.fin
    
    dump(fin)

