/*
 * AnchorChips / ScopeTek / AmScope  DCM and MDC camera driver
 *
 * Copyright (C) 2011 John McMaster <JohnDMcMaster@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
 */

#define MODULE_NAME "uvscopetek"

#include "gspca.h"

MODULE_AUTHOR("John McMaster");
MODULE_DESCRIPTION("Scopetek DCM/MDC high resolution camera driver");
MODULE_LICENSE("GPL");

#define sdbg( _format, ... ) printk( KERN_INFO "uvscopetek: " _format "\n", ## __VA_ARGS__ )
//#define sdbg_replay sdbg
#define sdbg_replay(...)



/* specific webcam descriptor */
struct sd {
	struct gspca_dev gspca_dev;	/* !! must be the first item */
	//How many bytes this frame
	unsigned int this_f;
	//Set to true if we think we can identify the start of a left right scan
	//Just worry about hsync and will check this for sanity
	//bool have_vsync;
	//Set to true if we think we can identify the start of frame
	//bool have_hsync;
	bool have_sync;
	//Bytes to throw away to complete a sync
	unsigned int sync_consume;
};

/* V4L2 controls supported by the driver */
static const struct ctrl sd_ctrls[] = {
};

//Andrew's guess
#define PIX_FMT		V4L2_PIX_FMT_SGBRG8
//#define PIX_FMT		V4L2_PIX_FMT_SBGGR8
//Website
//#define PIX_FMT		V4L2_PIX_FMT_RGB24
#define FRAME_W		640
#define FRAME_H		480
#define FRAME_SZ 		(FRAME_W * FRAME_H)
static const struct v4l2_pix_format vga_mode[] = {
	{640, 480,
		PIX_FMT,
		V4L2_FIELD_NONE,
		//padding bytes not data bytes?  V4L2 pdf doesn't indicate that
		//.bytesperline = 640,
		.bytesperline = 640,
		.sizeimage = 640 * 480,
		.colorspace = V4L2_COLORSPACE_SRGB},
};

#if MAX_NURBS < 4
#error "Not enough URBs in the gspca table"
#endif
#define SD_PKT_SZ 64
#define SD_NPKT 32


/* this function is called at probe time */
static int sd_config(struct gspca_dev *gspca_dev,
			const struct usb_device_id *id)
{
	sdbg("sd_config start");
	gspca_dev->cam.cam_mode = vga_mode;
	gspca_dev->cam.nmodes = ARRAY_SIZE(vga_mode);

	//FIXME: this might be able to simplify this driver
	gspca_dev->cam.no_urb_create = 0;
	//presumably above ignores this
	gspca_dev->cam.bulk_nurbs = 2;
	gspca_dev->cam.bulk_size = SD_PKT_SZ * SD_NPKT;
	gspca_dev->cam.bulk_size = 0x400;
	//Def need to use bulk transfers
	gspca_dev->cam.bulk = 1;
	
	//shouldn't really matter
	//oh yes it does...reversing skips the first element since otherwise why would be reverse
	gspca_dev->cam.reverse_alts = 0;
	sdbg("sd_config end");
	return 0;
}

/* this function is called at probe and resume time */
static int sd_init(struct gspca_dev *gspca_dev)
{
	sdbg("sd_init");

	return 0;
}

