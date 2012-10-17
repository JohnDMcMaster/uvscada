/*
 * AnchorChips FX2 / ToupTek UCMOS / AmScope MU series camera driver
 * TODO: bundle in ScopeTek / AmScope MDC cameras
 *
 * Copyright (C) 2012 John McMaster <JohnDMcMaster@gmail.com>
 *
 * Thanks to Sean O'Sullivan / the Rensselaer Center for Open Source
 * Software (RCOS) for helping me learn kernel development
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

#include <linux/kernel.h>
#include <linux/errno.h>
#include <linux/init.h>
#include <linux/slab.h>
#include <linux/module.h>
#include <linux/kref.h>
#include <linux/uaccess.h>
#include <linux/usb.h>
#include <linux/mutex.h>
#include "gspca.h"

#define INDEX_EXPOSURE      0x3012

#define INDEX_WIDTH         0x034C
#define INDEX_HEIGHT        0x034E
    
//Range 0x1000 (nothing) to 0x11FF (highest)
//At least thats what the win driver does...
//in pratice you can crank it up much higher
#define GAIN_BASE           0x1000
#define GAIN_MAX            0x01FF
#define INDEX_GAIN_GTOP     0x3056
#define INDEX_GAIN_B        0x3058
#define INDEX_GAIN_R        0x305A
#define INDEX_GAIN_GBOT     0x305C

#define MODULE_NAME "touptek"

MODULE_AUTHOR("John McMaster");
MODULE_DESCRIPTION("ToupTek UCMOS / Amscope MU microscope camera driver");
MODULE_LICENSE("GPL");

//#define sdbg(...)
#define sdbg( _format, ... ) printk( KERN_INFO "touptek DBG:%u: " _format "\n", __LINE__, ## __VA_ARGS__ )

#define sdinfo( _format, ... ) printk( KERN_INFO "touptek INFO:%u: " _format "\n", __LINE__, ## __VA_ARGS__ )
#define sdalert( _format, ... ) printk( KERN_INFO "touptek ALERT:%u: " _format "\n", __LINE__, ## __VA_ARGS__ )


/* specific webcam descriptor */
struct sd {
	struct gspca_dev gspca_dev;	/* !! must be the first item */
	//How many bytes this frame
	unsigned int this_f;
};

/* V4L2 controls supported by the driver */
static const struct ctrl sd_ctrls[] = {
    //FIXME: add gain and exposure controls
};

#define PIX_FMT		V4L2_PIX_FMT_SGBRG8
#define COLORSPACE  V4L2_COLORSPACE_SRGB

int do_reg_write(struct gspca_dev *dev, int wValue, int wIndex);

static const struct v4l2_pix_format vga_mode[] = {
	/*
	{800, 600,
		PIX_FMT,
		V4L2_FIELD_NONE,
		.bytesperline = 800,
		.sizeimage = 800 * 600,
		.colorspace = COLORSPACE},
	*/
	{1600, 1200,
		PIX_FMT,
		V4L2_FIELD_NONE,
		.bytesperline = 1600,
		.sizeimage = 1600 * 1200,
		.colorspace = V4L2_COLORSPACE_SRGB},
	/*
	{3264, 2448,
		PIX_FMT,
		V4L2_FIELD_NONE,
		.bytesperline = 3264,
		.sizeimage = 3264 * 2448,
		.colorspace = V4L2_COLORSPACE_SRGB},
	*/
};

#if MAX_NURBS < 4
#error "Not enough URBs in the gspca table"
#endif

#define reg_write(_value, _index) do { \
    int _rc = do_reg_write(dev, _value, _index ); \
    if (_rc) { \
        sdbg("failed"); \
        return _rc; \
    } \
} while(0)

int val_reply(const char *reply, int rc)
{
    if (rc < 0) {
        sdalert("reply has error %d", rc);
        return -EIO;
    }
    if (rc != 1) {
        sdalert("Bad reply size %d", rc);
        return -EIO;
    }
    if (reply[0] != 0x08) {
        sdalert("Bad reply 0x%02X", reply[0]);
        return -EIO;
    }
    return 0;
}

#define chk_ptr(_ptr) do { \
    if (_ptr == NULL) { \
        sdalert("Bad pointer"); \
        return -EFAULT;\
    } \
} while (0)

