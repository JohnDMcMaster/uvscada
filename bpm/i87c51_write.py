from uvscada.bpm import startup, cmd
from uvscada.util import hexdump, add_bool_arg
from uvscada.bpm.i87c51.write import replay

if __name__ == "__main__":
    import argparse 
    
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    add_bool_arg(parser, '--cycle', default=False, help='') 
    add_bool_arg(parser, '--cont', default=True, help='Continuity check') 
    args = parser.parse_args()

    if args.cycle:
        startup.cycle()

    dev, usbcontext = startup.get()
    _bulkRead, bulkWrite, controlRead, controlWrite = cmd.usb_wraps(dev)

    fw = 4096 * '\xFF'
    replay(dev, fw)

    print 'Complete'
