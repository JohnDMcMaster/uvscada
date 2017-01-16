//#include <libopencm3/usb/usb_fx07_common.h>
//#include <libopencm3/lm4f/usb.h>

void packet_init(usbd_device *usbd_dev);
void packet_service(void);

//not really a register
#define REG_NONE            0x00
#define REG_ACK             0x01
#define REG_NOP             0x02

typedef struct {
    /*
    inverted modular sum checksum
    maybe consider CRC later
    */
    uint8_t checksum;
    /*
    Monotonically increasing sequence number
    */
    uint8_t seq;
    /*
    High bit indicates write
    */
    uint8_t reg;
    /*
    Value specific to reg
    Should be set to 0 if unused
    */
    uint32_t value;
} __attribute__((packed)) packet_t;

struct ring packet_rx_ring;
uint8_t packet_rx_ring_buff[128];
uint8_t packet_rx_buff[sizeof(packet_t)];

/*
Only can have one pending packet at a time (64 bytes max)
But want to be able to handle buffering a lot more data potentially
*/
struct ring packet_tx_ring;
uint8_t packet_tx_ring_buff[256];
//Supposed to be 64 but having issues
uint8_t packet_tx_buff[4];
unsigned int tx_buff_n;

#define SLIP_END        192
#define SLIP_ESC        219

//large value indicates no packet is in progress
unsigned int g_rx_n;
//Last received sequence number of 0x100 if never
unsigned int g_seq_n;

//switched to just zero
//#define PACKET_INVALID      0xFF

//#define SEQ_NEVER           0x100
unsigned int g_seq_num_rx = 0;
uint8_t g_checksum_rx;
unsigned int g_seq = 0;
bool g_escape;

static char packet_buff_c[sizeof(packet_t)];
static packet_t *packet_buff = (packet_t *)&packet_buff_c;

void packet_process(packet_t *packet);
void packet_process_raw(packet_t *packet);

int32_t pkt_txbwc(char c);
int32_t pkt_txbw(const char *buff, unsigned int n);
int32_t pkt_txbws(const char *buff);

usbd_device *packet_usbd_dev;
void packet_init(usbd_device *usbd_dev) {
    packet_usbd_dev = usbd_dev;

    ring_init(&packet_rx_ring, packet_rx_ring_buff, sizeof(packet_rx_ring_buff));
    ring_init(&packet_tx_ring, packet_tx_ring_buff, sizeof(packet_tx_ring_buff));
    tx_buff_n = 0;

    //no packet yet
    g_rx_n = 0;
    g_escape = false;
    //g_seq_n = SEQ_NEVER;
    g_seq_n = 0;
}

static uint8_t checksum(const uint8_t *data, size_t data_size) {
    uint8_t ret = 0;
    for (unsigned int i = 0; i < data_size; ++i) {
        ret += data[i];
    }
    return ~ret;
}

void debug_hex(char *buff, int len);
void debug_hex(char *buff, int len) {
    pkt_txbws("Debug\r\n");
    for (int i = 0; i < len; ++i) {
        char c = buff[i];
        char ctmp;

        //char cbuff[3];
        //sprintf(cbuff, "%02X", buff[i]);
        //usbd_ep_write_packet(packet_usbd_dev, 0x82, cbuff, sizeof(cbuff));
        ctmp = nib2hex((c >> 4) & 0xF);
        //usbd_ep_write_packet(packet_usbd_dev, 0x82, &ctmp, 1);
        pkt_txbwc(ctmp);
        ctmp = nib2hex((c >> 0) & 0xF);
        //usbd_ep_write_packet(packet_usbd_dev, 0x82, &ctmp, 1);
        pkt_txbwc(ctmp);
    }
    pkt_txbws("\r\n");
}


/*
static inline void packet_write_ch(char c) {
    usbd_ep_write_packet(packet_usbd_dev, 0x82, &c, 1);    
}
*/

