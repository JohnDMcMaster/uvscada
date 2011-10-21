/*
 * USB uvscopetek driver - 2.2
 *
 * Copyright (C) 2001-2004 Greg Kroah-Hartman (greg@kroah.com)
 *
 *	This program is free software; you can redistribute it and/or
 *	modify it under the terms of the GNU General Public License as
 *	published by the Free Software Foundation, version 2.
 *
 * This driver is based on the 2.6.3 version of drivers/usb/usb-uvscopetek.c
 * but has been rewritten to be easier to read and use.
 *
 */

#include <linux/kernel.h>
#include <linux/errno.h>
#include <linux/init.h>
#include <linux/slab.h>
#include <linux/module.h>
#include <linux/kref.h>
#include <linux/uaccess.h>
#include <linux/usb.h>
#include <linux/mutex.h>


/* Define these values to match your devices */
#define UVSCOPETEK_VENDOR_ID	0x0547
#define UVSCOPETEK_PRODUCT_ID	0x4D88

/* table of devices that work with this driver */
static const struct usb_device_id uvscopetek_table[] = {
	{ USB_DEVICE(UVSCOPETEK_VENDOR_ID, UVSCOPETEK_PRODUCT_ID) },
	{ }					/* Terminating entry */
};
MODULE_DEVICE_TABLE(usb, uvscopetek_table);


/* Get a minor range for your devices from the usb maintainer */
#define uvscopetek_MINOR_BASE	192

/* our private defines. if this grows any larger, use your own .h file */
#define MAX_TRANSFER		(PAGE_SIZE - 512)
/* MAX_TRANSFER is chosen so that the VM is not stressed by
   allocations > PAGE_SIZE and the number of packets in a page
   is an integer 512 is the largest possible packet on EHCI */
#define WRITES_IN_FLIGHT	8
/* arbitrarily chosen */

/* Structure to hold all of our device specific stuff */
struct uvscopetek {
	struct usb_device	*udev;			/* the usb device for this device */
	struct usb_interface	*interface;		/* the interface for this device */
	struct semaphore	limit_sem;		/* limiting the number of writes in progress */
	struct usb_anchor	submitted;		/* in case we need to retract our submissions */
	struct urb		*bulk_in_urb;		/* the urb to read data with */
	unsigned char           *bulk_in_buffer;	/* the buffer to receive data */
	size_t			bulk_in_size;		/* the size of the receive buffer */
	size_t			bulk_in_filled;		/* number of bytes in the buffer */
	size_t			bulk_in_copied;		/* already copied to user space */
	__u8			bulk_in_endpointAddr;	/* the address of the bulk in endpoint */
	//__u8			bulk_out_endpointAddr;	/* the address of the bulk out endpoint */
	int			errors;			/* the last request tanked */
	int			open_count;		/* count the number of openers */
	bool			ongoing_read;		/* a read is going on */
	bool			processed_urb;		/* indicates we haven't processed the urb */
	spinlock_t		err_lock;		/* lock for errors */
	struct kref		kref;
	struct mutex		io_mutex;		/* synchronize I/O with disconnect */
	struct completion	bulk_in_completion;	/* to wait for an ongoing read */
};
#define to_uvscopetek_dev(d) container_of(d, struct uvscopetek, kref)

static struct usb_driver uvscopetek_driver;
static void uvscopetek_draw_down(struct uvscopetek *dev);

static void uvscopetek_delete(struct kref *kref)
{
	struct uvscopetek *dev = to_uvscopetek_dev(kref);

	usb_free_urb(dev->bulk_in_urb);
	usb_put_dev(dev->udev);
	kfree(dev->bulk_in_buffer);
	kfree(dev);
}

int validate_read(void *expected, size_t expected_size, void *actual, size_t actual_size, const char *msg) {
	if (expected_size != actual_size) {
		printk(KERN_ALERT "%s: expected %d bytes, got %d bytes\n", msg, expected_size, actual_size);
		return 1;
	}
	if (memcmp(expected, actual, expected_size)) {
		printk(KERN_ALERT "%s: regions do not match\n", msg);
		return 1;
	}
	printk(KERN_ALERT "%s: validate ok\n", msg);
	return 0;
}

