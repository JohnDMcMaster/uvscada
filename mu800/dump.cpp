
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

