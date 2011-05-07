#include <stdlib.h>
#include <unistd.h>
#include "TEMPer.h"

unsigned int SPIIn()
{
	return DSR() == 0;
}

double decode_temperature(unsigned int raw) {
	double ret = 0;
	
	if( raw > 0xFFFF ) {
		printf("invalid raw value\n");
		exit(1);
	}
	
	//3 LSBs are other stuff (thermocouple input, device ID, state)
	//sign bit should be forced to 0?
	bool thermocouple_open = raw & 0x04;
	if( thermocouple_open ) {
		printf("invalid: thermocouple open\n");
		ret = -1;
	} else if( raw & 0x8000 ) {
		printf("corrupted value: sign bit set\n");
		ret = -1;
	} else {
		
		raw >>= 3;
		ret = 0.25 * raw;
		printf_debug("0x%04X (%d) => %lf\n", raw, raw, ret);
		if( raw == 0xFFFF )
		{
		}
	}
	return ret;
}

double ReadThermocoupleTemp()
{
	/*
	The answer to the customer's question is that once /CS is brought high again, 
	the next conversion result should be ready no later than 0.22 seconds.   
	The customer should wait the maximum time for a conversion after /CS goes high 
	to guarantee the worst case timing of the A/D converter.
	*/
	/*
	Serial data is valid while SCK is high
	SCK should start low
	CS# should start high
	Start by getting CS# low to select chip
	Wait a bit...
	D15 = 0
	D1 = 0
	D0 = undefined?
	*/
	unsigned int mask = (1 << 15);
	unsigned int raw_high = 0;

	printf_debug("reading temp\n");
	
	//make sure we aren't bringing CS low
	//hmm doesn't have any effect
	//eh CS is SDA, we set it as needed
	//SDout(0);
	
	//printf("Clock low\n");
	Sclk(0);
	usleep(1000);
	debug_sleep(1);
	
	//printf("CS high\n");
	CS(1);
	usleep(1000);
	debug_sleep(1);

	//printf("Setting CS low\n");
	//Wake up you lazy bastard
	CS(0);
	usleep(1000);
	debug_sleep(1);
	
	for( ;; )
	{
		unsigned int read_high;
	
		//printf("Clock high\n");
		Sclk(1);
		usleep(1000);
		debug_sleep(1);
		read_high = SPIIn();
		
		/*
		"Read the 16 output bits on the falling edge of the clock"
		USB capture has only about 4 ms in between
		*/
		
		//printf("Clock low\n");
		Sclk(0);
		usleep(1000);
		//printf("read1: %d\n", read);
		usleep(3000);
		debug_sleep(1);
		
		if( read_high )
		{
			raw_high += mask;
		}
		
		if( mask == 1 )
		{
			break;
		}
		mask = mask >> 1;
	}
	//Back to idle
	CS(1);
	
	double to_ret = decode_temperature(raw_high);
	return to_ret;
}