/*
extern int usb_control_msg(struct usb_device *dev, unsigned int pipe,
	__u8 request, __u8 requesttype, __u16 value, __u16 index,
	void *data, __u16 size, int timeout);

	ret = usb_control_msg(serial->dev,    
			usb_rcvctrlpipe(serial->dev, 0),
			MOS7703_REQ_READ, MOS7703_REQTYPE_READ, 
			reg_class, reg,
			data, 0x01, MOS_URB_TIMEOUT);
*/

int camera_control_message(struct uvscopetek *dev, int requesttype, int request,
	int value, int index, char *bytes, int size) {
	int rc_tmp = 0;
	
	//XXX: should be endpoint 2?
	//82 should be mass data, 81 should be config in dump
	//but vmware can do funny stuff to device IDs
	rc_tmp = usb_control_msg(dev->udev, usb_sndctrlpipe(dev->udev, 0),
			request, requesttype, value, index, bytes, size, 500);
	if (rc_tmp < 0) {
		printk(KERN_ALERT "failed control: %d w/ req type 0x%02X, req 0x%02X, value 0x%04X, index 0x%04X, size 0x%04X\n", 
				rc_tmp,
				requesttype, request,
				value, index, size);
	}
	return rc_tmp;
}

#define CAMERA_CONTROL_MESSAGE(_requesttype, _request, \
	_value, _index, _bytes, _size) \
	n_rw = camera_control_message(dev, _requesttype, _request, \
		_value, _index, _bytes, _size); \
	if (n_rw < 0) return 1;
#define VALIDATE_READ(_expected, _expected_size, _actual, _actual_size, _msg) \
	if (validate_read(_expected, _expected_size, _actual, _actual_size, _msg)) \
		return 1
