from uvscada.bpm import startup, cmd
from uvscada.util import hexdump, add_bool_arg
from uvscada.bpm.i87c51.read import replay

if __name__ == "__main__":
    import argparse 
    
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    add_bool_arg(parser, '--cycle', default=False, help='') 
    add_bool_arg(parser, '--cont', default=True, help='Continuity check') 
    parser.add_argument('fout', nargs='?', help='Output file') 
    args = parser.parse_args()

    if args.cycle:
        startup.cycle()

    dev, usbcontext = startup.get()
    _bulkRead, bulkWrite, controlRead, controlWrite = cmd.usb_wraps(dev)

    fw_in = replay(dev, cont=args.cont)
    if args.fout:
        print 'Writing to %s' % args.fout
        open(args.fout, 'w').write(fw_in)
    else:
        hexdump(fw_in, indent='  ', label='Read data')
    print 'Bytes: %d 0x%04X' % (len(fw_in), len(fw_in))

    print 'Complete'
