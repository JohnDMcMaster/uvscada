import time
import libusb1
import bp1410_fw_fx2
from uvscada.usb import usb_wraps

def load_fx2(dev):
    _bulkRead, _bulkWrite, _controlRead, controlWrite = usb_wraps(dev)

    # hold fx2 in reset
    # Generated from packet 129/130
    controlWrite(0x40, 0xA0, 0xE600, 0x0000, "\x01")
    time.sleep(0.005)


    #print 'return'
    #return
    
    
    '''
    Load firmware
    What is the difference between 0xB0 and 0xA0 requests?
    odd phase shift
    -rw-r--r-- 1 root     root     1023 Apr 22 22:11 p131.bin
    -rw-r--r-- 1 root     root     1023 Apr 22 22:11 p133.bin
    -rw-r--r-- 1 root     root     1023 Apr 22 22:11 p135.bin
    -rw-r--r-- 1 root     root     1000 Apr 22 22:11 p137.bin
    '''    
    # Generated from packet 131/132
    #open('p131.bin', 'w').write(p131)
    controlWrite(0x40, 0xA0, 0x0000, 0x0000, bp1410_fw_fx2.p131)
    # odd...why are they writing the serial number out?
    # Generated from packet 133/134
    #open('p133.bin', 'w').write(p133)
    controlWrite(0x40, 0xA0, 0x03FF, 0x0000, bp1410_fw_fx2.p133)
    # Generated from packet 135/136
    #open('p135.bin', 'w').write(p135)
    controlWrite(0x40, 0xA0, 0x07FE, 0x0000, bp1410_fw_fx2.p135)
    # Generated from packet 137/138
    #open('p137.bin', 'w').write(p137)
    controlWrite(0x40, 0xA0, 0x0BFD, 0x0000, bp1410_fw_fx2.p137)

    time.sleep(0.003)
    
    # Generated from packet 139/140
    # release fx2 reset, resetting mcu
    controlWrite(0x40, 0xA0, 0xE600, 0x0000, "\x00")

