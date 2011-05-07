/*
uvcada TEMPer rev1 / TH1000
Copyright 2011 John McMaster <JohnDMcMaster@gmail.com>
Released under LGPL V3, see copying for details
*/

#include <sys/types.h>
#include <sys/stat.h>
#include <sys/ioctl.h>
#include <fcntl.h>
#include <termios.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <string>
#include <stdint.h>

#define BAUDRATE B9600
std::string g_device = "/dev/ttyUSB0";
#define _POSIX_SOURCE 1 /* POSIX compliant source */
#define FALSE 0
#define TRUE 1

//LSB for register address
#define I2C_WRITE					0
#define I2C_READ					1
//Address bytes must include R/W'
#define I2C_ADDRESS(addr, rw)		((addr) | (rw))

#define CH341_BIT_CTS 0x01
#define CH341_BIT_DSR 0x02
#define CH341_BIT_RI  0x04
#define CH341_BIT_DCD 0x08
#define CH341_BITS_MODEM_STAT 0x0f /* all bits */
#define CH341_BIT_RTS (1 << 6)
#define CH341_BIT_DTR (1 << 5)

#define TEMPERATURE_INVALID			-1

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
//24LC02
//Address is correct..freezers otherwise
//But just no data
#define EPROM_I2C_ADDR		0xA0
//2 Kib
#define EPROM_SIZE			256


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


volatile int STOP=FALSE;

//Receive or transit maybe?
//Also ref to temperature-to-digital (T-to-D) in datasheet
//Inverts read or write values
char m_CHic;
int fd;

#define debug_sleep(x)
//#define debug_sleep sleep

#define printf_debug printf

void Delay(int msec) {
	usleep(10 * msec);
}

void I2CDelay() {
	usleep(1000);
}

void msleep(int msec) {
	usleep(1000 * msec);
}

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


/*
SDA is on RTS inverted (out) and CTS (in) to complete bi-directional bus
SCL is DTR inverted
*/
void DTR(int set) {
	int status = 0;
	
	ioctl(fd, TIOCMGET, &status);
	if (set)
	{
		status |= TIOCM_DTR;
	}
	else
	{
		status &= ~TIOCM_DTR;
	}
	
	if (ioctl(fd, TIOCMSET, &status) < 0)
	{
		perror("ioctl");
		exit(1);
	}
}

void RTS(int set) {
	int status = 0;
	
	//Get previous status so we only twiddle one bit
	if (ioctl(fd, TIOCMGET, &status) < 0) {
		perror("ioctl");
		exit(1);
	}
	
	//printf("set RTS: %d\n", set);

	//Set/clear bit
	if (set) {
		status |= TIOCM_RTS;
	} else {
		status &= ~TIOCM_RTS;
	}
	
	//And write the status back
	if (ioctl(fd, TIOCMSET, &status) < 0) {
		perror("ioctl");
		exit(1);
	}
}

int CTS(void) {
	int status = 0;
	
	if (ioctl(fd, TIOCMGET, &status)) {
		perror("ioctl failed");
	}
	return (status & TIOCM_CTS);
}

int DSR(void) {
	int status = 0;
	
	if (ioctl(fd, TIOCMGET, &status)) {
		perror("ioctl failed");
	}
	return (status & TIOCM_DSR);
}

void Sclk(int a) {
	m_CHic = 'T';
	if (m_CHic == 'T')
	{
		DTR(a == 0);
	}
	else if (m_CHic == 'R')
	{
		DTR(a == 1);
	}
}

void SclkRaw(int a) {
	//Pin is inverted
	DTR(a == 0);
}

void SDout(int in) {
	RTS(!in);
}

void SDoutBit(unsigned int bit) {
	/*
	Active low so invert
	*/
	RTS(!bit);
}

int SDinNoCHic( void ) {
	//Make sure that we aren't driving it low
	SDout(1);
	Delay(100);
	//Pin is inverted
	return CTS() == 0;
}

int SDin(void) {
	int SDin = 0;

	//Make sure that we aren't driving it low
	SDout(1);
	Delay(100);
	int a = CTS();
	//printf("SDin CTS: %d, mCHic: %c, a: %d\n", a, m_CHic, a);
	if (m_CHic == 'T')
	{
		if (!a)
			SDin = 1;
		else
			SDin = 0;
	}
	if (m_CHic != 'R')
		return SDin;
	printf("A screw up\n");
	if (!a)
		return 0;
	return 1;
}

void HiLowSCLK(void) {
	//Delay(10);
	I2CDelay();
	Sclk(1);
	//Delay(20);
	I2CDelay();
	Sclk(0);
	//Delay(20);
	I2CDelay();
}

//http://www.lammertbies.nl/comm/info/I2C-bus.html#star
void I2CStart(void) {
	/*
	To create a START condition, the clock line SCL remains high, while the master changes the SDA line to the low condition.	
	SDA  UUU========________	
	SCL  UUUUUUU========____
	*/
	
	//Prereq state
	SDout(1);
	//Delay(4);
	I2CDelay();
	Sclk(1);
	//Delay(40);
	I2CDelay();

	//Changing SDA low while SCL is high is the start condition
	SDout(0);
	//Delay(30);
	I2CDelay();
	
	//Code will expect SCL low so that we can set data
	//Otherwise we might send a stop condition by mistake
	Sclk(0);
	//Delay(30);
	I2CDelay();
}

