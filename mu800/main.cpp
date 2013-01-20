#include <errno.h>
#include <stdio.h>
#include <stdint.h>
//#include <libusb/libusb.h> 
#include <libusb-1.0/libusb.h>
#include <string.h>
#include <string>
#include <stdlib.h>
#include <time.h>

#include "hexdump.cpp"

#define DEFAULT_TIMEOUT     500
#define N_FRAMES            4

/*
The original:
//Bus 002 Device 006: ID 0547:4d88 Anchor Chips, Inc. 
#define CAMERA_VENDOR_ID		0x0547
#define CAMERA_PRODUCT_ID		0x4D88

New guy (rev 2 cameras):
Bus 002 Device 007: ID 0547:6801 Anchor Chips, Inc. 
*/

/*
Bit 3...0: The endpoint number
Bit 6...4: Reserved, reset to zero
Bit 7:     Direction, ignored for
           control endpoints
       0 = OUT endpoint
       1 = IN endpoint
*/
//Best guesses
//Barely any observed traffic
//Have yet to show that images actually get send across
#define IMAGE_ENDPOINT 			0
//Observed from capture
#define	VIDEO_ENDPOINT 			2


//largest size the windows driver uses
#define TRANSFER_BUFF_SZ        (4 * 4096)
//#define TRANSFER_BUFF_SZ        1024

//Always in
#define DATA_EP     (VIDEO_ENDPOINT | LIBUSB_ENDPOINT_IN)


typedef struct {
    /*
    3264x2448
    1600x1200
    800x600
    */
    unsigned int width;
    unsigned int height;
    uint16_t key;
    struct libusb_device_handle *handle;
    struct libusb_device *dev;
} camera_t;
camera_t g_camera = {
    width: 3264,
    height: 2448,
};

bool g_verbose = true;


libusb_device_handle *locate_camera( void );


void shutdown() {
	if (g_camera.handle) {
		libusb_close(g_camera.handle);
	}
}

void camera_exit(int rc) {
    shutdown();
	exit(1);
}

const char* libusb_error_name 	( 	int  	error_code	) {
    switch (error_code) {
	case LIBUSB_SUCCESS:
	    return "LIBUSB_SUCCESS";
	case LIBUSB_ERROR_IO:
	    return "LIBUSB_ERROR_IO";
	case LIBUSB_ERROR_INVALID_PARAM:
	    return "LIBUSB_ERROR_INVALID_PARAM";
	case LIBUSB_ERROR_ACCESS:
	    return "LIBUSB_ERROR_ACCESS";
	case LIBUSB_ERROR_NO_DEVICE:
	    return "LIBUSB_ERROR_NO_DEVICE";
	case LIBUSB_ERROR_NOT_FOUND:
	    return "LIBUSB_ERROR_NOT_FOUND";
	case LIBUSB_ERROR_BUSY:
	    return "LIBUSB_ERROR_BUSY";
	case LIBUSB_ERROR_TIMEOUT:
	    return "LIBUSB_ERROR_TIMEOUT";
	case LIBUSB_ERROR_OVERFLOW:
	    return "LIBUSB_ERROR_OVERFLOW";
	case LIBUSB_ERROR_PIPE:
	    return "LIBUSB_ERROR_PIPE";
	case LIBUSB_ERROR_INTERRUPTED:
	    return "LIBUSB_ERROR_INTERRUPTED";
	case LIBUSB_ERROR_NO_MEM:
	    return "LIBUSB_ERROR_NO_MEM";
	case LIBUSB_ERROR_NOT_SUPPORTED:
	    return "LIBUSB_ERROR_NOT_SUPPORTED";
	case LIBUSB_ERROR_OTHER:
	    return "LIBUSB_ERROR_OTHER";
    default:
        return "unknown error";
    }
}

unsigned int camera_bulk_read(int ep, void *bytes, int size) {
    int actual_length = 0;
    
	//int libusb_bulk_read(usb_dev_handle *dev, int ep, char *bytes, int size,
	//	int timeout);
	int rc_tmp = libusb_bulk_transfer(g_camera.handle, ep, (unsigned char *)bytes, size, &actual_length, DEFAULT_TIMEOUT);
	
	if (rc_tmp < 0) {
		perror("ERROR");
		printf("failed bulk read: %d\n", rc_tmp);
		camera_exit(1);
	}
	if (actual_length < 0) {
		printf("bad actual read size: %d\n", actual_length);
		camera_exit(1);
	}
	
	return actual_length;
}

