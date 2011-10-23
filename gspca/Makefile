RM=rm -f
CP=cp
TAR=tar
GZIP=gzip
MKDIR=mkdir

EXTRA_CFLAGS += -I/home/mcmaster/document/build/linux/linux-2.6.34.8/drivers/media/video/gspca

KDIR:=/lib/modules/$(shell uname -r)/build

EXTRA_CFLAGS += -I$(KDIR)/drivers/usb/serial -Wall -Werror -g

obj-m:=uvscopetek.o

default:
	$(MAKE) -C $(KDIR) EXTRA_CFLAGS="$(EXTRA_CFLAGS)" SUBDIRS=$(PWD) modules

clean:
	$(RM) *.mod.c *.o *.ko .*.cmd *~ Modules.* modules.*

load:
	insmod uvscopetek.ko
	
unload:
	rmmod uvscopetek

install:
	-modprobe gspca_main
	insmod ./uvscopetek.ko

uninstall:
	rmmod uvscopetek
	-rmmod gspca_main

.PHONY: default clean load unload install uninstall dist

go: default
	-rmmod uvscopetek
	-modprobe gspca_main
	dmesg -c >/dev/null
	insmod ./uvscopetek.ko
	echo 'its in'
	mplayer /dev/video0
	dmesg |tail
	echo 'done done done'


