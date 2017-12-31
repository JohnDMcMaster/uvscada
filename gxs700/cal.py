import Image
import PIL.ImageOps
import numpy as np
import glob
import os

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Correct images against darkfield and flat field capture')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('df_png', help='Dark field .png ("force capture")')
    parser.add_argument('ff_png', help='Flat field .png ("no sample")')
    parser.add_argument('din', help='Input directory or file')
    parser.add_argument('dout', help='Output directory or file')

    args = parser.parse_args()

    im_df = Image.open(args.df_png)
    im_ff = Image.open(args.ff_png)
    
    # Take the min and max from the two sets to use as our low and high scalars
    np_df2 = np.array(im_df)
    np_ff2 = np.array(im_ff)

    # ff *should* be brighter than df
    # (due to .png pixel value inversion convention)
    mins = np.minimum(np_df2, np_ff2)
    maxs = np.maximum(np_df2, np_ff2)

    if not os.path.exists(args.dout):
        os.mkdir(args.dout)

    for fn_in in glob.glob(args.din + '/*.png'):
        print 'Processing %s' % fn_in
        im_in = Image.open(fn_in)
        np_in2 = np.array(im_in)
        np_scaled = 0xFFFF * (np_in2 - mins) / (maxs - mins)
        imc = Image.fromarray(np_scaled).convert("I")
        imc.save(os.path.join(args.dout, os.path.basename(fn_in)))
