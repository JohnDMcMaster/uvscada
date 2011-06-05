/* Function to read and write the XSV300 board USB port */

#include <stdio.h>
#include <stdint.h>
#include <usb.h>

//Bus 002 Device 006: ID 0547:4d88 Anchor Chips, Inc. 
#define CAMERA_VENDOR_ID		0x0547
#define CAMERA_PRODUCT_ID		0x4D88

//Best guesses
//Barely any observed traffic
//Have yet to show that images actually get send across
#define IMAGE_ENDPOINT 			0
//Heavy traffic during startup
#define CONFIG_ENDPOINT 		1
//Observed from capture
#define	VIDEO_ENDPOINT 			2

struct usb_dev_handle *g_camera_handle = NULL;


usb_dev_handle *locate_camera( void );

unsigned int camera_bulk_read(int ep, void *bytes, int size) {
	int rc_tmp = usb_bulk_read(g_camera_handle, ep, (char *)bytes, size, 500);
	
	if (rc_tmp < 0) {
		perror("ERROR");
		printf("failed read: %d\n", rc_tmp);
		exit(1);
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

void replay() {
	replay_EP1_0();
}

int validate_device( int vendor_id, int product_id ) {
	switch (vendor_id) {
	case 0x0547:
		switch (product_id) {
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
			printf("AmScope MD1800\n");
			return 0;
		case 0x4D90:
			printf("AmScope MD1900\n");
			return 0;
		case 0x9020:
			printf("AmScope MD700E\n");
			return 0;
		default:
			printf("Unknown product id\n");
			return 1;
		}
	case 0x04B4:
		switch (product_id) {
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
			//printf("** usb device %s found **\n", dev->filename);
			if (validate_device(dev->descriptor.idVendor, dev->descriptor.idProduct)) {
				continue;
			}
			
			located++;
			device_handle = usb_open(dev);
			printf("Camera Device Found @ Address %s \n", dev->filename);
			printf("Camera Vendor ID 0x%04X\n", dev->descriptor.idVendor);
			printf("Camera Product ID 0x%04X\n", dev->descriptor.idProduct);
		}
	}

	if (device_handle == 0) {
		return (0);
	} else {
		return (device_handle);
	}
}

int main(int argc, char **argv)
{
	int rc_tmp = 0;

	usb_init();
	//Prints out *lots* of information on how it found it
	//usb_set_debug(2);
	g_camera_handle = locate_camera();
 	if (g_camera_handle == NULL) {
		printf("Could not open the camera device\n");
		return 1;
	}
	
	//Config = 0 results in fail to claim
	//invalid arg if 2
	/*
	rc_tmp = usb_set_configuration(g_camera_handle, 1);
	printf("conf_stat=%d\n", rc_tmp);
	if (rc_tmp < 0) {
		perror("test");
		printf("Failed to configure\n");
		return 1;
	}
	*/
	
	rc_tmp = usb_claim_interface(g_camera_handle, 0);
	printf("claim_stat=%d\n", rc_tmp);
	if (rc_tmp < 0) {
		perror("test");
		printf("Failed to claim\n");
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
	
	//example_code();
	replay();
	
	usb_close(g_camera_handle);
	
	return 0;
}

