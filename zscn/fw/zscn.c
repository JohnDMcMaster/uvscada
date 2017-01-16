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

#include "packet.c"

void gpio_init(void);

void packet_process(packet_t *packet) {
    (void)packet;
}

void gpio_init(void) {
	rcc_clock_setup_hse_3v3(&rcc_hse_8mhz_3v3[RCC_CLOCK_3V3_120MHZ]);

	rcc_periph_clock_enable(RCC_GPIOA);
	rcc_periph_clock_enable(RCC_OTGFS);

	gpio_mode_setup(GPIOA, GPIO_MODE_AF, GPIO_PUPD_NONE,
			GPIO9 | GPIO11 | GPIO12);
	gpio_set_af(GPIOA, GPIO_AF10, GPIO9 | GPIO11 | GPIO12);

	//rcc_periph_clock_enable(RCC_GPIOA);
	//rcc_periph_clock_enable(RCC_GPIOB);
	//rcc_periph_clock_enable(RCC_GPIOC);
	rcc_periph_clock_enable(RCC_GPIOD);

	gpio_mode_setup(GPIOD, GPIO_MODE_OUTPUT, GPIO_PUPD_NONE, GPIO12);
	gpio_mode_setup(GPIOD, GPIO_MODE_OUTPUT, GPIO_PUPD_NONE, GPIO13);
	gpio_mode_setup(GPIOD, GPIO_MODE_OUTPUT, GPIO_PUPD_NONE, GPIO14);
	gpio_mode_setup(GPIOD, GPIO_MODE_OUTPUT, GPIO_PUPD_NONE, GPIO15);
}

int main(void)
{
    usbd_device *usbd_dev;

    gpio_init();
    usbd_dev = usb_init();
    packet_init(usbd_dev);

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
	    //char buff[] = "Hello\r\n";
	    
		usbd_poll(usbd_dev);
		packet_service();
		//pkt_txbws("Hello\r\n");
		//usbd_ep_write_packet(usbd_dev, 0x82, "?", 1);
        //usbd_ep_write_packet(packet_usbd_dev, 0x82, buff, sizeof(buff));
        //debug_hex(buff, sizeof(buff));
    
        /*
        gpio_toggle(GPIOD, LED_G_PIN);
        gpio_toggle(GPIOD, LED_O_PIN);
        gpio_toggle(GPIOD, LED_R_PIN);
        gpio_toggle(GPIOD, LED_B_PIN);
        */

        /*
        while (1) {
            int32_t c = ring_read_ch(&rx_ring, NULL);
            char cc;
            if (c < 0) {
                break;
            }
            cc = c + 1;
            usbd_ep_write_packet(usbd_dev, 0x82, &cc, 1);
        }
        */
	}
}

