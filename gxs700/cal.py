'''
cal file bytes
4576404

height = 1850
width = 1344
depth = 2
1850 * 1344 * 2 = 4972800

cal file 4576404
Sensor:  4972800

1346 x 1700
1346 * 1700 * 2
4576400
give it a try...
'''

from PIL import Image
import binascii
from uvscada.gxs700_util import histeq

if __name__ == "__main__":
    import argparse 
    
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--hist-eq', '-e', action='store_true', help='Equalize histogram')
    parser.add_argument('fin', help='File name in')
    parser.add_argument('fout', default=None, nargs='?', help='File name out')
    args = parser.parse_args()

    # 2103231663
    # 0x7d5cc4af
    buff = open(args.fin).read()
    header = buff[0:4]
    print 'Header: %s' % binascii.hexlify(header)
    
    raw = buff[4:]
    if args.hist_eq:
        print 'Equalizing histogram...'
        raw = histeq(raw, width=1346, height=1700)
    # http://effbot.org/imagingbook/decoder.htm
    im = Image.frombytes(
            "F", (1346, 1700), raw, "raw", "F;16")
            
    if args.fout:
        im2 = im.convert('I').save(args.fout)
    else:
        im.show()
