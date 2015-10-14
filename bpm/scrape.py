from uvscada.util import str2hex

import re
import sys
import ast
import json
import binascii

prefix = ' ' * 8

def fmt_terse(data):
    ret = str2hex(data, prefix=prefix)
    if len(data) > 16:
        ret += '\n%s' % prefix
    return ret

def pkt_strip(p):
    if ord(p[0]) != 0x08:
        raise Exception("Bad prefix")
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
        return (p[1:-2], False, suffix)
    # Extra data
    # So far this is always 0 (should verify?)
    elif size < len(p) - 3:
        # TODO: verify 0 padding
        return (p[1:1 + size], True, suffix)
    # Not supposed to happen
    else:
        print fmt_terse(p)
        print size
        raise Exception("Bad size")

def line(s):
    print '    %s' % s

def dump(fin):
    j = json.load(open(fin))
    pi = 0
    ps = j['data']
    
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
    
    print 'def replay(dev):'
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
            line('validate_read(%s, buff, "packet %d/%d")' % (
                    fmt_terse(data), p['packn'][0], p['packn'][1]))
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
                line('validate_read(%s, buff, "packet %d/%d")' % (
                        fmt_terse(data), p['packn'][0], p['packn'][1]))
            reply_full = binascii.unhexlify(p['data'])
            reply, truncate, suffix = pkt_strip(reply_full)
            truncate_str = ''
            if truncate:
                truncate_str = ', truncate=True'
            suffix_str = ''
            if suffix != 0x00:
                suffix_str = ', suffix=0x%02X' % suffix
            line('# Discarded %d / %d bytes => %d bytes' % (len(reply_full) - len(reply), len(reply_full), len(reply)))
            pack_str = 'packet %d/%d' % (
                     p['packn'][0], p['packn'][1])
            line('buff = bulk86(dev, target=0x%02X%s%s)' % (len(reply), truncate_str, suffix_str))
            line('validate_read(%s, buff, "%s")' % (fmt_terse(reply), pack_str))
        elif p['type'] == 'bulkWrite':
            '''
            bulkWrite(0x02, "\x01")
            '''
            # Not all 0x02 have readback
            if p['endp'] != 0x02 or peekp()['type'] != 'bulkRead':
                data = binascii.unhexlify(p['data'])
                line('bulkWrite(0x%02X, %s)' % (p['endp'], fmt_terse(data)))
            else:
                p_w = p
                pi, p_r = nextp()
                cmd = binascii.unhexlify(p_w['data'])
                reply_full = binascii.unhexlify(p_r['data'])
                if 0:
                    line("'''")
                    line(fmt_terse(reply_full))
                    line("'''")
                reply, truncate, suffix = pkt_strip(reply_full)
                truncate_str = ''
                if truncate:
                    truncate_str = ', truncate=True'
                #if suffix != 0:
                #    raise Exception("Unexpected")
                suffix_str = ''
                if suffix != 0x00:
                    suffix_str = ', suffix=0x%02X' % suffix
                pack_str = 'packet W: %d/%d, R: %d/%d' % (
                        p_w['packn'][0], p_w['packn'][1], p_r['packn'][0], p_r['packn'][1])
                line('buff = bulk2(dev, %s, target=0x%02X%s%s)' % (fmt_terse(cmd), len(reply), truncate_str, suffix_str))
                line('# Discarded %d / %d bytes => %d bytes' % (len(reply_full) - len(reply), len(reply_full), len(reply)))
                line('validate_read(%s, buff, "%s")' % (fmt_terse(reply), pack_str))
        else:
            raise Exception("Unknown type: %s" % p['type'])
        pi += 1

if __name__ == "__main__":
    import argparse 
    
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('fin')
    args = parser.parse_args()

    print 'from uvscada.bpm.startup import bulk2, bulk86'
    print
    dump(args.fin)
