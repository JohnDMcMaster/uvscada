RM=rm -f
CP=cp
TAR=tar
GZIP=gzip
MKDIR=mkdir

EXTRA_CFLAGS += -I/home/mcmaster/document/build/linux/linux-2.6.34.8/drivers/media/video/gspca

KDIR:=/lib/modules/$(shell uname -r)/build

EXTRA_CFLAGS += -I$(KDIR)/drivers/usb/serial -Wall -Werror

obj-m:=uvscopetek.o

default:
	$(MAKE) -C $(KDIR) $(EXTRA_CFLAGS) SUBDIRS=$(PWD) modules

clean:
	$(RM) *.mod.c *.o *.ko .*.cmd *~ Modules.* modules.*

load:
	insmod uvscopetek.ko
	
unload:
	rmmod uvscopetek

install:
	modprobe gspca_main
	insmod ./uvscopetek.ko

uninstall:
	rmmod uvscopetek
	-rmmod gspca_main

.PHONY: default clean load unload install uninstall dist

go: default
	-rmmod uvscopetek
	insmod ./uvscopetek.ko
	-dd if=/dev/uvscopetek0  of=dump.bin count=1024
	hexdump -C dump.bin
	dmesg |tail

gou:
	

run: default user
	-rmmod uvscopetek
	modprobe gspca_main
	insmod ./uvscopetek.ko
	./user
	hexdump -C read.bin |head -n 30
	
.PHONY: user
user:
	$(MAKE) -f user.mk all
	