void I2CStop(void) {
	/*
	The end of a communication session is signaled by a STOP condition. 
	The STOP condition is generated by changing the SDA data line to high while the clock line SCL is high.

	We assume SCL was brought low by the previous transmit finishing
	SDA  UUU______===
	SCL  UUUUUU======
	*/
	
	//Prereq state
	SDout(0);
	//Delay(50);
	I2CDelay();
	Sclk(1);
	//Delay(50);
	I2CDelay();
	
	//Bring it high to issue the stop condition
	SDout(1);
	//Delay(50);
	I2CDelay();
}

//Clock should be low at start
void I2CWriteByte(uint8_t byte) {
	printf("I2C: write byte 0x%02X\n", byte);
	//MSB first
	unsigned int mask = 0x80;
	for( ;; )
	{
		SDoutBit(byte & mask);
		HiLowSCLK();
		
		if( mask == 0x01 )
		{
			break;
		}
		mask = mask >> 1;
	}
	//Stop pulling line low
	//SDout( 1 );
}

uint8_t I2CReadByte( void ) {
	//Clock should be low before and after calling
	uint8_t byte = 0;
	//MSB first
	unsigned int mask = 0x80;
	
	//Stop pulling line low
	SDout( 1 );

	Delay(20);
	for( ;; )
	{
		//Data is valid when clock is high
		Sclk(1);
		//Delay(100);
		I2CDelay();
		if( SDin() )
		{
			byte += mask;
		}
		Sclk(0);
		//Delay(100);
		I2CDelay();
		
		if( mask == 0x01 )
		{
			break;
		}
		mask = mask >> 1;
	}
	printf("read byte 0x%02X\n", byte);
	return byte;
}	