int replay_wireshark_setup(struct uvscopetek *dev) {
	char buff[0x100];
	int n_rw = 0;
	int rc_tmp = 0;
	
	printk(KERN_ALERT "Replaying wireshark stuff 1\n");
	
	if (!dev) {
		printk(KERN_ALERT "replay: dev null\n");
		return 1;
	}

	printk(KERN_ALERT "trying test packet\n\n");
	//What is relationship between rcvctrlpipe and HOST_TO_DEVICE?
	/*
	 This is the first real packet
	 Its generated after hitting the capture button and is part of the configuration
	 Packets before this are just OS device name types
	 
	 Sources
	 	All 640X480
	 	VMWare (Linux)
		 	amscope/rgb_capture/2/vmware-usb-capture-USBIO.log
				Aug 20 09:43:09.293: vmx| USBIO: Down dev=1 endpt=0 datalen=0 numPackets=1 status=979578671 73753032
				Aug 20 09:43:09.293: vmx| USBIO:  000: 40 01 01 00 0f 00 00 00                         @.......        		  
		UsbSnoop (Windows kernel) on WinXP VM, normal capture not the TWAIN test
			[6574 ms]  >>>  URB 5 going down  >>> 
			-- URB_FUNCTION_VENDOR_DEVICE:
			  TransferFlags          = 00000002 (USBD_TRANSFER_DIRECTION_OUT, USBD_SHORT_TRANSFER_OK)
			  TransferBufferLength = 00000000
			  TransferBuffer       = 00000000
			  TransferBufferMDL    = 00000000

				no data supplied
			  UrbLink                 = 00000000
			  RequestTypeReservedBits = 00000000
			  Request                 = 00000001
			  Value                   = 00000001
			  Index                   = 0000000f
		Wireshark
			Summary
				No		Time		Source	Dest	Protocol	Info
				124		65.230054	host	57.0	USB			URB_CONTROL
			URB setup
				bmRequestType: 0x40
					0... .... = Direction: Host-to-device
					.10. .... = Type: Vendor (0x02)
					...0 0000 = Recipient: Device (0x00)
				Application Data: 0101000F00000000000000000000000000000000000000	
			Raw
				0000  40 01 01 00 0f 00 00 00  00 00 00 00 00 00 00 00   @....... ........
				0010  00 00 00 00 00 00 00 00                            ........    			
				
				It did a poor job breaking it out
					0x40: requesttype, translated as below
					0x01: request, translated as below
					0x00 0x01: value
					0x00 0x0F: index
					0x00 0x00: wLength
	*/
	rc_tmp = usb_control_msg(
		//struct usb_device *dev, 
		dev->udev, 
		//unsigned int pipe,
		usb_sndctrlpipe(dev->udev, 0),
		/*
		Request type captured as 0x40 => HOST_TO_DEVICE | USB_TYPE_VENDOR | USB_RECIP_DEVICE
		*/
		//__u8 request,
		0x01,
 		//__u8 requesttype,
		USB_DIR_OUT | USB_TYPE_VENDOR | USB_RECIP_DEVICE,
		//__u16 value,
		0x0001,
		//__u16 index,
		0x000F,
		//void *data,
		NULL,
		//__u16 size,
		0,
		//int timeout
		500);
	if (rc_tmp < 0) {
		printk(KERN_ALERT "failed test control: %d\n", rc_tmp);
		printk("\n");
		return rc_tmp;
	} else {
		printk(KERN_ALERT "didn't fail...\n");
	}
	printk(KERN_ALERT "\n");


	CAMERA_CONTROL_MESSAGE(0x40, 0x01, 0x0001, 0x000F, NULL, 0);
	printk(KERN_ALERT "trying packet 7\n");
	//Generated from packet 7
	CAMERA_CONTROL_MESSAGE(0x40, 0x01, 0x0000, 0x000F, NULL, 0);
	//Generated from packet 9
	CAMERA_CONTROL_MESSAGE(0x40, 0x01, 0x0001, 0x000F, NULL, 0);
	//Generated from packet 11
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0100, 0x0103, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 12");
	//Generated from packet 13
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0100, 0x0104, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 14");
	//Generated from packet 15
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0A, 0x0000, 0x3000, buff, 3);
	if (validate_read((char[]){0x2B, 0x00, 0x08}, 3, &buff, n_rw, "packet 16"))
		return 1;
	//Generated from packet 17
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0100, 0x0104, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 18");
	//Generated from packet 19
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0020, 0x0344, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 20");
	//Generated from packet 21
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0CA1, 0x0348, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 22");
	//Generated from packet 23
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0020, 0x0346, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 24");
	//Generated from packet 25
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0981, 0x034A, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 26");
	//Generated from packet 27
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x02FC, 0x3040, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 28");
	//Generated from packet 29
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0002, 0x0400, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 30");
	//Generated from packet 31
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0014, 0x0404, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 32");
	//Generated from packet 33
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0280, 0x034C, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 34");
	//Generated from packet 35
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x01E0, 0x034E, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 36");
	//Generated from packet 37
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x02C0, 0x300A, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 38");
	//Generated from packet 39
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0E00, 0x300C, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 40");
	//Generated from packet 41
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0000, 0x0104, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 42");
	//Generated from packet 43
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0000, 0x0100, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 44");
	//Generated from packet 45
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0100, 0x0104, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 46");
	//Generated from packet 47
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0004, 0x0300, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 48");
	//Generated from packet 49
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0001, 0x0302, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 50");
	//Generated from packet 51
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0008, 0x0308, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 52");
	//Generated from packet 53
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0001, 0x030A, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 54");
	//Generated from packet 55
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0004, 0x0304, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 56");
	//Generated from packet 57
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0020, 0x0306, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 58");
	//Generated from packet 59
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x90D8, 0x301A, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 60");
	//Generated from packet 61
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0000, 0x0104, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 62");
	//Generated from packet 63
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0100, 0x0100, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 64");
	//Generated from packet 65
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0A, 0x0000, 0x300C, buff, 3);
	if (validate_read((char[]){0x0E, 0x00, 0x08}, 3, &buff, n_rw, "packet 66"))
		return 1;
	//Generated from packet 67
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x90D8, 0x301A, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 68");
	//Generated from packet 69
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0805, 0x3064, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 70");
	//Generated from packet 71
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0000, 0x0104, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 72");
	//Generated from packet 73
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0100, 0x0100, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 74");
	//Generated from packet 75
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0001, 0x0402, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 76");
	//Generated from packet 77
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0001, 0x0104, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 78");
	//Generated from packet 79
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x0000, 0x0104, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 80");
	//Generated from packet 81
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x01F4, 0x3012, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 82");
	//Generated from packet 83
	CAMERA_CONTROL_MESSAGE(0xC0, 0x0B, 0x023E, 0x305E, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 84");
	//Generated from packet 85
	CAMERA_CONTROL_MESSAGE(0x40, 0x01, 0x0003, 0x000F, NULL, 0);
	
	printk(KERN_ALERT "Replaying success!\n");
	return 0;
}

