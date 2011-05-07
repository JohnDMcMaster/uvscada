#include <sys/ioctl.h>
#include <fcntl.h>
#include <termios.h>
#include <stdio.h>
#include <string>
#include <stdlib.h>
#include "TEMPer.h"

#define CH341_BIT_CTS 0x01
#define CH341_BIT_DSR 0x02
#define CH341_BIT_RI  0x04
#define CH341_BIT_DCD 0x08
#define CH341_BITS_MODEM_STAT 0x0f /* all bits */
#define CH341_BIT_RTS (1 << 6)
#define CH341_BIT_DTR (1 << 5)

#define BAUDRATE B9600
std::string g_device = "/dev/ttyUSB0";
#define _POSIX_SOURCE 1 /* POSIX compliant source */

int fd;

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

void CS(unsigned int state)
{
	//Shares pin with SDA on RTS
	//although its really more connected to CTS through a diode or something
	//and its inverted
	RTS(!state);
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

	// save current port settings
	tcgetattr(fd, &a_termios); 

	a_termios.c_cflag |= (CLOCAL | CREAD);

	a_termios.c_cflag &= ~PARENB;
	a_termios.c_cflag &= ~CSTOPB;
	a_termios.c_cflag &= ~CSIZE;
	a_termios.c_cflag |= CS8;

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
}