int do_reg_write(struct gspca_dev *dev, int wValue, int wIndex)
{
    char buff[1];
    int rc;
    
    chk_ptr(dev);
    
    rc = usb_control_msg(dev->dev, usb_rcvctrlpipe(dev->dev, 0),
            0x0B, 0xC0, wValue, wIndex, buff, 1, 500);
    sdbg("Sent bRequest=0x0C, bValue=0x0B, wValue=0x%04X, wIndex=0x%04X, rc = %d, ret = {0x%02X}",
            wValue, wIndex, rc, buff[0]);
    if (rc < 0) {
        sdalert("Failed reg_write(0x0B, 0xC0, 0x%04X, 0x%04X) w/ rc %d",
                wValue, wIndex, rc);
        return rc;
    }
    if (val_reply(buff, rc)) {
        sdalert("Bad reply to reg_write(0x0B, 0xC0, 0x%04X, 0x%04X\n",
                wValue, wIndex);
        return -EIO;
    }
    return 0;
}

int width(struct gspca_dev *dev) {
     const struct v4l2_pix_format *cam_mode = dev->cam.cam_mode;
     
    chk_ptr(dev);
    
    //is this needed?
    if (cam_mode == NULL) {
        sdalert("it can happen");
        return -EIO;
    }
    return cam_mode->width;
}

int height(struct gspca_dev *dev) {
     const struct v4l2_pix_format *cam_mode = dev->cam.cam_mode;
     
    chk_ptr(dev);
    
    //is this needed?
    if (cam_mode == NULL) {
        sdalert("it can happen");
        return -EIO;
    }
    return cam_mode->height;
}

int size(struct gspca_dev *dev) {
     const struct v4l2_pix_format *cam_mode = dev->cam.cam_mode;
     
    chk_ptr(dev);
    
    //is this needed?
    if (cam_mode == NULL) {
        sdalert("it can happen");
        return -EIO;
    }
    return cam_mode->sizeimage;
}

int set_exposure(struct gspca_dev *dev, unsigned int exposure_ms)
{
    uint16_t wValue;
    unsigned int w;
    
    chk_ptr(dev);
    w = width(dev);
    
    if (w == 800) {
        wValue = exposure_ms * 5;
    } else if (w == 1600) {
        wValue = exposure_ms * 3;
    } else if (w == 3264) {
        wValue = exposure_ms * 3 / 2;
    } else {
        sdbg("Invalid width %u", w);
        return -EINVAL;
    }
    //Wonder if theres a good reason for sending it twice
    reg_write(wValue, INDEX_EXPOSURE);
    reg_write(wValue, INDEX_EXPOSURE);
    
    return 0;
}

int set_gain(struct gspca_dev *dev)
{
    chk_ptr(dev);
    
    //TODO: add argument to configure
    //These are white balanced settings for "3.0" on a particular setup
    reg_write(0x11C5, INDEX_GAIN_GTOP);
    reg_write(0x11CF, INDEX_GAIN_B);
    reg_write(0x11ED, INDEX_GAIN_GBOT);
    reg_write(0x11C5, INDEX_GAIN_R);
    
    return 0;
}

//Packets that were encrypted
int configure_encrypted(struct gspca_dev *dev)
{
    unsigned int rc;
    unsigned int w;
    
    chk_ptr(dev);
    w = width(dev);
    
    sdbg("Encrypted begin, w = %u", w);
    reg_write(0x0100, 0x0103);
    sdbg("Past first packet");
    
    reg_write(0x0000, 0x0100);
    reg_write(0x0100, 0x0104);
    reg_write(0x0004, 0x0300);
    reg_write(0x0001, 0x0302);
    reg_write(0x0008, 0x0308);
    reg_write(0x0001, 0x030A);
    reg_write(0x0004, 0x0304);
    reg_write(0x0040, 0x0306);
    reg_write(0x0000, 0x0104);
    reg_write(0x0100, 0x0104);

    if (w == 800) {
        reg_write(0x0060, 0x0344);
        reg_write(0x0CD9, 0x0348);
        reg_write(0x0036, 0x0346);
        reg_write(0x098F, 0x034A);
        reg_write(0x07C7, 0x3040);
    } else if (w == 1600) {
        reg_write(0x009C, 0x0344);
        reg_write(0x0D19, 0x0348);
        reg_write(0x0068, 0x0346);
        reg_write(0x09C5, 0x034A);
        reg_write(0x06C3, 0x3040);
    } else if (w == 3264) {
        reg_write(0x00E8, 0x0344);
        reg_write(0x0DA7, 0x0348);
        reg_write(0x009E, 0x0346);
        reg_write(0x0A2D, 0x034A);
        reg_write(0x0241, 0x3040);
    } else {
        sdbg("bad width %u", w);
        return -EINVAL;
    }
    reg_write(0x0000, 0x0400);
    reg_write(0x0010, 0x0404);
    
    rc = width(dev);
    if (rc < 0) {
        return rc;
    }
    reg_write(rc, INDEX_WIDTH);
    rc = height(dev);
    if (rc < 0) {
        return rc;
    }
    reg_write(rc, INDEX_HEIGHT);
    
    if (w == 800) {
        reg_write(0x0384, 0x300A);
        reg_write(0x0960, 0x300C);
    } else if (w == 1600) {
        reg_write(0x0640, 0x300A);
        reg_write(0x0FA0, 0x300C);
    } else if (w == 3264) {
        reg_write(0x0B4B, 0x300A);
        reg_write(0x1F40, 0x300C);
    } else {
        sdbg("bad width %u", w);
        return -EINVAL;
    }
    
    reg_write(0x0000, 0x0104);
    reg_write(0x0301, 0x31AE);
    reg_write(0x0805, 0x3064);
    reg_write(0x0071, 0x3170);
    reg_write(0x10DE, 0x301A);
    reg_write(0x0000, 0x0100);
    reg_write(0x0010, 0x0306);
    reg_write(0x0100, 0x0100);
    
    rc = set_exposure(dev, 350);
    if (rc) {
        sdbg("Failed to set exposure");
        return rc;
    }
        
    reg_write(0x0100, 0x0104);
    
    rc = set_gain(dev);
    if (rc) {
        sdbg("Failed to set gain");
        return rc;
    }
    
    reg_write(0x0000, 0x0104);
    
    sdbg("Encrypted end");
    
    return 0;
}