unsigned int camera_bulk_write(int ep, void *bytes, int size) {
    int actual_length = 0;
	int rc_tmp =  libusb_bulk_transfer(g_camera.handle, ep, (unsigned char *)bytes, size, &actual_length, DEFAULT_TIMEOUT);
	
	if (rc_tmp < 0) {
		perror("ERROR");
		printf("failed write: %d\n", rc_tmp);
		camera_exit(1);
	}
	if (actual_length < 0) {
		printf("bad actual write size: %d\n", actual_length);
		camera_exit(1);
	}
	
	return actual_length;
}

/*
int libusb_control_msg(usb_dev_handle *dev, int requesttype, int request,
	int value, int index, char *bytes, int size, int timeout);
*/

unsigned int camera_control_message(int requesttype, int request,
		int value, int index, uint8_t *bytes, int size) {
	int rc_tmp = 0;
	
	/*
	WARNING: request / request type parameters are swapped between kernel and libusb
	request type is clearly listed first in USB spec and seems more logically first so I'm going to blame kernel on this
	although maybe libusb came after and was trying for multi OS comatibility right off the bat
	
	libusb 0.x
	int libusb_control_msg(usb_dev_handle *dev, int requesttype, int request, int value, int index, char *bytes, int size, int timeout);

    libusb 1.x
    int libusb_control_transfer 	( 	libusb_device_handle *  	dev_handle,
            uint8_t  	bmRequestType,
            uint8_t  	bRequest,
            uint16_t  	wValue,
            uint16_t  	wIndex,
            unsigned char *  	data,
            uint16_t  	wLength,
            unsigned int  	timeout 
        )
		
	kernel
	extern int usb_control_msg(struct libusb_device *dev, unsigned int pipe,
		__u8 request, __u8 requesttype, __u16 value, __u16 index,
		void *data, __u16 size, int timeout);
	*/
	rc_tmp = libusb_control_transfer(g_camera.handle, requesttype, request, value, index, (unsigned char *)bytes, size, DEFAULT_TIMEOUT);
	if (rc_tmp < 0) {
		printf("failed\n");
		exit(1);
	}
	return rc_tmp;
}

int validate_read(void *expected, size_t expected_size, void *actual, size_t actual_size, const char *msg) {
	if (expected_size != actual_size) {
		printf("%s: expected %d bytes, got %d bytes\n", msg, expected_size, actual_size);
		return -1;
	}
	if (memcmp(expected, actual, expected_size)) {
	    printf("%s: regions do not match\n", msg);
	    if (g_verbose) {
		    printf("  Actual:\n");
		    UVDHexdumpCore(actual, expected_size, "    ", false, 0);
		    printf("  Expected:\n");
		    UVDHexdumpCore(expected, expected_size, "    ", false, 0);
	    }
		return -1;
	}
	if (g_verbose) {
    	printf("Regions of length %d DO match\n", expected_size);
	}
	return 0;
}

//#include "fx2.cpp"


const char *g_image_file_out = "image.bin";

void capture() {
	unsigned int n_read = 0;
	int rc_tmp = 0;

	char *buff = NULL;
	unsigned int buff_pos = 0;
	
	unsigned int to_read = g_camera.width * g_camera.height * N_FRAMES;
	//800x600 size
	//const size_t buff_sz = 16384;
	//having issues..use something shorter
	const size_t buff_sz = TRANSFER_BUFF_SZ;
	printf("Going to read %d, single read buffer size %d\n", to_read, buff_sz);
	buff = (char *)malloc(to_read + buff_sz);
	if (buff == NULL) {
		printf("out of mem\n");
		camera_exit(1);
	}
	memset(buff, 0x00, to_read + buff_sz);
	fflush(stdout);
	int count = 0;
	unsigned int last_total = 0;
	/*
	Assuming RGB24 encoding @ 640 X 480 need 640 * 480 * 3 = 921600
	*/
	while (buff_pos < to_read) {
		++count;
		n_read = camera_bulk_read(DATA_EP, buff + buff_pos, buff_sz);
		//printf("read %d\n", n_read);
		buff_pos += n_read;
		last_total += n_read;
		if (last_total > 1000000) {
			//printf("Got %u\n", last_total);
			last_total = 0;
		}
	}
	
	//Log to file
	FILE *file = fopen(g_image_file_out, "wb");
	if (!file) {
		perror("fopen");
		camera_exit(1);
	}
	rc_tmp = fwrite(buff, 1, to_read, file);
	if (rc_tmp != (int)to_read) {
		printf("got %d expected %d\n", to_read, rc_tmp);
		camera_exit(1);
	}
	printf("Done!\n");
}

