#include <errno.h>
#include <stdio.h>
#include <stdint.h>
#include <usb.h>
#include <string.h>
#include <string>

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
//Heavy traffic during startup
//Does this actually exist?  Might be a VMWare relic
#define CONFIG_ENDPOINT 		1
//Observed from capture
#define	VIDEO_ENDPOINT 			2

struct usb_dev_handle *g_camera_handle = NULL;
struct usb_device *g_dev = NULL;

usb_dev_handle *locate_camera( void );

void camera_exit(int rc) {
	if (g_camera_handle) {
		usb_close(g_camera_handle);
	}
	exit(1);
}

unsigned int camera_bulk_read(int ep, void *bytes, int size) {
	//int usb_bulk_read(usb_dev_handle *dev, int ep, char *bytes, int size,
	//	int timeout);
	
	int rc_tmp = usb_bulk_read(g_camera_handle, ep, (char *)bytes, size, 500);
	
	if (rc_tmp < 0) {
		perror("ERROR");
		printf("failed read: %d\n", rc_tmp);
		camera_exit(1);
	}
	
	return rc_tmp;
}

unsigned int camera_bulk_write(int ep, void *bytes, int size) {
	int rc_tmp =  usb_bulk_write(g_camera_handle, ep, (char *)bytes, size, 500);
	
	if (rc_tmp < 0) {
		perror("ERROR");
		printf("failed write: %d\n", rc_tmp);
		camera_exit(1);
	}
	
	return rc_tmp;
}

void example_code( void ) {	
	int send_status = 0;
	unsigned char send_data = 0xFF;
	unsigned char receive_data = 0;

	send_status = usb_bulk_write(g_camera_handle, 4, (char *)&send_data, 1, 500);
	printf("TX stat=%d\n", send_status);
	
	usb_bulk_read(g_camera_handle, 3, (char *)&receive_data, 1, 500);	
	printf("RX stat=%d -> RX char=%d\n", send_status, receive_data);

	/* Write the data2send bytes to the 7-segs */
	/*
	send_status = usb_control_msg(g_camera_handle, 0x20, 0x09, 0x0200, 0x0001, send_data, 2, 500); 
	printf("TX stat=%d\n", send_status);
	usleep(10000);
	*/ 
	/* Read the bytes that were just sent to the 7-segs */
	/*	
	send_status = usb_control_msg(g_camera_handle, 0xA0, 0x01, 0x0100, 0x0001, receive_data, 2, 500); 
	printf("RX stat=%d data=0x%x, 0x%x\n", send_status, receive_data[0], receive_data[1]);
	usleep(10000);
	*/	
}

void replay_EP1_0() {
	uint8_t receive_data[0x100];
	unsigned int n_read = 0;
	
	n_read = camera_bulk_read(CONFIG_ENDPOINT, &receive_data, 6);	
	printf("Read: %d\n", n_read);
	//00 88 1C EC 22 00

	//00 13 1C 2B 23 00
}

void replay_vmware() {
	replay_EP1_0();
}

/*
int usb_control_msg(usb_dev_handle *dev, int requesttype, int request,
	int value, int index, char *bytes, int size, int timeout);
*/

unsigned int camera_control_message(int requesttype, int request,
		int value, int index, char *bytes, int size) {
	int rc_tmp = 0;
	
	/*
	WARNING: request / request type parameters are swapped between kernel and libusb
	request type is clearly listed first in USB spec and seems more logically first so I'm going to blame kernel on this
	although maybe libusb came after and was trying for multi OS comatibility right off the bat
	
	libusb
	int usb_control_msg(usb_dev_handle *dev, int requesttype, int request, int value, int index, char *bytes, int size, int timeout);
	
	kernel
	extern int usb_control_msg(struct usb_device *dev, unsigned int pipe,
		__u8 request, __u8 requesttype, __u16 value, __u16 index,
		void *data, __u16 size, int timeout);
	*/
	rc_tmp = usb_control_msg(g_camera_handle, requesttype, request, value, index, bytes, size, 500);
	if (rc_tmp < 0) {
		printf("failed\n");
	}
	return rc_tmp;
}

