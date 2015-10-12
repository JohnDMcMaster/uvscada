import binascii
import time
import usb1
import libusb1
import sys
import struct

from uvscada.wps7 import WPS7

from uvscada.usb import usb_wraps
from uvscada.bpm.bp1410_fw import load_fx2
from uvscada.bpm import bp1410_fw_sn, startup
from uvscada.bpm.startup import bulk2, bulk86
from uvscada.util import hexdump, add_bool_arg
from uvscada.util import str2hex
from uvscada.usb import validate_read, validate_readv

def dexit():
    print 'Debug break'
    sys.exit(0)

def open_dev(usbcontext=None):
    if usbcontext is None:
        usbcontext = usb1.USBContext()
    
    print 'Scanning for devices...'
    for udev in usbcontext.getDeviceList(skip_on_error=True):
        vid = udev.getVendorID()
        pid = udev.getProductID()
        if (vid, pid) == (0x14b9, 0x0001):
            print
            print
            print 'Found device'
            print 'Bus %03i Device %03i: ID %04x:%04x' % (
                udev.getBusNumber(),
                udev.getDeviceAddress(),
                vid,
                pid)
            return udev.open()
    raise Exception("Failed to find a device")

def replay_setup(dev):
    bulkRead, bulkWrite, controlRead, controlWrite = usb_wraps(dev)


    # Verified that control request allows bulk to be read
    # Generated from packet 281/282
    # None (0xB0)
    buff = controlRead(0xC0, 0xB0, 0x0000, 0x0000, 4096)
    # NOTE:: req max 4096 but got 3
    validate_read("\x00\x00\x00", buff, "packet 281/282")
    buff = bulk86(dev, target=1)
    validate_read("\x16", buff, "packet 283/284")
    
    # Generated from packet 285/286
    buff = bulk2(dev, "\x01", target=0x85)
    validate_readv((
              "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24"
              "\x00\x00\x30\x00\x83\x00\x30\x01\x09\x00\xC0\x00\x00\x00\x09\x00"
              "\x08\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00"
              "\xD0\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55"
              "\x01\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00"
              "\x00\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00"
              "\x01\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46"
              "\x00\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11"
              "\x00\x00\xC0\x1E\x00\x00",

            "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24\x00" \
            "\x00\x30\x00\x83\x00\x30\x01\x09\x00\xC0\x00\x00\x00\x09\x00\x08" \
            "\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00\xD0" \
            "\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55\x01" \
            "\x00\x00\x00\x00\x00\x02\x00\x80\x01\xC0\x01\x02\x00\x01\x00\x00" \
            "\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00\x01" \
            "\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46\x00" \
            "\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11\x00" \
            "\x00\xC0\x1E\x00\x00"),
              
              buff, "packet 287/288")
    
    # Generated from packet 289/290
    buff = bulk2(dev, "\x43\x19\x00\x00\x00\x3B\x7E\x25\x00\x00\xFE\xFF\x3B\x7C\x25\x00"
              "\x00\xFE\xFF\x00", target=2)
    validate_read("\xA4\x06", buff, "packet 291/292")
    
    # Generated from packet 293/294
    buff = bulk2(dev, "\x01", target=0x85)
    validate_readv((
              "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24"
              "\x00\x00\x30\x00\x83\x00\x30\x01\x09\x00\xC0\x00\x00\x00\x09\x00"
              "\x08\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00"
              "\xD0\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55"
              "\x01\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00"
              "\x00\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00"
              "\x01\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46"
              "\x00\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11"
              "\x00\x00\xC0\x1E\x00\x00",
              
            "\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24\x00" \
            "\x00\x30\x00\x83\x00\x30\x01\x09\x00\xC0\x00\x00\x00\x09\x00\x08" \
            "\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00\xD0" \
            "\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55\x01" \
            "\x00\x00\x00\x00\x00\x02\x00\x80\x01\xC0\x01\x02\x00\x01\x00\x00" \
            "\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00\x01" \
            "\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46\x00" \
            "\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11\x00" \
            "\x00\xC0\x1E\x00\x00"
              ), buff, "packet 295/296")
    
    # Generated from packet 297/298
    buff = bulk2(dev, "\x0E\x00", target = 0x20)
    validate_read("\x3A\x00\x90\x32\xA7\x02\x2A\x86\x01\x95\x3C\x36\x90\x00\x1F"
              "\x00\x01\x00\xD6\x05\x01\x00\x72\x24\x22\x39\x00\x00\x00\x00\x27"
              "\x1F", buff, "packet 299/300")
    
    # Generated from packet 301/302
    buff = bulk2(dev, "\x14\x38\x25\x00\x00\x04\x00\x90\x32\x90\x00\xA7\x02\x1F\x00\x14"
              "\x40\x25\x00\x00\x01\x00\x3C\x36\x0E\x01", target=0x20)
    validate_read("\x14\x00\x54\x41\x38\x34\x56\x4C\x56\x5F\x46\x58\x34\x00\x00"
              "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x3E"
              "\x2C", buff, "packet 303/304")
    
    # Generated from packet 305/306
    buff = bulk2(dev, "\x03", target=2)
    validate_read("\x31\x00", buff, "packet 307/308")
    
    # Generated from packet 309/310
    buff = bulk2(dev, "\x03", target=2)
    validate_read("\x31\x00", buff, "packet 311/312")
    
    # Generated from packet 313/314
    buff = bulk2(dev, "\x0E\x02", target=0x20)
    validate_read("\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
              "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
              "\xFF", buff, "packet 315/316")
    
    # Generated from packet 317/318
    buff = bulk2(dev, "\x01", target=0x85)
    validate_read("\x84\xA4\x06\x02\x00\x26\x00\x43\x00\xC0\x03\x00\x08\x10\x24"
              "\x00\x00\x30\x00\x83\x00\x30\x01\x09\x00\xC0\x00\x00\x00\x09\x00"
              "\x08\x00\xFF\x00\xC4\x1E\x00\x00\xCC\x1E\x00\x00\xB4\x46\x00\x00"
              "\xD0\x1E\x00\x00\xC0\x1E\x01\x00\xB0\x1E\x01\x00\x00\x00\x30\x55"
              "\x01\x00\x00\x00\x00\x00\x02\x00\x80\x01\xD0\x01\x02\x00\x01\x00"
              "\x00\x00\x56\x10\x00\x00\xA0\x25\x00\x00\x84\x25\x00\x00\x00\x00"
              "\x01\x00\x7C\x25\x00\x00\x7E\x25\x00\x00\x80\x25\x00\x00\x74\x46"
              "\x00\x00\x38\x11\x00\x00\x3C\x11\x00\x00\x40\x11\x00\x00\x44\x11"
              "\x00\x00\xC0\x1E\x00\x00", buff, "packet 319/320")

    # Generated from packet 321/322
    bulkWrite(0x02, "\x43\x19\x00\x00\x00")
    
    # Generated from packet 323/324
    bulkWrite(0x02, "\x20\x01\x00\x0C\x04")
    
    # Generated from packet 325/326
    bulkWrite(0x02, "\x41\x00\x00")
    
    # Generated from packet 327/328
    buff = bulk2(dev, "\x10\x80\x02", target=6)
    validate_read("\x80\x00\x00\x00\x09\x00", buff, "packet 329/330")
    
    # Generated from packet 331/332
    buff = bulk2(dev, "\x45\x01\x00\x00\x31\x00\x06", target=0x64)
    validate_read("\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
              "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
              "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
              "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
              "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
              "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
              "\xFF\xFF\xFF\xFF\xFF", buff, "packet 333/334")
    
    # Generated from packet 335/336
    buff = bulk2(dev, "\x49", target=2)
    validate_read("\x0F\x00", buff, "packet 337/338")
    
    # Generated from packet 339/340
    buff = bulk2(dev, "\x03", target=2)
    # failing this messes up state
    validate_readv(("\x31\x00", '\x71\x00'), buff, "packet 341/342")
    
    # Generated from packet 343/344
    buff = bulk2(dev, "\x03", target=2)
    validate_readv(("\x31\x00", '\x71\x00'), buff, "packet 345/346")

    '''
    For kicks tried:
    bulk2(dev, "\x0E\x01", target=0x20)
    00000000  14 00 54 41 38 34 56 4C  56 5F 46 58 34 00 00 00  |..TA84VLV_FX4...|
    TA84VLV_FX4
    Is this some sort of special FX4 socket configuration?
    Looks like an EEPROM read
    maybe just reading some random memory buffer though
    '''
    
    # Generated from packet 347/348
    buff = bulk2(dev, "\x0E\x02", target=0x20)
    validate_read("\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
              "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
              "\xFF", buff, "packet 349/350")
    
    # Generated from packet 351/352
    bulkWrite(0x02, "\x3B\x0C\x22\x00\xC0\x40\x00\x3B\x0E\x22\x00\xC0\x00\x00\x3B\x1A"
              "\x22\x00\xC0\x18\x00")
    
    # Generated from packet 353/354
    buff = bulk2(dev, "\x4A\x03\x00\x00\x00", target=2)
    validate_read("\x03\x00", buff, "packet 355/356")
    
    # Generated from packet 357/358
    bulkWrite(0x02, "\x4C\x00\x02")
    
    # Generated from packet 359/360
    # None (0xB2)
    controlWrite(0x40, 0xB2, 0x0000, 0x0000, "")
    
    # Generated from packet 361/362
    bulkWrite(0x02, "\x50\x45\x00\x00\x00")
    
    # Generated from packet 363/364
    buff = bulk2(dev,
              "\xE9\x03\x00\x00\x00\x90\x00\x00\xE9\x03\x00\x00\x00\x90\x01\x10"
              "\xE9\x03\x00\x00\x00\x90\x00\x00\xE9\x03\x00\x00\x00\x90\x01\x80"
              "\xE9\x02\x00\x00\x00\x90\x00\xE9\x04\x00\x00\x00\x00\x00\x00\x00"
              "\xE9\x03\x00\x00\x00\x90\x00\x00\x66\xB9\x00\x00\xB2\x00\xFB\xFF"
              "\x25\x44\x11\x00\x00",
              target=2, truncate=True)
    validate_read("\x80\x00", buff, "packet 365/366")
    
    # Generated from packet 367/368
    buff = bulk2(dev, "\x02", target=6, truncate=True)
    validate_read("\x81\x00\x50\x00\x09\x00", buff, "packet 369/370")
    
    # Generated from packet 371/372
    bulkWrite(0x02, "\x50\xC0\x00\x00\x00")
    
    # Generated from packet 373/374
    buff = bulk2(dev,
              "\x66\xB8\x01\x2D\x81\xE3\xFF\xFF\x00\x00\x66\xBB\x18\x00\x66\xC7"
              "\x05\x30\x40\x00\xC0\xF0\xFF\x89\xD9\xC1\xE1\x02\x66\xC7\x81\x02"
              "\x00\x00\x00\xF0\xFF\x66\x03\x05\xE4\x46\x00\x00\x66\x89\x05\x90"
              "\x40\x00\xC0\x89\xDA\x81\xCA\x00\x80\x00\x00\x66\x89\x15\x50\x40"
              "\x00\xC0\xC6\x05\x14\x22\x00\xC0\x7B\x81\xCA\x00\x40\x00\x00\x66"
              "\x89\x15\x50\x40\x00\xC0\x89\xD9\x66\xC1\xE1\x02\x66\x89\x81\x00"
              "\x00\x00\x00\x66\x2B\x05\xE4\x46\x00\x00\xC6\x05\x14\x22\x00\xC0"
              "\xBB\x81\xCB\x00\x80\x00\x00\x66\x89\x1D\x50\x40\x00\xC0\x89\xC2"
              "\x81\xE2\x07\x00\x00\x00\x03\xD2\x81\xCA\x01\x00\x00\x00\x89\xD9"
              "\x81\xE1\x03\x00\x00\x00\xD3\xE2\xD3\xE2\xD3\xE2\xD3\xE2\xD3\xE2"
              "\xC1\xE2\x0A\x89\xD9\x81\xE1\xFC\x03\x00\x00\x09\xCA\x88\x82\x00"
              "\x00\x00\x40\x66\xB9\x00\x00\xB2\x00\xFB\xFF\x25\x44\x11\x00\x00",
              target=2, truncate=True)
    validate_read("\x81\x00", buff, "packet 375/376")
    
    # Generated from packet 377/378
    buff = bulk2(dev, "\x02", target=6, truncate=True)
    validate_read("\x82\x00\x10\x01\x09\x00", buff, "packet 379/380")
    
    # Generated from packet 381/382
    buff = bulk2(dev, "\x04\x63\x05\x72\x06\x69\x07\x70\x08\x74\x09\x20\x0A\x74\x0B\x79"
              "\x57\x81\x00\x0C\x02\x30", target=2, truncate=True)
    validate_read("\x02\x00", buff, "packet 383/384")

    # When paired with below looping fails on average maybe about 3 iterations
    # (about 1 - 8 observed)
    # 31/71 bit changes
    # Generated from packet 385/386
    buff = bulk2(dev, "\x20\x01\x00\x2B\x3B\x0C\x22\x00\xC0\x40\x00\x3B\x0E\x22\x00\xC0"
              "\x00\x00\x3B\x1A\x22\x00\xC0\x18\x00\x0E\x01", target=0x20, truncate=True)
    validate_read(
              "\x14\x00\x54\x41\x38\x34\x56\x4C\x56\x5F\x46\x58\x34\x00\x00"
              "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x3E"
              "\x2C",
              buff, "packet 387/388")
        
    # 30k iterations by itself and always passes
    # Generated from packet 389/390
    buff = bulk2(dev, "\x03", target=2, truncate=True)
    validate_readv(("\x31\x00", "\x71\x00"), buff, "packet 391/392")
    
    # Generated from packet 393/394
    buff = bulk2(dev, "\x03", target=2, truncate=True)
    validate_readv(("\x31\x00", "\x71\x00"), buff, "packet 395/396")
    
    # Generated from packet 397/398
    buff = bulk2(dev, "\x0E\x02", target=0x20, truncate=True)
    validate_read(
              "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
              "\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
              "\xFF",
              buff, "packet 399/400")
    
    # Generated from packet 401/402
    bulkWrite(0x02, "\x48\x00\x20\x00\x00\x50\x12\x00\x00\x00")
    
    # Generated from packet 403/404
    buff = bulk2(dev, 
              "\x00\x00\x00\x00\x04\x00\x08\x00\x0C\x00\x10\x00\x14\x00\x18\x00"
              "\x1C\x00",
              target=2, truncate=True)
    validate_read("\x82\x00", buff, "packet 405/406")
    
    # Generated from packet 407/408
    buff = bulk2(dev, "\x02", target=6, truncate=True)
    validate_read("\x83\x00\x30\x01\x09\x00", buff, "packet 409/410")
    
    # Generated from packet 411/412
    buff = bulk2(dev,
              "\x1D\x10\x01\x09\x00\x00\x00\x15\x60\x00\x00\x00\x00\x00\x00\x00"
              "\x00\x00\x00\x00\x00\x00\x1C\x00\x00\x48\x00\x12\xAA",
              target=1, truncate=True)
    validate_read("\xAB", buff, "packet 413/414")