unsigned char *g_async_buff = NULL;
size_t g_async_buff_sz = 0;
unsigned int g_async_buff_pos = 0;
bool g_should_stall = false;
bool g_have_stalled = false;
unsigned int active_urbs = 0;

void capture_async_cb(struct libusb_transfer *transfer) {
    int rc = -1;
    int to_copy = 0;
    int remaining = g_async_buff_sz - g_async_buff_pos;
    /*
    Doc says that libusb is single threaded
    Assuming that I don't need to lock here
    */
    //printf("Got CB\n"); fflush(stdout);
    if (transfer->status != LIBUSB_TRANSFER_COMPLETED) {
        if (transfer->status == LIBUSB_TRANSFER_CANCELLED) {
            return;
        }
        if (g_should_stall) {
            --active_urbs;
            if (active_urbs) {
                printf("out of URBs, final code\n", transfer->status);
                exit(1);
            }
            goto resubmit;
        }
        printf("Transfer failed w/ code %u\n", transfer->status);
        exit(1);
    }
    
    if (transfer->actual_length > remaining) {
        to_copy = remaining;
    } else {
        to_copy = transfer->actual_length;
    }
    
	memcpy(g_async_buff + g_async_buff_pos, transfer->buffer, to_copy);
	g_async_buff_pos += to_copy;
    
    /*
    The hope is that the camera will detect getting behind and do something special
    */
    if (g_should_stall) {
        if (!g_have_stalled && g_async_buff_pos >= g_async_buff_sz / 2) {
            unsigned int stall_ms = 300;
            printf("Stalling @ %u for %u ms\n", g_async_buff_pos, stall_ms);
            usleep(stall_ms * 1000);
            g_have_stalled = true;
        }
    }
    
    //Resubmit
resubmit:
	rc = libusb_submit_transfer(transfer);
    if (rc) {
        printf("Failed to resubmit transfer: %s (%d)\n",
                libusb_error_name(rc) , rc); fflush(stdout);
        exit(1);
    }
}

void save_buffer(void) {
	//Log to file
	FILE *file_out = NULL;
	int rc = -1;
	
	file_out = fopen(g_image_file_out, "wb");
	if (!file_out) {
		perror("fopen");
		camera_exit(1);
	}
	rc = fwrite(g_async_buff, 1, g_async_buff_sz, file_out);
	if (rc != (int)g_async_buff_sz) {
		printf("got %d expected %d\n", g_async_buff_sz, rc);
		camera_exit(1);
	}
	printf("Done!\n");
}

#define N_TRANSFERS     16

void capture_async() {
    struct libusb_transfer *transfers[N_TRANSFERS];
	int rc = 0;
	
	g_async_buff_sz = g_camera.width * g_camera.height * N_FRAMES;
	
    printf("Allocating main buffer...\n");
	//Assemble everything into this buffer
	g_async_buff = (unsigned char *)malloc(g_async_buff_sz);
	if (g_async_buff == NULL) {
		printf("out of mem\n");
		camera_exit(1);
	}
	memset(g_async_buff, 0x00, g_async_buff_sz);

    printf("Preparing transfers (buff size: %u)...\n", TRANSFER_BUFF_SZ);
    //And cull up some minions to drag bacon in
    for (unsigned int i = 0; i < N_TRANSFERS; ++i) {
        struct libusb_transfer *transfer = NULL;
        
        size_t buff_sz = TRANSFER_BUFF_SZ;
        unsigned char *buff = (unsigned char *)malloc(buff_sz);
        
        if (buff == NULL) {
            printf("Failed to alloc transfer buffer\n");
            exit(1);
        }
        
        transfer = libusb_alloc_transfer( 0 );
        if (transfer == NULL) {
            printf("Failed to alloc transfer\n");
            exit(1);
        }
        
        transfers[i] = transfer;
        libusb_fill_bulk_transfer( transfer,
		    g_camera.handle, DATA_EP,
		    buff, buff_sz,
		    capture_async_cb, NULL, DEFAULT_TIMEOUT );
        ++active_urbs;
    }
    
    /*
    Everything is ready
    Smithers, release the hounds!
    */
    printf("Ready to roll, submitting transfers\n");
    fflush(stdout);
    for (unsigned int i = 0; i < N_TRANSFERS; ++i) {
        struct libusb_transfer *transfer = transfers[i];
    	int rc = -1;
    	
    	//printf("Submitting transfer\n"); fflush(stdout);
    	rc = libusb_submit_transfer(transfer);
    	//printf("Got rc\n"); fflush(stdout);
        if (rc) {
            printf("Failed to submit transfer: %s (%d)\n",
                    libusb_error_name(rc) , rc); fflush(stdout);
            exit(1);
        }
	}
	
	printf("Rolling\n");
	while (g_async_buff_pos < g_async_buff_sz) {
		struct timeval tv;
		tv.tv_sec  = 0;
		tv.tv_usec = 1000;
		
		rc = libusb_handle_events_timeout(NULL, &tv); 
		if (rc < 0) {
		    printf("failed to handle events\n");
			exit(1);
		}
	}
	
	printf("Buffer full!\n");
	
	printf("Releasing transfers...\n");
	printf("%u / %u transfers still alive\n", active_urbs, N_TRANSFERS);
	//Be a little nice
    for (unsigned int i = 0; i < N_TRANSFERS; ++i) {
        struct libusb_transfer *transfer = transfers[i];

		rc = libusb_cancel_transfer(transfer);
		if (rc < 0) {
	        printf("Warning: failed to cancel transfer\n");
	    }
	    free(transfer->buffer);
	}

	printf("Saving buffer...\n");
	save_buffer();
}

