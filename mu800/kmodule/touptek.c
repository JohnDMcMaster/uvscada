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

/*
Register value is linear with exposure time
Exposure (sec), E (reg)
0.000400, 0x0002
0.001000, 0x0005
0.005000, 0x0019
0.020000, 0x0064
0.080000, 0x0190
0.400000, 0x07D0
1.000000, 0x1388
2.000000, 0x2710
*/
#define INDEX_EXPOSURE      0x3012

//Haven't tried other indices
#define INDEX_WIDTH         0x034C
#define INDEX_HEIGHT        0x034E
    
/*
Gain does not vary with resolution (checked 640x480 vs 1600x1200)
Range 0x1000 (nothing) to 0x11FF (highest)
However, there appear to be gaps

Suspect three gain stages
0x1000: master channel enable bit
0x007F: low gain bits
0x0080: medium gain bit
0x0100: high gain bit

gain = enable * (1 + regH) * (1 + regM) * z * regL

zR = 0.0069605943152454778
    about 3/431 = 0.0069605568445475635
zB = 0.0095695970695970703
    about 6/627 = 0.0095693779904306216
zG = 0.010889328063241107
    about 6/551 = 0.010889292196007259
about 10 bits for constant + 7 bits for value => at least 17 bit intermediate
with 32 bit ints should be fine for overflow etc
Essentially gains are in range 0-0x001FF

However, V4L expects a main gain channel + R and B balance
To keep things simple for now saturate the values of balance is too high/low
This isn't really ideal but easy way to fit the Linux model

Raw data:
Gain,   GTOP,   B,      R,      GBOT
1.00,   0x105C, 0x1068, 0x10C8, 0x105C
1.20,   0x106E, 0x107E, 0x10D6, 0x106E
1.40,   0x10C0, 0x10CA, 0x10E5, 0x10C0
1.60,   0x10C9, 0x10D4, 0x10F3, 0x10C9
1.80,   0x10D2, 0x10DE, 0x11C1, 0x10D2
2.00,   0x10DC, 0x10E9, 0x11C8, 0x10DC
2.20,   0x10E5, 0x10F3, 0x11CF, 0x10E5
2.40,   0x10EE, 0x10FE, 0x11D7, 0x10EE
2.60,   0x10F7, 0x11C4, 0x11DE, 0x10F7
2.80,   0x11C0, 0x11CA, 0x11E5, 0x11C0
3.00,   0x11C5, 0x11CF, 0x11ED, 0x11C5

Converted using gain model turns out to be quite linear:
Gain, GTOP, B, R, GBOT
1.00, 92, 104, 144, 92
1.20, 110, 126, 172, 110
1.40, 128, 148, 202, 128
1.60, 146, 168, 230, 146
1.80, 164, 188, 260, 164
2.00, 184, 210, 288, 184
2.20, 202, 230, 316, 202
2.40, 220, 252, 348, 220
2.60, 238, 272, 376, 238
2.80, 256, 296, 404, 256
3.00, 276, 316, 436, 276
*/
#define GAIN_BASE           0x1000
/*
Maximum gain is 0x7FF * 2 * 2 => 0x1FFC (8188)
or about 13 effective bits of gain
The highest the commercial driver goes in my setup 436
However, because could potentially damage circuits
limit the gain until have a reason to go higher
*/
#define GAIN_MAX            511
#define BAL_MAX             511
#define INDEX_GAIN_GTOP     0x3056
#define INDEX_GAIN_B        0x3058
#define INDEX_GAIN_R        0x305A
#define INDEX_GAIN_GBOT     0x305C

#define MODULE_NAME "touptek"

MODULE_AUTHOR("John McMaster");
MODULE_DESCRIPTION("ToupTek UCMOS / Amscope MU microscope camera driver");
MODULE_LICENSE("GPL");

/*
First two frames are dark, dropping eases many apps
but hurts others due to the delay
XXX: what if the dark frames are bad pixel calibration?
I seem to be developing some hot pixels...will have to deal with that
*/
static int drop_frames = 0;
module_param(drop_frames, int, S_IRUGO);


//#define sdbg(...)
#define sdbg( _format, ... ) printk( KERN_INFO "touptek DBG:%u: " _format "\n", __LINE__, ## __VA_ARGS__ )

