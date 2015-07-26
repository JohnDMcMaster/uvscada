RM=rm -f
CP=cp
TAR=tar
GZIP=gzip
MKDIR=mkdir

EXTRA_CFLAGS += -I/home/mcmaster/document/build/linux/linux-2.6.34.8/drivers/media/video/gspca

KDIR:=/lib/modules/$(shell uname -r)/build

EXTRA_CFLAGS += -I$(KDIR)/drivers/usb/serial -Wall -Werror -g -Wno-unused-function

obj-m:=ov519.o

default:
	$(MAKE) -C $(KDIR) EXTRA_CFLAGS="$(EXTRA_CFLAGS)" SUBDIRS=$(PWD) modules

clean:
	$(RM) *.mod.c *.o *.ko .*.cmd *~ Modules.* modules.*

load:
	insmod ov519.ko
	
unload:
	rmmod ov519

install:
	-modprobe gspca_main
	insmod ./ov519.ko

uninstall:
	rmmod ov519
	-rmmod gspca_main

.PHONY: default clean load unload install uninstall dist

run: clean default
	-rmmod ov519
	-modprobe gspca_main
	dmesg -c >/dev/null
	insmod ./ov519.ko
	echo 'its in'
	sudo -u mcmaster vlc v4l2:///dev/video0

go: default
	-rmmod ov519
	-modprobe gspca_main
	dmesg -c >/dev/null
	insmod ./ov519.ko
	echo 'its in'
	mplayer /dev/video0
	dmesg |tail
	echo 'done done done'

cheese: default
	-rmmod ov519
	-modprobe gspca_main
	dmesg -c >/dev/null
	insmod ./ov519.ko
	echo 'its in'
	sudo -u mcmaster cheese
	echo 'done done done'

.PHONY: user
user:
	g++ user.cpp -o user

