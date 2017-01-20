/*
zscn impedance scanner
lib

Based on file from libopencm3 project
See it for GPL stuff
*/

#include <stdlib.h>
#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>
#include <libopencm3/usb/usbd.h>
#include <libopencm3/usb/cdc.h>
#include <libopencm3/cm3/scb.h>

#include "ring.h"

#include "ring.c"

/*
green   PD12
orange  PD13
red     PD14
blue    PD15
*/

#define LED_G_PIN   GPIO12
#define LED_O_PIN   GPIO13
#define LED_R_PIN   GPIO14
#define LED_B_PIN   GPIO15

#define CHANS       64

#define CMD_0       0x00
#define CMD_1       0x80
#define CMD_LED_G   (0xFA & 0x7F)
#define CMD_LED_O   (0xFB & 0x7F)
#define CMD_LED_R   (0xFC & 0x7F)
#define CMD_LED_B   (0xFD & 0x7F)
#define CMD_RST     0xFE
#define CMD_NOP     0xFF

static void cdcacm_data_rx_cb(usbd_device *usbd_dev, uint8_t ep);

#include "usb.c"

char nib2hex(uint8_t n);
char nib2hex(uint8_t n) {
    if (n <= 9) {
        return '0' + n;
    } else {
        return 'A' + n - 10;
    }
}

//#include "packet.c"

void gpio_init(void);

typedef struct {
    int port;
    int pin;
} chan_t;

chan_t chans[] = {
    {GPIOA, GPIO1},
    {GPIOA, GPIO2},
    {GPIOA, GPIO3},
    {GPIOA, GPIO4},
    {GPIOA, GPIO5}, //C5
    {GPIOA, GPIO7},
    {GPIOA, GPIO8},
    {GPIOA, GPIO15},
    {GPIOB, GPIO0},
    {GPIOB, GPIO1}, //C10
    {GPIOB, GPIO2},
    {GPIOB, GPIO4},
    {GPIOB, GPIO5},
    {GPIOB, GPIO6},
    {GPIOB, GPIO7}, //C15
    {GPIOB, GPIO8},
    {GPIOB, GPIO10},
    {GPIOB, GPIO11},
    {GPIOB, GPIO12},
    {GPIOB, GPIO13},//C20
    {GPIOB, GPIO14},
    {GPIOB, GPIO15},
    {GPIOC, GPIO1},
    {GPIOC, GPIO2},
    {GPIOC, GPIO4}, //C25
    {GPIOC, GPIO5},
    {GPIOC, GPIO6},
    {GPIOC, GPIO7},
    {GPIOC, GPIO8},
    {GPIOC, GPIO9}, //C30
    {GPIOC, GPIO10},
    {GPIOC, GPIO11},
    {GPIOC, GPIO12},
    {GPIOC, GPIO13},
    {GPIOC, GPIO14},//C35
    {GPIOC, GPIO15},
    {GPIOD, GPIO0},
    {GPIOD, GPIO1},
    {GPIOD, GPIO2},
    {GPIOD, GPIO3}, //C40
    {GPIOD, GPIO4},
    {GPIOD, GPIO6},
    {GPIOD, GPIO7},
    {GPIOD, GPIO8},
    {GPIOD, GPIO9}, //C45
    {GPIOD, GPIO10},
    {GPIOD, GPIO11},
    {GPIOD, GPIO15},
    {GPIOE, GPIO0},
    {GPIOE, GPIO1},//C50
    {GPIOE, GPIO2},
    {GPIOE, GPIO3},
    {GPIOE, GPIO4},
    {GPIOE, GPIO5},
    {GPIOE, GPIO6}, //C55
    {GPIOE, GPIO7},
    {GPIOE, GPIO8},
    {GPIOE, GPIO9},
    {GPIOE, GPIO10},
    {GPIOE, GPIO11},//C60
    {GPIOE, GPIO12},
    {GPIOE, GPIO13},
    {GPIOE, GPIO14},
    {GPIOE, GPIO15},
};

