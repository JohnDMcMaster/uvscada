	char buff[0x100];
	int n_rw = 0;
	int rc_tmp = 0;
	
	(void)rc_tmp;
	
	if (!dev) {
		printk(KERN_ALERT "replay: dev null\n");
		return 1;
	}

	//printk(KERN_ALERT "trying test packet\n\n");
	//What is relationship between rcvctrlpipe and HOST_TO_DEVICE?
	/*
	 This is the first real packet
	 Its generated after hitting the capture button and is part of the configuration
	 Packets before this are just OS device name types
	 
	 Sources
	 	All 640X480
	 	VMWare (Linux)
		 	amscope/rgb_capture/2/vmware-usb-capture-USBIO.log
				Aug 20 09:43:09.293: vmx| USBIO: Down dev=1 endpt=0 datalen=0 numPackets=1 status=979578671 73753032
				Aug 20 09:43:09.293: vmx| USBIO:  000: 40 01 01 00 0f 00 00 00                         @.......        		  
		UsbSnoop (Windows kernel) on WinXP VM, normal capture not the TWAIN test
			[6574 ms]  >>>  URB 5 going down  >>> 
			-- URB_FUNCTION_VENDOR_DEVICE:
			  TransferFlags          = 00000002 (USBD_TRANSFER_DIRECTION_OUT, USBD_SHORT_TRANSFER_OK)
			  TransferBufferLength = 00000000
			  TransferBuffer       = 00000000
			  TransferBufferMDL    = 00000000

				no data supplied
			  UrbLink                 = 00000000
			  RequestTypeReservedBits = 00000000
			  Request                 = 00000001
			  Value                   = 00000001
			  Index                   = 0000000f
		Wireshark
			Summary
				No		Time		Source	Dest	Protocol	Info
				124		65.230054	host	57.0	USB			URB_CONTROL
			URB setup
				bmRequestType: 0x40
					0... .... = Direction: Host-to-device
					.10. .... = Type: Vendor (0x02)
					...0 0000 = Recipient: Device (0x00)
				Application Data: 0101000F00000000000000000000000000000000000000	
			Raw
				0000  40 01 01 00 0f 00 00 00  00 00 00 00 00 00 00 00   @....... ........
				0010  00 00 00 00 00 00 00 00                            ........    			
				
				It did a poor job breaking it out
					0x40: requesttype, translated as below
					0x01: request, translated as below
					0x00 0x01: value
					0x00 0x0F: index
					0x00 0x00: wLength
	*/
#if 0
	rc_tmp = usb_control_msg(
		//struct usb_device *dev, 
		dev->udev, 
		//unsigned int pipe,
		usb_sndctrlpipe(dev->udev, 0),
		/*
		Request type captured as 0x40 => HOST_TO_DEVICE | USB_TYPE_VENDOR | USB_RECIP_DEVICE
		*/
		//__u8 request,
		0x01,
 		//__u8 requesttype,
		USB_DIR_OUT | USB_TYPE_VENDOR | USB_RECIP_DEVICE,
		//__u16 value,
		0x0001,
		//__u16 index,
		0x000F,
		//void *data,
		NULL,
		//__u16 size,
		0,
		//int timeout
		500);
	if (rc_tmp < 0) {
		printk(KERN_ALERT "failed test control: %d\n", rc_tmp);
		printk("\n");
		return rc_tmp;
	} else {
		printk(KERN_ALERT "didn't fail...\n");
	}
	printk(KERN_ALERT "\n");
