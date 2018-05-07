#!/usr/bin/env python

from PIL import Image
import glob
import os
import numpy as np

'''
cap_00000_dark_0.jpg
cap_00000_dark_1.jpg
cap_00000_dark_2.jpg
cap_00000_dark_3.jpg
cap_00000_dark_4.jpg
cap_00000_dark_5.jpg
cap_00000_dark_6.jpg
cap_00000_dark_7.jpg
cap_00000_dark_8.jpg
cap_00000_dark_9.jpg
cap_00001_light_0.jpg
cap_00001_light_1.jpg
cap_00001_light_2.jpg
cap_00001_light_3.jpg
cap_00001_light_4.jpg
cap_00001_light_5.jpg
cap_00001_light_6.jpg
cap_00001_light_7.jpg
cap_00001_light_8.jpg
cap_00001_light_9.jpg
'''

def histeq_np(npim, nbr_bins=256):
    '''
    Given a numpy nD array (ie image), return a histogram equalized numpy nD array of pixels
    That is, return 2D if given 2D, or 1D if 1D
    '''

    # get image histogram
    imhist,bins = np.histogram(npim.flatten(), nbr_bins, normed=True)
    cdf = imhist.cumsum() #cumulative distribution function
    cdf = 0xFFFF * cdf / cdf[-1] #normalize

    # use linear interpolation of cdf to find new pixel values
    ret1d = np.interp(npim.flatten(), bins[:-1], cdf)
    return ret1d.reshape(npim.shape)

def run():
    quick = 0

    def write():
        print
        print 'Averaging averages'
        average_dark = np.average(image_dls['dark'], axis=0)
        average_light = np.average(image_dls['light'], axis=0)
    
        print 'Averaging averages'
        average_image = np.subtract(average_dark, average_light)
        if 1:
            hist_image = histeq_np(average_image, nbr_bins=256)
        else:
            hist_image = average_image
            hist_image = average_dark
        image_final = Image.fromarray(hist_image.astype('uint8'))
        image_final.save('out.jpg')
        print

    image_dls = {'dark': [], 'light':[]}
    dir_in = '2018-05-02_02_pic16c57'
    dir_out = dir_in + '.out'
    if not os.path.exists(dir_out):
        os.mkdir(dir_out)
    #for fn in sorted(glob.glob(dir_in + '/*.jpg')):
    #    pass
    capi = 0
    mode, mode_next = 'dark', 'light'
    write_next = 2
    print 'Averaging image bursts'
    while True:
        if quick and len(image_dls['dark']) > 3:
            break

        images = []
        while True:
            if quick and len(images) > 3:
                break
            fn = '%s/cap_%05u_%s_%u.jpg' % (dir_in, capi, mode, len(images))
            if not os.path.exists(fn):
                break
            try:
                im = Image.open(fn)
            except:
                print 'WARNING: bad image load'
                break
            # Image.fromarray(np.array(im))
            images.append(im)
        print 'Run %d_%s len %d' % (capi, mode, len(images))

        #print '%d images' % len(images)
        if len(images) == 0:
            break
        arrays = [np.array(image) for image in images]
        average_image = np.average(arrays, axis=0)
        #print len(average_image), len(average_image[0])
        #assert len(average_image) == len(arrays[0])
        #Image.fromarray(average_image.astype('uint8'))
        image_dls[mode].append(average_image)

        capi += 1
        mode, mode_next = mode_next, mode
        if capi >= write_next:
            write()
            write_next *= 2
    write()

if __name__ == '__main__':
    import argparse
    run()