static int uvscopetek_open(struct inode *inode, struct file *file)
{
	struct uvscopetek *dev;
	struct usb_interface *interface;
	int subminor;
	int retval = 0;

	subminor = iminor(inode);

	interface = usb_find_interface(&uvscopetek_driver, subminor);
	if (!interface) {
		err("%s - error, can't find device for minor %d",
		     __func__, subminor);
		retval = -ENODEV;
		goto exit;
	}

	dev = usb_get_intfdata(interface);
	if (!dev) {
		retval = -ENODEV;
		goto exit;
	}

	/* increment our usage count for the device */
	kref_get(&dev->kref);

	/* lock the device to allow correctly handling errors
	 * in resumption */
	mutex_lock(&dev->io_mutex);

	if (!dev->open_count) {
		++dev->open_count;
		printk(KERN_ALERT "open: new count: %d\n", dev->open_count);
		retval = usb_autopm_get_interface(interface);
		if (retval) {
			printk(KERN_ALERT "open: failed to get interface\n");
			dev->open_count--;
			mutex_unlock(&dev->io_mutex);
			kref_put(&dev->kref, uvscopetek_delete);
			goto exit;
		}
		if (replay_wireshark_setup(dev)) {
			printk(KERN_ALERT "open: failed to replay\n");
			dev->open_count--;
			mutex_unlock(&dev->io_mutex);
			kref_put(&dev->kref, uvscopetek_delete);
			goto exit;
		}
	} else { //uncomment this block if you want exclusive open
		printk(KERN_ALERT "open: already open (%d)\n", dev->open_count);
		retval = -EBUSY;
		mutex_unlock(&dev->io_mutex);
		kref_put(&dev->kref, uvscopetek_delete);
		goto exit;
	}
	/* prevent the device from being autosuspended */

	/* save our object in the file's private structure */
	file->private_data = dev;
	mutex_unlock(&dev->io_mutex);

exit:
	return retval;
}

static int uvscopetek_release(struct inode *inode, struct file *file)
{
	struct uvscopetek *dev;

	dev = (struct uvscopetek *)file->private_data;
	if (dev == NULL)
		return -ENODEV;

	/* allow the device to be autosuspended */
	mutex_lock(&dev->io_mutex);
	if (!--dev->open_count && dev->interface)
		usb_autopm_put_interface(dev->interface);
	mutex_unlock(&dev->io_mutex);

	/* decrement the count on our device */
	kref_put(&dev->kref, uvscopetek_delete);
	return 0;
}

static int uvscopetek_flush(struct file *file, fl_owner_t id)
{
	struct uvscopetek *dev;
	int res;

	dev = (struct uvscopetek *)file->private_data;
	if (dev == NULL)
		return -ENODEV;

	/* wait for io to stop */
	mutex_lock(&dev->io_mutex);
	uvscopetek_draw_down(dev);

	/* read out errors, leave subsequent opens a clean slate */
	spin_lock_irq(&dev->err_lock);
	res = dev->errors ? (dev->errors == -EPIPE ? -EPIPE : -EIO) : 0;
	dev->errors = 0;
	spin_unlock_irq(&dev->err_lock);

	mutex_unlock(&dev->io_mutex);

	return res;
}

static void uvscopetek_read_bulk_callback(struct urb *urb)
{
	struct uvscopetek *dev;

	dev = urb->context;

	spin_lock(&dev->err_lock);
	/* sync/async unlink faults aren't errors */
	if (urb->status) {
		if (!(urb->status == -ENOENT ||
		    urb->status == -ECONNRESET ||
		    urb->status == -ESHUTDOWN))
			err("%s - nonzero write bulk status received: %d",
			    __func__, urb->status);

		dev->errors = urb->status;
	} else {
		dev->bulk_in_filled = urb->actual_length;
	}
	dev->ongoing_read = 0;
	spin_unlock(&dev->err_lock);

	complete(&dev->bulk_in_completion);
}