double cur_time(void) {
    struct timeval t;
    gettimeofday(&t, NULL);
    
    return t.tv_sec + t.tv_usec / 1000000.0;
}

//Return true if returned exactly {0x80}s
int val_reply(const uint8_t *reply, size_t size) {
    if (size != 1) {
        printf("Bad reply size %u\n", size);
        return -1;
    } else if (reply[0] != 0x08) {
        printf("Bad reply 0x%02X\n", reply[0]);
        return -1;
    }
    return 0;
}

int dev_init() {
#define std_ctrl(_request, _value, _index) do {\
    if (val_reply(buff, camera_control_message(0xC0, _request, _value, _index, buff, 1))) { \
        printf("Failed req(0xC0, 0x%02X, 0x%04X, 0x%04X\n", _request, _value, _index);\
        return -1; \
    } \
} while(0)
#define std_enc_ctrl std_ctrl

    
    struct libusb_device_handle *udev = g_camera.handle;
    uint8_t buff[4096];
    unsigned int n_rw = 0;

    //Reference packet numbers are from 01_3264_2448.cap
    
    /*
    First driver sets a sort of encryption key
    Reference packets 154-155
    A number of futur requests of this type have wValue and wIndex encrypted as follows:
    -Compute key = this wValue rotate left by 4 bits
        (decrypt.py rotates right because we are decrypting)
    -Later packets encrypt packets by XOR'ing with key
        XOR encrypt/decrypt is symmetrical
    Therefore by setting 0 we XOR with 0 and the shifting and XOR drops out
    Finally, the driver sends a 2 byte control out but always gets 1 back so just use the standard control
    */
    g_camera.key = 0x0000;
    n_rw = camera_control_message(0xC0, 0x16, g_camera.key, 0x0000, buff, 2);
    if (val_reply(buff, n_rw)) {
        printf("Failed key req\n");
        return -1;
    }
    
    //Packets 158/159
    printf("Setting alt\n");
    if (libusb_set_interface_alt_setting (g_camera.handle, 0, 1)) {
        printf("Failed to set alt setting\n");
        return -1;
    }

    /*
    Does some funky string reads here
    Optional, don't care about them
    */

    //Next (172-175) does some sort of challenge / response to make sure its not cloned hardware
    //It seems to be optional and I don't care to learn how it works since
    //I want to work with their hardware, not clone it
    
    //The following transactions are constant (no encryption)
    //Packets 176-183
    camera_control_message(0x40, 0x01, 0x0001, 0x000F, NULL, 0);
    camera_control_message(0x40, 0x01, 0x0000, 0x000F, NULL, 0);
    camera_control_message(0x40, 0x01, 0x0001, 0x000F, NULL, 0);
    n_rw = camera_control_message(0xC0, 0x20, 0x0000, 0x0000, buff, 4);
    if (validate_read((char[]){0xE6, 0x0D, 0x00, 0x00}, 4, buff, n_rw, "packet 182/183")) {
        return -1;
    }
    
    /*
    184/185 is a large read, possibly EEPROM configuration (ex: bad pixel) data
    Skip it since we don't know what to do with it
    Its partially encrypted
    */
    /*
    n_rw = camera_control_message(0xC0, 0x20, 0x0000, 0x0000, buff, 3590);
    if (3590 != n_rw) {
        printf("Wrong length back from EEPROM read\n");
        return -1;
    }
    */
    
    /*
    Now begins the encrypted packets (186-263)
    */


    //Unknown purpose
    std_enc_ctrl(0x0B, 0x0100, 0x0103);
    std_enc_ctrl(0x0B, 0x0000, 0x0100);
    std_enc_ctrl(0x0B, 0x0100, 0x0104);
    std_enc_ctrl(0x0B, 0x0004, 0x0300);
    std_enc_ctrl(0x0B, 0x0001, 0x0302);
    std_enc_ctrl(0x0B, 0x0008, 0x0308);
    std_enc_ctrl(0x0B, 0x0001, 0x030A);
    std_enc_ctrl(0x0B, 0x0004, 0x0304);
    std_enc_ctrl(0x0B, 0x0040, 0x0306);
    std_enc_ctrl(0x0B, 0x0000, 0x0104);
    std_enc_ctrl(0x0B, 0x0100, 0x0104);

    //Registers have an unknown purpose
    if (g_camera.width == 800) {
        std_enc_ctrl(0x0B, 0x0060, 0x0344);
        std_enc_ctrl(0x0B, 0x0CD9, 0x0348);
        std_enc_ctrl(0x0B, 0x0036, 0x0346);
        std_enc_ctrl(0x0B, 0x098F, 0x034A);
        std_enc_ctrl(0x0B, 0x07C7, 0x3040);
    } else if (g_camera.width == 1600) {
        std_enc_ctrl(0x0B, 0x009C, 0x0344);
        std_enc_ctrl(0x0B, 0x0D19, 0x0348);
        std_enc_ctrl(0x0B, 0x0068, 0x0346);
        std_enc_ctrl(0x0B, 0x09C5, 0x034A);
        std_enc_ctrl(0x0B, 0x06C3, 0x3040);
    } else {
        std_enc_ctrl(0x0B, 0x00E8, 0x0344);
        std_enc_ctrl(0x0B, 0x0DA7, 0x0348);
        std_enc_ctrl(0x0B, 0x009E, 0x0346);
        std_enc_ctrl(0x0B, 0x0A2D, 0x034A);
        std_enc_ctrl(0x0B, 0x0241, 0x3040);
    }
    std_enc_ctrl(0x0B, 0x0000, 0x0400);
    std_enc_ctrl(0x0B, 0x0010, 0x0404);
    
    