void packet_write(uint8_t reg, uint32_t value);
void packet_write(uint8_t reg, uint32_t value) {
    packet_t packet;
    uint8_t *packetb = (uint8_t *)&packet;

    packet.seq = g_seq++;
    packet.reg = reg;
    packet.value = value;
    packet.checksum = checksum(packetb + 1, sizeof(packet) - 1);

    pkt_txbwc(SLIP_END);
    for (unsigned int i = 0; i < sizeof(packet); ++i) {
        uint8_t b = packetb[i];

        if (b == SLIP_END) {
            //If a data byte is the same code as END character, a two byte sequence of
            //ESC and octal 334 (decimal 220) is sent instead.  
            pkt_txbwc(SLIP_ESC);
            pkt_txbwc(220);
        } else if (b == SLIP_ESC) {
            //If it the same as an ESC character, an two byte sequence of ESC and octal 335 (decimal
            //221) is sent instead
            pkt_txbwc(SLIP_ESC);
            pkt_txbwc(221);
        } else {
            pkt_txbwc(b);
        }
    }
    //When the last byte in the packet has been
    //sent, an END character is then transmitted
    pkt_txbwc(SLIP_END);
}

//void packet_rx_buff(const char *buff, size_t len);
void packet_rx_c(uint8_t c);
/*
void packet_rx_buff(const char *buff, size_t len) {
    for (size_t i = 0; i < len; ++i) {
        packet_rx_c(buff[i]);
    }
}
*/

void packet_rx_c(uint8_t c) {
    //gpio_toggle(GPIOD, LED_G_PIN);

    //dbg("RX char 0x%02X, cur size: %d", c, g_rx_n);
    //usart_send_blocking(USART1, c);
    //printf("Force RX: 0x%04X\n", c);
    if (g_escape) {
        //enough room?
        if (g_rx_n >= sizeof(packet_rx_buff)) {
            //dbg("overflow");
            g_rx_n = 0;
        } else {
            //If a data byte is the same code as END character, a two byte sequence of
            //ESC and octal 334 (decimal 220) is sent instead.  
            if (c == 220) {
                packet_rx_buff[g_rx_n++] = SLIP_END;
            //If it the same as an ESC character, an two byte sequence of ESC and octal 335 (decimal
            //221) is sent instead
            } else if (c == 221) {
                packet_rx_buff[g_rx_n++] = SLIP_ESC;
            } else {
                g_rx_n = 0;
            }
        }
        g_escape = false;
    } else if (c == SLIP_END) {
        //dbg("end RX");
        
        //Not the right size? drop it
        if (g_rx_n != sizeof(packet_t)) {
            //dbg("Drop packet: got %d / %d packet bytes", g_rx_n, sizeof(packet_rx_buff));
        } else {
            packet_process_raw(packet_buff);
        }
        g_rx_n = 0;
        g_escape = false;
    } else if (c == SLIP_ESC) {
        //dbg("escape RX");
        g_escape = true;
    //Ordinary character
    } else {
        //enough room?
        if (g_rx_n >= sizeof(packet_rx_buff)) {
            g_rx_n = 0;
        } else {
            packet_rx_buff[g_rx_n++] = c;
        }
    }
}

void packet_process_raw(packet_t *packet) {
    uint8_t computed_checksum;

    gpio_toggle(GPIOD, LED_B_PIN);
    //usbd_ep_write_packet(packet_usbd_dev, 0x82, "Test1\r\n", sizeof("Test1\r\n"));
    
    //debug_hex("Dump\r\n", sizeof("Dump\r\n"));
    //debug_hex((char *)packet, sizeof(packet_t));
    
    //Verify checksum
    //Skip checksum
    computed_checksum = checksum(packet_rx_buff + 1, sizeof(packet_rx_buff) - 1);
    if (packet->checksum != computed_checksum) {
        gpio_toggle(GPIOD, LED_R_PIN);
        //nope!
        //dbg("Drop packet: checksum mismatch, got: 0x%02X, compute: 0x%02X", packet->checksum, computed_checksum);
        return;
    }
    
    /*
    //Retransmit?
    if (packet->seq == g_seq_num_rx) {
        if (packet->checksum != g_checksum_rx) {
            //TODO: add flags in upper value bits
            packet_write(REG_ACK, g_seq_num_rx);
        } else {
            //Don't actually execute the command, just retransmit ack
            //TODO: add flags in upper value bits
            packet_write(REG_ACK, g_seq_num_rx);
        return;
    }
    */
    g_seq_num_rx = packet->seq;
    g_checksum_rx = packet->checksum;
    //TODO: add flags in upper value bits
    packet_write(REG_ACK, g_seq_num_rx);
    
    gpio_toggle(GPIOD, LED_O_PIN);
    packet_process(packet);
}