int I2CWaitACK() {
	int ret;
	//Make sure we aren't bringing the line low
	SDout(1);
	//Delay(100);
	I2CDelay();
	Sclk(1);
	//Delay(100);
	I2CDelay();
	ret = SDin();
	Sclk(0);
	I2CDelay();
	return ret;
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

void FM75Init(void) {
	fprintf(stderr, "Init starting\n");
	printf("m_chic: %c\n", m_CHic);
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


double Bin2Dec(const char *s) {
	double lDec = 0.0;

	if (s == NULL || strlen(s) == 0)
		s = "0";

	while (*s != '\0')
	{
		if (*s == '1')
			lDec += pow(2.0, strlen(s) - 1);
		s++;
	}
	return lDec;
}

uint8_t ReadACKMine()
{
	//Assume clock was low at start
	uint8_t tt = SDin();
	HiLowSCLK();
	return tt;
}

void I2CScan() {
	/*
	Device at 0x9E
		FM75
	Device at 0xA0
		24C02
	*/
	for( int i = 0; i < 256; i += 2 ) 
	{
		I2CStart();
		//Dummy write
		I2CWriteByte(I2C_ADDRESS(i, I2C_WRITE));
		//Requires longer delay than others...why?
		msleep(1);
		//Set to 0 if someone brought it low
		if( ReadACKMine() == 0 ) 
		{
			printf("Device at 0x%02X\n", i);
		}
	}
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

const char *TEMPerName() {
	uint8_t at_0x58 = ReadEEPROM(0x58);
	uint8_t at_0x59 = ReadEEPROM(0x59);
	
	if ((at_0x58 == 0x58) & (at_0x59 == 0x59)) {
		return "TEMPerV1";
	} else if ((at_0x58 == 0x58) & (at_0x59 != 0x59)) {
		return "TEMPerV2";  
	} else if ((at_0x58 == 0x59) & (at_0x59 == 0x5A)) {
		return "TEMPerHum";
	} else if ((at_0x58 == 0x5B) & (at_0x59 == 0x00)) {
		return "TH1000";
	} else {
		printf("unknown type, 58: 0x%02X, 59: 0x%02X\n", at_0x58, at_0x59);
		return "<unk>";
	}
}

std::string to_binary(unsigned int n) {
	unsigned int i;
	std::string ret;
	
	i = 1 << (2 * 8 - 1);

	while (i > 0) {
		if (n & i)
			ret += "1";
		else
			ret += "0";
		i >>= 1;
	}
	return ret;
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

	printf("Getting temperature done: 0x%04X / %s => %f\n", raw, to_binary(raw).c_str(), temperature);

	return temperature;
}

void CS(unsigned int state)
{
	//Shares pin with SDA on RTS
	//although its really more connected to CTS through a diode or something
	//and its inverted
	RTS(!state);
}

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
		printf("0x%04X (%d) => %lf\n", raw, raw, ret);
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
	unsigned int raw_low_edge = 0;
	unsigned int raw_low = 0;
	unsigned int raw_high_edge = 0;
	unsigned int raw_high = 0;

	printf("reading temp\n");
	
	//make sure we aren't bringing CS low
	//hmm doesn't have any effect
	//eh CS is SDA, we set it as needed
	//SDout(0);
	
	//printf("Clock low\n");
	SclkRaw(0);
	msleep(3);
	debug_sleep(1);
	
	//printf("CS high\n");
	CS(1);
	msleep(500);
	debug_sleep(1);

	//printf("Setting CS low\n");
	//Wake up you lazy bastard
	CS(0);
	msleep(1);
	debug_sleep(1);
	
	for( ;; )
	{
		//read1 and read2 always match
		unsigned int read_low_edge;
		unsigned int read_low;
		unsigned int read_high_edge;
		unsigned int read_high;
	
		//printf("Clock high\n");
		SclkRaw(1);
		read_high_edge = SPIIn();
		msleep(3);
		debug_sleep(1);
		read_high = SPIIn();
		
		/*
		"Read the 16 output bits on the falling edge of the clock"
		USB capture has only about 4 ms in between
		*/
		
		//printf("Clock low\n");
		SclkRaw(0);
		read_low_edge = SPIIn();
		msleep(1);
		//printf("read1: %d\n", read);
		msleep(3);
		debug_sleep(1);
		//To see if we are forgetting data
		read_low = SPIIn();

		//Data should be valid
		if( read_low_edge )
		{
			raw_low_edge += mask;
		}
		if( read_low )
		{
			raw_low += mask;
		}
		if( read_high_edge )
		{
			raw_high_edge += mask;
		}
		if( read_high )
		{
			raw_high += mask;
		}
		
		printf("high': %d, high: %d, low': %d, low: %d\n", read_high_edge, read_high, read_low_edge, read_low);
		/*
		if( read2 != read )
		{
			printf("read1: %d, read2: %d\n", read, read2);
		}
		*/
		if( mask == 1 )
		{
			break;
		}
		mask = mask >> 1;
	}
	//Back to idle
	CS(1);
	
	printf("<***\n");
	double to_ret = decode_temperature(raw_high_edge);
	decode_temperature(raw_high);
	decode_temperature(raw_low_edge);
	decode_temperature(raw_low);
	printf(">***\n");
	return to_ret;
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

//verified does work as expected on 24C02
void hilosda( void ) {
	for (;;) {
		printf("off\n");
		SDout(0);
		debug_sleep(3);

		printf("on\n");
		SDout(1);
		debug_sleep(3);
	}
}

//Verified works as expected on 24C02 and MAX6675
void hiloscl( void ) {
	for (;;) {
		printf("off\n");
		Sclk(0);
		debug_sleep(3);

		printf("on\n");
		Sclk(1);
		debug_sleep(3);
	}
}

//Verified is setting CS as expected
void hiloCS( void ) {
	for (;;) {
		printf("CS off\n");
		CS(0);
		debug_sleep(3);

		printf("CS on\n");
		CS(1);
		debug_sleep(3);
	}
}

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

void init_port()
{
	struct termios a_termios;

	//FIXME: setup termios
	printf("opening port %s\n", g_device.c_str());
	//fd = open(g_device.c_str(), O_RDWR | O_NOCTTY );
	fd = open(g_device.c_str(), O_RDWR | O_NONBLOCK);
	if (fd <0) {
		printf("failed to open: %s\n", g_device.c_str());
		perror(g_device.c_str());
		exit(-1);
	}

	printf("setting up\n");

	tcgetattr(fd, &a_termios); /* save current port settings */

	a_termios.c_cflag |= (CLOCAL | CREAD);

	a_termios.c_cflag &= ~PARENB;
	a_termios.c_cflag &= ~CSTOPB;
	a_termios.c_cflag &= ~CSIZE;
	a_termios.c_cflag |= CS8;

	cfsetispeed(&a_termios, BAUDRATE);
	cfsetospeed(&a_termios, BAUDRATE);

	a_termios.c_cflag |= CRTSCTS;

	a_termios.c_iflag |= IGNPAR;
	a_termios.c_oflag &= ~OPOST;

	/* set input mode (non-canonical, no echo,...) */
	a_termios.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG);

	a_termios.c_cc[VTIME]    = 1;   /* inter-character timer unused */
	a_termios.c_cc[VMIN]     = 1;   /* blocking read until 5 chars received */

	tcflush(fd, TCIFLUSH);
	tcsetattr(fd,TCSANOW,&a_termios);

	m_CHic = 'T';
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
			msleep(500);
			msleep(300);
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
			internal_temp = ReadInternalTempOld();
			internal_temp = ReadInternalTemp();
			//internal_temp = ReadInternalTempMutated();
			
			printf("internal: %lf\n", internal_temp);			
			msleep(500);
			debug_sleep(3);
		}
	}
	else if( arg == "--read-all" )
	{
		FM75Init();
		for( ;; ) 
		{
			double internal_temp = ReadInternalTemp();
			double thermocouple_temp = ReadThermocoupleTemp();
			
			printf("internal: %lf\n", internal_temp);			
			printf("thermocouple: %lf\n", thermocouple_temp);			
			msleep(500);
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

