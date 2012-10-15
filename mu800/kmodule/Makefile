RM=rm -f
CP=cp
TAR=tar
GZIP=gzip
MKDIR=mkdir

#KDIR:=/lib/modules/$(shell uname -r)/build
KDIR:=/home/mcmaster/document/build/linux/linux-2.6.34.8

#EXTRA_CFLAGS += -I$(KDIR)/include/config/usb
EXTRA_CFLAGS += -I/home/mcmaster/document/build/linux/linux-3.1/drivers/media/video/gspca/
EXTRA_CFLAGS += -Wall -Werror

obj-m:=touptek.o

default:
	$(MAKE) -C $(KDIR) $(EXTRA_CFLAGS) SUBDIRS=$(PWD) modules

clean:
	$(RM) *.mod.c *.o *.ko .*.cmd *~ Modules.* modules.* *.symvers

load:
	insmod touptek.ko
	
unload:
	rmmod touptek

install:
	insmod ./touptek.ko

uninstall:
	rmmod touptek

.PHONY: default clean load unload install uninstall dist

go: default
	-rmmod touptek
	insmod ./touptek.ko
	#-dd if=/dev/touptek0  of=dump.bin count=1024
	#hexdump -C dump.bin
	#dmesg |tail
	mplayer /dev/touptek0 -rawvideo format=rgb24:w=1600:h=1200 -demuxer rawvideo

run: default user
	-rmmod touptek
	insmod ./touptek.ko
	./user
	hexdump -C read.bin |head -n 30
	
.PHONY: user
user:
	g++ user.cpp -o user
	