void gpio_init(void) {
	rcc_clock_setup_hse_3v3(&rcc_hse_8mhz_3v3[RCC_CLOCK_3V3_120MHZ]);

	rcc_periph_clock_enable(RCC_GPIOA);
	rcc_periph_clock_enable(RCC_GPIOB);
	rcc_periph_clock_enable(RCC_GPIOC);
	rcc_periph_clock_enable(RCC_GPIOD);
	rcc_periph_clock_enable(RCC_GPIOE);
	rcc_periph_clock_enable(RCC_OTGFS);

	gpio_mode_setup(GPIOA, GPIO_MODE_AF, GPIO_PUPD_NONE,
			GPIO9 | GPIO11 | GPIO12);
	gpio_set_af(GPIOA, GPIO_AF10, GPIO9 | GPIO11 | GPIO12);

	gpio_mode_setup(GPIOD, GPIO_MODE_OUTPUT, GPIO_PUPD_NONE, LED_G_PIN);
	gpio_mode_setup(GPIOD, GPIO_MODE_OUTPUT, GPIO_PUPD_NONE, LED_O_PIN);
	gpio_mode_setup(GPIOD, GPIO_MODE_OUTPUT, GPIO_PUPD_NONE, LED_R_PIN);
	gpio_mode_setup(GPIOD, GPIO_MODE_OUTPUT, GPIO_PUPD_NONE, LED_B_PIN);

    for (int chani = 0; chani < CHANS; ++chani) {
        chan_t *chan = &chans[chani];
    	gpio_mode_setup(chan->port, GPIO_MODE_OUTPUT, GPIO_PUPD_NONE, chan->pin);
    }
}

void led_cmd(int pin, uint8_t cmd);
void led_cmd(int pin, uint8_t cmd) {
    if (cmd & CMD_1) {
        gpio_set(GPIOD, pin);
    } else {
        gpio_clear(GPIOD, pin);
    }
}

void rst(void);
void rst (void) {
    for (int chani = 0; chani < CHANS; ++chani) {
        chan_t *chan = &chans[chani];
        gpio_clear(chan->port, chan->pin);
    }
    gpio_clear(GPIOD, LED_G_PIN);
    gpio_clear(GPIOD, LED_O_PIN);
    gpio_clear(GPIOD, LED_R_PIN);
    gpio_clear(GPIOD, LED_B_PIN);
}

void cdcacm_data_rx_cb(usbd_device *usbd_dev, uint8_t ep)
{
	char buff[64];
	int len;
	
	(void)ep;

	len = usbd_ep_read_packet(usbd_dev, 0x01, buff, 64);
	if (len > 0) {
	    for (int i = 0; i < len; ++i) {
	        uint8_t cmd = buff[i];
	        uint8_t cmdm = cmd & 0x7F;
	        
	        if (cmd == CMD_NOP) {
	            //Skip
	        } else if (cmd == 'a') {
	            usbd_ep_write_packet(usbd_dev, 0x82, "!", 1);
	        //} else if (true) {
	            //skip
	        } else if (cmd == CMD_RST) {
	            rst();
	        } else if (cmdm == CMD_LED_G) {
	            led_cmd(LED_G_PIN, cmd);
	        } else if (cmdm == CMD_LED_O) {
	            led_cmd(LED_O_PIN, cmd);
	        } else if (cmdm == CMD_LED_R) {
	            led_cmd(LED_R_PIN, cmd);
	        } else if (cmdm == CMD_LED_B) {
	            led_cmd(LED_B_PIN, cmd);
	        } else {
	            int chani = cmd & 0x7F;
                chan_t *chan;
                
                if (chani < 64) {
                    chan = &chans[chani];
                    if (cmd & CMD_1) {
                        gpio_set(chan->port, chan->pin);
                    } else {
                        gpio_clear(chan->port, chan->pin);
                    }
                }
            }
	    }
	
        usbd_ep_write_packet(usbd_dev, 0x82, buff, len);
	}
}

int main(void)
{
    usbd_device *usbd_dev;

    gpio_init();
    usbd_dev = usb_init();
    //packet_init(usbd_dev);

    /*
    gpio_set(GPIOD, LED_G_PIN);
    gpio_clear(GPIOD, LED_G_PIN);
    gpio_toggle(GPIOD, LED_G_PIN);
    */

    /*
    gpio_set(GPIOD, LED_G_PIN);
    gpio_set(GPIOD, LED_O_PIN);
    gpio_set(GPIOD, LED_R_PIN);
    gpio_set(GPIOD, LED_B_PIN);
    */
    /*
    gpio_set(GPIOD, LED_R_PIN);
    gpio_set(GPIOD, LED_B_PIN);
    */
    /*
	while (1) {
	}
	*/

	while (1) {
	    //int rc;
	    
		usbd_poll(usbd_dev);
        //rc = usbd_ep_write_packet(packet_usbd_dev, 0x82, packet_tx_buff, tx_buff_n);
	}
}

