#include <errno.h>
#include <stdio.h>
#include <stdint.h>
//#include <libusb/libusb.h> 
#include <libusb-1.0/libusb.h>
#include <string.h>
#include <string>
#include <stdlib.h>

#include "hexdump.cpp"

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


struct libusb_device_handle *g_camera_handle = NULL;
struct libusb_device *g_dev = NULL;

libusb_device_handle *locate_camera( void );
bool g_verbose = true;

void camera_exit(int rc) {
	if (g_camera_handle) {
		libusb_close(g_camera_handle);
	}
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


/*
Although wLength is two byte, response is only one byte
So I don't think its a good idea to request strings > 0xFF
*/
#if 0
int extract_string(int i, unsigned int buff_size = 0xFF) {
	char buff[0xFF];
	int rc_tmp;
	
	if (buff_size > sizeof(buff)) {
	    printf("bad buff size\n");
	    exit(1);
	}
	
	//rc_tmp = libusb_get_string_simple(g_camera_handle, i, buff, buff_size);
	rc_tmp = libusb_get_string(g_camera_handle, i, 0x0409, buff, buff_size);
	if (rc_tmp < 0) {
		printf("error @ %d\n", i);
		/*
		if (!g_keep_going) {
		    break;
	    }
	    */
	    return -1;
	}
	//printf("%02X%02X%02X%02X\n", buff[0], buff[1], buff[2], buff[3]);
	//buff[rc_tmp] = 0;
	//wchar..how to print?
	//in any case I'm getting weird chars back so better to hex dump
	//printf("string[%d]: %s\n", i, &buff[0]); fflush(stdout);
    printf("Got string, dumping\n");
    UVDHexdumpCore(buff, rc_tmp, "    ", false, 0);
    return 0;
}

void extract_string_fatal(int i, unsigned int buff_size = 0xFF) {
    if (extract_string(i, buff_size)) {
		printf("failed to extract string\n");
		camera_exit(1);
    }
}
#endif

unsigned int camera_bulk_read(int ep, void *bytes, int size) {
    int actual_length = 0;
    
	//int libusb_bulk_read(usb_dev_handle *dev, int ep, char *bytes, int size,
	//	int timeout);
	int rc_tmp = libusb_bulk_transfer(g_camera_handle, ep, (unsigned char *)bytes, size, &actual_length, 500);
	
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
	int rc_tmp =  libusb_bulk_transfer(g_camera_handle, ep, (unsigned char *)bytes, size, &actual_length, 500);
	
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

//generator spits out that
#define dev_ctrl_msg camera_control_message
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
	extern int libusb_control_msg(struct libusb_device *dev, unsigned int pipe,
		__u8 request, __u8 requesttype, __u16 value, __u16 index,
		void *data, __u16 size, int timeout);
	*/
	rc_tmp = libusb_control_transfer(g_camera_handle, requesttype, request, value, index, (unsigned char *)bytes, size, 500);
	if (rc_tmp < 0) {
		printf("failed\n");
		exit(1);
	}
	return rc_tmp;
}

void validate_read(void *expected, size_t expected_size, void *actual, size_t actual_size, const char *msg) {
	if (expected_size != actual_size) {
		printf("%s: expected %d bytes, got %d bytes\n", msg, expected_size, actual_size);
		camera_exit(1);		
	}
	if (memcmp(expected, actual, expected_size)) {
		printf("%s: regions do not match\n", msg);
		printf("  Actual:\n");
		UVDHexdumpCore(actual, expected_size, "    ", false, 0);
		printf("  Expected:\n");
		UVDHexdumpCore(expected, expected_size, "    ", false, 0);
		//camera_exit(1);
		return;
	}
	printf("Regions of length %d DO match\n", expected_size);
}

//#include "fx2.cpp"


const char *g_image_file_out = "image.bin";

void capture() {
	unsigned int n_read = 0;
	int rc_tmp = 0;

	char *buff = NULL;
	unsigned int buff_pos = 0;
	
	unsigned int to_read = 800 * 600 * 4;
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
const size_t g_async_buff_sz = 800 * 600 * 4;
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
    if (!g_have_stalled && g_should_stall && g_async_buff_pos >= g_async_buff_sz / 2) {
        unsigned int stall_ms = 300;
        printf("Stalling @ %u for %u ms\n", g_async_buff_pos, stall_ms);
        usleep(stall_ms * 1000);
        g_have_stalled = true;
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
		    g_camera_handle, DATA_EP,
		    buff, buff_sz,
		    capture_async_cb, NULL, 500 );
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

void replay() {
    struct libusb_device_handle *udev = g_camera_handle;
    
    /*
    This piece has been highly variable
    What is wValue and why does it seem random each device init?
    */
    if (1) {
        /*
        printf("\n");
        printf("Replaying early setup...\n");
        {
            #include "captures/800x600_1/touptek_0_early_setup.c"
        }
        */
        int n_rw = 0;
        uint8_t buff[64];

        //Generated from packet 5/6
        n_rw = dev_ctrl_msg(0xC0, 0x16, 0xA20F, 0x0000, buff, 2);
        //WARNING: shrinking response, max 2 but got 1
        validate_read((char[]){0x08}, 1, buff, n_rw, "packet 5/6");
    }
    
    printf("Setting alt\n");
    if (libusb_set_interface_alt_setting (g_camera_handle, 0, 1)) {
        printf("Failed to set alt setting\n");
        camera_exit(1);
    }

    /*
    This seems to be optional
    if (0) {
        //Between these two there were a few string fetch packets
        printf("\n");
        printf("Requesting strings...\n");
        //This is what replay has
        extract_string_fatal(1, 0xFF);
        extract_string_fatal(1, 0xFF);
        extract_string_fatal(1, 0xFF);
        extract_string_fatal(1, 2);
        extract_string_fatal(1, 2);
        extract_string_fatal(1, 2);
    }
    */

    if (1) {
        printf("\n");
        printf("Replaying late/main setup...\n");
        if (1) {
            #include "captures/800x600_1/touptek_0_main_setup.c"
        }



    }
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
			printf("AmScope MU800\n");
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
		g_dev = dev;
		printf("Camera Device Found\n");
	}
	
	if (located > 1) {
	    printf("WARNING: more devices than expected\n");
	}
	if (g_dev) {
         rc = libusb_open(g_dev, &handle);
         if (rc) {
            printf("Failed to get dev descriptor\n");
        	libusb_free_device_list(list, 1);
            return NULL;
         }
	}
	libusb_free_device_list(list, 1);
	
	return handle;
}

#if 0
#include "dump.cpp"

/*
Strings from dump
1 (hex): 03 54
err nvm I think wireshark is confused
*/

void dump_strings() {
    printf("Dumping strings\n");
	//Think index 0 is special case to get language ID
	for (int i = 1; ; ++i) {
	    extract_string(i);
	}
}
#endif

void relocate_camera() {
	if (g_camera_handle) {
		libusb_close(g_camera_handle);
	}
	
	g_camera_handle = locate_camera();
	printf("Handle: 0x%08X\n", (int)g_camera_handle);
 	if (g_camera_handle == NULL) {
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
		int c = getopt(argc, argv, "h?vs");
		
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

    /*
	//print_all_device_information();
	if (should_dump_strings) {
    	dump_strings();
	    exit(1);
	}
	if (g_verbose) {
    	usb_set_debug(4);
	}
	*/

		
	/*
	Config = 0 results in fail to claim since it would put it into address mode
	Should I try to enumerate these?
	invalid arg if 2
	Kernel seems to chose config 1
		usb 1-3: new high speed USB device using ehci_hcd and address 122
		usb 1-3: config 1 interface 0 altsetting 0 bulk endpoint 0x82 has invalid maxpacket 1024
		usb 1-3: New USB device found, idVendor=0547, idProduct=4d88
		usb 1-3: New USB device strings: Mfr=1, Product=2, SerialNumber=0
		usb 1-3: Product: DCM800
		usb 1-3: Manufacturer: ScopeTek
	*/
	rc_tmp = libusb_set_configuration(g_camera_handle, 1);
	printf("conf_stat=%d\n", rc_tmp);
	if (rc_tmp < 0) {
		perror("test");
		printf("Failed to configure\n");
		return 1;
	}
	
	//relocate_camera();
	//print_all_device_information();
	
	rc_tmp = libusb_claim_interface(g_camera_handle, 0);
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
	
	/*
	rc_tmp = libusb_set_altinterface(g_camera_handle, 0);
	printf("alt_stat=%d\n", rc_tmp);
	if (rc_tmp < 0) {
		perror("test");
		printf("Failed to set alt interface\n");
		return 1;
	}
	*/
	//sleep(5);
	
	//download_ram();
	replay();
	//It tries to dump string a bunch of times
	//capture();
	capture_async();
	
	libusb_close(g_camera_handle);
	
	return 0;
}

