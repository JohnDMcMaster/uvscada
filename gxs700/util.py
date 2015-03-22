# https://github.com/vpelletier/python-libusb1
# Python-ish (classes, exceptions, ...) wrapper around libusb1.py . See docstrings (pydoc recommended) for usage.
import usb1
# Bare ctype wrapper, inspired from library C header file.
import libusb1
import sys
import load_firmware

pidvid2name = {
        #(0x5328, 0x2009): 'Dexis Platinum (pre-enumeration)'
        # note: load_firmware.py loads the gendex firmware
        (0x5328, 0x2030): 'Gendex GXS700 (post enumeration)'
        #(0x5328, 0x202F): 'Gendex GXS700 (pre-enumeration)'
        }

def check_device(usbcontext=None):
    if usbcontext is None:
        usbcontext = usb1.USBContext()
    
    for udev in usbcontext.getDeviceList(skip_on_error=True):
        vid = udev.getVendorID()
        pid = udev.getProductID()
        if (vid, pid) in pidvid2name.keys():
            print
            print
            print 'Found device'
            print 'Bus %03i Device %03i: ID %04x:%04x' % (
                udev.getBusNumber(),
                udev.getDeviceAddress(),
                vid,
                pid)
            return udev
    return None

def open_dev(usbcontext=None):
    '''
    Return a device with the firmware loaded
    '''
    
    if usbcontext is None:
        usbcontext = usb1.USBContext()
    
    print 'Checking if firmware load is needed'
    if load_firmware.load_all(wait=True):
        pass
    else:
        print 'Firmware load not needed'
    
    print 'Scanning for devices...'
    udev = check_device(usbcontext)
    if udev is None:
        raise Exception("Failed to find a device")

    dev = udev.open()
    return dev

def hexdumps(*args, **kwargs):
    '''Hexdump by returning a string'''
    buff = StringIO.StringIO()
    kwargs['f'] = buff
    hexdump(*args, **kwargs)
    return buff.getvalue()

def hexdump(data, label=None, indent='', address_width=8, f=sys.stdout):
    def isprint(c):
        return c >= ' ' and c <= '~'

    bytes_per_half_row = 8
    bytes_per_row = 16
    data = bytearray(data)
    data_len = len(data)
    
    def hexdump_half_row(start):
        left = max(data_len - start, 0)
        
        real_data = min(bytes_per_half_row, left)

        f.write(''.join('%02X ' % c for c in data[start:start+real_data]))
        f.write(''.join('   '*(bytes_per_half_row-real_data)))
        f.write(' ')

        return start + bytes_per_half_row

    pos = 0
    while pos < data_len:
        row_start = pos
        f.write(indent)
        if address_width:
            f.write(('%%0%dX  ' % address_width) % pos)
        pos = hexdump_half_row(pos)
        pos = hexdump_half_row(pos)
        f.write("|")
        # Char view
        left = data_len - row_start
        real_data = min(bytes_per_row, left)

        f.write(''.join([c if isprint(c) else '.' for c in str(data[row_start:row_start+real_data])]))
        f.write((" " * (bytes_per_row - real_data)) + "|\n")

