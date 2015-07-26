'''
USB 2.0 max speed: 480 Mbps => 60 MB/s
frame size: 4972800 bytes ~= 5 MB/s
never going to get faster than 12 frames per second from data bottleneck
integration time and other issues will make it actually take much longer

max is about 1/3 fps
State 2 to state 4
    frame1.cap: 10.547345 - 10.237953 = 0.309392
    frame2.cap: 4.093158 - 3.784668 =   0.30849
state 4 to state 8
    frame1.cap: 12.547843 - 10.547345 = 2.000498 seconds
    frame2.cap: 6.092412 - 4.093158 = 1.999254 seconds
bulk transfer
    not checked
from state 2 to end of bulk
    frame1.cap: 13.221687 - 10.237953 = 2.983734
    frame2.cap: 6.773520 - 3.784668 = 2.988852

Currently this code takes about 4.7 sec to capture an image
(with bulking taking much longer than it should)
we should be able to get it down to at least 3
'''

# https://github.com/vpelletier/python-libusb1
# Python-ish (classes, exceptions, ...) wrapper around libusb1.py . See docstrings (pydoc recommended) for usage.
import usb1
# Bare ctype wrapper, inspired from library C header file.
import libusb1
import binascii
import sys
import argparse
import time
from util import open_dev
import os
from uvscada import gxs700

def validate_read(expected, actual, msg, ignore_errors=False):
    if expected != actual:
        print 'Failed %s' % msg
        print '  Expected; %s' % binascii.hexlify(expected,)
        print '  Actual:   %s' % binascii.hexlify(actual,)
        if not ignore_errors:
            raise Exception('failed validate: %s' % msg)