static int uvscopetek_do_read_io(struct uvscopetek *dev, size_t count)
{
	int rv;

	/* prepare a read */
	usb_fill_bulk_urb(dev->bulk_in_urb,
			dev->udev,
			usb_rcvbulkpipe(dev->udev,
				dev->bulk_in_endpointAddr),
			dev->bulk_in_buffer,
			min(dev->bulk_in_size, count),
			uvscopetek_read_bulk_callback,
			dev);
	/* tell everybody to leave the URB alone */
	spin_lock_irq(&dev->err_lock);
	dev->ongoing_read = 1;
	spin_unlock_irq(&dev->err_lock);

	/* do it */
	rv = usb_submit_urb(dev->bulk_in_urb, GFP_KERNEL);
	if (rv < 0) {
		err("%s - failed submitting read urb, error %d",
			__func__, rv);
		dev->bulk_in_filled = 0;
		rv = (rv == -ENOMEM) ? rv : -EIO;
		spin_lock_irq(&dev->err_lock);
		dev->ongoing_read = 0;
		spin_unlock_irq(&dev->err_lock);
	}

	return rv;
}

static ssize_t uvscopetek_read(struct file *file, char *buffer, size_t count,
			 loff_t *ppos)
{
	struct uvscopetek *dev;
	int rv;
	bool ongoing_io;

	printk(KERN_ALERT "read: disabled\n");
	return 0;

	if (!file) {
		printk(KERN_ALERT "read: null file\n");
		return 0;
	}
	
	dev = (struct uvscopetek *)file->private_data;
	
	if (!dev) {
		printk(KERN_ALERT "read: null dev\n");
		return 0;
	}

	/* if we cannot read at all, return EOF */
	if (!dev->bulk_in_urb || !count)
		return 0;

	/* no concurrent readers */
	rv = mutex_lock_interruptible(&dev->io_mutex);
	if (rv < 0)
		return rv;

	if (!dev->interface) {		/* disconnect() was called */
		rv = -ENODEV;
		goto exit;
	}

	/* if IO is under way, we must not touch things */
retry:
	spin_lock_irq(&dev->err_lock);
	ongoing_io = dev->ongoing_read;
	spin_unlock_irq(&dev->err_lock);

	if (ongoing_io) {
		/* nonblocking IO shall not wait */
		if (file->f_flags & O_NONBLOCK) {
			rv = -EAGAIN;
			goto exit;
		}
		/*
		 * IO may take forever
		 * hence wait in an interruptible state
		 */
		rv = wait_for_completion_interruptible(&dev->bulk_in_completion);
		if (rv < 0)
			goto exit;
		/*
		 * by waiting we also semiprocessed the urb
		 * we must finish now
		 */
		dev->bulk_in_copied = 0;
		dev->processed_urb = 1;
	}

	if (!dev->processed_urb) {
		/*
		 * the URB hasn't been processed
		 * do it now
		 */
		wait_for_completion(&dev->bulk_in_completion);
		dev->bulk_in_copied = 0;
		dev->processed_urb = 1;
	}

	/* errors must be reported */
	rv = dev->errors;
	if (rv < 0) {
		/* any error is reported once */
		dev->errors = 0;
		/* to preserve notifications about reset */
		rv = (rv == -EPIPE) ? rv : -EIO;
		/* no data to deliver */
		dev->bulk_in_filled = 0;
		/* report it */
		goto exit;
	}

	/*
	 * if the buffer is filled we may satisfy the read
	 * else we need to start IO
	 */

	if (dev->bulk_in_filled) {
		/* we had read data */
		size_t available = dev->bulk_in_filled - dev->bulk_in_copied;
		size_t chunk = min(available, count);

		if (!available) {
			/*
			 * all data has been used
			 * actual IO needs to be done
			 */
			rv = uvscopetek_do_read_io(dev, count);
			if (rv < 0)
				goto exit;
			else
				goto retry;
		}
		/*
		 * data is available
		 * chunk tells us how much shall be copied
		 */

		if (copy_to_user(buffer,
				 dev->bulk_in_buffer + dev->bulk_in_copied,
				 chunk))
			rv = -EFAULT;
		else
			rv = chunk;

		dev->bulk_in_copied += chunk;

		/*
		 * if we are asked for more than we have,
		 * we start IO but don't wait
		 */
		if (available < count)
			uvscopetek_do_read_io(dev, count - chunk);
	} else {
		/* no data in the buffer */
		rv = uvscopetek_do_read_io(dev, count);
		if (rv < 0)
			goto exit;
		else if (!(file->f_flags & O_NONBLOCK))
			goto retry;
		rv = -EAGAIN;
	}
exit:
	mutex_unlock(&dev->io_mutex);
	return rv;
}