#endif

	/*
	I think I originally generated these from a Wireshark capture as it looks like they were generated from C arrays as produced by Wireshark
	*/
	CAMERA_CONTROL_MESSAGE(USB_DIR_OUT | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x01, 0x0001, 0x000F, NULL, 0);
	printk(KERN_ALERT "trying packet 7\n");
	printk(KERN_ALERT "Generated from packet 7\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_OUT | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x01, 0x0000, 0x000F, NULL, 0);
	printk(KERN_ALERT "Generated from packet 9\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_OUT | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x01, 0x0001, 0x000F, NULL, 0);
	
	printk(KERN_ALERT "Generated from packet 11\n");	
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0100, 0x0103, buff, 1);
	
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 12");
	printk(KERN_ALERT "Generated from packet 13\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0100, 0x0104, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 14");
	printk(KERN_ALERT "Generated from packet 15\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0A, 0x0000, 0x3000, buff, 3);
	if (validate_read((char[]){0x2B, 0x00, 0x08}, 3, &buff, n_rw, "packet 16"))
		return 1;
	printk(KERN_ALERT "Generated from packet 17\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0100, 0x0104, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 18");
	printk(KERN_ALERT "Generated from packet 19\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0020, 0x0344, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 20");
	printk(KERN_ALERT "Generated from packet 21\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0CA1, 0x0348, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 22");
	printk(KERN_ALERT "Generated from packet 23\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0020, 0x0346, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 24");
	printk(KERN_ALERT "Generated from packet 25\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0981, 0x034A, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 26");
	printk(KERN_ALERT "Generated from packet 27\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x02FC, 0x3040, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 28");
	printk(KERN_ALERT "Generated from packet 29\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0002, 0x0400, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 30");
	printk(KERN_ALERT "Generated from packet 31\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0014, 0x0404, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 32");
	printk(KERN_ALERT "Generated from packet 33\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0280, 0x034C, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 34");
	printk(KERN_ALERT "Generated from packet 35\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x01E0, 0x034E, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 36");
	printk(KERN_ALERT "Generated from packet 37\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x02C0, 0x300A, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 38");
	printk(KERN_ALERT "Generated from packet 39\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0E00, 0x300C, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 40");
	printk(KERN_ALERT "Generated from packet 41\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0000, 0x0104, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 42");
	printk(KERN_ALERT "Generated from packet 43\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0000, 0x0100, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 44");
	printk(KERN_ALERT "Generated from packet 45\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0100, 0x0104, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 46");
	printk(KERN_ALERT "Generated from packet 47\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0004, 0x0300, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 48");
	printk(KERN_ALERT "Generated from packet 49\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0001, 0x0302, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 50");
	printk(KERN_ALERT "Generated from packet 51\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0008, 0x0308, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 52");
	printk(KERN_ALERT "Generated from packet 53\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0001, 0x030A, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 54");
	printk(KERN_ALERT "Generated from packet 55\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0004, 0x0304, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 56");
	printk(KERN_ALERT "Generated from packet 57\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0020, 0x0306, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 58");
	printk(KERN_ALERT "Generated from packet 59\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x90D8, 0x301A, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 60");
	printk(KERN_ALERT "Generated from packet 61\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0000, 0x0104, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 62");
	printk(KERN_ALERT "Generated from packet 63\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0100, 0x0100, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 64");
	printk(KERN_ALERT "Generated from packet 65\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0A, 0x0000, 0x300C, buff, 3);
	if (validate_read((char[]){0x0E, 0x00, 0x08}, 3, &buff, n_rw, "packet 66"))
		return 1;
	printk(KERN_ALERT "Generated from packet 67\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x90D8, 0x301A, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 68");
	printk(KERN_ALERT "Generated from packet 69\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0805, 0x3064, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 70");
	printk(KERN_ALERT "Generated from packet 71\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0000, 0x0104, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 72");
	printk(KERN_ALERT "Generated from packet 73\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0100, 0x0100, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 74");
	printk(KERN_ALERT "Generated from packet 75\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0001, 0x0402, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 76");
	printk(KERN_ALERT "Generated from packet 77\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0001, 0x0104, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 78");
	printk(KERN_ALERT "Generated from packet 79\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x0000, 0x0104, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 80");
	printk(KERN_ALERT "Generated from packet 81\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x01F4, 0x3012, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 82");
	printk(KERN_ALERT "Generated from packet 83\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x0B, 0x023E, 0x305E, buff, 1);
	VALIDATE_READ((char[]){0x08}, 1, &buff, n_rw, "packet 84");
	printk(KERN_ALERT "Generated from packet 85\n");
	CAMERA_CONTROL_MESSAGE(USB_DIR_OUT | USB_TYPE_VENDOR | USB_RECIP_DEVICE, 0x01, 0x0003, 0x000F, NULL, 0);

