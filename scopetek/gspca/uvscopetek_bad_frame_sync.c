/*
 * AnchorChips / ScopeTek / AmScope  DCM and MDC camera driver
 *
 * Copyright (C) 2011 John McMaster <JohnDMcMaster@gmail.com>
 *
 * Thanks to Sean O'Sullivan and the Rensselaer Polytech Center for Open
 * Source Software (RCOS) for their support developing open source projects!
 * While they did not contribute directly to this driver, they really helped
 * me to start contributing to open source projects.
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
	{FRAME_W, FRAME_H,
		PIX_FMT,
		V4L2_FIELD_NONE,
		//padding bytes not data bytes?  V4L2 pdf doesn't indicate that
		//.bytesperline = 640,
		.bytesperline = FRAME_W,
		.sizeimage = FRAME_SZ,
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

//Second pixel
#define SYNC_HOFFSET		1
//Second line
#define SYNC_VOFFSET		1
	
static void sd_pkt_scan(struct gspca_dev *gspca_dev,
			u8 *data,		/* isoc packet */
			int len)		/* iso packet length */
{
	static bool first_sync = true;
	
	int i = 0;
	struct sd *sd = (struct sd *)gspca_dev;
	
	if (true) {
		for (i = 1; i < len && i < 0x2; ++i)
			sdbg("sd_pkt_scan[%d of %d]: 0x%02X", i, len, data[i]);
	}
	
	if (!first_sync) {
		//sdbg("first_sync kill");
		//return;
	}
		
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
	
#if 0
	//If we have data see if we can make a sync check
	if (false && len) {
		/*
		Always do the frame sync if its in current range
		line sync at 640 * n + 2 where n != 1
		frame sync at 642
		*/
		unsigned int nlen = len + sd->this_f;
		
		//Can we do a frame sync?
		if (sd->this_f < 642 && nlen >= 642) {
			unsigned int syncd_o = 642 - sd->this_f - 1;
			u8 syncd = data[syncd_o];
			
			sd->have_sync = syncd == 0x06;
			if (!sd->have_sync) {
				sdbg("lost hsync @ %u", syncd_o);
			}
		//How about a low order sync
		} /*else if (sd->this_f < 2 && nlen >= 2) {
			unsigned int prev = 2 - sd->this_f;
			unsigned int new = 640 - prev;
			u8 syncd = data[new - 1];
		//A standard sync
		} else if () {
		}
		*/
#if 0		
		/*
		p previous packets
		c current packets
		if 
		
		
		
		0: need 2
		1: need 1
		2: need FRAME_W
		...
		FRAME_W: need 2
		FRAME_W + 1: need 1
		FRAME_W + 2: need FRAME_W
		*/
		//unsigned int next_frame_pos = sd->this_f
		//unsigned int have = ((sd->this_f + SYNC_HOFFSET) % FRAME_W) + SYNC_HOFFSET;
		
		//0 => FRAME_W - 1
		//1 => 0
		//2 => 1
		unsigned int have = sd->this_f;
		unsigned int needed = 2;
		
		//Take to nearest frame
		if (sd->this_f > SYNC_HOFFSET) {
			have = (sd->this_f - SYNC_HOFFSET + FRAME_W) % FRAME_W;
			needed = FRAME_W - have;
		}
		//unsigned int needed = FRAME_W + 2;
		//Sync is second byte on line
		//unsigned int frame_already = ((sd->this_f + 1) % FRAME_W);
		//if (frame_already + len >= FRAME_W) % 
		
		//Note that needed is at least 1
		if (len >= needed) {
			//The second line byte is 0x08 except on the frame sync line
			//Range 2 to 641 inclusive
			//bool is_frame_line = sd->this_f >= SYNC_HOFFSET * SYNC_VOFFSET + 1 && sd->this_f < SYNC_HOFFSET * SYNC_VOFFSET + FRAME_W + 1;
			bool is_frame_line = sd->this_f >= 2 && sd->this_f <= 641;
			unsigned int syncd_offset = needed - 1;
			u8 syncd = data[syncd_offset];
			
			if (is_frame_line ? syncd != 0x06 : syncd != 0x08) {
#endif
				//sdbg("Lost sync @ %u + %u w/ 0x%02X, needed 0x%04X (%u), have 0x%04X, look @ 0x%04X",
				//		sd->this_f, len, syncd, needed, needed, have, syncd_offset);
			  	//sdbg("is_frame_line: %d", is_frame_line);
		  	if (!sd->have_sync) {
			  	sd->have_sync = false;
				if (first_sync) {
			  		//print_hex_dump(KERN_ALERT, "uvscopetek packet lsync XXX: ", DUMP_PREFIX_ADDRESS, 16, 1, data + needed - 4, 16, false);
			  		print_hex_dump(KERN_ALERT, "uvscopetek packet lsync: ", DUMP_PREFIX_ADDRESS, 16, 1, data, len, false);
			  		first_sync = false;
				}

				//If we were in the middle of a frame invalidate it
				if (sd->this_f)
					gspca_frame_add(gspca_dev, LAST_PACKET, NULL, 0);
				//We will wait for next data to sync, don't try any fancy looping
				sd->this_f = 0;
				len = 0;
			} else
				sdbg("sync OK");
		//}
		//We just happend to be on a boundary, don't sweat it as this seems unlikely
	}
#endif

	if (sd->this_f + len >= FRAME_SZ) {
		unsigned int remainder = FRAME_SZ - sd->this_f;
		sdbg("Completing, so far %u + %u new >= %u frame size, rxing last %u of %u",
				sd->this_f, len, FRAME_SZ, remainder, FRAME_SZ);
		//Completed a frame
		gspca_frame_add(gspca_dev, LAST_PACKET, data, remainder);
		//FRAME_SZ = 0;
		len -= remainder;
		data += remainder;
		sd->this_f = 0;
	}
	if (len > 0) {
		if (sd->this_f == 0) {
			sdbg("start frame w/ %u bytes", len);
	  		print_hex_dump(KERN_ALERT, "uvscopetek packet start: ", DUMP_PREFIX_ADDRESS, 16, 1, data, len, false);
			gspca_frame_add(gspca_dev, FIRST_PACKET,
					data, len);
		} else {
			sdbg("continue frame w/ %u new bytes w/ %u so far of needed 0x%02X",
					len, sd->this_f, FRAME_SZ);
			gspca_frame_add(gspca_dev, INTER_PACKET, data, len);
		}
		sd->this_f += len;
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