#define INDEX_WIDTH         0x034C
#define INDEX_HEIGHT        0x034E
    //std_enc_ctrl(0x0B, 0x0CC0, 0x034C)
    std_enc_ctrl(0x0B, g_camera.width, INDEX_WIDTH);
    //std_enc_ctrl(0x0B, 0x0990, 0x034E)
    std_enc_ctrl(0x0B, g_camera.height, INDEX_HEIGHT);
    
    
    //Unknown purpose
    if (g_camera.width == 800) {
        std_enc_ctrl(0x0B, 0x0384, 0x300A);
        std_enc_ctrl(0x0B, 0x0960, 0x300C);
    } else if (g_camera.width == 1600) {
        std_enc_ctrl(0x0B, 0x0640, 0x300A);
        std_enc_ctrl(0x0B, 0x0FA0, 0x300C);
    } else {
        std_enc_ctrl(0x0B, 0x0B4B, 0x300A);
        std_enc_ctrl(0x0B, 0x1F40, 0x300C);
    }
    
    //Unknown purpose
    std_enc_ctrl(0x0B, 0x0000, 0x0104);
    std_enc_ctrl(0x0B, 0x0301, 0x31AE);
    std_enc_ctrl(0x0B, 0x0805, 0x3064);
    std_enc_ctrl(0x0B, 0x0071, 0x3170);
    std_enc_ctrl(0x0B, 0x10DE, 0x301A);
    std_enc_ctrl(0x0B, 0x0000, 0x0100);
    std_enc_ctrl(0x0B, 0x0010, 0x0306);
    std_enc_ctrl(0x0B, 0x0100, 0x0100);
    
    
    
    /*
    Took the same time at 100 ms vs 350 ms exposure (2.0 seconds)
    At 700 it took about 2.57 seconds
    3 seconds at 1200
        Had to increase URB timeout...
    Test
        Capturing 16 1600x1200 frames
        Captured in 13.278530 sec
        
        30720000 bytes (30MiB)
        30MB / 13.28 sec = 2.314 MB / sec
        
        13.279 / 16 = 0.83 sec / frame
        How does this compare to exposure of 1200 ms?
        My captures times have been pretty non-linear...not going to worry about it
    */
    float exposure_ms = 350;
    uint16_t wValue = 0;
    if (g_camera.width == 1200) {
        /*
        First was at default exposure of 350 ms
        6d6 => 1750
        
        std_enc_ctrl(0x0B, 0x06D6, 0x3012);
        std_enc_ctrl(0x0B, 0x06D6, 0x3012);
        */
        /*
        This was approx 101 ms
        1fb => 507
        When the mouse is moved over the slider it says 740
            Not either...
        
        std_enc_ctrl(0x0B, 0x01FB, 0x3012);
        std_enc_ctrl(0x0B, 0x01FB, 0x3012);

        507 * 350/101 = 1757
        Winner!  Its linear
        m = 5
        0x6d6 / 0x1fb = 3.45

        1750 =  m * 350
        
        In theory from 0 to  0xFFFF / 5 = 13107 ms
        */
        wValue = exposure_ms * 5;
    } else if (g_camera.width == 1600) {
        /*
        350:
            std_enc_ctrl(0x0B, 0x041A, 0x3012);
            std_enc_ctrl(0x0B, 0x041A, 0x3012);
        101:
            std_enc_ctrl(0x0B, 0x0130, 0x3012);
            std_enc_ctrl(0x0B, 0x0130, 0x3012);
        0x41a / 0x130 = 3.45
        Same ratio
        41a => 1050
    
        1050 =  m * 350, m = 1050/350 = 3
        Hmm was expecting that it might have some linear relationship to resolution...
        */
        wValue = exposure_ms * 3;
    } else {
        /*
        std_enc_ctrl(0x0B, 0x020D, 0x3012);
        std_enc_ctrl(0x0B, 0x020D, 0x3012);
        
        0x020d => 525
        525 = m * 350 => m = 525 / 350 = 1.5
        */
        wValue = exposure_ms * 1.5;
    }
    //Wonder if theres a good reason for sending it twice
    std_enc_ctrl(0x0B, wValue, 0x3012);
    std_enc_ctrl(0x0B, wValue, 0x3012);
    
    
    
    
    
    
    
    std_enc_ctrl(0x0B, 0x0100, 0x0104);
    
    
    
    
    