def replay_449_768(gxs):
    # Generated from packet 449/450
    #buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    #validate_read("\x05\x40\x07\x3A", buff, "packet 449/450")
    # Generated from packet 451/452
    #buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    #validate_read("\x05\x40\x07\x3A", buff, "packet 451/452")
    # 1344 x 1850
    if gxs.img_wh() != (0x0540, 0x073A):
        raise Exception("Unexpected w/h")
    
    '''
    FIXME: fails verification if already ran
    Failed packet 453/454
      Expected; 0000
      Actual:   0001
    '''
    # Generated from packet 453/454
    #buff = dev.controlRead(0xC0, 0xB0, 0x0003, 0x2002, 2)
    #validate_read("\x00\x00", buff, "packet 453/454", True)
    # sometimes this fails...why?
    if gxs.fpga_r(0x2002) != 0x0000:
        print "WARNING: bad FPGA read"
    
    # Generated from packet 455/456
    #buff = dev.controlRead(0xC0, 0xB0, 0x0004, 0x0000, 2)
    #validate_read("\x12\x34", buff, "packet 455/456")
    if gxs.fpga_rsig() != 0x1234:
        raise Exception("Invalid FPGA signature")
    
    # Generated from packet 457/458
    gxs.fpga_wv2(0x0400, "\x00\x00\x60\x00\x00\x00")
    # Generated from packet 459/460
    gxs.fpga_wv2(0x0404, "\x00\xE5\xC0\x00\x00\x00")
    # Generated from packet 461/462
    gxs.fpga_wv2(0x0408, "\x00\xF7\x20\x00\x00\x01")
    # Generated from packet 463/464
    gxs.fpga_wv2(0x040C, "\x00\xE5\x80\x00\x00\x01")
    # Generated from packet 465/466
    gxs.fpga_wv2(0x0410, "\x00\xF7\xE0\x00\x00\x01")
    # Generated from packet 467/468
    gxs.fpga_wv2(0x0414, "\x00\xE5\xA0\x00\x00\x02")
    # Generated from packet 469/470
    gxs.fpga_wv2(0x0418, "\x00\xC5\x20\x00\x00\x04")
    # Generated from packet 471/472
    gxs.fpga_wv2(0x041C, "\x00\x05\x38\x00\x00\x04")
    # Generated from packet 473/474
    gxs.fpga_wv2(0x0420, "\x00\x04\x98\x00\x00\x04")
    # Generated from packet 475/476
    gxs.fpga_wv2(0x0424, "\x00\x00\xF8\x02\x00\x0C")
    # Generated from packet 477/478
    gxs.fpga_wv2(0x0428, "\x08\x00\x3F\x00\x00\x00")
    # Generated from packet 479/480
    gxs.fpga_wv2(0x042C, "\x08\x00\x42\x04\x00\x00")
    # Generated from packet 481/482
    gxs.fpga_wv2(0x0430, "\x08\x04\x4B\x04\x00\x00")
    # Generated from packet 483/484
    gxs.fpga_wv2(0x0434, "\x08\x06\x54\x04\x00\x00")
    # Generated from packet 485/486
    gxs.fpga_wv2(0x0438, "\x08\x04\x5D\x04\x00\x00")
    # Generated from packet 487/488
    gxs.fpga_wv2(0x043C, "\x08\x06\x66\x04\x00\x00")
    # Generated from packet 489/490
    gxs.fpga_wv2(0x0440, "\x08\x04\x6F\x04\x00\x00")
    # Generated from packet 491/492
    gxs.fpga_wv2(0x0444, "\x08\x00\x72\x04\x00\x00")
    # Generated from packet 493/494
    gxs.fpga_wv2(0x0448, "\x08\x01\x78\x04\x00\x00")
    # Generated from packet 495/496
    gxs.fpga_wv2(0x044C, "\x08\x03\x7E\x04\x00\x00")
    # Generated from packet 497/498
    gxs.fpga_wv2(0x0450, "\x08\x01\x84\x04\x00\x00")
    # Generated from packet 499/500
    gxs.fpga_wv2(0x0454, "\x08\xC3\x8A\x04\x00\x00")
    # Generated from packet 501/502
    gxs.fpga_wv2(0x0458, "\x08\xC1\x90\x04\x00\x00")
    # Generated from packet 503/504
    gxs.fpga_wv2(0x045C, "\x08\xC0\x96\x04\x00\x00")
    # Generated from packet 505/506
    gxs.fpga_wv2(0x0460, "\x08\xC2\x9C\x04\x00\x00")
    # Generated from packet 507/508
    gxs.fpga_wv2(0x0464, "\x08\xC0\xA2\x04\x00\x08")
    # Generated from packet 509/510
    gxs.fpga_wv2(0x0468, "\x08\x42\x06\x04\x00\x00")
    # Generated from packet 511/512
    gxs.fpga_wv2(0x046C, "\x08\x00\x0C\x04\x00\x00")
    # Generated from packet 513/514
    gxs.fpga_wv2(0x0470, "\x08\x82\x12\x04\x00\x00")
    # Generated from packet 515/516
    gxs.fpga_wv2(0x0474, "\x08\x00\x18\x04\x00\x08")
    # Generated from packet 517/518
    gxs.fpga_wv2(0x0478, "\x0F\x42\x18\x04\x00\x00")
    # Generated from packet 519/520
    gxs.fpga_wv2(0x047C, "\x0F\x02\x22\x04\x00\x00")
    # Generated from packet 521/522
    gxs.fpga_wv2(0x0480, "\x0E\x02\x6A\x04\x00\x00")
    # Generated from packet 523/524
    gxs.fpga_wv2(0x0484, "\x0A\x02\x6F\x04\x00\x00")
    # Generated from packet 525/526
    gxs.fpga_wv2(0x0488, "\x0A\x82\x87\x04\x00\x00")
    # Generated from packet 527/528
    gxs.fpga_wv2(0x048C, "\x0A\x02\xFF\x04\x00\x00")
    # Generated from packet 529/530
    gxs.fpga_wv2(0x0490, "\x08\x02\x04\x04\x00\x09")
    # Generated from packet 531/532
    gxs.fpga_wv2(0x0494, "\x08\x20\x09\x04\x00\x00")
    # Generated from packet 533/534
    gxs.fpga_wv2(0x0498, "\x08\x30\x12\x04\x00\x00")
    # Generated from packet 535/536
    gxs.fpga_wv2(0x049C, "\x08\x20\x1B\x04\x00\x00")
    # Generated from packet 537/538
    gxs.fpga_wv2(0x04A0, "\x08\x30\x24\x04\x00\x00")
    # Generated from packet 539/540
    gxs.fpga_wv2(0x04A4, "\x08\x20\x2D\x04\x00\x00")
    # Generated from packet 541/542
    gxs.fpga_wv2(0x04A8, "\x08\x00\x36\x04\x00\x00")
    # Generated from packet 543/544
    gxs.fpga_wv2(0x04AC, "\x08\x0A\x3F\x04\x00\x00")
    # Generated from packet 545/546
    gxs.fpga_wv2(0x04B0, "\x08\x1A\x48\x04\x00\x00")
    # Generated from packet 547/548
    gxs.fpga_wv2(0x04B4, "\x08\x0A\x51\x04\x00\x00")
    # Generated from packet 549/550
    gxs.fpga_wv2(0x04B8, "\x08\x1A\x5A\x04\x00\x00")
    # Generated from packet 551/552
    gxs.fpga_wv2(0x04BC, "\x08\x0A\x63\x04\x00\x00")
    # Generated from packet 553/554
    gxs.fpga_wv2(0x04C0, "\x08\x00\x64\x04\x00\x00")
    # Generated from packet 555/556
    gxs.fpga_wv2(0x04C4, "\x08\x10\x6C\x04\x00\x08")
    # Generated from packet 557/558
    gxs.fpga_wv2(0x04C8, "\x08\x10\x04\x0C\x00\x00")
    # Generated from packet 559/560
    gxs.fpga_wv2(0x04CC, "\x08\x00\x08\x0C\x00\x00")
    # Generated from packet 561/562
    gxs.fpga_wv2(0x04D0, "\x08\x10\x0C\x0C\x00\x00")
    # Generated from packet 563/564
    gxs.fpga_wv2(0x04D4, "\x08\x00\x10\x0C\x00\x08")
    # Generated from packet 565/566
    gxs.fpga_wv2(0x04D8, "\x08\x10\x09\x1C\x00\x00")
    # Generated from packet 567/568
    gxs.fpga_wv2(0x04DC, "\x08\x00\x12\x1C\x00\x00")
    # Generated from packet 569/570
    gxs.fpga_wv2(0x04E0, "\x08\x10\x1B\x1C\x00\x00")
    # Generated from packet 571/572
    gxs.fpga_wv2(0x04E4, "\x08\x00\x1C\x1C\x00\x00")
    # Generated from packet 573/574
    gxs.fpga_wv2(0x04E8, "\x08\x00\x24\x1D\x00\x08")
    # Generated from packet 575/576
    gxs.fpga_wv2(0x04EC, "\x08\x22\x3C\x00\x00\x00")
    # Generated from packet 577/578
    gxs.fpga_wv2(0x04F0, "\x08\x32\x78\x00\x00\x00")
    # Generated from packet 579/580
    gxs.fpga_wv2(0x04F4, "\x08\x22\xB4\x00\x00\x00")
    # Generated from packet 581/582
    gxs.fpga_wv2(0x04F8, "\x08\x32\xF0\x00\x00\x00")
    # Generated from packet 583/584
    gxs.fpga_wv2(0x04FC, "\x08\x22\x2C\x00\x00\x01")
    # Generated from packet 585/586
    gxs.fpga_wv2(0x0500, "\x08\x02\x35\x00\x00\x01")
    # Generated from packet 587/588
    gxs.fpga_wv2(0x0504, "\x08\x0A\x3E\x00\x00\x01")
    # Generated from packet 589/590
    gxs.fpga_wv2(0x0508, "\x08\x1A\x47\x00\x00\x01")
    # Generated from packet 591/592
    gxs.fpga_wv2(0x050C, "\x08\x0A\x4C\x00\x00\x01")
    # Generated from packet 593/594
    gxs.fpga_wv2(0x0510, "\x08\x1A\x50\x00\x00\x01")
    # Generated from packet 595/596
    gxs.fpga_wv2(0x0514, "\x08\x0A\x59\x00\x00\x01")
    # Generated from packet 597/598
    gxs.fpga_wv2(0x0518, "\x08\x02\x5E\x00\x00\x01")
    # Generated from packet 599/600
    gxs.fpga_wv2(0x051C, "\x08\x12\x66\x00\x00\x01")
    # Generated from packet 601/602
    gxs.fpga_wv2(0x0520, "\x08\x02\x67\x00\x00\x01")
    # Generated from packet 603/604
    gxs.fpga_wv2(0x0524, "\x08\x02\x6F\x01\x00\x09")
    # Generated from packet 605/606
    gxs.fpga_wv2(0x0528, "\x08\x00\x08\x0C\x00\x00")
    # Generated from packet 607/608
    gxs.fpga_wv2(0x052C, "\x08\x00\x10\x04\x00\x00")
    # Generated from packet 609/610
    gxs.fpga_wv2(0x0530, "\x08\x00\x18\x00\x00\x08")
    # Generated from packet 611/612
    gxs.fpga_wv2(0x0534, "\x08\x10\x09\x00\x00\x00")
    # Generated from packet 613/614
    gxs.fpga_wv2(0x0538, "\x08\x00\x12\x00\x00\x00")
    # Generated from packet 615/616
    gxs.fpga_wv2(0x053C, "\x08\x10\x1B\x00\x00\x00")
    # Generated from packet 617/618
    gxs.fpga_wv2(0x0540, "\x08\x00\x1C\x00\x00\x00")
    # Generated from packet 619/620
    gxs.fpga_wv2(0x0544, "\x08\x00\x24\x01\x00\x08")
    # Generated from packet 621/622
    gxs.fpga_wv2(0x0548, "\x08\x10\x09\x1C\x00\x00")
    # Generated from packet 623/624
    gxs.fpga_wv2(0x054C, "\x08\x00\x12\x1C\x00\x00")
    # Generated from packet 625/626
    gxs.fpga_wv2(0x0550, "\x08\x10\x1B\x1C\x00\x00")
    # Generated from packet 627/628
    gxs.fpga_wv2(0x0554, "\x08\x00\x1C\x1C\x00\x00")
    # Generated from packet 629/630
    gxs.fpga_wv2(0x0558, "\x08\x00\x24\x1D\x00\x08")
    # Generated from packet 631/632
    gxs.fpga_wv2(0x055C, "\x08\xC2\x06\x00\x00\x00")
    # Generated from packet 633/634
    gxs.fpga_wv2(0x0560, "\x08\xC0\x0C\x00\x00\x00")
    # Generated from packet 635/636
    gxs.fpga_wv2(0x0564, "\x08\xC2\x12\x00\x00\x00")
    # Generated from packet 637/638
    gxs.fpga_wv2(0x0568, "\x08\xC0\x18\x00\x00\x08")
    # Generated from packet 639/640
    gxs.fpga_wv2(0x056C, "\x08\x45\x09\x80\x00\x00")
    # Generated from packet 641/642
    gxs.fpga_wv2(0x0570, "\x08\xC5\x36\x80\x00\x00")
    # Generated from packet 643/644
    gxs.fpga_wv2(0x0574, "\x08\x45\x3F\x80\x00\x00")
    # Generated from packet 645/646
    gxs.fpga_wv2(0x0578, "\x08\x04\x48\x80\x00\x00")
    # Generated from packet 647/648
    gxs.fpga_wv2(0x057C, "\x08\x00\x51\x80\x00\x08")
    # Generated from packet 649/650
    gxs.fpga_wv2(0x0580, "\x08\x00\x04\x80\x00\x08")
    # Generated from packet 651/652
    gxs.fpga_wv2(0x0584, "\x09\x24\x60\x00\x00\x00")
    # Generated from packet 653/654
    gxs.fpga_wv2(0x0588, "\x09\x36\xC0\x00\x00\x00")
    # Generated from packet 655/656
    gxs.fpga_wv2(0x058C, "\x09\x24\x20\x00\x00\x01")
    # Generated from packet 657/658
    gxs.fpga_wv2(0x0590, "\x09\x36\x80\x00\x00\x01")
    # Generated from packet 659/660
    gxs.fpga_wv2(0x0594, "\x09\x24\x40\x00\x00\x02")
    # Generated from packet 661/662
    gxs.fpga_wv2(0x0598, "\x09\x00\xA0\x00\x00\x02")
    # Generated from packet 663/664
    gxs.fpga_wv2(0x059C, "\x09\x01\x00\x00\x00\x03")
    # Generated from packet 665/666
    gxs.fpga_wv2(0x05A0, "\x09\x03\x60\x00\x00\x03")
    # Generated from packet 667/668
    gxs.fpga_wv2(0x05A4, "\x09\x01\xC0\x00\x00\x03")
    # Generated from packet 669/670
    gxs.fpga_wv2(0x05A8, "\x09\x03\x20\x00\x00\x04")
    # Generated from packet 671/672
    gxs.fpga_wv2(0x05AC, "\x09\x01\x80\x00\x00\x04")
    # Generated from packet 673/674
    gxs.fpga_wv2(0x05B0, "\x09\x00\x40\x00\x00\x0D")
    # Generated from packet 675/676
    gxs.fpga_wv2(0x05B4, "\x0F\x42\x18\x00\x00\x00")
    # Generated from packet 677/678
    gxs.fpga_wv2(0x05B8, "\x0F\x02\x22\x00\x00\x00")
    # Generated from packet 679/680
    gxs.fpga_wv2(0x05BC, "\x0E\x02\x6A\x00\x00\x00")
    # Generated from packet 681/682
    gxs.fpga_wv2(0x05C0, "\x0A\x00\x6F\x00\x00\x00")
    # Generated from packet 683/684
    gxs.fpga_wv2(0x05C4, "\x0A\x80\x87\x00\x00\x00")
    # Generated from packet 685/686
    gxs.fpga_wv2(0x05C8, "\x0A\x00\xFF\x00\x00\x00")
    # Generated from packet 687/688
    gxs.fpga_wv2(0x05CC, "\x08\x00\x04\x00\x00\x09")
    
    # Generated from packet 689/690
    #buff = dev.controlRead(0xC0, 0xB0, 0x0004, 0x0000, 2)
    #validate_read("\x12\x34", buff, "packet 689/690")
    if gxs.fpga_rsig() != 0x1234:
        raise Exception("Invalid FPGA signature")
    
    # Generated from packet 691/692
    gxs.fpga_wv2(0x1000, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    # Generated from packet 693/694
    gxs.fpga_wv2(0x1008, "\x00\x02\x00\x00\x00\x00\x90\x00\x00\x00")
    # Generated from packet 695/696
    gxs.fpga_wv2(0x1010, "\x00\x03\x00\x00\x00\x00\x90\x00\x00\x0A")
    # Generated from packet 697/698
    gxs.fpga_wv2(0x1018, "\x04\x03\xCC\x00\x00\x00\x90\x00\x00\x1A")
    # Generated from packet 699/700
    gxs.fpga_wv2(0x1020, "\x00\x05\x00\x00\x00\x00\x90\x00\x00\x1E")
    # Generated from packet 701/702
    gxs.fpga_wv2(0x1028, "\x00\x06\x00\x00\x00\x00\x00\x00\x00\x25")
    # Generated from packet 703/704
    gxs.fpga_wv2(0x1030, "\x07\x06\x63\x00\x00\x00\x00\x00\x00\x32")
    # Generated from packet 705/706
    gxs.fpga_wv2(0x1038, "\x08\x07\x20\x00\x00\x00\x00\x00\x00\x36")
    # Generated from packet 707/708
    gxs.fpga_wv2(0x1040, "\x09\x08\xF5\x13\xFF\xF0\x00\x00\x00\x32")
    # Generated from packet 709/710
    gxs.fpga_wv2(0x1048, "\x0A\x09\x20\x00\x00\x00\x00\x00\x00\x36")
    # Generated from packet 711/712
    gxs.fpga_wv2(0x1050, "\x0B\x0A\xF5\x13\xFF\xF0\x00\x00\x00\x32")
    # Generated from packet 713/714
    gxs.fpga_wv2(0x1058, "\x0C\x0B\x20\x00\x00\x00\x00\x00\x00\x36")
    # Generated from packet 715/716
    gxs.fpga_wv2(0x1060, "\x0D\x0C\xF5\x13\xFF\xF0\x00\x00\x00\x32")
    # Generated from packet 717/718
    gxs.fpga_wv2(0x1068, "\x0E\x0D\x20\x00\x00\x00\x00\x00\x00\x36")
    # Generated from packet 719/720
    gxs.fpga_wv2(0x1070, "\x0F\x0E\xF5\x13\xFF\xF0\x00\x00\x00\x32")
    # Generated from packet 721/722
    gxs.fpga_wv2(0x1078, "\x10\x0F\x20\x00\x00\x00\x00\x00\x00\x36")
    # Generated from packet 723/724
    gxs.fpga_wv2(0x1080, "\x11\x10\x0A\x13\xFF\xF0\x00\x00\x00\x32")
    # Generated from packet 725/726
    gxs.fpga_wv2(0x1088, "\x03\x11\x0A\x12\x00\x70\x00\x00\x00\x32")
    # Generated from packet 727/728
    gxs.fpga_wv2(0x1090, "\x02\x12\xDC\x13\xFF\xF0\x90\x00\x00\x1A")
    # Generated from packet 729/730
    gxs.fpga_wv2(0x1098, "\x00\x14\x00\x00\x00\x00\x90\x00\x00\x5B")
    # Generated from packet 731/732
    gxs.fpga_wv2(0x10A0, "\x15\x14\xFF\x00\x00\x0F\x00\x00\x00\x60")
    # Generated from packet 733/734
    gxs.fpga_wv2(0x10A8, "\x00\x16\x00\x00\x00\x00\x90\x00\x00\x61")
    # Generated from packet 735/736
    gxs.fpga_wv2(0x10B0, "\x00\x17\x00\x00\x00\x00\x90\x00\x00\x6D")
    # Generated from packet 737/738
    gxs.fpga_wv2(0x10B8, "\x00\x18\x00\x00\x00\x00\x00\x00\x00\x3B")
    # Generated from packet 739/740
    gxs.fpga_wv2(0x10C0, "\x16\x18\x3E\x01\x73\x95\x00\x00\x00\x4D")
    # Generated from packet 741/742
    gxs.fpga_wv2(0x10C8, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    # Generated from packet 743/744
    gxs.fpga_wv2(0x10D0, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    # Generated from packet 745/746
    gxs.fpga_wv2(0x10D8, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    # Generated from packet 747/748
    gxs.fpga_wv2(0x10E0, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    # Generated from packet 749/750
    gxs.fpga_wv2(0x10E8, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    # Generated from packet 751/752
    gxs.fpga_wv2(0x10F0, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    # Generated from packet 753/754
    gxs.fpga_wv2(0x10F8, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    
    
    # Generated from packet 755/756
    gxs.fpga_w(0x2002, 0x0001)
    
    # Generated from packet 757/758
    #buff = dev.controlRead(0xC0, 0xB0, 0x0003, 0x2002, 2)
    #validate_read("\x00\x01", buff, "packet 757/758")
    v = gxs.fpga_r(0x2002)
    if v != 0x0001:
        raise Exception("Bad FPGA read: 0x%04X" % v)
    
    # Generated from packet 759/760
    # XXX: why did the integration time change?
    #dev.controlWrite(0x40, 0xB0, 0x002C, 0x0000, "\x00\x64")
    gxs.int_t_w(0x0064)
    
    '''
    FIXME: fails verification if already ran
      Expected; 01
      Actual:   02
    '''
    # Generated from packet 761/762
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    #validate_read("\x01", buff, "packet 761/762", True)
    if gxs.state() != 1:
        print 'WARNING: unexpected state'
    
    # Generated from packet 763/764
    #dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # Generated from packet 765/766
    #dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # 1344 x 1850
    gxs.img_wh_w(0x0540, 0x073A)
    
    # Generated from packet 767/768
    #dev.controlWrite(0x40, 0xB0, 0x000E, 0x0000, "")
    gxs.flash_sec_act(0x0000)

'''
def get_state(dev):
    buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    if args.verbose:
        print 'r1: %s' % binascii.hexlify(buff)
    return ord(buff)
'''

def cleanup(gxs):
    # frame3.cap
    
    # Generated from packet 1179/1180
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    #validate_read("\x01", buff, "packet 1179/1180")
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    # Generated from packet 1181/1182
    #buff = dev.controlRead(0xC0, 0xB0, 0x0080, 0x0000, 1)
    #validate_read("\x00", buff, "packet 1181/1182")
    if gxs.error():
        raise Exception('Unexpected error')
    
    # Generated from packet 1183/1184
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    #validate_read("\x01", buff, "packet 1183/1184")
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    # Generated from packet 1185/1186
    #buff = dev.controlRead(0xC0, 0xB0, 0x0080, 0x0000, 1)
    #validate_read("\x00", buff, "packet 1185/1186")
    if gxs.error():
        raise Exception('Unexpected error')
    
    # XXX: looks like info written to eprom?
    # doesn't show up
    # Generated from packet 1187/1188
    #dev.controlWrite(0x40, 0xB0, 0x000C, 0x0020, "\x32\x30\x31\x35\x2F\x30\x33\x2F\x31\x39\x2D\x32\x31\x3A\x34\x34"
    #          "\x3A\x34\x33\x3A\x30\x38\x37")
    gxs.eeprom_w(0x0020, "2015/03/19-21:44:43:087")
    
    # Generated from packet 1189/1190
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    #validate_read("\x01", buff, "packet 1189/1190")
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    # Generated from packet 1191/1192
    #buff = dev.controlRead(0xC0, 0xB0, 0x0080, 0x0000, 1)
    #validate_read("\x00", buff, "packet 1191/1192")
    if gxs.error():
        raise Exception('Unexpected error')
    
    # Generated from packet 1193/1194
    #dev.controlWrite(0x40, 0xB0, 0x002C, 0x0000, "\x02\xBC")
    gxs.int_t_w(0x02BC)
    
    # Generated from packet 1195/1196
    #dev.controlWrite(0x40, 0xB0, 0x0021, 0x0000, "\x00")
    gxs.cap_mode_w(0)

    # Generated from packet 1197/1198
    #dev.controlWrite(0x40, 0xB0, 0x002E, 0x0000, "\x00")
    gxs.hw_trig_arm()
    
    # Generated from packet 1199/1200
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    #validate_read("\x01", buff, "packet 1199/1200")
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    # Generated from packet 1201/1202
    #buff = dev.controlRead(0xC0, 0xB0, 0x0080, 0x0000, 1)
    #validate_read("\x00", buff, "packet 1201/1202")
    if gxs.error():
        raise Exception('Unexpected error')
    
    # Generated from packet 1203/1204
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    #validate_read("\x01", buff, "packet 1203/1204")
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    # Generated from packet 1205/1206
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    #validate_read("\x01", buff, "packet 1205/1206")
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    # Generated from packet 1207/1208
    #dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # Generated from packet 1209/1210
    #dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # 1344 x 1850
    gxs.img_wh_w(0x0540, 0x073A)
    
    # Generated from packet 1211/1212
    #dev.controlWrite(0x40, 0xB0, 0x000E, 0x0000, "")
    gxs.flash_sec_act(0x0000)
    
    # Generated from packet 1219/1220
    #buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    #validate_read("\x05\x40\x07\x3A", buff, "packet 1219/1220")
    # Generated from packet 1221/1222
    #buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    #validate_read("\x05\x40\x07\x3A", buff, "packet 1221/1222")
    # 1344 x 1850
    if gxs.img_wh() != (0x0540, 0x073A):
        raise Exception("Unexpected w/h")
    
    
    # Generated from packet 1223/1224
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    #validate_read("\x01", buff, "packet 1223/1224")
    if gxs.state() != 1:
        raise Exception('Unexpected state')

    # Generated from packet 1225/1226
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    #validate_read("\x01", buff, "packet 1225/1226")
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    # Generated from packet 1227/1228
    #buff = dev.controlRead(0xC0, 0xB0, 0x0080, 0x0000, 1)
    #validate_read("\x00", buff, "packet 1227/1228")
    if gxs.error():
        raise Exception('Unexpected error')
    
    # Generated from packet 1229/1230
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    if gxs.state() != 1:
        raise Exception('Unexpected state')

class USBDbg:
    def __init__(self, dev):
        self.dev = dev

    def controlWrite(self, request_type, request, value, index, data,
                     timeout=0):
        print 'DBG: controlWrite(request_type=%02X, request=%04X, value=%04X, index=%04X, data=%s, timeout=%d)' % (
                request_type, request, value, index, binascii.hexlify(data), timeout)
        self.dev.controlWrite(request_type, request, value, index, data, timeout)

    def controlRead(self, request_type, request, value, index, length,
                    timeout=0):
        print 'DBG: controlRead(request_type=%02X, request=%04X, value=%04X, index=%04X, length=%04X, timeout=%d)' % (
                request_type, request, value, index, length, timeout)
        return self.dev.controlRead(request_type, request, value, index, length, timeout)

    def getTransfer(self):
        return self.dev.getTransfer()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    parser.add_argument('--number', '-n', type=int, default=1, help='number to take')
    args = parser.parse_args()

    usbcontext = usb1.USBContext()
    dev = open_dev(usbcontext)
    #dev = USBDbg(dev)
    gxs = gxs700.GXS700(usbcontext, dev)
    
    #gxs.rst()

    #state = get_state(dev)
    state = gxs.state()
    print 'Init state: %d' % state
    if state == 0x08:
        print 'Flusing stale capture'
        gxs._cap_frame_bulk()
    elif state != 0x01:
        print 'Not idle, refusing to setup'
        sys.exit(1)

    # Generated from packet 437/438
    #dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # Generated from packet 439/440
    #dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # 1344 x 1850
    gxs.img_wh_w(0x0540, 0x073A)
    
    # Generated from packet 441/442
    #dev.controlWrite(0x40, 0xB0, 0x000E, 0x0000, "")
    gxs.flash_sec_act(0x0000)

    
    # 443-448
    #dump_eeprom(dev, args.verbose)
        
    replay_449_768(gxs)

    # 769-774 re-read EEPROM

    # Generated from packet 775/776
    #buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    #validate_read("\x05\x40\x07\x3A", buff, "packet 775/776")
    # Generated from packet 777/778
    #buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    #validate_read("\x05\x40\x07\x3A", buff, "packet 777/778")
    # 1344 x 1850
    if gxs.img_wh() != (0x0540, 0x073A):
        raise Exception("Unexpected w/h")
    
    
    '''
    FIXME: fails verification if already plugged in
    '''
    # Generated from packet 779/780
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    #validate_read("\x01", buff, "packet 779/780", True)
    if gxs.state() != 1:
        print 'WARNING: unexpected state'

    # Generated from packet 781/782
    #dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # Generated from packet 783/784
    #dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # 1344 x 1850
    gxs.img_wh_w(0x0540, 0x073A)
    
    
    # Generated from packet 785/786
    #dev.controlWrite(0x40, 0xB0, 0x000E, 0x0000, "")
    gxs.flash_sec_act(0x0000)
    
    
    # 787-792 re-read EEPROM


    # Generated from packet 793/794
    #buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    #validate_read("\x05\x40\x07\x3A", buff, "packet 793/794")
    # Generated from packet 795/796
    #buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    #validate_read("\x05\x40\x07\x3A", buff, "packet 795/796")
    # 1344 x 1850
    if gxs.img_wh() != (0x0540, 0x073A):
        raise Exception("Unexpected w/h")
    
    # Generated from packet 797/798
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    #validate_read("\x01", buff, "packet 797/798", True)
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    # Generated from packet 799/800
    #dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # Generated from packet 801/802
    #dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # 1344 x 1850
    gxs.img_wh_w(0x0540, 0x073A)
    
    # Generated from packet 803/804
    #dev.controlWrite(0x40, 0xB0, 0x000E, 0x0000, "")
    gxs.flash_sec_act(0x0000)


    # 805-810 re-read EEPROM
    

    # Generated from packet 811/812
    #buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    #validate_read("\x05\x40\x07\x3A", buff, "packet 811/812")
    # Generated from packet 813/814
    #buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    #validate_read("\x05\x40\x07\x3A", buff, "packet 813/814")
    # 1344 x 1850
    if gxs.img_wh() != (0x0540, 0x073A):
        raise Exception("Unexpected w/h")
    
    
    # Generated from packet 815/816
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    #validate_read("\x01", buff, "packet 815/816", True)
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    # Generated from packet 817/818
    #dev.controlWrite(0x40, 0xB0, 0x002C, 0x0000, "\x02\xBC")
    gxs.int_t_w(0x02BC)
    
    # Generated from packet 819/820
    #dev.controlWrite(0x40, 0xB0, 0x0021, 0x0000, "\x00")
    gxs.cap_mode_w(0)
    
    # Generated from packet 821/822
    #dev.controlWrite(0x40, 0xB0, 0x002E, 0x0000, "\x00")
    gxs.hw_trig_arm()
    
    # Generated from packet 823/824
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    #validate_read("\x01", buff, "packet 823/824", True)
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    # Generated from packet 825/826
    #buff = dev.controlRead(0xC0, 0xB0, 0x0080, 0x0000, 1)
    #validate_read("\x00", buff, "packet 825/826")
    if gxs.error():
        raise Exception('Unexpected error')
    
    # Generated from packet 827/828
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    #validate_read("\x01", buff, "packet 827/828", True)
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    
    '''
    wonder what this means...
    repeatedly fails verification
    what about other captures?
    
    Failed packet 829/830
      Expected; 8700000051000000
      Actual:   910000005b000000

    Failed packet 829/830
      Expected; 8700000051000000
      Actual:   910000005b000000
  
    frame1.cap
        validate_read("\x8E\x00\x00\x00\x58\x00\x00\x00", buff, "packet 783/784")
    cap1.cap
        validate_read("\x87\x00\x00\x00\x51\x00\x00\x00", buff, "packet 829/830")
    cap2.cap
        validate_read("\x87\x00\x00\x00\x51\x00\x00\x00", buff, "packet 829/830")
    '''
    # Generated from packet 829/830
    buff = dev.controlRead(0xC0, 0xB0, 0x0040, 0x0000, 128)
    # NOTE:: req max 128 but got 8
    # FIXME
    validate_read("\x87\x00\x00\x00\x51\x00\x00\x00", buff, "packet 829/830", True)
    
    # Generated from packet 831/832
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    #validate_read("\x01", buff, "packet 831/832", True)
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    # Generated from packet 833/834
    buff = dev.controlRead(0xC0, 0xB0, 0x0040, 0x0000, 128)
    # NOTE:: req max 128 but got 8
    # FIXME
    validate_read("\x87\x00\x00\x00\x51\x00\x00\x00", buff, "packet 833/834", True)
    
    # Generated from packet 835/836
    #buff = dev.controlRead(0xC0, 0xB0, 0x0080, 0x0000, 1)
    #validate_read("\x00", buff, "packet 835/836")
    if gxs.error():
        raise Exception('Unexpected error')
    
    # Generated from packet 837/838
    buff = dev.controlRead(0xC0, 0xB0, 0x0051, 0x0000, 28)
    # NOTE:: req max 28 but got 12
    validate_read("\x00\x05\x00\x0A\x00\x03\x00\x06\x00\x04\x00\x05", buff, "packet 837/838")
    
    # Generated from packet 839/840
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    #validate_read("\x01", buff, "packet 839/840", True)
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    # Generated from packet 841/842
    #buff = dev.controlRead(0xC0, 0xB0, 0x0080, 0x0000, 1)
    #validate_read("\x00", buff, "packet 841/842")
    if gxs.error():
        raise Exception('Unexpected error')
    
    # Generated from packet 843/844
    #dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # Generated from packet 845/846
    #dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # 1344 x 1850
    gxs.img_wh_w(0x0540, 0x073A)
    
    # Generated from packet 847/848
    #dev.controlWrite(0x40, 0xB0, 0x000E, 0x0000, "")
    gxs.flash_sec_act(0x0000)


    # 849-854 re-read EEPROM


    # Generated from packet 855/856
    #buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    #validate_read("\x05\x40\x07\x3A", buff, "packet 855/856")
    # Generated from packet 857/858
    #buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    #validate_read("\x05\x40\x07\x3A", buff, "packet 857/858")
    # 1344 x 1850
    if gxs.img_wh() != (0x0540, 0x073A):
        raise Exception("Unexpected w/h")

    
    # Generated from packet 859/860
    #buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    #validate_read("\x01", buff, "packet 859/860", True)
    if gxs.state() != 1:
        raise Exception('Unexpected state')
    
    fn = ''
    
    taken = 0
    imagen = 0
    while os.path.exists('capture_%03d.bin' % imagen):
        imagen += 1
    print 'Taking first image to %s' % ('capture_%03d.bin' % imagen,)
    
    while taken < args.number:
        print
        print
        print
        print 'Requesting next image...'
        imgb = gxs.cap_bin()
        
        fn = 'capture_%03d.bin' % imagen
        print 'Writing %s' % fn
        open(fn, 'w').write(imgb)

        fn = 'capture_%03d.png' % imagen
        print 'Decoding %s' % fn
        img = gxs700.GXS700.decode(imgb)
        print 'Writing %s' % fn
        img.save(fn)

        taken += 1
        imagen += 1

        cleanup(gxs)