void cdcacm_data_rx_cb(usbd_device *usbd_dev, uint8_t ep)
{
	char buf[64];
	int len;
	
	(void)ep;

	len = usbd_ep_read_packet(usbd_dev, 0x01, buf, 64);

	if (len) {
        ring_writec(&packet_rx_ring, buf, len);
	}
}

int32_t pkt_txbwc(char c) {
    return ring_write(&packet_tx_ring, (uint8_t *)&c, sizeof(c));
}

int32_t pkt_txbw(const char *buff, unsigned int n) {
    return ring_write(&packet_tx_ring, (uint8_t *)buff, n);
}

unsigned int my_strlen(const char *s);
unsigned int my_strlen(const char *s) {
    int i = 0;
    while (*s) {
        ++i;
        ++s;
    }
    return i;
}

int32_t pkt_txbws(const char *buff) {
    return ring_write(&packet_tx_ring, (uint8_t *)buff, my_strlen(buff));
}

#if 0
not compatible with this MCU?
unclear which core is being used
static uint16_t ep_busy(void)
{
	const uint8_t addr = 0x82;
	const uint8_t ep = addr & 0xf;
	uint16_t i;

	/* Don't touch the FIFO if there is still a packet being transmitted */
	if (ep == 0 && (USB_CSRL0 & USB_CSRL0_TXRDY)) {
		return 1;
	} else if (USB_TXCSRL(ep) & USB_TXCSRL_TXRDY) {
		return 1;
	}
	return 0;
}
#endif

void packet_service(void) {
    /*
    if (!ep_busy()) {
        int32_t tx_buff_n;
        
        //Suck as much data as we can from the tx buffer and queue packet
        tx_buff_n = ring_read(&packet_tx_ring, &packet_tx_buff, sizeof(packet_tx_buff));
        if (tx_buff_n) {
            usbd_ep_write_packet(packet_usbd_dev, 0x82, packet_tx_buff, tx_buff_n);
        }
    }
    */
    /*
	if (REBASE(OTG_DIEPTSIZ(addr)) & OTG_DIEPSIZ0_PKTCNT) {
		return 0;
	}
	*/
	//Not ideal but probably good enough
    //If packet isn't in progress, fetch more data
    if (!tx_buff_n) {
        //gpio_toggle(GPIOD, LED_G_PIN);
        //Suck as much data as we can from the tx buffer and queue packet
        tx_buff_n = ring_readu(&packet_tx_ring, (uint8_t *)&packet_tx_buff, sizeof(packet_tx_buff));
    }
    //If have data, push to packet
    //If packet is in progress, request will be denied (ret 0)
    if (tx_buff_n) {
        int rc;
        
        //gpio_toggle(GPIOD, LED_B_PIN);
        rc = usbd_ep_write_packet(packet_usbd_dev, 0x82, packet_tx_buff, tx_buff_n);
        //rc = usbd_ep_write_packet(packet_usbd_dev, 0x82, packet_tx_buff, 4);
        //rc = usbd_ep_write_packet(packet_usbd_dev, 0x82, "!", 1);
        //rc = usbd_ep_write_packet(packet_usbd_dev, 0x82, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", tx_buff_n);
        //Freeze
        //rc = usbd_ep_write_packet(packet_usbd_dev, 0x82, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", 64);
        //rc = usbd_ep_write_packet(packet_usbd_dev, 0x82, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", 8);
        if (rc) {
            //gpio_toggle(GPIOD, LED_R_PIN);
            tx_buff_n = 0;
        }
    } else {
        //pkt_txbws("Hello this is a test\r\n");
    }

    while (1) {
        int32_t c = ring_read_ch(&packet_rx_ring, NULL);
        if (c < 0) {
            break;
        }
        packet_rx_c(c);
        gpio_toggle(GPIOD, LED_O_PIN);
    }
}

