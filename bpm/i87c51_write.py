from uvscada.bpm import startup, cmd
from uvscada.util import hexdump, add_bool_arg
from uvscada.bpm.i87c51.write import replay

if __name__ == "__main__":
    import argparse 
    
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    add_bool_arg(parser, '--cycle', default=False, help='') 
    add_bool_arg(parser, '--cont', default=True, help='Continuity check') 
    parser.add_argument('fin', nargs='?', help='Input file') 
    args = parser.parse_args()

    if args.cycle:
        startup.cycle()

    dev, usbcontext = startup.get()

    if args.fin:
        fw = open(args.fin, 'r').read()
    else:
        fw = 4096 * '\xFF'
    if len(fw) != 4096:
        raise Exception("Bad FW length")
    replay(dev, fw)

    print 'Complete'
