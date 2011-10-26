/*
 * AnchorChips / ScopeTek / AmScope  DCM and MDC camera driver
 *
 * Copyright (C) 2011 John McMaster <JohnDMcMaster@gmail.com>
 *
 * Original copyright:
 * Benq DC E300 subdriver
 * Copyright (C) 2009 Jean-Francois Moine (http://moinejf.free.fr)
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

#define MODULE_NAME "benq"

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
};

/* V4L2 controls supported by the driver */
static const struct ctrl sd_ctrls[] = {
};

//Andrew's guess
#define PIX_FMT		V4L2_PIX_FMT_SGBRG8
//Website
//#define PIX_FMT		V4L2_PIX_FMT_RGB24
static const struct v4l2_pix_format vga_mode[] = {
	{640, 480, PIX_FMT, V4L2_FIELD_NONE,
		.bytesperline = 640,
		.sizeimage = 640 * 480,
		.colorspace = V4L2_COLORSPACE_SRGB},
};

static unsigned int g_bytes = 0;
static unsigned int g_frame_size = 640 * 480;

#if MAX_NURBS < 4
#error "Not enough URBs in the gspca table"
#endif
#define SD_PKT_SZ 64
#define SD_NPKT 32

static void sd_isoc_irq(struct urb *urb);


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
	struct urb *urb;
	int i, n;

	sdbg("sd_start start XXX");
	
	g_bytes = 0;
	replay_wireshark_setup_neo(gspca_dev);

	if (true) {
		sdbg("Not reinit URBs");
	} else {
		sdbg("Reinit URBs");
		/* create 2 URBs on endpoint 0x082 */
		for (n = 0; n < 2; n++) {
			urb = usb_alloc_urb(SD_NPKT, GFP_KERNEL);
			if (!urb) {
				err("usb_alloc_urb failed");
				return -ENOMEM;
			}
			gspca_dev->urb[n] = urb;
			urb->transfer_buffer = usb_buffer_alloc(gspca_dev->dev,
							SD_PKT_SZ * SD_NPKT,
							GFP_KERNEL,
							&urb->transfer_dma);

			if (urb->transfer_buffer == NULL) {
				err("usb_buffer_alloc failed");
				return -ENOMEM;
			}
			urb->dev = gspca_dev->dev;
			urb->context = gspca_dev;
			urb->transfer_buffer_length = SD_PKT_SZ * SD_NPKT;
			urb->pipe = usb_rcvisocpipe(gspca_dev->dev,
						0x82);
			urb->transfer_flags = URB_ISO_ASAP
						| URB_NO_TRANSFER_DMA_MAP;
			urb->interval = 1;
			urb->complete = sd_isoc_irq;
			urb->number_of_packets = SD_NPKT;
			for (i = 0; i < SD_NPKT; i++) {
				urb->iso_frame_desc[i].length = SD_PKT_SZ;
				urb->iso_frame_desc[i].offset = SD_PKT_SZ * i;
			}
		}
	}
	sdbg("sd_start end");

	return gspca_dev->usb_err;
}

static void sd_pkt_scan(struct gspca_dev *gspca_dev,
			u8 *data,		/* isoc packet */
			int len)		/* iso packet length */
{
	int i = 0;
	
	/* unused */
	for (i = 0; i < len && i < 0x1; ++i) {
		sdbg("sd_pkt_scan[%d of %d]: 0x%02X", i, len, data[i]);
	}
	
	//if a frame is in progress see if we can finish it off
	//do {
		if (g_bytes + len >= g_frame_size) {
			unsigned int remainder = g_frame_size - len;
			sdbg("Completing frame");
			//Completed a frame
			gspca_frame_add(gspca_dev, LAST_PACKET,
					data, remainder);
			g_frame_size = 0;
			len -= remainder;
			data += remainder;
			g_bytes = 0;
		}
		if (len > 0) {
			if (g_bytes == 0) {
				sdbg("start frame");
				gspca_frame_add(gspca_dev, FIRST_PACKET,
						data, len);
			} else {
				sdbg("continue frame");
				gspca_frame_add(gspca_dev, INTER_PACKET,
						data, len);
			}
			g_bytes += len;
		}
	//} while (len > 0);
	
}

/* reception of an URB */
static void sd_isoc_irq(struct urb *urb)
{
	struct gspca_dev *gspca_dev = (struct gspca_dev *) urb->context;
	u8 *data;
	int i, st;

	sdbg("sd_isoc_irq\n");
	PDEBUG(D_PACK, "sd isoc irq");
	if (!gspca_dev->streaming)
		return;
	if (urb->status != 0) {
		if (urb->status == -ESHUTDOWN)
			return;		/* disconnection */
#ifdef CONFIG_PM
		if (gspca_dev->frozen)
			return;
#endif
		PDEBUG(D_ERR|D_PACK, "urb status: %d", urb->status);
		return;
	}
	
	for (i = 0; i < urb->number_of_packets; i++) {
		unsigned int data_len = 0;
		/* check the packet status and length */
		/*
		my lengths aren't picky, I take what I can get
		they seem to float everywhere
		
		if (urb->iso_frame_desc[i].actual_length != SD_PKT_SZ) {
			PDEBUG(D_ERR, "ISOC bad lengths %d / %d",
				urb->iso_frame_desc[i].actual_length);
			gspca_dev->last_packet_type = DISCARD_PACKET;
			continue;
		}
		*/
		
		data_len = urb->iso_frame_desc[i].actual_length;
		st = urb->iso_frame_desc[i].status;
		if (st == 0)
			st = urb->iso_frame_desc[i].status;
		if (st) {
			PDEBUG(D_ERR,
				"ISOC data error: [%d] status=%d",
				i, st);
			gspca_dev->last_packet_type = DISCARD_PACKET;
			continue;
		}
		data = (u8 *) urb->transfer_buffer
					+ urb->iso_frame_desc[i].offset;
		sd_pkt_scan(gspca_dev, data, data_len);
	}

	/* resubmit the URBs */
	st = usb_submit_urb(urb, GFP_ATOMIC);
	if (st < 0)
		PDEBUG(D_ERR|D_PACK, "usb_submit_urb() ret %d", st);
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