#if 0
static void uvscopetek_write_bulk_callback(struct urb *urb)
{
	struct uvscopetek *dev;

	dev = urb->context;

	/* sync/async unlink faults aren't errors */
	if (urb->status) {
		if (!(urb->status == -ENOENT ||
		    urb->status == -ECONNRESET ||
		    urb->status == -ESHUTDOWN))
			err("%s - nonzero write bulk status received: %d",
			    __func__, urb->status);

		spin_lock(&dev->err_lock);
		dev->errors = urb->status;
		spin_unlock(&dev->err_lock);
	}

	/* free up our allocated buffer */
	usb_buffer_free(urb->dev, urb->transfer_buffer_length,
			urb->transfer_buffer, urb->transfer_dma);
	up(&dev->limit_sem);
}

static ssize_t uvscopetek_write(struct file *file, const char *user_buffer,
			  size_t count, loff_t *ppos)
{
	struct uvscopetek *dev;
	int retval = 0;
	struct urb *urb = NULL;
	char *buf = NULL;
	size_t writesize = min(count, (size_t)MAX_TRANSFER);

	dev = (struct uvscopetek *)file->private_data;

	/* verify that we actually have some data to write */
	if (count == 0)
		goto exit;

	/*
	 * limit the number of URBs in flight to stop a user from using up all
	 * RAM
	 */
	if (!(file->f_flags & O_NONBLOCK)) {
		if (down_interruptible(&dev->limit_sem)) {
			retval = -ERESTARTSYS;
			goto exit;
		}
	} else {
		if (down_trylock(&dev->limit_sem)) {
			retval = -EAGAIN;
			goto exit;
		}
	}

	spin_lock_irq(&dev->err_lock);
	retval = dev->errors;
	if (retval < 0) {
		/* any error is reported once */
		dev->errors = 0;
		/* to preserve notifications about reset */
		retval = (retval == -EPIPE) ? retval : -EIO;
	}
	spin_unlock_irq(&dev->err_lock);
	if (retval < 0)
		goto error;

	/* create a urb, and a buffer for it, and copy the data to the urb */
	urb = usb_alloc_urb(0, GFP_KERNEL);
	if (!urb) {
		retval = -ENOMEM;
		goto error;
	}

	buf = usb_buffer_alloc(dev->udev, writesize, GFP_KERNEL,
			       &urb->transfer_dma);
	if (!buf) {
		retval = -ENOMEM;
		goto error;
	}

	if (copy_from_user(buf, user_buffer, writesize)) {
		retval = -EFAULT;
		goto error;
	}

	/* this lock makes sure we don't submit URBs to gone devices */
	mutex_lock(&dev->io_mutex);
	if (!dev->interface) {		/* disconnect() was called */
		mutex_unlock(&dev->io_mutex);
		retval = -ENODEV;
		goto error;
	}

	/* initialize the urb properly */
	usb_fill_bulk_urb(urb, dev->udev,
			  usb_sndbulkpipe(dev->udev, dev->bulk_out_endpointAddr),
			  buf, writesize, uvscopetek_write_bulk_callback, dev);
	urb->transfer_flags |= URB_NO_TRANSFER_DMA_MAP;
	usb_anchor_urb(urb, &dev->submitted);

	/* send the data out the bulk port */
	retval = usb_submit_urb(urb, GFP_KERNEL);
	mutex_unlock(&dev->io_mutex);
	if (retval) {
		err("%s - failed submitting write urb, error %d", __func__,
		    retval);
		goto error_unanchor;
	}

	/*
	 * release our reference to this urb, the USB core will eventually free
	 * it entirely
	 */
	usb_free_urb(urb);


	return writesize;

error_unanchor:
	usb_unanchor_urb(urb);
error:
	if (urb) {
		usb_buffer_free(dev->udev, writesize, buf, urb->transfer_dma);
		usb_free_urb(urb);
	}
	up(&dev->limit_sem);

exit:
	return retval;
}
#endif

static const struct file_operations uvscopetek_fops = {
	.owner =	THIS_MODULE,
	.read =		uvscopetek_read,
	//.write =	uvscopetek_write,
	.open =		uvscopetek_open,
	.release =	uvscopetek_release,
	.flush =	uvscopetek_flush,
};

