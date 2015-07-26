#!/usr/bin/env python
from ctypes import *
import mu800

if __name__ == "__main__":
    print 'main'
    print 'Taking raw image'
    img = mu800.raw_image()
    print 'Took image'
    mu800.decode(img)
    print 'Done'
    