scalars = {
    # -3.5V: leftover after below
    # also gave a weird value when I tried to scale other ADCs
    0x01: -3.476 / 0x38F0,
    # 30V:  best guess based on scaling other readings
    0x10: 37.28 / 0xBA70,
    # -5V: best guess based on scaling other readings
    0x05: -4.93 / 0x31D0,
    # 0V: very likely based on 0 reading
    0x15: 37.28 / 0xBA70,
    # +5V: reasonable confidence
    # removing, reconnecting J1 shifts +5V by 100 mV or so as well as +15V, and +35V
    # +15V and +35V are already known and this was already suspected to be +5V
    0x0c: 5.44 / 0x3310,
    # 15V: confident
    # Disconnecting causes this to go up by 1.5 times, no other channel changes
    # (good thing it didn't damage anything...)
    0x09: 16.00 / 0xA050,
    # 35V: confident
    # Tapped line and varied voltage to confirm is 35V
    # Calibrated with meter
    # I can hear a SMPS moving with voltage
    # meter: 29.76
    #   0x9430 (29.632 V)
    #   0x9420 (29.619 V)
    #   0x9430 (29.632 V)
    0x14: 29.76 / 0x9430,
}

def read_adc(dev):
    bulkRead, bulkWrite, _controlRead, _controlWrite = usb_wraps(dev)

    print 'WARNING: best guess'
    for reg in (0x01, 0x10, 0x05, 0x15, 0x0C, 0x09, 0x14):
        print '0x%02X' % reg
        for i in xrange(3):
            buff = bulk2(dev, "\x19" + chr(reg) + "\x00", target=2, truncate=True)
            b = struct.unpack('<H', buff)[0]
            print '  0x%04X (%0.3f V)' % (b, scalars[reg] * b)

