#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string>

/*
0x3480
0x4600
------
0x1120 = 4384

640 * 480 = 307200 = 0x4B000
*/

//Size that the Windows driver uses as seen through UsbSnoop
//Note that it has 4 outstanding requests at one time
//May need to change the internal kernel buffering
#define WIN_BUFF_SZ			0x1400
//char buff[WIN_BUFF_SZ];
char buff[800 * 600];

int main( int argc, char **argv ) {
	int fd = 0;
	FILE *out = NULL;
	std::string dev = "/dev/video0";
	std::string out_file_name = "out.bin";
	
	if (argc > 1) {
		dev = argv[1];
	}
	if (argc > 2) {
		out_file_name = argv[2];
	}
	
	fd = open(dev.c_str(), 0);
	if (fd < 0) { 
		perror("open");
		exit(1);
	}
	out = fopen(out_file_name.c_str(), "w");
	if (out == NULL) { 
		perror("fopen");
		exit(1);
	}
	printf("Open OK\n");
	
	unsigned int to_read = 800 * 600 * 4;
	unsigned n_written = 0;
	while (to_read) {
		unsigned int this_read = sizeof(buff);
		
		if (this_read > to_read) {
		    this_read = to_read;
		}
		
    	printf("Read size %d\n", this_read);
		int rc = read(fd, &buff, this_read);
		int err = errno;
		if (rc < 0) {
			perror("read");
	    	printf("read rc %d, errno: %d\n", rc, err);
			exit(1);
		}
		if (rc != this_read) {
			printf("WARNING: wanted %d got %d, may have wrong frame size\n",
					this_read, rc );
			break;
		}
		if ((unsigned)rc > this_read || (unsigned)rc > to_read) {
			printf("WTF? %d %d %d\n", rc, this_read, to_read);
			//exit(1);
			rc = to_read;
			break;
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

