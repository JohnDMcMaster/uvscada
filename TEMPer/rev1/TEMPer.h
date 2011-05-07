#ifndef UVTEMPER_REV1_H
#define UVTEMPER_REV1_H

#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>

#define debug_sleep(x)
//#define debug_sleep sleep

//#define printf_debug printf
#ifndef printf_debug
#define printf_debug(...)
#endif

#define TEMPERATURE_INVALID			-1


/*
Serial
*/
void DTR(int set);
void RTS(int set);
int CTS(void);
int DSR(void);
void CS(unsigned int state);
void init_port();

/*
I2C
*/
//LSB for register address
#define I2C_WRITE					0
#define I2C_READ					1
//Address bytes must include R/W'
#define I2C_ADDRESS(addr, rw)		((addr) | (rw))
void Sclk(int a);
void SDout(int in);
int SDin(void);
void HiLowSCLK(void);
uint8_t ReadACKMine();
void I2CStart(void);
void I2CStop(void);
void I2CWriteByte(uint8_t byte);
uint8_t I2CReadByte( void );
int I2CWaitACK();
void I2CScan();
void I2CDelay();

/*
EEPROM
*/
uint8_t ReadEEPROM(uint8_t address);
void WriteEEPROM(uint8_t address, uint8_t data);
void dumpEEPROM();

/*
FM75
*/
void FM75Init(void);
double ReadInternalTemp(void);

/*
MAX6675
*/
double ReadThermocoupleTemp();

/*
Misc
*/
void tuneTiming();
const char *TEMPerName();

#endif