#define sdinfo( _format, ... ) printk( KERN_INFO "touptek INFO:%u: " _format "\n", __LINE__, ## __VA_ARGS__ )
#define sdalert( _format, ... ) printk( KERN_INFO "touptek ALERT:%u: " _format "\n", __LINE__, ## __VA_ARGS__ )


/* specific webcam descriptor */
struct sd {
	struct gspca_dev gspca_dev;	/* !! must be the first item */
	/* How many bytes this frame */
	unsigned int this_f;
	//Bytes to throw away to complete a sync
	unsigned int sync_consume;
    
    /*
    Device has separate gains for each Bayer quadrant
    V4L supports master gain which is referenced to G1/G2 and supplies
    individual balance controls for R/B
    */
	u16 global_gain, red_bal, blue_bal;
	/* In ms */
	unsigned int exposure;
};

static int sd_setredbalance(struct gspca_dev *gspca_dev, s32 val);
static int sd_getredbalance(struct gspca_dev *gspca_dev, s32 *val);
static int sd_setbluebalance(struct gspca_dev *gspca_dev, s32 val);
static int sd_getbluebalance(struct gspca_dev *gspca_dev, s32 *val);
static int sd_setgain(struct gspca_dev *gspca_dev, s32 val);
static int sd_getgain(struct gspca_dev *gspca_dev, s32 *val);
static int sd_setexposure(struct gspca_dev *gspca_dev, s32 val);
static int sd_getexposure(struct gspca_dev *gspca_dev, s32 *val);
static int set_exposure(struct gspca_dev *dev);
static int set_gain(struct gspca_dev *dev, int set);

/* V4L2 controls supported by the driver */
static const struct ctrl sd_ctrls[] = {
	{
	    {
		.id      = V4L2_CID_EXPOSURE,
		.type    = V4L2_CTRL_TYPE_INTEGER,
		.name    = "Exposure",
		.minimum = 0,
		/* Mostly limited by URB timeouts */
		.maximum = 800,
		.step    = 1,
#define EXPOSURE_DEFAULT        350
		.default_value = EXPOSURE_DEFAULT,
	    },
	    .set = sd_setexposure,
	    .get = sd_getexposure,
	},
/*
Gain implementation
Goal: simple conversion for default gain at 1.00
Want to do something similar to mt9v011.c's set_balance
Problem: can lead to gains higher than possible
When this happens the gain is clipped and a debug warning is emitted

green_gain = sd->global_gain
blue_gain = sd->global_gain + ((uint32_t)sd->global_gain) * sd->blue_bal / GAIN_MAX;
red_gain = sd->global_gain + ((uint32_t)sd->global_gain) * sd->blue_bal / GAIN_MAX;

Want initial gain of 1.4 (since it works well for me ;) ):
-G: 128 => global_gain = 128
-B: 148 => blue_bal = 80
    148 = 128 + 128 * blue_bal / 511
-R: 202 => red_bal = 295
    202 = 128 + 128 * red_bal / 511
*/
	{
	    {
		.id      = V4L2_CID_GAIN,
		.type    = V4L2_CTRL_TYPE_INTEGER,
		.name    = "Gain",
		.minimum = 0,
		.maximum = GAIN_MAX,
		.step    = 1,
#define GAIN_DEFAULT 128
		.default_value = GAIN_DEFAULT,
	    },
	    .set = sd_setgain,
	    .get = sd_getgain,
	},
	{
	    {
		.id	 = V4L2_CID_BLUE_BALANCE,
		.type	 = V4L2_CTRL_TYPE_INTEGER,
		.name	 = "Blue Balance",
		.minimum = 0,
		.maximum = BAL_MAX,
		.step	 = 1,
#define BLUE_DEFAULT 80
		.default_value = BLUE_DEFAULT,
	    },
	    .set = sd_setbluebalance,
	    .get = sd_getbluebalance,
	},
	{
	    {
		.id	 = V4L2_CID_RED_BALANCE,
		.type	 = V4L2_CTRL_TYPE_INTEGER,
		.name	 = "Red Balance",
		.minimum = 0,
		.maximum = BAL_MAX,
		.step	 = 1,
#define RED_DEFAULT 295
		.default_value = RED_DEFAULT,
	    },
	    .set = sd_setredbalance,
	    .get = sd_getredbalance,
	},
};


