#include <stdio.h>
#include <stdint.h>
#include <string>
#include <stdlib.h>
#include "TEMPer.h"

//24LC02
//Address is correct..freezers otherwise
//But just no data
#define EPROM_I2C_ADDR		0xA0
//2 Kib
#define EPROM_SIZE			256

uint32_t g_bytesPerRow = 16;
uint32_t g_bytesPerHalfRow = 8;

static unsigned int hexdumpHalfRow(const uint8_t *data, size_t size, uint32_t start)
{
	uint32_t col = 0;

	for( ; col < g_bytesPerHalfRow && start + col < size; ++col )
	{
		uint32_t index = start + col;
		uint8_t c = data[index];
		
		printf("%.2X ", (unsigned int)c);
		fflush(stdout);
	}

	//pad remaining
	while( col < g_bytesPerHalfRow )
	{
		printf("   ");
		fflush(stdout);
		++col;
	}

	//End pad
	printf(" ");
	fflush(stdout);

	return start + g_bytesPerHalfRow;
}

void UVDHexdumpCore(const uint8_t *data, size_t size, const std::string &prefix)
{
	/*
	[mcmaster@gespenst icd2prog-0.3.0]$ hexdump -C /bin/ls |head
	00000000  7f 45 4c 46 01 01 01 00  00 00 00 00 00 00 00 00  |.ELF............|
	00000010  02 00 03 00 01 00 00 00  f0 99 04 08 34 00 00 00  |............4...|
	00017380  00 00 00 00 01 00 00 00  00 00 00 00              |............|
	*/

	size_t pos = 0;
	while( pos < size )
	{
		uint32_t row_start = pos;
		uint32_t i = 0;

		printf("%s", prefix.c_str());
		fflush(stdout);

		pos = hexdumpHalfRow(data, size, pos);
		pos = hexdumpHalfRow(data, size, pos);

		printf("|");
		fflush(stdout);

		//Char view
		for( i = row_start; i < row_start + g_bytesPerRow && i < size; ++i )
		{
			char c = data[i];
			if( isprint(c) )
			{
				printf("%c", c);
				fflush(stdout);
			}
			else
			{
				printf("%c", '.');
				fflush(stdout);
			}

		} 
		for( ; i < row_start + g_bytesPerRow; ++i )
		{
			printf(" ");
			fflush(stdout);
		}

		printf("|\n");
		fflush(stdout);
	}
	fflush(stdout);
}

void UVDHexdump(const uint8_t *data, size_t size)
{
	UVDHexdumpCore(data, size, "");
}

uint8_t ReadEEPROM(uint8_t address) {
	uint8_t byte;
	
	I2CStart();
	//Dummy write
	//160
	//I2CWriteByte(0xA0);
	//Ends on low clock
	I2CWriteByte(I2C_ADDRESS(EPROM_I2C_ADDR, I2C_WRITE));
	//Delay(10);
	I2CDelay();
	//Ends on low clock
	if( ReadACKMine() != 0 ) 
	{
		printf("bad device ack\n");
		return 0;
	}
	I2CWriteByte(address);
	//Delay(10);
	I2CDelay();
	//But no data
	if( ReadACKMine() != 0 ) 
	{
		printf("bad address ack\n");
		return 0;
	}
	//XXX: datasheet doesn't have this, other stuff does...needed?
	//is this a repeated start?
	I2CStop();
	
	//Now do the actual read
	I2CStart();
	I2CWriteByte(I2C_ADDRESS(EPROM_I2C_ADDR, I2C_READ));
	//Delay(10);
	I2CDelay();
	if( ReadACKMine() != 0 ) 
	{
		printf("bad device ack 2\n");
		return 0;
	}
	byte = I2CReadByte();
	//No ACK
	I2CStop();
	
	return byte;
}

void WriteEEPROM(uint8_t address, uint8_t data) {	
	I2CStart();
	//Dummy write
	//160
	//I2CWriteByte(0xA0);
	I2CWriteByte(I2C_ADDRESS(EPROM_I2C_ADDR, I2C_WRITE));
	//Delay(100);
	I2CDelay();
	if( ReadACKMine() != 0 ) 
	{
		printf("bad device ack\n");
		return;
	}
	I2CWriteByte(address);
	//Delay(100);
	I2CDelay();
	if( ReadACKMine() != 0 ) 
	{
		printf("bad address ack\n");
		return;
	}
	I2CWriteByte(data);
	//Delay(100);
	I2CDelay();
	if( ReadACKMine() != 0 ) 
	{
		printf("bad data ack\n");
		return;
	}
	I2CStop();
}

void dumpEEPROM() 
{
	/*
	My EEPROM seems to be blank
	*/
	uint8_t *buff = (uint8_t *)malloc(EPROM_SIZE);
	
	for( unsigned int i = 0; i < EPROM_SIZE; ++i ) 
	{
		uint8_t read = ReadEEPROM(i);
		buff[i] = read;
		if( false ) {
			printf("0x%04X: 0x%02X\n", i, read);
		}
		printf(".");
		fflush(stdout);
	}
	printf("\n");
	
	if (true) {
		UVDHexdump(buff, EPROM_SIZE);
	}
	if (false) {
		FILE *file_p = fopen("eeprom.bin", "w");
		fwrite( buff, 1, EPROM_SIZE, file_p );
		fclose(file_p);
	}
}