void camera_control_message_all(int requesttype, int request,
		int value, int index, char *bytes, int size) {
	unsigned int rc = camera_control_message(requesttype, request,
			value, index, bytes, size);
	if (rc != size) {
		printf("expected %d got %d bytes\n", size, rc);
		exit(1);
	}
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

void replay_wireshark_setup() {
	char buff[0x100];
	unsigned int n_rw = 0;
	printf("Replaying wireshark stuff\n");
	

	//Generated from packet 5
	n_rw = camera_control_message(0x40, 0x01, 0x0001, 0x000F, NULL, 0);
	//Generated from packet 7
	n_rw = camera_control_message(0x40, 0x01, 0x0000, 0x000F, NULL, 0);
	//Generated from packet 9
	n_rw = camera_control_message(0x40, 0x01, 0x0001, 0x000F, NULL, 0);
	//Generated from packet 11
	n_rw = camera_control_message(0xC0, 0x0B, 0x0100, 0x0103, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 12");
	//Generated from packet 13
	n_rw = camera_control_message(0xC0, 0x0B, 0x0100, 0x0104, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 14");
	//Generated from packet 15
	n_rw = camera_control_message(0xC0, 0x0A, 0x0000, 0x3000, (char *)&buff, 3);
	validate_read((char[]){0x2B, 0x00, 0x08}, 3, &buff, n_rw, "packet 16");
	//Generated from packet 17
	n_rw = camera_control_message(0xC0, 0x0B, 0x0100, 0x0104, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 18");
	//Generated from packet 19
	n_rw = camera_control_message(0xC0, 0x0B, 0x0020, 0x0344, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 20");
	//Generated from packet 21
	n_rw = camera_control_message(0xC0, 0x0B, 0x0CA1, 0x0348, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 22");
	//Generated from packet 23
	n_rw = camera_control_message(0xC0, 0x0B, 0x0020, 0x0346, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 24");
	//Generated from packet 25
	n_rw = camera_control_message(0xC0, 0x0B, 0x0981, 0x034A, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 26");
	//Generated from packet 27
	n_rw = camera_control_message(0xC0, 0x0B, 0x02FC, 0x3040, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 28");
	//Generated from packet 29
	n_rw = camera_control_message(0xC0, 0x0B, 0x0002, 0x0400, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 30");
	//Generated from packet 31
	n_rw = camera_control_message(0xC0, 0x0B, 0x0014, 0x0404, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 32");
	//Generated from packet 33
	n_rw = camera_control_message(0xC0, 0x0B, 0x0280, 0x034C, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 34");
	//Generated from packet 35
	n_rw = camera_control_message(0xC0, 0x0B, 0x01E0, 0x034E, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 36");
	//Generated from packet 37
	n_rw = camera_control_message(0xC0, 0x0B, 0x02C0, 0x300A, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 38");
	//Generated from packet 39
	n_rw = camera_control_message(0xC0, 0x0B, 0x0E00, 0x300C, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 40");
	//Generated from packet 41
	n_rw = camera_control_message(0xC0, 0x0B, 0x0000, 0x0104, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 42");
	//Generated from packet 43
	n_rw = camera_control_message(0xC0, 0x0B, 0x0000, 0x0100, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 44");
	//Generated from packet 45
	n_rw = camera_control_message(0xC0, 0x0B, 0x0100, 0x0104, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 46");
	//Generated from packet 47
	n_rw = camera_control_message(0xC0, 0x0B, 0x0004, 0x0300, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 48");
	//Generated from packet 49
	n_rw = camera_control_message(0xC0, 0x0B, 0x0001, 0x0302, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 50");
	//Generated from packet 51
	n_rw = camera_control_message(0xC0, 0x0B, 0x0008, 0x0308, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 52");
	//Generated from packet 53
	n_rw = camera_control_message(0xC0, 0x0B, 0x0001, 0x030A, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 54");
	//Generated from packet 55
	n_rw = camera_control_message(0xC0, 0x0B, 0x0004, 0x0304, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 56");
	//Generated from packet 57
	n_rw = camera_control_message(0xC0, 0x0B, 0x0020, 0x0306, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 58");
	//Generated from packet 59
	n_rw = camera_control_message(0xC0, 0x0B, 0x90D8, 0x301A, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 60");
	//Generated from packet 61
	n_rw = camera_control_message(0xC0, 0x0B, 0x0000, 0x0104, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 62");
	//Generated from packet 63
	n_rw = camera_control_message(0xC0, 0x0B, 0x0100, 0x0100, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 64");
	//Generated from packet 65
	n_rw = camera_control_message(0xC0, 0x0A, 0x0000, 0x300C, (char *)&buff, 3);
	validate_read((char[]){0x0E, 0x00, 0x08}, 3, &buff, n_rw, "packet 66");
	//Generated from packet 67
	n_rw = camera_control_message(0xC0, 0x0B, 0x90D8, 0x301A, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 68");
	//Generated from packet 69
	n_rw = camera_control_message(0xC0, 0x0B, 0x0805, 0x3064, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 70");
	//Generated from packet 71
	n_rw = camera_control_message(0xC0, 0x0B, 0x0000, 0x0104, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 72");
	//Generated from packet 73
	n_rw = camera_control_message(0xC0, 0x0B, 0x0100, 0x0100, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 74");
	//Generated from packet 75
	n_rw = camera_control_message(0xC0, 0x0B, 0x0001, 0x0402, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 76");
	//Generated from packet 77
	n_rw = camera_control_message(0xC0, 0x0B, 0x0001, 0x0104, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 78");
	//Generated from packet 79
	n_rw = camera_control_message(0xC0, 0x0B, 0x0000, 0x0104, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 80");
	//Generated from packet 81
	n_rw = camera_control_message(0xC0, 0x0B, 0x01F4, 0x3012, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 82");
	//Generated from packet 83
	n_rw = camera_control_message(0xC0, 0x0B, 0x023E, 0x305E, (char *)&buff, 1);
	validate_read((char[]){0x08}, 1, &buff, n_rw, "packet 84");
	//Generated from packet 85
	n_rw = camera_control_message(0x40, 0x01, 0x0003, 0x000F, NULL, 0);
}


#define REQ_FIRMWARE_LOAD		0xA0
#define REG_CPUCS				0xE600

void fx2_reg_write( unsigned int address, uint8_t val ) {
	camera_control_message_all(
				USB_ENDPOINT_OUT | USB_TYPE_VENDOR | USB_RECIP_ENDPOINT,
				REQ_FIRMWARE_LOAD,
				address, 0x00,
				(char *)&val, sizeof(val));
}
void fx2_reg_read( unsigned int address, uint8_t *val ) {
	camera_control_message_all(
				USB_ENDPOINT_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE,
				REQ_FIRMWARE_LOAD,
				address, 0x00,
				(char *)val, sizeof(*val));
}


uint8_t *dump_fx2_mem( unsigned int start, size_t size ) {	
	unsigned int end = start + size - 1;
	uint8_t *buff_ret = (uint8_t *)malloc(size);
	uint8_t *buff = buff_ret;
	size_t default_size = 16;
	
	for (unsigned int address = start; address <= end; ) {
		int rc_tmp = -1;
		size_t this_size = default_size;
		size_t remaining = 0;

		remaining = end - address + 1;
		//printf("loop 0x%04X of 0x%04X hitting 0x%02X @ 0x%p\n", address, end, remaining, buff);
		if (this_size > remaining) {
			this_size = remaining;
		}

		rc_tmp = usb_control_msg(g_camera_handle,
				USB_ENDPOINT_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE,
				REQ_FIRMWARE_LOAD,
				address, 0x00,
				(char *)buff, this_size, 500);
		if (rc_tmp < 0) {
			printf("failed\n");
			exit(1);
		}
		if (rc_tmp != this_size) {
			printf("0x%04X: transfer size wrong, wanted %d got %d\n", address, this_size, rc_tmp);
			exit(1);
		} else {
			//printf("0x%04X: ", address);
			//UVDHexdumpCore( buff, this_size, "  " );
			buff += this_size;
		}
		address += this_size;
	}
	return buff_ret;
}

void hexdump_fx2_mem( unsigned int start, unsigned int end, const char *file ) {
	size_t code_sz = end - start + 1;
	uint8_t *code = NULL;
	
	code = dump_fx2_mem( start, code_sz );
	UVDHexdumpCore( code, code_sz, "", true, start );
	if (file) {
		FILE *f = fopen(file, "w");
		if (f == NULL) {
			printf("file open failed\n");
			exit(1);
		}
		fwrite(code, 1, code_sz, f);
		fclose(f);
	}
	free( code );
}


void fx2_reset() {
	printf("Resetting MCU\n");
	fx2_reg_write( REG_CPUCS, 1 );
	printf("Reset OK\n");
}

void fx2_start() {
	printf("Brining out of reset MCU\n");
	fx2_reg_write( REG_CPUCS, 0 );
	printf("Starting OK\n");
}

void download_ram() {
	/*
	Download from our perspective is upload from their's
	
		               Table 2-24. Firmware Upload
	Byte        Field    Value           Meaning     Firmware Response
		                                            None Required.
		                 0xC0
	 0   bmRequestType           Vendor Request, IN
		                 0xA0
	 1   bRequest                “Firmware Load”
	 2   wValueL        AddrL    Starting address
		                AddrH
	 3   wValueH
	 4   wIndexL         0x00
	 5   wIndexH         0x00
		                 LenL
	 6   wLengthL                Number of Bytes
		                 LenH
	 7   wLengthH
	*/
	
	//Must be reset before reading / writing is allowed
	fx2_reset();
	
	if (true) {
		printf("Code short:\n");
		hexdump_fx2_mem( 0x0000, 0x00F, NULL );
	}
	if (true) {
		printf("\n\n\n\n");
		printf("Code:\n");
		hexdump_fx2_mem( 0x0000, 0x1FFF, "code.bin" );
	}
	if (true) {
		printf("\n\n\n\n");
		printf("RAM:\n");
		hexdump_fx2_mem( 0xE000, 0xE1FF, "ram.bin" );
	}
	/*
	Leaving this out seems to make the next read not work until plugged back in
	or probably doing this first
	But other RAM stuff still works
	*/
	fx2_start();
	
	/*
	aha:
		Prior to ReNumeration, the host downloads data into the EZ-
		USB’s internal RAM. The host can access two on-chip EZ-
		USB RAM spaces — Program / Data RAM at 0x0000-
		0x3FFF and Data RAM at 0xE000-0xE1FF — which it can
		download or upload only when the CPU is held in reset.
		The host must write to the CPUCS register to put the CPU in
		or out of reset. These two RAM spaces may also be boot-
		loaded by a ‘C2’ EEPROM connected to the I2C bus.
	Didn't realize it had to be held in reset...hmm
	Here it is
		A host loader program must write 0x01 to the CPUCS regis-
		ter to put the CPU into RESET, load all or part of the EZ-
		USB RAM with firmware, then reload the CPUCS register
		with ‘0’ to take the CPU out of RESET. The CPUCS register
		(at 0xE600) is the only EZ-USB register that can be written
		using the Firmware Download command.
	
	0x0000:0x1FFF: eight KB RAM code and data
	0x2000:0xDFFF: 48 KB external data memory
	0xE000:0xE1FF: 0.5 KB RAM data
		Seemed to dump
	0xE200:0xFFFF: 7.5 KB USB registers and 4K EP buffers
	*/
	//for (unsigned int address = 0xE000; address < 0xE1FF; address += sizeof(buff)) {
}
		
const char *g_image_file_out = "image.bin";

#define DATA_ENDPOINT 0x82
void replay_wireshark_bulk() {
	/*
	A slew of read requests are launched in parallel:
		16384 @ 87
		16384
		16384
		13312
		16384
		3072
		16384
		16384
		16384 @ 95
		13312 @ 96		
	Then 14336 bytes come back @ 97
	More requests
		16384 @ 98
		2048
		16384
		16384
		16384
		14336 @ 103
		16384
		2048
		16384
		16384
		16384
		14336 @ 109
	16 reads come back @ 110 - 125
	
	*/
	unsigned int n_read = 0;
	int rc_tmp = 0;

	//n_read = camera_bulk_read(DATA_ENDPOINT, void *bytes, int size) {
	char *buff = NULL;
	unsigned int buff_pos = 0;
	
	//unsigned int to_read = 640 * 480 * 3 * 3;
	unsigned int to_read = 4 * 1024 * 1024;
	const size_t buff_sz = to_read;
	printf("Going to read %d, single read buffer size %d\n", to_read, buff_sz);
	buff = (char *)malloc(to_read + buff_sz);
	if (buff == NULL) {
		printf("out of mem\n");
		camera_exit(1);
	}
	fflush(stdout);
	int count = 0;
	unsigned int last_total = 0;
	/*
	Assuming RGB24 encoding @ 640 X 480 need 640 * 480 * 3 = 921600
	*/
	while (buff_pos < to_read) {
		++count;
		n_read = camera_bulk_read(DATA_ENDPOINT, buff + buff_pos, buff_sz);
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

void replay_wireshark() {
	replay_wireshark_setup();
	replay_wireshark_bulk();
}

void replay() {
	/*
	Its amazing how different the capture on the same stream is between these tools
	VMWare does acceleration that only guarnatees equivilence according to USB spec
	SnoopyPro just seems to not work
	I tried it on a real machine thinking maybe VMWare tools was getting in the way
	It captures some packets...but not enough

	One unexplained thing is that VMWare captures a bunch of packets during AmScope startup to inexistant EP1 but usbmon (Wireshark) does not
	Must be some VMWare internal thing, but odd that it would be aware of the program startup when the real device is not
	*/
	
	//replay_vmware();
	//replay_snoopypro();
	replay_wireshark();
}

int validate_device( int vendor_id, int product_id ) {
	switch (vendor_id) {
	case 0x0547:
		switch (product_id) {
		/*
		Just by chance saw this
		
		http://www.oplenic.com/faq.asp?page=7
		A:Dear chris,Please check your email box,we have email it to you.DCM130 is Amscope MD600,2009-06-25
		*/
		//20784
//#define PROD_ID_AMSCOPE_MD600E
		case 0x5130:
			printf("AmScope MD600E\n");
			return 0;
		case 0x5258:
			printf("AmScope MD700\n");
			return 0;
		case 0x4D33:
			printf("AmScope MD800E\n");
			return 0;
		case 0x4454:
			printf("AmScope MD900\n");
			return 0;
		case 0x5257:
			printf("AmScope MD900\n");
			return 0;
		case 0x4D35:
			printf("AmScope MD900E\n");
			return 0;
		case 0x4D53:
			printf("AmScope MD900E\n");
			return 0;
		case 0x4D88:
			printf("ScopeTek DCM800 (AmScope MD1800)\n");
			return 0;
		case 0x4D90:
			printf("ScopeTek DCM900?  (AmScope MD1900)\n");
			return 0;
		case 0x9020:
			printf("AmScope MD700E\n");
			return 0;
		/*
        New guy (rev 2 cameras):
        Bus 002 Device 007: ID 0547:6801 Anchor Chips, Inc. 
        */
		case 0x6801:
			printf("AmScope MU800\n");
			return 0;
        
		//NOT in stonedrv.sys or its .inf
		//Not sure if its related
		case 0x92A0:
			printf("Jeff's camera\n");
			return 0;
		default:
			printf("Unknown product id\n");
			return 1;
		}
	case 0x04B4:
		switch (product_id) {
		//NOT in stonedrv.sys, but in its .inf
		case 0xE035:
			printf("AmScope MD400E\n");
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

usb_dev_handle *locate_camera( void ) {
	unsigned char located = 0;
	struct usb_bus *bus = NULL;
	struct usb_device *dev = NULL;
	usb_dev_handle *device_handle = NULL;

	usb_find_busses();
	usb_find_devices();

 	for (bus = usb_busses; bus; bus = bus->next) {
		for (dev = bus->devices; dev; dev = dev->next) {
			printf("** usb device %s %s found (idVendor=0x%04X, idProduct=0x%04X) **\n",
					bus->dirname, dev->filename, dev->descriptor.idVendor, dev->descriptor.idProduct);
			if (validate_device(dev->descriptor.idVendor, dev->descriptor.idProduct)) {
				continue;
			}
			
			located++;
			device_handle = usb_open(dev);
			g_dev = dev;
			printf("Camera Device Found @ Address %s \n", dev->filename);
			printf("Camera Vendor ID 0x%04X\n", dev->descriptor.idVendor);
			printf("Camera Product ID 0x%04X\n", dev->descriptor.idProduct);
		}
	}

	return device_handle;
}

void print_device(const char *prefix, const struct usb_device *device) {
	printf("%snext: %u\n", prefix, (int)device->next);
	printf("%sprev: %u\n", prefix, (int)device->prev);
	printf("%sfilename: %s\n", prefix, device->filename);
	printf("%sbus: %u\n", prefix, (int)device->bus);
	printf("%sconfig: %u\n", prefix, (int)device->config);
	printf("%sdev: %u\n", prefix, (int)device->dev);
	printf("%sdevnum: %u\n", prefix, (int)device->devnum);
	printf("%snum_children: %u\n", prefix, (int)device->num_children);
	printf("%schildren: %u\n", prefix, (int)device->children);
}

void print_config(const char *prefix, const struct usb_config_descriptor *config) {
	printf("%sbLength: %u\n", prefix, config->bLength);
	printf("%sbDescriptorType: %u\n", prefix, config->bDescriptorType);
	printf("%swTotalLength: %u\n", prefix, config->wTotalLength);
	printf("%sbNumInterfaces: %u\n", prefix, config->bNumInterfaces);
	printf("%sbConfigurationValue: %u\n", prefix, config->bConfigurationValue);
	printf("%siConfiguration: %u\n", prefix, config->iConfiguration);
	printf("%sbmAttributes: %u\n", prefix, config->bmAttributes);
	printf("%sMaxPower: %u\n", prefix, config->MaxPower);
	printf("%sextra: %u\n", prefix, (int)config->extra);
	printf("%sextralen: %u\n", prefix, config->extralen);
}

void print_interface(const char *prefix, struct usb_interface *interface) {
	printf("%snum_altsetting: %u\n", prefix, interface->num_altsetting);
}

void print_endpoint_descriptor(const char *prefix, struct usb_endpoint_descriptor *in) {
	printf("%sbLength: %u\n", prefix, in->bLength);
	printf("%sbDescriptorType: %u\n", prefix, (int)in->bDescriptorType);
	printf("%sbEndpointAddress: 0x%02X\n", prefix, (int)in->bEndpointAddress);
	printf("%sbmAttributes: %u\n", prefix, (int)in->bmAttributes);
	printf("%swMaxPacketSize: %u\n", prefix, (int)in->wMaxPacketSize);
	printf("%sbInterval: %u\n", prefix, (int)in->bInterval);
	printf("%sbRefresh: %u\n", prefix, (int)in->bRefresh);
	printf("%sbSynchAddress: %u\n", prefix, (int)in->bSynchAddress);
	printf("%sextra: %u\n", prefix, (int)in->extra);
	printf("%sextralen: %u\n", prefix, (int)in->extralen);
}

void print_interface_descriptor(const char *prefix, struct usb_interface_descriptor *in) {
	printf("%sbLength: %u\n", prefix, (int)in->bLength);
	printf("%sbDescriptorType: %u\n", prefix, (int)in->bDescriptorType);
	printf("%sbInterfaceNumber: %u\n", prefix, (int)in->bInterfaceNumber);
	printf("%sbAlternateSetting: %u\n", prefix, (int)in->bAlternateSetting);
	printf("%sbNumEndpoints: %u\n", prefix, (int)in->bNumEndpoints);
	printf("%sbInterfaceClass: %u\n", prefix, (int)in->bInterfaceClass);
	printf("%sbInterfaceSubClass: %u\n", prefix, (int)in->bInterfaceSubClass);
	printf("%sbInterfaceProtocol: %u\n", prefix, (int)in->bInterfaceProtocol);
	printf("%siInterface: %u\n", prefix, (int)in->iInterface);
	printf("%sendpoint: 0x%08X\n", prefix, (int)in->endpoint);
	printf("%sextra: %u\n", prefix, (int)in->extra);
	printf("%sextralen: %u\n", prefix, (int)in->extralen);
}

void print_device_descriptor(const char *prefix, struct usb_device_descriptor *in) {	
	printf("%sbLength: %u\n", prefix, (int)in->bLength);
	printf("%sbDescriptorType: %u\n", prefix, (int)in->bDescriptorType);
	printf("%sbcdUSB: %u\n", prefix, (int)in->bcdUSB);
	printf("%sbDeviceClass: %u\n", prefix, (int)in->bDeviceClass);
	printf("%sbDeviceSubClass: %u\n", prefix, (int)in->bDeviceSubClass);
	printf("%sbDeviceProtocol: %u\n", prefix, (int)in->bDeviceProtocol);
	printf("%sbMaxPacketSize0: %u\n", prefix, (int)in->bMaxPacketSize0);
	printf("%sidVendor: 0x%04X\n", prefix, (int)in->idVendor);
	printf("%sidProduct: 0x%04X\n", prefix, (int)in->idProduct);
	printf("%sbcdDevice: %u\n", prefix, (int)in->bcdDevice);
	printf("%siManufacturer: %u\n", prefix, (int)in->iManufacturer);
	printf("%siProduct: %u\n", prefix, (int)in->iProduct);
	printf("%siSerialNumber: %u\n", prefix, (int)in->iSerialNumber);
	printf("%sbNumConfigurations: %u\n", prefix, (int)in->bNumConfigurations);
}

void print_all_device_information() {
	printf("\nDevice information\n");
	print_device("", g_dev);
	printf("Device descriptor:\n");
	print_device_descriptor("  ", &g_dev->descriptor);
	/* Loop through all of the configurations */
	for (int config_index = 0; config_index < g_dev->descriptor.bNumConfigurations; ++config_index) {
		struct usb_config_descriptor *config = &g_dev->config[config_index];

		printf("Config:\n");
		print_config("  ", config);
		
		/* Loop through all of the interfaces */
		for (int interface_index = 0; interface_index < config->bNumInterfaces; ++interface_index) {
			struct usb_interface *interface = &g_dev->config[config_index].interface[interface_index];
			
			printf("  Interface:\n");
			print_interface("    ", interface);
		
			/* Loop through all of the alternate settings */
			for (int alt_index = 0; alt_index < interface->num_altsetting; ++alt_index) {
				struct usb_interface_descriptor *interface_descriptor = &interface->altsetting[alt_index];
				
				printf("    Interface descriptor:\n");
				print_interface_descriptor("      ", interface_descriptor);
				
				for (int endpoint_index = 0; endpoint_index < interface_descriptor->bNumEndpoints; ++endpoint_index) {
					struct usb_endpoint_descriptor *endpoint_descriptor = &interface_descriptor->endpoint[endpoint_index];
				
					printf("      Endpoint descriptor:\n");
					print_endpoint_descriptor("        ", endpoint_descriptor);
				}
			}
		}
	}
	printf("\n");
	printf("\n");
}

void dump_strings() {
	//Think index 0 is special case to get language ID
	for (int i = 1; ; ++i) {
		char buff[0x100];
		int rc_tmp;
		
		rc_tmp = usb_get_string_simple(g_camera_handle, i, &buff[0], sizeof(buff));
		if (rc_tmp < 0) {
			printf("error @ %d\n", i);
			break;
		}
		//printf("%02X%02X%02X%02X\n", buff[0], buff[1], buff[2], buff[3]);
		buff[rc_tmp] = 0;
		printf("string[%d]: %s\n", i, &buff[0]); fflush(stdout);
	}
}

void relocate_camera() {
	if (g_camera_handle) {
		usb_close(g_camera_handle);
	}
	
	g_camera_handle = locate_camera();
	printf("Handle: 0x%08X\n", (int)g_camera_handle);
 	if (g_camera_handle == NULL) {
		printf("Could not open the camera device\n");
		exit(1);
	}
}

int main(int argc, char **argv) {
	int rc_tmp = 0;

	if (argc > 1) {
		g_image_file_out = argv[1];
	}

	usb_init();
	//Prints out *lots* of information on how it found it
	//usb_set_debug(2);
	relocate_camera();

	//print_all_device_information();
	//dump_strings();
	usb_set_debug(4);


		
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
	rc_tmp = usb_set_configuration(g_camera_handle, 1);
	printf("conf_stat=%d\n", rc_tmp);
	if (rc_tmp < 0) {
		perror("test");
		printf("Failed to configure\n");
		return 1;
	}
	
	//relocate_camera();
	//print_all_device_information();
	
	rc_tmp = usb_claim_interface(g_camera_handle, 0);
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
	rc_tmp = usb_set_altinterface(g_camera_handle, 0);
	printf("alt_stat=%d\n", rc_tmp);
	if (rc_tmp < 0) {
		perror("test");
		printf("Failed to set alt interface\n");
		return 1;
	}
	*/
	//sleep(5);
	
	//example_code();
	//download_ram();
	replay();
	
	usb_close(g_camera_handle);
	
	return 0;
}

