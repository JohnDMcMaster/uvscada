#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdlib.h>
#include <unistd.h>
#include <string>

//Size that the Windows driver uses as seen through UsbSnoop
//Note that it has 4 outstanding requests at one time
//May need to change the internal kernel buffering
#define WIN_BUFF_SZ			0x1400
//char buff[WIN_BUFF_SZ];
char buff[0x400];

int main( void ) {
	int fd = 0;
	FILE *out = NULL;
	
	fd = open("/dev/uvscopetek0", 0);
	if (fd < 0) { 
		perror("open");
		exit(1);
	}
	std::string out_file_name = "out.bin";
	out = fopen(out_file_name.c_str(), "w");
	if (out == NULL) { 
		perror("fopen");
		exit(1);
	}
	
	unsigned int to_read = 640 * 480 * 3    * 4;
	unsigned n_written = 0;
	while (to_read) {
		unsigned int this_read = to_read;
		if (this_read > sizeof(buff)) {
			this_read = sizeof(buff);
		}
		int rc = read(fd, &buff, this_read);
		if (rc < 0) {
			perror("read");
			exit(1);
		}
		if ((unsigned)rc > this_read || (unsigned)rc > to_read) {
			printf("WTF? %d %d %d\n", rc, this_read, to_read);
			//exit(1);
			rc = to_read;
		}
		//printf("read %d bytes (%d / %d)\n", rc, i, limit);
		to_read -= rc;
		//printf("read %d bytes, need %d more\n", rc, to_read);
		printf(".");
		int frc = fwrite( buff, 1, rc, out );
		if (frc > 0) {
			n_written += frc;
		}
		if (frc != rc) {
			perror("fwrite");
			printf("fwrite wanted %d got %d\n", rc, frc);
			break;
		}
	}
	fclose(out);
	printf("wrote %u bytes to %s\n", n_written, out_file_name.c_str() );
	
	return 0;
}

