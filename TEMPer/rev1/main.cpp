#include "TEMPer.h"
#include <stdio.h>
#include <string>
#include <stdlib.h>

void help( void ) {
	printf("usage: TEMPer [args]\n");
	printf("--write-test\n" );
	printf("--scan\n" );
	printf("--dump\n" );
	printf("--name\n" );
	printf("--read-thermocouple\n" );
	printf("--read-internal\n" );
	printf("--read-all\n" );
}

int main(int argc, char **argv)
{	
	std::string arg;
	
	printf("main()\n");
	
	if( argc < 2 ) {
		help();
		exit(1);
	}
	
	printf("initializing port\n");
	init_port();
	
	arg = argv[1];
	if( arg == "--write-test" )
	{
		printf("writing to address 0\n");
		WriteEEPROM(0x0000, 0x3F);
		printf("Write done\n");
		printf("Read back: 0x%02X\n", ReadEEPROM(0x0000));
	}	
	else if( arg == "--scan" )
	{
		I2CScan();
	}
	else if( arg == "--dump" )
	{
		dumpEEPROM();
	}
	else if( arg == "--timing" )
	{
		tuneTiming();
	}
	else if( arg == "--name" )
	{
		printf("name: %s\n", TEMPerName());
	}
	else if( arg == "--read-thermocouple" )
	{
		sleep(3);
		for( ;; ) 
		{
			double thermocouple_temp = ReadThermocoupleTemp();
			
			printf("thermocouple: %lf\n", thermocouple_temp);			
			usleep(500000);
			debug_sleep(3);
		}
	}
	else if( arg == "--read-internal" )
	{
		printf("Initializing external\n");
		FM75Init();
		printf("Initialized\n");
		for( ;; ) 
		{
			double internal_temp;
			internal_temp = ReadInternalTemp();
			//internal_temp = ReadInternalTempMutated();
			
			printf("internal: %lf\n", internal_temp);			
			usleep(500000);
			debug_sleep(3);
		}
	}
	else if( arg == "--read-all" )
	{
		FM75Init();
		for( ;; ) 
		{
			double internal_temp;			
			double thermocouple_temp;
			
			printf("\n");			
			printf("Reading internal\n");
			fflush(stdout);
			internal_temp = ReadInternalTemp();
			printf("Reading thermocouple\n");
			fflush(stdout);
			thermocouple_temp = ReadThermocoupleTemp();
			printf("internal: %lf\n", internal_temp);			
			printf("thermocouple: %lf\n", thermocouple_temp);			
			usleep(500000);
			debug_sleep(3);
		}
	}
	else
	{
		help();
		exit(1);
	}
	
	return 0;
}