//Range 0x1000 (nothing) to 0x11FF (highest)
#define GAIN_BASE           0x1000
#define GAIN_MAX            0x01FF
#define INDEX_GAIN_GTOP     0x3056
#define INDEX_GAIN_B        0x3058
#define INDEX_GAIN_R        0x305A
#define INDEX_GAIN_GBOT     0x305C
    /*
    Gain registers
    Suspect related to the RGB or possibly bayer filter
    Bayer would explain the duplicate 11C5
    Yep, created screenshot to illu
    */
    //Gain: 3.0
    if (0) {
        std_enc_ctrl(0x0B, 0x11C5, 0x3056);
        std_enc_ctrl(0x0B, 0x11CF, 0x3058);
        std_enc_ctrl(0x0B, 0x11ED, 0x305A);
        std_enc_ctrl(0x0B, 0x11C5, 0x305C);
    }
    //Gain: 1.0
    if (0) {
        std_enc_ctrl(0x0B, 0x105C, 0x3056);
        std_enc_ctrl(0x0B, 0x1068, 0x3058);
        std_enc_ctrl(0x0B, 0x10C8, 0x305A);
        std_enc_ctrl(0x0B, 0x105C, 0x305C);
    }
    //Gain: mixed
    if (0) {
        /*
        0x1000 seems to be completely off
        Still a reasonable image at 0x10FF
        Seems to be modular, at 0x12FF it looked like 0x10FF
            Sure enough 0x1200 was blank
            Set the two green channels phased by 0x200 as above and indistinguishable
        Hmm no it is modular but a little more complicated
        If the lower byte is 0 the image is always dark
        Very high gain at 0x7FFF
        0x8FFF is dark
        0x9+FFF are all saturated
        Anything of 0x**00 is dark
        Upper bits do in fact affect gain
        This is likely best played around with a slider
        Image faintly visible at FF01
        Very faint at 0x01FF, 0xFF01
        */
        std_enc_ctrl(0x0B, 0x01FF, INDEX_GAIN_GTOP);
        std_enc_ctrl(0x0B, 0x1100, INDEX_GAIN_B);
        std_enc_ctrl(0x0B, 0x1100, INDEX_GAIN_R);
        std_enc_ctrl(0x0B, 0x1100, INDEX_GAIN_GBOT);
    }
    if (1) {
        /*
        0x68 = 1.0 * m, m = 0x68
        
        
        */
        double gain = 1.5;
#define GAIN_BASE           0x1000
#define GAIN_MAX            0x01FF
        
        std_enc_ctrl(0x0B, 0x01FF, INDEX_GAIN_GTOP);
        std_enc_ctrl(0x0B, 0x1100, INDEX_GAIN_B);
        std_enc_ctrl(0x0B, 0x1100, INDEX_GAIN_R);
        std_enc_ctrl(0x0B, 0x1100, INDEX_GAIN_GBOT);
    }    
    
    
    
    
    
    std_enc_ctrl(0x0B, 0x0000, 0x0104);


    //Omitted this by accident, does not work without it
    camera_control_message(0x40, 0x01, 0x0003, 0x000F, NULL, 0);
    
    return 0;
}