/*
 * usb class driver info in order to get a minor number from the usb core,
 * and to have the device registered with the driver core
 */
static struct usb_class_driver uvscopetek_class = {
	.name =		"uvscopetek%d",
	.fops =		&uvscopetek_fops,
	.minor_base =	uvscopetek_MINOR_BASE,
};

#define sdbg( _format, ... ) printk( KERN_INFO "uvscopetek: " _format, ## __VA_ARGS__ )


void print_probe_info( struct usb_interface *interface,
		      const struct usb_device_id *id ) {
	struct usb_host_interface *iface_desc = NULL;
	 int i;
		      
	sdbg("USB_DIR_OUT: 0x%02X\n", USB_DIR_OUT);
	sdbg("USB_DIR_IN: 0x%02X\n", USB_DIR_IN);
  			      
  	sdbg( "num_altsetting: %d\n", interface->num_altsetting);
  	sdbg("is first: %d\n", interface->cur_altsetting == interface->altsetting );
  	
	iface_desc = interface->cur_altsetting;
	if (iface_desc == NULL) {
		sdbg( "iface_desc NULL\n" );
		return;
	}
	sdbg( "bNumEndpoints: %d\n", iface_desc->desc.bNumEndpoints );
	for (i = 0; i < iface_desc->desc.bNumEndpoints; ++i) {
		struct usb_host_endpoint *endpoint_ = &iface_desc->endpoint[i];
		struct usb_endpoint_descriptor *endpoint = &endpoint_->desc;

		sdbg( "Endpoint %d", i );
		sdbg("\tbLength: 0x%02X\n", endpoint->bLength);
		sdbg("\tbDescriptorType: 0x%02X\n", endpoint->bDescriptorType);
		sdbg("\tbEndpointAddress: 0x%02X\n", endpoint->bEndpointAddress);
		sdbg("\tbmAttributes: 0x%02X\n", endpoint->bmAttributes);
		sdbg("\twMaxPacketSize: 0x%04X\n", endpoint->wMaxPacketSize );
		sdbg("\tbInterval: 0x%02X\n", endpoint->bInterval);
		
		if (endpoint->bEndpointAddress & USB_DIR_IN) {
			sdbg("USB_DIR_IN\n");
		} else {
			sdbg("USB_DIR_OUT\n");
		}
	}
}

static int uvscopetek_probe(struct usb_interface *interface,
		      const struct usb_device_id *id)
{
	struct uvscopetek *dev;
	struct usb_host_interface *iface_desc;
	struct usb_endpoint_descriptor *endpoint;
	size_t buffer_size;
	int i;
	int retval = -ENOMEM;

	/* allocate memory for our device state and initialize it */
	dev = kzalloc(sizeof(*dev), GFP_KERNEL);
	if (!dev) {
		err("Out of memory");
		goto error;
	}
	kref_init(&dev->kref);
	sema_init(&dev->limit_sem, WRITES_IN_FLIGHT);
	mutex_init(&dev->io_mutex);
	spin_lock_init(&dev->err_lock);
	init_usb_anchor(&dev->submitted);
	init_completion(&dev->bulk_in_completion);

	dev->udev = usb_get_dev(interface_to_usbdev(interface));
	dev->interface = interface;

	print_probe_info( interface, id );

	/* set up the endpoint information */
	/* use only the first bulk-in and bulk-out endpoints */
	iface_desc = interface->cur_altsetting;
	for (i = 0; i < iface_desc->desc.bNumEndpoints; ++i) {
		endpoint = &iface_desc->endpoint[i].desc;

		if (!dev->bulk_in_endpointAddr &&
		    usb_endpoint_is_bulk_in(endpoint)) {
			/* we found a bulk in endpoint */
			buffer_size = le16_to_cpu(endpoint->wMaxPacketSize);
			dev->bulk_in_size = buffer_size;
			dev->bulk_in_endpointAddr = endpoint->bEndpointAddress;
			printk(KERN_ALERT "Selected endpoint 0x%02X\n", dev->bulk_in_endpointAddr);
			dev->bulk_in_buffer = kmalloc(buffer_size, GFP_KERNEL);
			if (!dev->bulk_in_buffer) {
				err("Could not allocate bulk_in_buffer");
				goto error;
			}
			dev->bulk_in_urb = usb_alloc_urb(0, GFP_KERNEL);
			if (!dev->bulk_in_urb) {
				err("Could not allocate bulk_in_urb");
				goto error;
			}
		}

		#if 0
		if (!dev->bulk_out_endpointAddr &&
		    usb_endpoint_is_bulk_out(endpoint)) {
			/* we found a bulk out endpoint */
			dev->bulk_out_endpointAddr = endpoint->bEndpointAddress;
		}
		#endif
	}
	if (!(dev->bulk_in_endpointAddr/* && dev->bulk_out_endpointAddr*/)) {
		err("Could not find both bulk-in and bulk-out endpoints");
		goto error;
	}

	/* save our data pointer in this interface device */
	usb_set_intfdata(interface, dev);

	/* we can register the device now, as it is ready */
	retval = usb_register_dev(interface, &uvscopetek_class);
	if (retval) {
		/* something prevented us from registering this driver */
		err("Not able to get a minor for this device.");
		usb_set_intfdata(interface, NULL);
		goto error;
	}

	/* let the user know what node this device is now attached to */
	dev_info(&interface->dev,
		 "USB uvscopetek device now attached to uvscopetek-%d",
		 interface->minor);
	return 0;

error:
	if (dev)
		/* this frees allocated memory */
		kref_put(&dev->kref, uvscopetek_delete);
	return retval;
}

