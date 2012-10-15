#include "gspca.h"

#define MODULE_NAME "uvscopetek"
MODULE_LICENSE("GPL");

struct sd {
	//Must be first
	struct gspca_dev gspca_dev;
	//Tracks how many bytes into a frame we are
	unsigned int fbytes;
};

//Not needed for PoC
static const struct ctrl sd_ctrls[] = {
};

//Capture was 640 X 480 so this is a good start
//Note that we could look this up as sizeimage for a more proper driver
#define FRAME_W 		640
#define FRAME_H 		480
#define FRAME_SZ 		(FRAME_W * FRAME_H)

static const struct v4l2_pix_format vga_mode[] = {
	{FRAME_W, FRAME_H,
		V4L2_PIX_FMT_SGBRG8,
		V4L2_FIELD_NONE,
		.bytesperline = FRAME_W,
		//Typically bytesperline * height 
		.sizeimage = FRAME_SZ,
		.colorspace = V4L2_COLORSPACE_SRGB},
};

/* this function is called at probe time */
static int sd_config(struct gspca_dev *gspca_dev,
			const struct usb_device_id *id)
{
	gspca_dev->cam.cam_mode = vga_mode;
	gspca_dev->cam.nmodes = ARRAY_SIZE(vga_mode);

	//Go automatic
	gspca_dev->cam.no_urb_create = 0;
	//Think setting this to 0 would make it more automatic
	gspca_dev->cam.bulk_nurbs = 2;
	//Maximum endpoint size, I think size of 0 would select this
	gspca_dev->cam.bulk_size = 0x400;
	//Use bulk transfers as opposed to isoc
	gspca_dev->cam.bulk = 1;
	//Note that reversing skips the first element since otherwise why would be reverse
	gspca_dev->cam.reverse_alts = 0;
	return 0;
}

/* this function is called at probe and resume time */
static int sd_init(struct gspca_dev *gspca_dev)
{
	sdbg("sd_init");

	return 0;
}

static int validate_read(void *expected, size_t expected_size,
		void *actual, size_t actual_size, const char *msg) {
	if (expected_size != actual_size) {
		printk(KERN_ALERT "read %s: expected %d bytes, got %d bytes\n",
				msg, expected_size, actual_size);
		return -1;
	}
	if (memcmp(expected, actual, expected_size)) {
		printk(KERN_ALERT "read %s: regions do not match\n", msg);
		return -1;
	}
	return 0;
}

static int validate_write( unsigned int size, int n_rw, const char *desc) {
	if (size != n_rw) {
		printk(KERN_ALERT "write %s failed: expected %u got %d",
				desc, size, n_rw);
		return -1;
	}
	return 0;
}

int replay_wireshark_setup_neo(struct gspca_dev *gspca_dev) {
	struct usb_device *udev = gspca_dev->dev;
	
	{
//Including the file makes it easier to regenerate
#include "replay.c"
	}
	
	return 0;
}

static int sd_start(struct gspca_dev *gspca_dev)
{
	struct urb *urb;

	gspca_dev->fbytes = 0;
	replay_wireshark_setup_neo(gspca_dev);

	return gspca_dev->usb_err;
}

static void sd_pkt_scan(struct gspca_dev *gspca_dev,
			u8 *data,		/* isoc packet */
			int len)		/* iso packet length */
{
	//if a frame is in progress see if we can finish it off
	if (gspca_dev->fbytes + len >= FRAME_SZ) {
		unsigned int remainder = FRAME_SZ - gspca_dev->fbytes;
		
		//Completed a frame
		gspca_frame_add(gspca_dev, LAST_PACKET,
				data, remainder);
		len -= remainder;
		data += remainder;
		gspca_dev->fbytes = 0;
	}
	if (len > 0) {
		if (gspca_dev->fbytes == 0)
			gspca_frame_add(gspca_dev, FIRST_PACKET, data, len);
		else
			gspca_frame_add(gspca_dev, INTER_PACKET, data, len);
		gspca_dev->fbytes += len;
	}
}

/* sub-driver description */
static const struct sd_desc sd_desc = {
	.name = MODULE_NAME,
	.ctrls = sd_ctrls,
	.nctrls = ARRAY_SIZE(sd_ctrls),
	.config = sd_config,
	.init = sd_init,
	.start = sd_start,
	.pkt_scan = sd_pkt_scan,
};

/* -- module initialisation -- */
static const __devinitdata struct usb_device_id device_table[] = {
	{USB_DEVICE(0x0547, 0x4D88)},
	{}
};
MODULE_DEVICE_TABLE(usb, device_table);

/* -- device connect -- */
static int sd_probe(struct usb_interface *intf,
			const struct usb_device_id *id)
{
	int rc = 0;
	rc = gspca_dev_probe(intf, id, &sd_desc, sizeof(struct sd), THIS_MODULE);
	return rc;
}

static struct usb_driver sd_driver = {
	.name = MODULE_NAME,
	.id_table = device_table,
	.probe = sd_probe,
	.disconnect = gspca_disconnect,
#ifdef CONFIG_PM
	.suspend = gspca_suspend,
	.resume = gspca_resume,
#endif
};

/* -- module insert / remove -- */
static int __init sd_mod_init(void)
{
	int ret;

	ret = usb_register(&sd_driver);
	if (ret < 0)
		return ret;
	return 0;
}
static void __exit sd_mod_exit(void)
{
	usb_deregister(&sd_driver);
}

module_init(sd_mod_init);
module_exit(sd_mod_exit);

