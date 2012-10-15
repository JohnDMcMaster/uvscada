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


#define BUFF_SZ		0x14000
//static uint8_t g_buff[BUFF_SZ];
static uint8_t *g_buff_alloc = NULL;

/* Get a minor range for your devices from the usb maintainer */
#define uvscopetek_MINOR_BASE	192

/* our private defines. if this grows any larger, use your own .h file */
#define MAX_TRANSFER		(PAGE_SIZE - 512)
/* MAX_TRANSFER is chosen so that the VM is not stressed by
   allocations > PAGE_SIZE and the number of packets in a page
   is an integer 512 is the largest possible packet on EHCI */
#define WRITES_IN_FLIGHT	8
/* arbitrarily chosen */


#define sdbg( _format, ... ) printk( KERN_INFO "uvscopetek: " _format "\n", ## __VA_ARGS__ )
//#define sdbg_write sdbg
#define sdbg_write(...)


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
	//struct v4l2_device v4l2;
};
#define to_uvscopetek_dev(d) container_of(d, struct uvscopetek, kref)

static struct usb_driver uvscopetek_driver;
static void uvscopetek_draw_down(struct uvscopetek *dev);

static void uvscopetek_delete(struct kref *kref)
{
	struct uvscopetek *dev = to_uvscopetek_dev(kref);

	kfree(g_buff_alloc);
	g_buff_alloc = NULL;

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
	sdbg_write("%s: validate ok", msg);
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
	unsigned int pipe = 0;
	
	//XXX: should be endpoint 2?
	//82 should be mass data, 81 should be config in dump
	//but vmware can do funny stuff to device IDs
	if (requesttype & USB_DIR_IN) {
		pipe = usb_rcvctrlpipe(dev->udev, 0);
		printk(KERN_ALERT "creating recv pipe, buff 0x%p, size %d", bytes, size);
	} else {
		printk(KERN_ALERT "creating send pipe");
		pipe = usb_sndctrlpipe(dev->udev, 0);
	}
	rc_tmp = usb_control_msg(dev->udev, pipe,
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

int replay_wireshark_setup_orig(struct uvscopetek *dev);
int replay_wireshark_setup_neo(struct uvscopetek *dev);
int replay_wireshark_setup_twain(struct uvscopetek *dev);

int replay_wireshark_setup(struct uvscopetek *dev) {
	//Note: we still get image data even without these,
	//presumably it has default config
	
	//return replay_wireshark_setup_twain(dev);
	//Either of these two seem to do fine, twain capture makes mplayer timeout on packets
	return replay_wireshark_setup_neo(dev);
	//return replay_wireshark_setup_orig( dev );
	return 0;
}

int validate_write( unsigned int size, int n_rw, const char *desc) {
	if (size != n_rw) {
		sdbg("write %s failed: expected %u got %d",
				desc, size, n_rw);
		return -1;
	}
	return 0;
}

int send_bright(struct uvscopetek *dev, unsigned int wValue ) {
	int n_rw = 0;
	char buff[16];
	
	n_rw = usb_control_msg(dev->udev, usb_rcvctrlpipe(dev->udev, 0), 0x0B, 0x0C, wValue, 12306, buff, 1, 500);
	if (validate_read((char[]){0x08}, 1, buff, n_rw, "packet test") < 0)
		return 1;
	return 0;
}

int replay_wireshark_setup_neo(struct uvscopetek *dev) {
	sdbg("neo replay");
	{
#include "replay.c"

		if (false) {
			unsigned int wValue[] = {0x0292, 0x02C1, 0x02F0, 0x031F, 0x034E, 0x037D, 0x03AC, 0x03DB, 0x040A, 0x0439, 0x0468, 0x0497, 0x04C6};
			unsigned int i ;
			for (i = 0; i < sizeof(wValue) / sizeof(wValue[0]); ++i) {
				if (send_bright(dev, wValue[i]) < 0)
					return 1;
			}
		}
	}

	sdbg("neo replay done");
	return 0;
}

int replay_wireshark_setup_twain(struct uvscopetek *dev) {
	sdbg("twain replay");
	{
#include "twain_replay.c"
	}
	sdbg("twain replay done");
	return 0;
}

int replay_wireshark_setup_orig(struct uvscopetek *dev) {
	printk(KERN_ALERT "Replaying wireshark stuff 1\n");
	{
#include "replay_orig.c"
	}
	printk(KERN_ALERT "Replaying success!\n");
	return 0;
}

static int update_buffer(struct uvscopetek *dev, unsigned int count) {
	static int counter = 0;
	uint8_t pois = 0xFF;
	int actual_length = 0;
	int rv = 0;
	unsigned int i = 0;
	
	sdbg_write("count %d", count);
	if (count > 0x400) {
		count = 0x400;
	}
	//memset( g_buff, pois, sizeof(g_buff) );
	memset( g_buff_alloc, pois, BUFF_SZ );
	for (i = 0; actual_length == 0 && i < 16; ++i) {
		rv = usb_bulk_msg(dev->udev,
				usb_rcvbulkpipe(dev->udev, dev->bulk_in_endpointAddr),
				g_buff_alloc,
				count, &actual_length, 500);
		//printk("rv %d, read %d\n", rv, actual_length);
		if (rv) {
			printk(KERN_ALERT "failed read :( %d\n", rv);
			printk(KERN_ALERT "count %d\n", count);
			return rv;
		}
		if (actual_length < 0) {
			printk(KERN_ALERT "failed read w/ length %d\n", actual_length);
			return -1;
		}
	}
	/*
	{
		int nz = 0;
		unsigned int i = 0;
		for (i = 0; i < actual_length; ++i) {
			if (i < 10)
				printk(KERN_ALERT "0x%02X\n", (unsigned int)g_buff_alloc[i]);
			if (g_buff_alloc[i] != pois) {
				printk(KERN_ALERT "HIT @ 0x%04X!\n", i);
				++nz;
			}
		}
		printk(KERN_ALERT "nz: %d\n", nz);
		sdbg_write("nz: %d", nz);
	}
	*/
	sdbg("count %d => %d", count, actual_length);
	
	counter += actual_length;
	if (actual_length >= 640 * 480) {
		send_bright(dev, 0x0100);
		counter = 0;
	}
	
	
	return actual_length;
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


	if (dev->open_count) {
		printk(KERN_ALERT "open: already open (%d)\n", dev->open_count);
		retval = -EBUSY;
		mutex_unlock(&dev->io_mutex);
		kref_put(&dev->kref, uvscopetek_delete);
		goto exit;
	}
		
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
	//update_buffer(dev, 123);
	
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


static int uvscopetek_do_read_io(struct uvscopetek *dev, size_t count) /*__attribute__ ((unused))*/
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
	//bool ongoing_io;
	int actual_length = 0;

	//printk(KERN_ALERT "read: disabled\n");
	//return 0;

	if (BUFF_SZ < count) {
		printk(KERN_ALERT "buffer too big\n");
		return 0;
	}

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

	actual_length = update_buffer(dev, count);
	/*
	static inline __must_check long __copy_to_user(void __user *to,
			const void *from, unsigned long n)
	*/
	if (copy_to_user(buffer,
			 g_buff_alloc,
			 actual_length)) {
		printk(KERN_ALERT "failed to copy to user\n");
		rv = -EFAULT;
		goto exit;
	}
	sdbg_write( "ZOMG SUCCESS!!11! w/ %d", actual_length);
	
	rv = actual_length;

#if 0
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
	
#endif

exit:
	mutex_unlock(&dev->io_mutex);
	sdbg_write("returning %d", rv );
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
		sdbg( "iface_desc NULL" );
		return;
	}
	sdbg( "bNumEndpoints: %d", iface_desc->desc.bNumEndpoints );
	for (i = 0; i < iface_desc->desc.bNumEndpoints; ++i) {
		struct usb_host_endpoint *endpoint_ = &iface_desc->endpoint[i];
		struct usb_endpoint_descriptor *endpoint = &endpoint_->desc;

		sdbg( "Endpoint %d", i );
		sdbg("\tbLength: 0x%02X", endpoint->bLength);
		sdbg("\tbDescriptorType: 0x%02X", endpoint->bDescriptorType);
		sdbg("\tbEndpointAddress: 0x%02X", endpoint->bEndpointAddress);
		sdbg("\tbmAttributes: 0x%02X", endpoint->bmAttributes);
		sdbg("\twMaxPacketSize: 0x%04X", endpoint->wMaxPacketSize );
		sdbg("\tbInterval: 0x%02X", endpoint->bInterval);
		
		if (endpoint->bEndpointAddress & USB_DIR_IN) {
			sdbg("USB_DIR_IN");
		} else {
			sdbg("USB_DIR_OUT");
		}
	}
}

#if 0
/*
Generated by uvusbreplay 0.1
uvusbreplay copyright 2011 John McMaster <JohnDMcMaster@gmail.com>
Date: 10/22/11 13:49:23.
Source data: /home/mcmaster/document/external/uvscopetek/captures/twain_image/wireshark/1/640x320_wireshark.cap
Source range: 294 - 295
*/
int n_rw = 0;
char buff[64];
//Generated from packet 294/295
n_rw = usb_control_msg(dev->udev, usb_rcvctrlpipe(dev->udev, 0), 0x0B, USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0263, 0x3012, buff, 1, 500);
if (validate_read((char[]){0x08}, 1, buff, n_rw, "packet 294/295") < 0)
        return 1;

*/
#endif


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
	(void)uvscopetek_do_read_io;

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
	printk(KERN_ALERT "Using bulk in address 0x%02X\n", dev->bulk_in_endpointAddr);

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

	g_buff_alloc = kzalloc(BUFF_SZ, GFP_KERNEL);
	if (!g_buff_alloc) {
		err("Out of memory");
		return -1;
	}

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