int validate_device( int vendor_id, int product_id ) {
    /*
    From toupcam.inf
    "UCMOS00350KPA"=TOUPCAM.Dev, USB\VID_0547&PID_6035
    "UCMOS01300KPA"=TOUPCAM.Dev, USB\VID_0547&PID_6130
    "UCMOS02000KPA"=TOUPCAM.Dev, USB\VID_0547&PID_6200
    "UCMOS03100KPA"=TOUPCAM.Dev, USB\VID_0547&PID_6310
    "UCMOS05100KPA"=TOUPCAM.Dev, USB\VID_0547&PID_6510
    "UCMOS08000KPA"=TOUPCAM.Dev, USB\VID_0547&PID_6800
    "UCMOS08000KPB"=TOUPCAM.Dev, USB\VID_0547&PID_6801
    "UCMOS09000KPA"=TOUPCAM.Dev, USB\VID_0547&PID_6900
    "UCMOS09000KPB"=TOUPCAM.Dev, USB\VID_0547&PID_6901
    "UCMOS10000KPA"=TOUPCAM.Dev, USB\VID_0547&PID_6010
    "UCMOS14000KPA"=TOUPCAM.Dev, USB\VID_0547&PID_6014
    "UCMOS01300KMA"=TOUPCAM.Dev, USB\VID_0547&PID_6131
    "UCMOS05100KMA"=TOUPCAM.Dev, USB\VID_0547&PID_6511
    "UHCCD00800KPA"=TOUPCAM.Dev, USB\VID_0547&PID_8080
    "UHCCD01400KPA"=TOUPCAM.Dev, USB\VID_0547&PID_8140
    "EXCCD01400KPA"=TOUPCAM.Dev, USB\VID_0547&PID_8141
    "UHCCD02000KPA"=TOUPCAM.Dev, USB\VID_0547&PID_8200
    "UHCCD02000KPB"=TOUPCAM.Dev, USB\VID_0547&PID_8201
    "UHCCD03100KPA"=TOUPCAM.Dev, USB\VID_0547&PID_8310
    "UHCCD05000KPA"=TOUPCAM.Dev, USB\VID_0547&PID_8500
    "UHCCD05100KPA"=TOUPCAM.Dev, USB\VID_0547&PID_8510
    "UHCCD06000KPA"=TOUPCAM.Dev, USB\VID_0547&PID_8600
    "UHCCD08000KPA"=TOUPCAM.Dev, USB\VID_0547&PID_8800
    "UHCCD03150KPA"=TOUPCAM.Dev, USB\VID_0547&PID_8315
    "UHCCD00800KMA"=TOUPCAM.Dev, USB\VID_0547&PID_7800
    "UHCCD01400KMA"=TOUPCAM.Dev, USB\VID_0547&PID_7140
    "UHCCD01400KMB"=TOUPCAM.Dev, USB\VID_0547&PID_7141
    "UHCCD02000KMA"=TOUPCAM.Dev, USB\VID_0547&PID_7200
    "UHCCD03150KMA"=TOUPCAM.Dev, USB\VID_0547&PID_7315
    "Auto Focus Controller"=TOUPCAM.Dev, USB\VID_0547&PID_1010
    */
	switch (vendor_id) {
	case 0x0547:
		/*
        New guy (rev 2 cameras):
        Bus 002 Device 007: ID 0547:6801 Anchor Chips, Inc. 
        */
        switch (product_id) {
		case 0x6801: 
			printf("ToupTek UCMOS08000KPB (AmScope MU800)\n");
			return 0;
        
		default:
			printf("Unknown product id\n");
			return 1;
		}
	default:
		//printf("Unknown vendor id\n");
		return 1;
	}
}

