#include "TEMPer.h"

/*
Register layout for pointer value

000000 00: command (1 byte)
000000 01: config (1 byte)
000000 10: THYST (2 bytes)
000000 11: TOS (2 bytes)
*/
#define FM75_REG_TEMP		0x00
#define FM75_REG_CFG		0x01
#define FM75_REG_THYST		0x02
#define FM75_REG_TOS		0x03

#define FM75_I2C_ADDR		0x9E

//Note MSB is reserved / don't care
// Resolution (R1/R0)
#define FM75_RESOLUTION_9_BIT			0x00
#define FM75_RESOLUTION_9_BIT_SCALAR	0.5
#define FM75_RESOLUTION_10_BIT			0x20
#define FM75_RESOLUTION_10_BIT_SCALAR	0.25
#define FM75_RESOLUTION_11_BIT			0x40
#define FM75_RESOLUTION_11_BIT_SCALAR	0.125
#define FM75_RESOLUTION_12_BIT			0x60
#define FM75_RESOLUTION_12_BIT_SCALAR	0.0625
//Essentially we can get away with always using this since otherwise LSB are 0 anyway
//Note 4 LSB area always 0
#define FM75_RESOLUTION_FULL_SCALAR		(0.0625 / 16)
//Fault tolerance (F1/F0)
#define FM75_FAULT_TOLERANCE_1			0x00
#define FM75_FAULT_TOLERANCE_2			0x08
#define FM75_FAULT_TOLERANCE_4			0x10
#define FM75_FAULT_TOLERANCE_6			0x18
//Over-limit Signal (OS) output polarity (POL)
#define FM75_POL_ACT_LOW				0x00
#define FM75_POL_ACT_HIGH				0x04
//Thermostat mode (CMP/INT)
#define FM75_THERM_MODE_CMP				0x00
#define FM75_THERM_MODE_INT				0x02
//Shutdown (SD) 
#define FM75_SHUTDOWN_NORMAL			0x00
#define FM75_SHUTDOWN_SHUTDOWN			0x01

static void FM75RegWrite(unsigned int pointerRegister, uint8_t data);


void FM75Init(void) {
	fprintf(stderr, "Init starting\n");
	//FM75RegWrite(FM75_REG_CFG, 0x30);
	FM75RegWrite(FM75_REG_CFG,
			FM75_RESOLUTION_10_BIT 
			| FM75_FAULT_TOLERANCE_1 
			| FM75_POL_ACT_LOW 
			| FM75_THERM_MODE_CMP 
			| FM75_SHUTDOWN_NORMAL);
	//Hmm this can't be right
	//This reg is read only
	//Without this, value is inaccruate and doesn't seem to respond...grr
	//Ah got it this was a hack
	//They need to setup pointer to temp reg and used the same util function
	//write is ignored
	FM75RegWrite(FM75_REG_TEMP, 0x00);
	printf_debug("Init done\n");
}


//Sets pointer and does write
void FM75RegWrite(unsigned int pointerRegister, uint8_t data) {
	//Reset
	I2CStop();
	//Delay(100);
	I2CDelay();
	I2CStart();
	
	/*
	Slave address is at 1001XXX
	*/
	/*
	Slave address 
	
	The lowest order bit indicates a read, or write request. 
	A low bit indicates a write, a high bit a read request. 
	Data is transferred with the most significant bit first. 
	*/
	//User selectable bits are at 111, write
	I2CWriteByte(I2C_ADDRESS(FM75_I2C_ADDR, I2C_WRITE));
	I2CWaitACK();
	
	//The 6 MSBs of the pointer must be 0
	I2CWriteByte(pointerRegister);
	I2CWaitACK();
	
	//Next byte is data to put in register
	I2CWriteByte(data);
	I2CWaitACK();
	//Whats this for?  Clear ACK?
	SDout(0);
	HiLowSCLK();
	I2CStop();
}

double ReadInternalTemp(void)
{
	double temperature;
	uint16_t raw = 0;

	I2CStart();
	
	I2CWriteByte(I2C_ADDRESS(FM75_I2C_ADDR, I2C_READ));
	//ACK on high clock
	Sclk(1);
	//Delay(10);
	I2CDelay();
	if (SDin() != 0) {
		return TEMPERATURE_INVALID;
	}
	Sclk(0);
	//Delay(10);
	I2CDelay();

	
	raw += I2CReadByte() << 8;
	I2CWaitACK();
	raw += I2CReadByte();
	I2CWaitACK();
	
	I2CStop();

	temperature = raw * FM75_RESOLUTION_FULL_SCALAR;

	printf_debug("Getting temperature done: 0x%04X / %s => %f\n", raw, to_binary(raw).c_str(), temperature);

	return temperature;
}