#define PIX_FMT		V4L2_PIX_FMT_SGRBG8
#define COLORSPACE  V4L2_COLORSPACE_SRGB

int do_reg_write(struct gspca_dev *gspca_dev, int wValue, int wIndex);

static const struct v4l2_pix_format vga_mode[] = {
#if 0
	{800, 600,
		PIX_FMT,
		V4L2_FIELD_NONE,
		.bytesperline = 800,
		.sizeimage = 800 * 600,
		.colorspace = COLORSPACE},
#endif
#if 1
	{1600, 1200,
		PIX_FMT,
		V4L2_FIELD_NONE,
		.bytesperline = 1600,
		.sizeimage = 1600 * 1200,
		.colorspace = V4L2_COLORSPACE_SRGB},
#endif
#if 0
	{3264, 2448,
		PIX_FMT,
		V4L2_FIELD_NONE,
		.bytesperline = 3264,
		.sizeimage = 3264 * 2448,
		.colorspace = V4L2_COLORSPACE_SRGB},
#endif
};

#if MAX_NURBS < 4
#error "Not enough URBs in the gspca table"
#endif

#define reg_write(_value, _index) do { \
    int _rc = do_reg_write(gspca_dev, _value, _index ); \
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

int do_reg_write(struct gspca_dev *gspca_dev, int wValue, int wIndex)
{
    char buff[1];
    int rc;
    
    chk_ptr(gspca_dev);
    
    rc = usb_control_msg(gspca_dev->dev, usb_rcvctrlpipe(gspca_dev->dev, 0),
            0x0B, 0xC0, wValue, wIndex, buff, 1, 500);
    sdbg("Sent bRequest=0x0B, bRequestType=0xC0, wValue=0x%04X, wIndex=0x%04X, rc = %d, ret = {0x%02X}",
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

int width(struct gspca_dev *gspca_dev) {
     const struct v4l2_pix_format *cam_mode = gspca_dev->cam.cam_mode;
     
    /* is this needed? */
    if (cam_mode == NULL) {
        sdalert("it can happen");
        return -EIO;
    }
    return cam_mode->width;
}

int height(struct gspca_dev *gspca_dev) {
     const struct v4l2_pix_format *cam_mode = gspca_dev->cam.cam_mode;
     
    /* is this needed? */
    if (cam_mode == NULL) {
        sdalert("it can happen");
        return -EIO;
    }
    return cam_mode->height;
}

int size(struct gspca_dev *gspca_dev) {
     const struct v4l2_pix_format *cam_mode = gspca_dev->cam.cam_mode;
     
    chk_ptr(gspca_dev);
    
    /* is this needed? */
    if (cam_mode == NULL) {
        sdalert("it can happen");
        return -EIO;
    }
    return cam_mode->sizeimage;
}

static int sd_setexposure(struct gspca_dev *gspca_dev, s32 val)
{
	struct sd *sd = (struct sd *) gspca_dev;

	sd->exposure = val;
	if (gspca_dev->streaming)
		return set_exposure(gspca_dev);
	return 0;
}

static int sd_getexposure(struct gspca_dev *gspca_dev, s32 *val)
{
	struct sd *sd = (struct sd *) gspca_dev;
	*val = sd->exposure;
	return 0;
}

static int sd_setgain(struct gspca_dev *gspca_dev, s32 val)
{
	struct sd *sd = (struct sd *) gspca_dev;

	sd->global_gain = val;
	if (gspca_dev->streaming)
		return set_gain(gspca_dev, 1);
	return 0;
}

static int sd_getgain(struct gspca_dev *gspca_dev, s32 *val)
{
	struct sd *sd = (struct sd *) gspca_dev;
	*val = sd->global_gain;
	return 0;
}

int set_exposure(struct gspca_dev *gspca_dev)
{
	struct sd *sd = (struct sd *)gspca_dev;
    uint16_t wValue;
    unsigned int w;
    
    chk_ptr(gspca_dev);
    w = width(gspca_dev);
    
    if (w == 800)
        wValue = sd->exposure * 5;
    else if (w == 1600)
        wValue = sd->exposure * 3;
    else if (w == 3264)
        wValue = sd->exposure * 3 / 2;
    else {
        sdbg("Invalid width %u", w);
        return -EINVAL;
    }
    sdbg("exposure: 0x%04X", wValue);
    /* Wonder if theres a good reason for sending it twice */
    reg_write(wValue, INDEX_EXPOSURE);
    reg_write(wValue, INDEX_EXPOSURE);
    
    return 0;
}

int gainify(int in) {
    /*
    TODO: check if there are any issues with corner cases
    0x000 (0):0x07F (127): regL
    0x080 (128) - 0x0FF (255): regM, regL
    0x100 (256) - max: regH, regM, regL
    */
    if (in <= 0x7F)
        return 0x1000 | in;
    else if (in <= 0xFF)
        return 0x1080 | in / 2;
    else
        return 0x1180 | in / 4;
}

int set_gain(struct gspca_dev *gspca_dev, int set)
{
	struct sd *sd = (struct sd *)gspca_dev;
	u16 green_gain, blue_gain, red_gain;
    
    chk_ptr(gspca_dev);
	green_gain = gainify(sd->global_gain);
    sdbg("gain G1/G2 (0x%04X): 0x%04X (source 0x%04X, default: 0x%04X)",
            INDEX_GAIN_GTOP, green_gain, sd->global_gain, GAIN_DEFAULT);
	
	blue_gain = sd->global_gain + ((uint32_t)sd->global_gain) * sd->blue_bal / GAIN_MAX;
	if (blue_gain > GAIN_MAX) {
	    sdbg("Blue gain overflowd 0x%04X w/ value 0x%04X, truncating", GAIN_MAX, blue_gain);
	    blue_gain = GAIN_MAX;
	}
	blue_gain = gainify(blue_gain);
    sdbg("gain B (0x%04X): 0x%04X w/ source 0x%04X, default 0x%04X",
            INDEX_GAIN_B, blue_gain, sd->blue_bal, BLUE_DEFAULT);
	
	red_gain = sd->global_gain + ((uint32_t)sd->global_gain) * sd->red_bal / GAIN_MAX;
    if (red_gain > GAIN_MAX) {
	    sdbg("Red gain overflowd 0x%04X w/ value 0x%04X, truncating", GAIN_MAX, red_gain);
	    red_gain = GAIN_MAX;
	}
	red_gain = gainify(red_gain);
    sdbg("gain R (0x%04X): 0x%04X w / source 0x%04X, default 0x%04X",
            INDEX_GAIN_R, red_gain, sd->red_bal, RED_DEFAULT);
    
    if (set) {
        reg_write(green_gain, INDEX_GAIN_GTOP);
        reg_write(blue_gain, INDEX_GAIN_B);
        reg_write(red_gain, INDEX_GAIN_R);
        reg_write(green_gain, INDEX_GAIN_GBOT);
    }
    
    return 0;
}

static int sd_setredbalance(struct gspca_dev *gspca_dev, s32 val)
{
	struct sd *sd = (struct sd *) gspca_dev;

	sd->red_bal = val;
	if (gspca_dev->streaming)
		return set_gain(gspca_dev, 1);
	return 0;
}

static int sd_getredbalance(struct gspca_dev *gspca_dev, s32 *val)
{
	struct sd *sd = (struct sd *) gspca_dev;
	*val = sd->red_bal;
	return 0;
}

static int sd_setbluebalance(struct gspca_dev *gspca_dev, s32 val)
{
	struct sd *sd = (struct sd *) gspca_dev;

	sd->blue_bal = val;
	if (gspca_dev->streaming)
		return set_gain(gspca_dev, 1);
	return 0;
}

static int sd_getbluebalance(struct gspca_dev *gspca_dev, s32 *val)
{
	struct sd *sd = (struct sd *) gspca_dev;
	*val = sd->blue_bal;
	return 0;
}

/* Packets that were encrypted, no idea if the grouping is significant */
int configure_encrypted(struct gspca_dev *gspca_dev)
{
    unsigned int rc;
    unsigned int w;
    
    chk_ptr(gspca_dev);
    w = width(gspca_dev);
    
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
    
    rc = width(gspca_dev);
    if (rc < 0) {
        return rc;
    }
    reg_write(rc, INDEX_WIDTH);
    rc = height(gspca_dev);
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
    
    sdbg("Setting exposure");
    rc = set_exposure(gspca_dev);
    if (rc) {
        sdbg("Failed to set exposure");
        return rc;
    }
        
    reg_write(0x0100, 0x0104);
    
    sdbg("Setting gain");
    rc = set_gain(gspca_dev, 1);
    if (rc) {
        sdbg("Failed to set gain");
        return rc;
    }
    
    reg_write(0x0000, 0x0104);
    
    sdbg("Encrypted end");
    
    return 0;
}

int configure(struct gspca_dev *gspca_dev)
{
    uint8_t buff[4];
    unsigned int rc;

    chk_ptr(gspca_dev);
    
    sdbg("Beginning configure");
    
    /*
    First driver sets a sort of encryption key
    A number of futur requests of this type have wValue and wIndex encrypted
    as follows:
    -Compute key = this wValue rotate left by 4 bits
        (decrypt.py rotates right because we are decrypting)
    -Later packets encrypt packets by XOR'ing with key
        XOR encrypt/decrypt is symmetrical
        wValue, and wIndex are encrypted
        bRequest is not and bRequestType is always 0xC0
            This allows resyncing if key is unknown?
    By setting 0 we XOR with 0 and the shifting and XOR drops out
    */
    rc = usb_control_msg(gspca_dev->dev, usb_rcvctrlpipe(gspca_dev->dev, 0),
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
    Next does some sort of 2 packet challenge / response
    (to make sure its not cloned hardware?)
    Ignore: I want to work with their hardware, not clone it
    16 bytes out challenge, requestType: 0x40
    16 bytes in response, requestType: 0xC0
    */
    
    rc = usb_control_msg(gspca_dev->dev, usb_sndctrlpipe(gspca_dev->dev, 0),
            0x01, 0x40, 0x0001, 0x000F, NULL, 0, 500);
    if (rc < 0) {
        sdalert("failed to replay packet 176 w/ rc %d\n", rc);
        return rc;
    }
    
    rc = usb_control_msg(gspca_dev->dev, usb_sndctrlpipe(gspca_dev->dev, 0),
            0x01, 0x40, 0x0000, 0x000F, NULL, 0, 500);
    if (rc < 0) {
        sdalert("failed to replay packet 178 w/ rc %d\n", rc);
        return rc;
    }

    rc = usb_control_msg(gspca_dev->dev, usb_sndctrlpipe(gspca_dev->dev, 0),
            0x01, 0x40, 0x0001, 0x000F, NULL, 0, 500);
    if (rc < 0) {
        sdalert("failed to replay packet 180 w/ rc %d\n", rc);
        return rc;
    }
    
    rc = usb_control_msg(gspca_dev->dev, usb_rcvctrlpipe(gspca_dev->dev, 0),
            0x20, 0xC0, 0x0000, 0x0000, buff, 4, 500);
    if (rc != 4 || memcmp((char[]){0xE6, 0x0D, 0x00, 0x00}, buff, 4)) {
        sdalert("failed to replay packet 182 w/ rc %d\n", rc);
        if (rc < 0) {
            return rc;
        }
        return -EIO;
    }
    
    /* Large (EEPROM?) read, skip it since no idea what to do with it */
    
    rc = configure_encrypted(gspca_dev);
    if (rc)
        return rc;

    /* Omitted this by accident, does not work without it */
    rc = usb_control_msg(gspca_dev->dev, usb_sndctrlpipe(gspca_dev->dev, 0),
            0x01, 0x40, 0x0003, 0x000F, NULL, 0, 500);

    sdbg("Configure complete");
    
    return 0;
}

/* this function is called at probe time */
static int sd_config(struct gspca_dev *gspca_dev,
			const struct usb_device_id *id)
{
    chk_ptr(gspca_dev);
    
	sdbg("sd_config start");
	gspca_dev->cam.cam_mode = vga_mode;
	gspca_dev->cam.nmodes = ARRAY_SIZE(vga_mode);
	sdbg("cam modes size: %d", gspca_dev->cam.nmodes);

    sdbg("Input flags: 0x%08X", gspca_dev->cam.input_flags);
    /* Yes we want URBs and we want them now! */
	gspca_dev->cam.no_urb_create = 0;
	/*
	TODO: considering increasing much higher
	Without frame sync we need to make sure we never drop
	*/
	sdbg("Max nurbs: %d", MAX_NURBS);
	gspca_dev->cam.bulk_nurbs = 4;
	/* Largest size the windows driver uses */
	gspca_dev->cam.bulk_size = 0x4000;
	/* Def need to use bulk transfers */
	gspca_dev->cam.bulk = 1;
	
	/*
	shouldn't really matter
	oh yes it does...reversing skips the first element since otherwise why would be reverse
	*/
	gspca_dev->cam.reverse_alts = 0;
	sdbg("n alts: %d", gspca_dev->nbalt);
	sdbg("sd_config end");
	return 0;
}

/* -- start the camera -- */
static int sd_start(struct gspca_dev *gspca_dev)
{
	struct sd *sd = (struct sd *)gspca_dev;
    int rc;

    chk_ptr(gspca_dev);
    
	sdbg("sd_start() begin");
	
	sd->this_f = 0;
	
	rc = configure(gspca_dev);
	if (rc < 0) {
	    sdalert("Failed configure");
	    return rc;
	}
	//First two frames have messed up gains
	//Drop them to avoid special cases in user apps?
	rc = size(gspca_dev);
	if (rc < 0) {
	    sdbg("Failed size");
	    return rc;
    }
	sd->sync_consume = drop_frames * rc;
    sdbg("Dropping %u bytes at init", sd->sync_consume);

	sdbg("sd_start() end, status %d", gspca_dev->usb_err);

	return gspca_dev->usb_err;
}

static void sd_pkt_scan(struct gspca_dev *gspca_dev,
			u8 *data,		/* isoc packet */
			int len)		/* iso packet length */
{
	struct sd *sd = (struct sd *)gspca_dev;
	size_t frame_sz;
		
    if (gspca_dev == NULL) {
        sdalert("Bad pointer (dev)");
        return;
    }
    if (data == NULL) {
        sdalert("Bad pointer (data)");
        return;
    }
    
    //XXX: this might not be interrupt safe
    //sdbg("sd_pkt_scan");
	frame_sz = size(gspca_dev);

    //Drop data as needed for sync
	if (sd->sync_consume) {
		//sdbg("Got %u of %u needed to sync", len, sd->sync_consume );
		if (len < sd->sync_consume) {
			sd->sync_consume -= len;
			len = 0;
		} else {
		    data += sd->sync_consume;
			len -= sd->sync_consume;
			sd->sync_consume = 0; 
			sdbg("Sync'd, %u data left, frame has %u", len, sd->this_f);
		}
	}

	//if a frame is in progress see if we can finish it off
	if (sd->this_f + len >= frame_sz) {
		unsigned int remainder = frame_sz - sd->this_f;
		//sdbg("Completing frame, so far %u + %u new >= %u frame size just getting the last %u of %u",
		//i		sd->this_f, len, frame_sz, remainder, frame_sz);
		//Completed a frame
		gspca_frame_add(gspca_dev, LAST_PACKET,
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
			gspca_frame_add(gspca_dev, FIRST_PACKET,
					data, len);
		} else {
			//sdbg("continue frame w/ %u new bytes w/ %u so far of needed %u",
			//        len, sd->this_f, frame_sz);
			gspca_frame_add(gspca_dev, INTER_PACKET,
					data, len);
		}
		sd->this_f += len;
	}
}

/* this function is called at probe and resume time */

static int sd_init(struct gspca_dev *gspca_dev)
{
	struct sd *sd = (struct sd *)gspca_dev;
	
    chk_ptr(gspca_dev);
	sdbg("sd_init");

    /* Setting at init allows one app to adjust and another take pictures */
    sd->exposure = EXPOSURE_DEFAULT;
    sd->global_gain = GAIN_DEFAULT;
    sd->red_bal = RED_DEFAULT;
    sd->blue_bal = BLUE_DEFAULT;
    //Dummy calculation to print gains
    set_gain(gspca_dev, 0);
    
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
	sdinfo("registered (1)");
	return 0;
}
static void __exit sd_mod_exit(void)
{
	usb_deregister(&sd_driver);
	sdinfo("deregistered");
}

module_init(sd_mod_init);
module_exit(sd_mod_exit);

