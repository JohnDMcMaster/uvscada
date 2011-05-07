/*
uvcada TEMPer rev1 / TH1000
Copyright 2011 John McMaster <JohnDMcMaster@gmail.com>
Released under LGPL V3, see copying for details
*/

#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <string>
#include <stdint.h>
#include "TEMPer.h"


void Delay(int msec) {
	usleep(10 * msec);
}

void msleep(int msec) {
	usleep(1000 * msec);
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

void tuneTiming() {
	//Reduce timing until errors, then back up until reliable
}

void temper_init() {
	init_port();
	FM75Init();
}