static void uvscopetek_disconnect(struct usb_interface *interface)
{
	struct uvscopetek *dev;
	int minor = interface->minor;

	dev = usb_get_intfdata(interface);
	usb_set_intfdata(interface, NULL);

	/* give back our minor */
	usb_deregister_dev(interface, &uvscopetek_class);

	/* prevent more I/O from starting */
	mutex_lock(&dev->io_mutex);
	dev->interface = NULL;
	mutex_unlock(&dev->io_mutex);

	usb_kill_anchored_urbs(&dev->submitted);

	/* decrement our usage count */
	kref_put(&dev->kref, uvscopetek_delete);

	dev_info(&interface->dev, "USB uvscopetek #%d now disconnected", minor);
}

static void uvscopetek_draw_down(struct uvscopetek *dev)
{
	int time;

	time = usb_wait_anchor_empty_timeout(&dev->submitted, 1000);
	if (!time)
		usb_kill_anchored_urbs(&dev->submitted);
	usb_kill_urb(dev->bulk_in_urb);
}

static int uvscopetek_suspend(struct usb_interface *intf, pm_message_t message)
{
	struct uvscopetek *dev = usb_get_intfdata(intf);

	if (!dev)
		return 0;
	uvscopetek_draw_down(dev);
	return 0;
}

static int uvscopetek_resume(struct usb_interface *intf)
{
	return 0;
}

static int uvscopetek_pre_reset(struct usb_interface *intf)
{
	struct uvscopetek *dev = usb_get_intfdata(intf);

	mutex_lock(&dev->io_mutex);
	uvscopetek_draw_down(dev);

	return 0;
}

static int uvscopetek_post_reset(struct usb_interface *intf)
{
	struct uvscopetek *dev = usb_get_intfdata(intf);

	/* we are sure no URBs are active - no locking needed */
	dev->errors = -EPIPE;
	mutex_unlock(&dev->io_mutex);

	return 0;
}

static struct usb_driver uvscopetek_driver = {
	.name =		"uvscopetek",
	.probe =	uvscopetek_probe,
	.disconnect =	uvscopetek_disconnect,
	.suspend =	uvscopetek_suspend,
	.resume =	uvscopetek_resume,
	.pre_reset =	uvscopetek_pre_reset,
	.post_reset =	uvscopetek_post_reset,
	.id_table =	uvscopetek_table,
	.supports_autosuspend = 1,
};

static int __init uvscopetek_init(void)
{
	int result;

	/* register this driver with the USB subsystem */
	result = usb_register(&uvscopetek_driver);
	if (result)
		err("usb_register failed. Error number %d", result);

	return result;
}

static void __exit uvscopetek_exit(void)
{
	/* deregister this driver with the USB subsystem */
	usb_deregister(&uvscopetek_driver);
}

module_init(uvscopetek_init);
module_exit(uvscopetek_exit);

MODULE_LICENSE("GPL");
