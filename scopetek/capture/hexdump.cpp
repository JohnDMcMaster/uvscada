

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

void UVDHexdumpCore(const void *data_in, size_t size, const std::string &prefix, bool print_address, unsigned int address_start)
{
	/*
	[mcmaster@gespenst icd2prog-0.3.0]$ hexdump -C /bin/ls |head
	00000000  7f 45 4c 46 01 01 01 00  00 00 00 00 00 00 00 00  |.ELF............|
	00000010  02 00 03 00 01 00 00 00  f0 99 04 08 34 00 00 00  |............4...|
	00017380  00 00 00 00 01 00 00 00  00 00 00 00              |............|
	*/
	const uint8_t *data = (const uint8_t *)data_in;

	size_t pos = 0;
	while( pos < size )
	{
		uint32_t row_start = pos;
		uint32_t i = 0;

		if (print_address) {
			printf("0x%04X: ", address_start + pos);
		}

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

void UVDHexdump(const void *data, size_t size)
{
	UVDHexdumpCore(data, size, "", false, 0);
}

