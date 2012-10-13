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

