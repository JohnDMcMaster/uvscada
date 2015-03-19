# https://github.com/vpelletier/python-libusb1
# Python-ish (classes, exceptions, ...) wrapper around libusb1.py . See docstrings (pydoc recommended) for usage.
import usb1
# Bare ctype wrapper, inspired from library C header file.
import libusb1
import binascii
import sys
import argparse
import time

from dump_eeprom import dump_eeprom

def validate_read(expected, actual, msg):
    if expected != actual:
        print 'Failed %s' % msg
        print '  Expected; %s' % binascii.hexlify(expected,)
        print '  Actual:   %s' % binascii.hexlify(actual,)
        raise Exception('failed validate: %s' % msg)

def replay_449_768():
    # Generated from packet 449/450
    buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    validate_read("\x05\x40\x07\x3A", buff, "packet 449/450")
    # Generated from packet 451/452
    buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    validate_read("\x05\x40\x07\x3A", buff, "packet 451/452")
    # Generated from packet 453/454
    buff = dev.controlRead(0xC0, 0xB0, 0x0003, 0x2002, 2)
    validate_read("\x00\x00", buff, "packet 453/454")
    # Generated from packet 455/456
    buff = dev.controlRead(0xC0, 0xB0, 0x0004, 0x0000, 2)
    validate_read("\x12\x34", buff, "packet 455/456")
    # Generated from packet 457/458
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0400, "\x00\x00\x60\x00\x00\x00")
    # Generated from packet 459/460
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0404, "\x00\xE5\xC0\x00\x00\x00")
    # Generated from packet 461/462
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0408, "\x00\xF7\x20\x00\x00\x01")
    # Generated from packet 463/464
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x040C, "\x00\xE5\x80\x00\x00\x01")
    # Generated from packet 465/466
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0410, "\x00\xF7\xE0\x00\x00\x01")
    # Generated from packet 467/468
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0414, "\x00\xE5\xA0\x00\x00\x02")
    # Generated from packet 469/470
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0418, "\x00\xC5\x20\x00\x00\x04")
    # Generated from packet 471/472
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x041C, "\x00\x05\x38\x00\x00\x04")
    # Generated from packet 473/474
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0420, "\x00\x04\x98\x00\x00\x04")
    # Generated from packet 475/476
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0424, "\x00\x00\xF8\x02\x00\x0C")
    # Generated from packet 477/478
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0428, "\x08\x00\x3F\x00\x00\x00")
    # Generated from packet 479/480
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x042C, "\x08\x00\x42\x04\x00\x00")
    # Generated from packet 481/482
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0430, "\x08\x04\x4B\x04\x00\x00")
    # Generated from packet 483/484
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0434, "\x08\x06\x54\x04\x00\x00")
    # Generated from packet 485/486
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0438, "\x08\x04\x5D\x04\x00\x00")
    # Generated from packet 487/488
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x043C, "\x08\x06\x66\x04\x00\x00")
    # Generated from packet 489/490
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0440, "\x08\x04\x6F\x04\x00\x00")
    # Generated from packet 491/492
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0444, "\x08\x00\x72\x04\x00\x00")
    # Generated from packet 493/494
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0448, "\x08\x01\x78\x04\x00\x00")
    # Generated from packet 495/496
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x044C, "\x08\x03\x7E\x04\x00\x00")
    # Generated from packet 497/498
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0450, "\x08\x01\x84\x04\x00\x00")
    # Generated from packet 499/500
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0454, "\x08\xC3\x8A\x04\x00\x00")
    # Generated from packet 501/502
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0458, "\x08\xC1\x90\x04\x00\x00")
    # Generated from packet 503/504
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x045C, "\x08\xC0\x96\x04\x00\x00")
    # Generated from packet 505/506
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0460, "\x08\xC2\x9C\x04\x00\x00")
    # Generated from packet 507/508
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0464, "\x08\xC0\xA2\x04\x00\x08")
    # Generated from packet 509/510
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0468, "\x08\x42\x06\x04\x00\x00")
    # Generated from packet 511/512
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x046C, "\x08\x00\x0C\x04\x00\x00")
    # Generated from packet 513/514
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0470, "\x08\x82\x12\x04\x00\x00")
    # Generated from packet 515/516
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0474, "\x08\x00\x18\x04\x00\x08")
    # Generated from packet 517/518
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0478, "\x0F\x42\x18\x04\x00\x00")
    # Generated from packet 519/520
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x047C, "\x0F\x02\x22\x04\x00\x00")
    # Generated from packet 521/522
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0480, "\x0E\x02\x6A\x04\x00\x00")
    # Generated from packet 523/524
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0484, "\x0A\x02\x6F\x04\x00\x00")
    # Generated from packet 525/526
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0488, "\x0A\x82\x87\x04\x00\x00")
    # Generated from packet 527/528
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x048C, "\x0A\x02\xFF\x04\x00\x00")
    # Generated from packet 529/530
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0490, "\x08\x02\x04\x04\x00\x09")
    # Generated from packet 531/532
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0494, "\x08\x20\x09\x04\x00\x00")
    # Generated from packet 533/534
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0498, "\x08\x30\x12\x04\x00\x00")
    # Generated from packet 535/536
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x049C, "\x08\x20\x1B\x04\x00\x00")
    # Generated from packet 537/538
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04A0, "\x08\x30\x24\x04\x00\x00")
    # Generated from packet 539/540
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04A4, "\x08\x20\x2D\x04\x00\x00")
    # Generated from packet 541/542
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04A8, "\x08\x00\x36\x04\x00\x00")
    # Generated from packet 543/544
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04AC, "\x08\x0A\x3F\x04\x00\x00")
    # Generated from packet 545/546
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04B0, "\x08\x1A\x48\x04\x00\x00")
    # Generated from packet 547/548
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04B4, "\x08\x0A\x51\x04\x00\x00")
    # Generated from packet 549/550
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04B8, "\x08\x1A\x5A\x04\x00\x00")
    # Generated from packet 551/552
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04BC, "\x08\x0A\x63\x04\x00\x00")
    # Generated from packet 553/554
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04C0, "\x08\x00\x64\x04\x00\x00")
    # Generated from packet 555/556
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04C4, "\x08\x10\x6C\x04\x00\x08")
    # Generated from packet 557/558
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04C8, "\x08\x10\x04\x0C\x00\x00")
    # Generated from packet 559/560
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04CC, "\x08\x00\x08\x0C\x00\x00")
    # Generated from packet 561/562
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04D0, "\x08\x10\x0C\x0C\x00\x00")
    # Generated from packet 563/564
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04D4, "\x08\x00\x10\x0C\x00\x08")
    # Generated from packet 565/566
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04D8, "\x08\x10\x09\x1C\x00\x00")
    # Generated from packet 567/568
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04DC, "\x08\x00\x12\x1C\x00\x00")
    # Generated from packet 569/570
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04E0, "\x08\x10\x1B\x1C\x00\x00")
    # Generated from packet 571/572
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04E4, "\x08\x00\x1C\x1C\x00\x00")
    # Generated from packet 573/574
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04E8, "\x08\x00\x24\x1D\x00\x08")
    # Generated from packet 575/576
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04EC, "\x08\x22\x3C\x00\x00\x00")
    # Generated from packet 577/578
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04F0, "\x08\x32\x78\x00\x00\x00")
    # Generated from packet 579/580
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04F4, "\x08\x22\xB4\x00\x00\x00")
    # Generated from packet 581/582
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04F8, "\x08\x32\xF0\x00\x00\x00")
    # Generated from packet 583/584
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x04FC, "\x08\x22\x2C\x00\x00\x01")
    # Generated from packet 585/586
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0500, "\x08\x02\x35\x00\x00\x01")
    # Generated from packet 587/588
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0504, "\x08\x0A\x3E\x00\x00\x01")
    # Generated from packet 589/590
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0508, "\x08\x1A\x47\x00\x00\x01")
    # Generated from packet 591/592
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x050C, "\x08\x0A\x4C\x00\x00\x01")
    # Generated from packet 593/594
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0510, "\x08\x1A\x50\x00\x00\x01")
    # Generated from packet 595/596
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0514, "\x08\x0A\x59\x00\x00\x01")
    # Generated from packet 597/598
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0518, "\x08\x02\x5E\x00\x00\x01")
    # Generated from packet 599/600
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x051C, "\x08\x12\x66\x00\x00\x01")
    # Generated from packet 601/602
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0520, "\x08\x02\x67\x00\x00\x01")
    # Generated from packet 603/604
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0524, "\x08\x02\x6F\x01\x00\x09")
    # Generated from packet 605/606
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0528, "\x08\x00\x08\x0C\x00\x00")
    # Generated from packet 607/608
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x052C, "\x08\x00\x10\x04\x00\x00")
    # Generated from packet 609/610
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0530, "\x08\x00\x18\x00\x00\x08")
    # Generated from packet 611/612
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0534, "\x08\x10\x09\x00\x00\x00")
    # Generated from packet 613/614
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0538, "\x08\x00\x12\x00\x00\x00")
    # Generated from packet 615/616
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x053C, "\x08\x10\x1B\x00\x00\x00")
    # Generated from packet 617/618
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0540, "\x08\x00\x1C\x00\x00\x00")
    # Generated from packet 619/620
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0544, "\x08\x00\x24\x01\x00\x08")
    # Generated from packet 621/622
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0548, "\x08\x10\x09\x1C\x00\x00")
    # Generated from packet 623/624
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x054C, "\x08\x00\x12\x1C\x00\x00")
    # Generated from packet 625/626
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0550, "\x08\x10\x1B\x1C\x00\x00")
    # Generated from packet 627/628
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0554, "\x08\x00\x1C\x1C\x00\x00")
    # Generated from packet 629/630
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0558, "\x08\x00\x24\x1D\x00\x08")
    # Generated from packet 631/632
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x055C, "\x08\xC2\x06\x00\x00\x00")
    # Generated from packet 633/634
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0560, "\x08\xC0\x0C\x00\x00\x00")
    # Generated from packet 635/636
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0564, "\x08\xC2\x12\x00\x00\x00")
    # Generated from packet 637/638
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0568, "\x08\xC0\x18\x00\x00\x08")
    # Generated from packet 639/640
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x056C, "\x08\x45\x09\x80\x00\x00")
    # Generated from packet 641/642
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0570, "\x08\xC5\x36\x80\x00\x00")
    # Generated from packet 643/644
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0574, "\x08\x45\x3F\x80\x00\x00")
    # Generated from packet 645/646
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0578, "\x08\x04\x48\x80\x00\x00")
    # Generated from packet 647/648
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x057C, "\x08\x00\x51\x80\x00\x08")
    # Generated from packet 649/650
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0580, "\x08\x00\x04\x80\x00\x08")
    # Generated from packet 651/652
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0584, "\x09\x24\x60\x00\x00\x00")
    # Generated from packet 653/654
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0588, "\x09\x36\xC0\x00\x00\x00")
    # Generated from packet 655/656
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x058C, "\x09\x24\x20\x00\x00\x01")
    # Generated from packet 657/658
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0590, "\x09\x36\x80\x00\x00\x01")
    # Generated from packet 659/660
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0594, "\x09\x24\x40\x00\x00\x02")
    # Generated from packet 661/662
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x0598, "\x09\x00\xA0\x00\x00\x02")
    # Generated from packet 663/664
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x059C, "\x09\x01\x00\x00\x00\x03")
    # Generated from packet 665/666
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x05A0, "\x09\x03\x60\x00\x00\x03")
    # Generated from packet 667/668
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x05A4, "\x09\x01\xC0\x00\x00\x03")
    # Generated from packet 669/670
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x05A8, "\x09\x03\x20\x00\x00\x04")
    # Generated from packet 671/672
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x05AC, "\x09\x01\x80\x00\x00\x04")
    # Generated from packet 673/674
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x05B0, "\x09\x00\x40\x00\x00\x0D")
    # Generated from packet 675/676
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x05B4, "\x0F\x42\x18\x00\x00\x00")
    # Generated from packet 677/678
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x05B8, "\x0F\x02\x22\x00\x00\x00")
    # Generated from packet 679/680
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x05BC, "\x0E\x02\x6A\x00\x00\x00")
    # Generated from packet 681/682
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x05C0, "\x0A\x00\x6F\x00\x00\x00")
    # Generated from packet 683/684
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x05C4, "\x0A\x80\x87\x00\x00\x00")
    # Generated from packet 685/686
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x05C8, "\x0A\x00\xFF\x00\x00\x00")
    # Generated from packet 687/688
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x05CC, "\x08\x00\x04\x00\x00\x09")
    # Generated from packet 689/690
    buff = dev.controlRead(0xC0, 0xB0, 0x0004, 0x0000, 2)
    validate_read("\x12\x34", buff, "packet 689/690")
    # Generated from packet 691/692
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1000, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    # Generated from packet 693/694
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1008, "\x00\x02\x00\x00\x00\x00\x90\x00\x00\x00")
    # Generated from packet 695/696
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1010, "\x00\x03\x00\x00\x00\x00\x90\x00\x00\x0A")
    # Generated from packet 697/698
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1018, "\x04\x03\xCC\x00\x00\x00\x90\x00\x00\x1A")
    # Generated from packet 699/700
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1020, "\x00\x05\x00\x00\x00\x00\x90\x00\x00\x1E")
    # Generated from packet 701/702
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1028, "\x00\x06\x00\x00\x00\x00\x00\x00\x00\x25")
    # Generated from packet 703/704
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1030, "\x07\x06\x63\x00\x00\x00\x00\x00\x00\x32")
    # Generated from packet 705/706
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1038, "\x08\x07\x20\x00\x00\x00\x00\x00\x00\x36")
    # Generated from packet 707/708
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1040, "\x09\x08\xF5\x13\xFF\xF0\x00\x00\x00\x32")
    # Generated from packet 709/710
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1048, "\x0A\x09\x20\x00\x00\x00\x00\x00\x00\x36")
    # Generated from packet 711/712
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1050, "\x0B\x0A\xF5\x13\xFF\xF0\x00\x00\x00\x32")
    # Generated from packet 713/714
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1058, "\x0C\x0B\x20\x00\x00\x00\x00\x00\x00\x36")
    # Generated from packet 715/716
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1060, "\x0D\x0C\xF5\x13\xFF\xF0\x00\x00\x00\x32")
    # Generated from packet 717/718
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1068, "\x0E\x0D\x20\x00\x00\x00\x00\x00\x00\x36")
    # Generated from packet 719/720
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1070, "\x0F\x0E\xF5\x13\xFF\xF0\x00\x00\x00\x32")
    # Generated from packet 721/722
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1078, "\x10\x0F\x20\x00\x00\x00\x00\x00\x00\x36")
    # Generated from packet 723/724
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1080, "\x11\x10\x0A\x13\xFF\xF0\x00\x00\x00\x32")
    # Generated from packet 725/726
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1088, "\x03\x11\x0A\x12\x00\x70\x00\x00\x00\x32")
    # Generated from packet 727/728
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1090, "\x02\x12\xDC\x13\xFF\xF0\x90\x00\x00\x1A")
    # Generated from packet 729/730
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x1098, "\x00\x14\x00\x00\x00\x00\x90\x00\x00\x5B")
    # Generated from packet 731/732
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x10A0, "\x15\x14\xFF\x00\x00\x0F\x00\x00\x00\x60")
    # Generated from packet 733/734
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x10A8, "\x00\x16\x00\x00\x00\x00\x90\x00\x00\x61")
    # Generated from packet 735/736
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x10B0, "\x00\x17\x00\x00\x00\x00\x90\x00\x00\x6D")
    # Generated from packet 737/738
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x10B8, "\x00\x18\x00\x00\x00\x00\x00\x00\x00\x3B")
    # Generated from packet 739/740
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x10C0, "\x16\x18\x3E\x01\x73\x95\x00\x00\x00\x4D")
    # Generated from packet 741/742
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x10C8, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    # Generated from packet 743/744
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x10D0, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    # Generated from packet 745/746
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x10D8, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    # Generated from packet 747/748
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x10E0, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    # Generated from packet 749/750
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x10E8, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    # Generated from packet 751/752
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x10F0, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    # Generated from packet 753/754
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x10F8, "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    # Generated from packet 755/756
    dev.controlWrite(0x40, 0xB0, 0x0002, 0x2002, "\x00\x01")
    # Generated from packet 757/758
    buff = dev.controlRead(0xC0, 0xB0, 0x0003, 0x2002, 2)
    validate_read("\x00\x01", buff, "packet 757/758")
    # Generated from packet 759/760
    dev.controlWrite(0x40, 0xB0, 0x002C, 0x0000, "\x00\x64")
    # Generated from packet 761/762
    buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    validate_read("\x01", buff, "packet 761/762")
    # Generated from packet 763/764
    dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # Generated from packet 765/766
    dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # Generated from packet 767/768
    dev.controlWrite(0x40, 0xB0, 0x000E, 0x0000, "")

