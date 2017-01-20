from uvscada.util import hexdump, add_bool_arg
import os
import sys
import time

if __name__ == "__main__":
    import argparse 
    
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('din', help='Input dir') 
    args = parser.parse_args()

    bini = 270
    while True:
        fn = os.path.join(args.din, 'read-%0.5d.bin' % bini)
        if not os.path.exists(fn):
            break
        
        os.system('clear')
        print bini
        
        # 4096 x ?
        dat = open(fn).read()
        rows = 4096 / 256
        cols = 4096 / rows
        for row in xrange(rows):
            for col in xrange(cols):
                #if col > 209:
                #    break
                if col == cols / 2:
                    sys.stdout.write('\n')
                val = ord(dat[row * cols + col])
                bl = val.bit_length()
                if bl <= 0:
                    c = ' '
                elif bl <= 3:
                    c = '.'
                elif bl <= 6:
                    c = ':'
                else:
                    c = '='
                sys.stdout.write(c)
            sys.stdout.write('\n')
        sys.stdout.flush()
        
        time.sleep(0.1)
        bini += 1