libusb_device_handle *locate_camera( void ) {
	// Discover devices
	libusb_device **list;
	libusb_device *found  = NULL;
	libusb_device_handle *handle = NULL;
	unsigned char located = 0;
	size_t count = 0;
	int rc = -1;

	count = libusb_get_device_list(NULL, &list);
	if (count < 0) {
        printf("Error fetching device list\n");
	    return NULL;
	}
    
	for (int i = 0; i < count; i++) {
		libusb_device *dev = list[i];
		int rc = -1;
    	struct libusb_device_descriptor desc;

		// device seem to have desc.idVendor set to 0bd7 = 3031(decimal)
		// (can find this using lsusb example )
		rc = libusb_get_device_descriptor(dev, &desc);
        if (rc) {
            printf("Failed to get dev descriptor\n");
        	libusb_free_device_list(list, 1);
            return NULL;
        }

		printf("** usb device idVendor=0x%04X, idProduct=0x%04X **\n",
				desc.idVendor, desc.idProduct);
		if (validate_device(desc.idVendor, desc.idProduct)) {
			continue;
		}
		
		located++;
		g_camera.dev = dev;
		printf("Camera Device Found\n");
	}
	
	if (located > 1) {
	    printf("WARNING: more devices than expected\n");
	}
	if (g_camera.dev) {
         rc = libusb_open(g_camera.dev, &handle);
         if (rc) {
            printf("Failed to get dev descriptor\n");
        	libusb_free_device_list(list, 1);
            return NULL;
         }
	}
	libusb_free_device_list(list, 1);
	
	return handle;
}

void relocate_camera() {
	if (g_camera.handle) {
		libusb_close(g_camera.handle);
	}
	
	g_camera.handle = locate_camera();
	printf("Handle: 0x%08X\n", (int)g_camera.handle);
 	if (g_camera.handle == NULL) {
		printf("Could not open the camera device\n");
		exit(1);
	}
}

void usage() {
	printf("mu800 [options]\n");
	printf("Options:\n");
	printf("-s: dump strings\n");
}

int main(int argc, char **argv) {	
	bool should_dump_strings = false;
	int rc_tmp = 0;
	
	opterr = 0;
	while (true) {
		int c = getopt(argc, argv, "h?vsr:");
		
		if (c == -1) {
			break;
		}
		
		switch (c)
		{
			case 'h':
			case '?':
				usage();
				exit(1);
				break;
			
			case 'v':
				g_verbose = true;
				break;
			
			case 's':
				should_dump_strings = true;
				break;

			case 'r':
			    //FIXME: select resolution
				break;
				
			default:
				printf("Unknown argument %c\n", c);
				usage();
				exit(1);
		}
	}

    //FIXME: do somehting for more than 1 fn...
    for ( ; optind < argc; optind++) {
		g_image_file_out = argv[optind];
	}

	libusb_init(NULL);
	//Prints out *lots* of information on how it found it
	libusb_set_debug(NULL, 4);
	relocate_camera();
		
	rc_tmp = libusb_set_configuration(g_camera.handle, 1);
	printf("conf_stat=%d\n", rc_tmp);
	if (rc_tmp < 0) {
		perror("test");
		printf("Failed to configure\n");
		return 1;
	}
	
	rc_tmp = libusb_claim_interface(g_camera.handle, 0);
	printf("claim_stat=%d\n", rc_tmp);
	if (rc_tmp < 0) {
		perror("test");
		printf("Failed to claim\n");
		switch (rc_tmp) {
		case EBUSY:
			printf("Interface is not available to be claimed\n");
			break;
		case ENOMEM:
			printf("Insufficient memory\n");
			break;
		default:
			printf("Unknown rc %d\n", rc_tmp);
		}
		return 1;
	}
	
	if (0) {
        g_camera.width = 800;
        g_camera.height = 600;
    }
    if (1) {
        g_camera.width = 1600;
        g_camera.height = 1200;
    }
    if (0) {
        g_camera.width = 3264;
        g_camera.height = 2448;
    }
	
	//download_ram();
	if (dev_init()) {
	    printf("Failed to initialize camera\n");
    	shutdown();
	    return 1;
	}
	

    printf("Capturing %u %ux%u frames\n", N_FRAMES, g_camera.width, g_camera.height);

	//It tries to dump string a bunch of times
	//capture();
    double start = cur_time();
	capture_async();
    double end = cur_time();
    printf("Captured in %f sec\n", end - start);
	shutdown();
	
	return 0;
}