int validate_read(void *expected, size_t expected_size, void *actual, size_t actual_size, const char *msg) {
	if (expected_size != actual_size) {
		printk(KERN_ALERT "%s: expected %d bytes, got %d bytes\n", msg, expected_size, actual_size);
		return -1;
	}
	if (memcmp(expected, actual, expected_size)) {
		printk(KERN_ALERT "%s: regions do not match\n", msg);
		return -1;
	}
	sdbg_replay("%s: validate ok", msg);
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

int replay_wireshark_setup_neo(struct gspca_dev *gspca_dev) {
	struct usb_device *udev = gspca_dev->dev;
	
	sdbg("neo replay");
	{
#include "replay.c"
	}
	sdbg("neo replay done");
	return 0;
}

/* -- start the camera -- */
static int sd_start(struct gspca_dev *gspca_dev)
{
	struct sd *sd = NULL;

	sdbg("sd_start start XXX");
	
	sd = (struct sd *)gspca_dev;
	sd->this_f = 0;
	//sd->have_vsync = false;
	sd->have_sync = false;
	sd->sync_consume = 0;
	
	replay_wireshark_setup_neo(gspca_dev);

	sdbg("Not reinit URBs");
	sdbg("sd_start end");

	return gspca_dev->usb_err;
}

static u8 *try_sync(struct gspca_dev *gspca_dev,
			u8 *data,		/* isoc packet */
			int *lenp)		/* iso packet length */
{
	struct sd *sd = (struct sd *)gspca_dev;
	//Horizontal sync begins with "08 06 08 08 08 08 08 08"
	//Some of the later 08's are unreliable...will have to see how reliable these are
	const u8 look[] = {0x08, 0x06, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08};
	
	sdbg("Attempting frame sync...");
	
	while (*lenp >= sizeof(look)) {
		unsigned int i = 0;

		//Keep going as long as we can possibly make a match and 
		//Note that we might throw away a match this way but packets are large enough that
		//we can stand waiting for the next frame in the unlikely chance it occurs
		//1024 byte packet, 8 byte search
		for (i = 0; i < sizeof(look) && data[i] == look[i]; ++i) {
		}
		//Found it?
		if (i == sizeof(look)) {
			sdbg("Frame sync OK");
			//We are the second line in the frame
			//Don't try verifying the rest of the frame as it seems unreliable
			sd->sync_consume = FRAME_SZ - FRAME_W;
			sd->have_sync = true;
			return data;
		}
		//Nope, chop off the junk data
		//We might be able to chop off a little more but I'm not sure if it matters that much
		--(*lenp);
		++data;
	}
	sdbg("Failed sync");
	//Trash the rest, we still don't have sync
	data += *lenp;
	*lenp = 0;
	return data;
}

static void sd_pkt_scan(struct gspca_dev *gspca_dev,
			u8 *data,		/* isoc packet */
			int len)		/* iso packet length */
{
	int i = 0;
	static struct sd s_sd = {.this_f = 0};
	struct sd *sd = (struct sd *)gspca_dev;
	static bool first_sync = true;
	
	sd = &s_sd;
//return;
	/* unused */
	for (i = 0; i < len && i < 0x1; ++i) {
		sdbg("sd_pkt_scan[%d of %d]: 0x%02X", i, len, data[i]);
	}
	
	if (!first_sync) {
		//sdbg("first_sync kill");
		//return;
	}
	
	
#if 0
	if (!sd->have_sync) {
		//Fun time
		data = try_sync( gspca_dev, data, &len );
		if ((!sd->have_sync) && len != 0)
			sdbg("messed up sync?");
	}
	
	if (sd->sync_consume) {
		sdbg("Got %u of %u needed to sync, %u", len, sd->sync_consume, sd->have_sync );
		if (len < sd->sync_consume) {
			sd->sync_consume -= len;
			len = 0;
		} else {
			len -= sd->sync_consume;
			sd->sync_consume = 0; 
			sdbg("Sync'd, %u data left, frame has %u", len, sd->this_f);
		}
	}
#endif
	//if a frame is in progress see if we can finish it off
	//do {
		if (sd->this_f + len >= FRAME_SZ) {
			unsigned int remainder = FRAME_SZ - sd->this_f;
			sdbg("Completing frame, so far %u + %u new >= %u frame size just getting the last %u of %u",
					sd->this_f, len, FRAME_SZ, remainder, FRAME_SZ);
			//Completed a frame
			gspca_frame_add(gspca_dev, LAST_PACKET,
					data, remainder);
			//FRAME_SZ = 0;
			len -= remainder;
			data += remainder;
			sd->this_f = 0;
		}
		if (len > 0) {
			if (sd->this_f == 0) {
				sdbg("start frame w/ %u bytes", len);
				gspca_frame_add(gspca_dev, FIRST_PACKET,
						data, len);
			} else {
				sdbg("continue frame w/ %u new bytes w/ %u so far of needed %u", len, sd->this_f, FRAME_SZ);
				gspca_frame_add(gspca_dev, INTER_PACKET,
						data, len);
			}
			sd->this_f += len;
		}
	//} while (len > 0);
	
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

#define UVSCOPETEK_VENDOR_ID	0x0547
#define UVSCOPETEK_PRODUCT_ID	0x4D88

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
	sdbg("sd_probe start, alt 0x%p", intf->cur_altsetting);
	rc = gspca_dev_probe(intf, id, &sd_desc, sizeof(struct sd),
				THIS_MODULE);
	sdbg("sd_probe done");
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
	info("registered");
	return 0;
}
static void __exit sd_mod_exit(void)
{
	usb_deregister(&sd_driver);
	info("deregistered");
}

module_init(sd_mod_init);
module_exit(sd_mod_exit);

