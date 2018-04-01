'''
Export as .csv since Saleae parsing isn't supported
Written for PIC16C55X

CH0: clock
CH1: data

Once in configura-
tion memory, the highest bit of the PC stays a '1', thus
always pointing to the configuration memory. The only
way to point to user program memory is to reset the
part and reenter program/verify mode, as described in
Section 2.2.

In the configuration memory space, 0x2000-0x20FF
are utilized. When in a configuration memory, as in the
user memory, the 0x2000-0x2XFF segment is repeat-
edly accessed as the PC exceeds 0x2XFF (see
Figure 2-1).
'''

# DS30261C page 3-42
cmd_s2i = {
    'LOAD_CFG':   0b000000,
    'LOAD_DAT':   0b000010,
    'READ_DAT':   0b000100,
    'INC_ADDR':   0b000110,
    'BEGIN_PROG': 0b001000,
    'END_PROG':   0b001110,
    }
cmd_i2s = dict([(v, k) for k, v in cmd_s2i.iteritems()])

class BadCommand(Exception):
    pass

def next_cmd(fin):
    '''
    Latched on falling edge of clock
        Expected to be sent on rising edge
    LSB first

    header
    6 clocks, 6 bits
    
    when data:
    16 clocks
    first: start bit
    last: stop bit
    '''

    def next_line():
        while True:
            l = fin.readline()
            if not l:
                raise EOFError()
            t, clk, dat = l.split(',')
            t = float(t)
            clk = int(clk)
            dat = int(dat)
            return t, clk, dat
    
    def next_bitt():
        clk_last = 0
        clk = 0
        while True:
            clk_last = clk
            t, clk, dat = next_line()
            # Hack: ignore startup glitch
            if t < 0.001:
                continue
            # falling edge?
            if clk_last == 1 and clk == 0:
                return t, dat
    def next_bit():
        return next_bitt()[1]

    cmdi = 0
    for i in xrange(6):
        # LSB first
        cmdi |= next_bit() << i
    cmds = cmd_i2s.get(cmdi, None)
    if cmds is None:
        raise BadCommand("%d" % cmdi)
    payload = None
    if cmds in ('LOAD_CFG', 'LOAD_DAT', 'READ_DAT'):
        t, start_bit = next_bitt()
        if 0 and start_bit != 0:
            raise BadCommand("Invalid start bit @ %0.6f" % t)

        payload = 0
        for i in xrange(14):
            payload |= next_bit() << i

        t, stop_bit = next_bitt()
        if 0 and stop_bit != 0:
            raise BadCommand("Invalid stop bit @ %0.6f" % t)
    return cmds, payload

def gen_cmds(fin):
    while True:
        try:
            cmd = next_cmd(fin)
        except EOFError:
            break
        yield cmd

def run(fin):
    # Skip header
    fin.readline()
    # FIXME: why isn't the first LOAD_CONFIG 0x2000 instead of 0x0000?
    pc = 0
    for cmd, payload in gen_cmds(fin):
        if payload is not None:
            print '%s: 0x%04X' % (cmd, payload)
        else:
            print '%s' % cmd

        if cmd == 'LOAD_CFG':
            pc = payload
        elif cmd == 'INC_ADDR':
            pc += 1

        if cmd == 'READ_DAT':
            if pc == 7:
                def bit(n):
                    return 1 if payload & (1 << n) else 0
                print '  CONFIG'
                print '  CP1-13: %d' % bit(13)
                print '  CP0-12: %d' % bit(12)
                print '  CP1-11: %d' % bit(11)
                print '  CP0-10: %d' % bit(10)
                print '  CP1-9:  %d' % bit(9)
                print '  CP0-8:  %d' % bit(8)
                print '  RES-7:  %d' % bit(7)
                print '  0-6:    %d' % bit(6)
                print '  CP1-5:  %d' % bit(5)
                print '  CP0-4:  %d' % bit(4)
                print '  PWRITEn %d' % bit(3)
                print '  WDTE:   %d' % bit(2)
                print '  FOSC1:  %d' % bit(1)
                print '  FOSC0:  %d' % bit(0)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Decode Saleae captures')
    parser.add_argument('--verbose', action="store_true", help='Verbose output')
    parser.add_argument('fin')
    args = parser.parse_args()

    run(open(args.fin, 'r'))