int configure(struct gspca_dev *dev)
{
    uint8_t buff[4];
    unsigned int rc;

    chk_ptr(dev);
    
    sdbg("Beginning configure");
    
    /*
    First driver sets a sort of encryption key
    A number of futur requests of this type have wValue and wIndex encrypted
    as follows:
    -Compute key = this wValue rotate left by 4 bits
        (decrypt.py rotates right because we are decrypting)
    -Later packets encrypt packets by XOR'ing with key
        XOR encrypt/decrypt is symmetrical
    By setting 0 we XOR with 0 and the shifting and XOR drops out
    */
    rc = usb_control_msg(dev->dev, usb_rcvctrlpipe(dev->dev, 0),
            0x16, 0xC0, 0x0000, 0x0000, buff, 2, 500);
    if (val_reply(buff, rc)) {
        sdalert("failed key req");
        return -EIO;
    }
    
    /*
    if (libusb_set_interface_alt_setting (g_camera.handle, 0, 1)) {
        sdalert("Failed to set alt setting");
        return -EIO;
    }
    */

    /*
    Next does some sort of challenge / response
    (to make sure its not cloned hardware?)
    Ignore: I want to work with their hardware, not clone it
    */
    
    rc = usb_control_msg(dev->dev, usb_sndctrlpipe(dev->dev, 0),
            0x01, 0x40, 0x0001, 0x000F, NULL, 0, 500);
    if (rc < 0) {
        sdalert("failed to replay packet 176 w/ rc %d\n", rc);
        return rc;
    }
    
    rc = usb_control_msg(dev->dev, usb_sndctrlpipe(dev->dev, 0),
            0x01, 0x40, 0x0000, 0x000F, NULL, 0, 500);
    if (rc < 0) {
        sdalert("failed to replay packet 178 w/ rc %d\n", rc);
        return rc;
    }

    rc = usb_control_msg(dev->dev, usb_sndctrlpipe(dev->dev, 0),
            0x01, 0x40, 0x0001, 0x000F, NULL, 0, 500);
    if (rc < 0) {
        sdalert("failed to replay packet 180 w/ rc %d\n", rc);
        return rc;
    }
    
    rc = usb_control_msg(dev->dev, usb_rcvctrlpipe(dev->dev, 0),
            0x20, 0xC0, 0x0000, 0x0000, buff, 4, 500);
    if (rc != 4 || memcmp((char[]){0xE6, 0x0D, 0x00, 0x00}, buff, 4)) {
        sdalert("failed to replay packet 182 w/ rc %d\n", rc);
        if (rc < 0) {
            return rc;
        }
        return -EIO;
    }
    
    /* Large (EEPROM?) read, skip it since no idea what to do with it */
    
    rc = configure_encrypted(dev);
    if (rc)
        return rc;

    //Omitted this by accident, does not work without it
    rc = usb_control_msg(dev->dev, usb_sndctrlpipe(dev->dev, 0),
            0x01, 0x40, 0x0003, 0x000F, NULL, 0, 500);

    sdbg("Configure complete");
    
    return 0;
}

