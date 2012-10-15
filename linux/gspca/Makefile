RM=rm -f
CP=cp
TAR=tar
GZIP=gzip
MKDIR=mkdir

EXTRA_CFLAGS += -I/home/mcmaster/document/build/linux/linux-2.6.34.8/drivers/media/video/gspca

KDIR:=/lib/modules/$(shell uname -r)/build

EXTRA_CFLAGS += -I$(KDIR)/drivers/usb/serial -Wall -Werror
#CFLAGS +=  -g
EXTRA_CFLAGS += -g


# Comment/uncomment the following line to disable/enable debugging
DEBUG = y
# Add your debugging flag (or not) to CFLAGS
ifeq ($(DEBUG),y)
  DEBFLAGS = -O -g -DSCULL_DEBUG # "-O" is needed to expand inlines
else
  DEBFLAGS = -O2
endif

EXTRA_CFLAGS += $(DEBFLAGS)

obj-m:=gspca_uv.o

default:
	$(MAKE) -C $(KDIR) EXTRA_CFLAGS="$(EXTRA_CFLAGS)" SUBDIRS=$(PWD) modules

clean:
	$(RM) *.mod.c *.o *.ko .*.cmd *~ Modules.* modules.*

load:
	insmod gspca_uv.ko
	
unload:
	rmmod gspca

install:
	insmod ./gspca_uv.ko

uninstall:
	-rmmod gspca_uv

.PHONY: default clean load unload install uninstall dist

go: default
	-rmmod uvscopetek
	-rmmod gspca_main
	-rmmod gspca_uv
	modprobe videodev
	modprobe v4l1_compat
	insmod ./gspca_uv.ko debug=0xFF
	echo 'ready2roll'
	