pidvid2name = {
        #(0x5328, 0x2009): 'Dexis Platinum (pre-enumeration)'
        (0x5328, 0x2030): 'Gendex GXS700 (post enumeration)'
        #(0x5328, 0x202F): 'Gendex GXS700 (pre-enumeration)'
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replay captured USB packets')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose')
    args = parser.parse_args()

    usbcontext = usb1.USBContext()
    print 'Scanning for devices...'
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
            break
    else:
        raise Exception("Failed to find a device")
    
    dev = udev.open()

    # Generated from packet 437/438
    dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # Generated from packet 439/440
    dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # Generated from packet 441/442
    dev.controlWrite(0x40, 0xB0, 0x000E, 0x0000, "")
    
    # 443-448
    dump_eeprom(dev, args.verbose)
        
    replay_449_768()

    # 769-774 re-read EEPROM

    # Generated from packet 775/776
    buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    validate_read("\x05\x40\x07\x3A", buff, "packet 775/776")
    # Generated from packet 777/778
    buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    validate_read("\x05\x40\x07\x3A", buff, "packet 777/778")
    # Generated from packet 779/780
    buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    validate_read("\x01", buff, "packet 779/780")
    # Generated from packet 781/782
    dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # Generated from packet 783/784
    dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # Generated from packet 785/786
    dev.controlWrite(0x40, 0xB0, 0x000E, 0x0000, "")
    
    
    # 787-792 re-read EEPROM


    # Generated from packet 793/794
    buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    validate_read("\x05\x40\x07\x3A", buff, "packet 793/794")
    # Generated from packet 795/796
    buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    validate_read("\x05\x40\x07\x3A", buff, "packet 795/796")
    # Generated from packet 797/798
    buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    validate_read("\x01", buff, "packet 797/798")
    # Generated from packet 799/800
    dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # Generated from packet 801/802
    dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # Generated from packet 803/804
    dev.controlWrite(0x40, 0xB0, 0x000E, 0x0000, "")


    # 805-810 re-read EEPROM
    

    # Generated from packet 811/812
    buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    validate_read("\x05\x40\x07\x3A", buff, "packet 811/812")
    # Generated from packet 813/814
    buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    validate_read("\x05\x40\x07\x3A", buff, "packet 813/814")
    # Generated from packet 815/816
    buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    validate_read("\x01", buff, "packet 815/816")
    # Generated from packet 817/818
    dev.controlWrite(0x40, 0xB0, 0x002C, 0x0000, "\x02\xBC")
    # Generated from packet 819/820
    dev.controlWrite(0x40, 0xB0, 0x0021, 0x0000, "\x00")
    # Generated from packet 821/822
    dev.controlWrite(0x40, 0xB0, 0x002E, 0x0000, "\x00")
    # Generated from packet 823/824
    buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    validate_read("\x01", buff, "packet 823/824")
    # Generated from packet 825/826
    buff = dev.controlRead(0xC0, 0xB0, 0x0080, 0x0000, 1)
    validate_read("\x00", buff, "packet 825/826")
    # Generated from packet 827/828
    buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    validate_read("\x01", buff, "packet 827/828")
    # Generated from packet 829/830
    buff = dev.controlRead(0xC0, 0xB0, 0x0040, 0x0000, 128)
    # NOTE:: req max 128 but got 8
    validate_read("\x87\x00\x00\x00\x51\x00\x00\x00", buff, "packet 829/830")
    # Generated from packet 831/832
    buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    validate_read("\x01", buff, "packet 831/832")
    # Generated from packet 833/834
    buff = dev.controlRead(0xC0, 0xB0, 0x0040, 0x0000, 128)
    # NOTE:: req max 128 but got 8
    validate_read("\x87\x00\x00\x00\x51\x00\x00\x00", buff, "packet 833/834")
    # Generated from packet 835/836
    buff = dev.controlRead(0xC0, 0xB0, 0x0080, 0x0000, 1)
    validate_read("\x00", buff, "packet 835/836")
    # Generated from packet 837/838
    buff = dev.controlRead(0xC0, 0xB0, 0x0051, 0x0000, 28)
    # NOTE:: req max 28 but got 12
    validate_read("\x00\x05\x00\x0A\x00\x03\x00\x06\x00\x04\x00\x05", buff, "packet 837/838")
    # Generated from packet 839/840
    buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    validate_read("\x01", buff, "packet 839/840")
    # Generated from packet 841/842
    buff = dev.controlRead(0xC0, 0xB0, 0x0080, 0x0000, 1)
    validate_read("\x00", buff, "packet 841/842")
    # Generated from packet 843/844
    dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # Generated from packet 845/846
    dev.controlWrite(0x40, 0xB0, 0x0022, 0x0000, "\x05\x40\x07\x3A")
    # Generated from packet 847/848
    dev.controlWrite(0x40, 0xB0, 0x000E, 0x0000, "")


    # 849-854 re-read EEPROM


    # Generated from packet 855/856
    buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    validate_read("\x05\x40\x07\x3A", buff, "packet 855/856")
    # Generated from packet 857/858
    buff = dev.controlRead(0xC0, 0xB0, 0x0023, 0x0000, 4)
    validate_read("\x05\x40\x07\x3A", buff, "packet 857/858")
    # Generated from packet 859/860
    buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
    validate_read("\x01", buff, "packet 859/860")
        
    # these repeat forever, about every 7 ms per loop in the original app
    i = 0
    while True:
        print
        print 'scan %d' % i
        
        # Generated from packet 861/862
        buff = dev.controlRead(0xC0, 0xB0, 0x0020, 0x0000, 1)
        print 'r1: %s' % binascii.hexlify(buff)
        validate_read("\x01", buff, "packet 861/862")
        
        # Generated from packet 863/864
        buff = dev.controlRead(0xC0, 0xB0, 0x0080, 0x0000, 1)
        print 'r2: %s' % binascii.hexlify(buff)
        validate_read("\x00", buff, "packet 863/864")

        i = i + 1
        time.sleep(0.5)