/* this function is called at probe time */
static int sd_config(struct gspca_dev *dev,
			const struct usb_device_id *id)
{
    chk_ptr(dev);
    
	sdbg("sd_config start");
	dev->cam.cam_mode = vga_mode;
	dev->cam.nmodes = ARRAY_SIZE(vga_mode);
	sdbg("cam modes size: %d", dev->cam.nmodes);

    sdbg("Input flags: 0x%08X", dev->cam.input_flags);
    //Yes we want URBs and we want them now!
	dev->cam.no_urb_create = 0;
	//TODO: considering increasing much higher
	//Without frame sync we need to make sure we never drop
	dbg("Max nurbs: %d", MAX_NURBS);
	dev->cam.bulk_nurbs = 4;
	//Largest size the windows driver uses
	dev->cam.bulk_size = 0x4000;
	//Def need to use bulk transfers
	dev->cam.bulk = 1;
	
	//shouldn't really matter
	//oh yes it does...reversing skips the first element since otherwise why would be reverse
	dev->cam.reverse_alts = 0;
	sdbg("n alts: %d", dev->nbalt);
	sdbg("sd_config end");
	return 0;
}

/* -- start the camera -- */
static int sd_start(struct gspca_dev *dev)
{
	struct sd *sd = NULL;
    int rc;

    chk_ptr(dev);
    
	sdbg("sd_start() begin");
	
	sd = (struct sd *)dev;
	sd->this_f = 0;
	
	rc = configure(dev);
	if (rc) {
	    sdalert("Failed configure");
	    return rc;
	}

	sdbg("sd_start() end, status %d", dev->usb_err);

	return dev->usb_err;
}

static void sd_pkt_scan(struct gspca_dev *dev,
			u8 *data,		/* isoc packet */
			int len)		/* iso packet length */
{
	struct sd *sd = (struct sd *)dev;
	size_t frame_sz;
		
    if (dev == NULL) {
        sdalert("Bad pointer (dev)");
        return;
    }
    if (data == NULL) {
        sdalert("Bad pointer (data)");
        return;
    }
    
    //XXX: this might not be interrupt safe
    //sdbg("sd_pkt_scan");
	frame_sz = size(dev);

	//if a frame is in progress see if we can finish it off
	if (sd->this_f + len >= frame_sz) {
		unsigned int remainder = frame_sz - sd->this_f;
		//sdbg("Completing frame, so far %u + %u new >= %u frame size just getting the last %u of %u",
		//i		sd->this_f, len, frame_sz, remainder, frame_sz);
		//Completed a frame
		gspca_frame_add(dev, LAST_PACKET,
				data, remainder);
		len -= remainder;
		data += remainder;
		sd->this_f = 0;
		
		if (len > 0) {
			printk(KERN_ALERT "Didn't complete frame cleanly\n");
			len = 0;
		}
	}
	if (len > 0) {
		if (sd->this_f == 0) {
			//sdbg("start frame w/ %u bytes", len);
			//memset(data, 0xFF, len);
			gspca_frame_add(dev, FIRST_PACKET,
					data, len);
		} else {
			//sdbg("continue frame w/ %u new bytes w/ %u so far of needed %u",
			//        len, sd->this_f, frame_sz);
			gspca_frame_add(dev, INTER_PACKET,
					data, len);
		}
		sd->this_f += len;
	}
}

/* this function is called at probe and resume time */

static int sd_init(struct gspca_dev *dev)
{
	sdbg("sd_init");

    chk_ptr(dev);
    
	return 0;
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

/* table of devices that work with this driver */
/* TODO: should add the untested devices? */
static const struct usb_device_id device_table[] = {
	{ USB_DEVICE(0x0547, 0x6801) },
	{ }					/* Terminating entry */
};
MODULE_DEVICE_TABLE(usb, device_table);

/* -- device connect -- */
static int sd_probe(struct usb_interface *intf,
			const struct usb_device_id *id)
{
	int rc = 0;

    chk_ptr(intf);
    chk_ptr(id);

	sdbg("sd_probe start, alt 0x%p", intf->cur_altsetting);
	rc = gspca_dev_probe(intf, id, &sd_desc, sizeof(struct sd),
				THIS_MODULE);
	sdbg("sd_probe done, rc %d", rc);
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
	sdinfo("registered");
	return 0;
}
static void __exit sd_mod_exit(void)
{
	usb_deregister(&sd_driver);
	sdinfo("deregistered");
}

module_init(sd_mod_init);
module_exit(sd_mod_exit);