def cleanup_adc(dev):
    _bulkRead, bulkWrite, _controlRead, _controlWrite = usb_wraps(dev)
    
    # Generated from packet 1220/1221
    bulkWrite(0x02, "\x50\x1A\x00\x00\x00")
    
    # Generated from packet 1222/1223
    buff = bulk2(dev,
            "\x66\xB9\x00\x00\xB2\x02\xFB\xFF\x25\x44\x11\x00\x00\x66\xB9\x00"
            "\x00\xB2\x02\xFB\xFF\x25\x44\x11\x00\x00",
            target=2, truncate=True)
    validate_read("\x83\x00", buff, "packet 1224/1225")
    
    # Generated from packet 1226/1227
    buff = bulk2(dev, "\x02", target=6, truncate=True)
    validate_read("\x84\x00\x50\x01\x09\x00", buff, "packet 1228/1229")
    
    # Generated from packet 1230/1231
    buff = bulk2(dev, "\x57\x83\x00", target=2, truncate=True)
    validate_read("\x00\x00", buff, "packet 1232/1233")
    
    # Generated from packet 1234/1235
    buff = bulk2(dev, "\x0C\x04\x30", target=2, truncate=True)
    validate_read("\x04\x00", buff, "packet 1236/1237")

if __name__ == "__main__":
    import argparse 
    
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    add_bool_arg(parser, '--cycle', default=False, help='') 
    args = parser.parse_args()

    if args.cycle:
        print 'Cycling'
        wps = WPS7(host='raijin')
        wps.cycle([1, 2], t=2.0)
        # 1 second too short
        time.sleep(3)
        print 'Cycled'

    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext)
    dev.claimInterface(0)
    #dev.resetDevice()
    startup.replay(dev)

    print
    print
    # didn't fix 17/18 issue
    #time.sleep(5)
    print
    
    if 0:
        replay_setup(dev)
        read_adc(dev)
    if 1:
        import os

        replay_setup(dev)
        try:
            while True:
                os.system('clear')
                read_adc(dev)
                time.sleep(0.2)
        finally:
            print 'Cleaning up on exit'
            cleanup_adc(dev)

    if 0:
        import curses
        import atexit
        
        @atexit.register
        def goodbye():
            """ Reset terminal from curses mode on exit """
            curses.nocbreak()
            if stdscr:
                stdscr.keypad(0)
            curses.echo()
            curses.endwin()        

        stdscr = curses.initscr()
        replay_setup(dev)
        while True:
            stdscr.clear()
            read_adc(dev)
            time.sleep(0.2)
        
    print 'Complete'
