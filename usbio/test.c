#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>

int open_test() {
	int fd;
	
	fd = open("/dev/ttyACM0", O_RDWR | O_NONBLOCK);
	printf("fd: %d\n", fd);
	if (fd < 0) {
		perror("damnit");
		return 1;
	}
	printf("wrote %d\n", write(fd, "~out9=1~", strlen("~out9=1~")));
	perror("shit");
	fsync(fd);
	sleep(1);
	printf("wrote %d\n", write(fd, "~out9=0~", strlen("~out9=0~")));
	fsync(fd);
	return 0;
}

int termios_test(void) {
	struct termios tio;
	int tty_fd;
	const char *device = "/dev/ttyACM0";
	int i;

	/*	
	struct termios stdio;
	memset( &stdio,0,sizeof(stdio) );
	stdio.c_iflag = 0;
	stdio.c_oflag = 0;
	stdio.c_cflag = 0;
	stdio.c_lflag = 0;
	stdio.c_cc[VMIN] = 1;
	stdio.c_cc[VTIME] = 0;
	tcsetattr(STDOUT_FILENO,TCSANOW, &stdio);
	tcsetattr(STDOUT_FILENO,TCSAFLUSH, &stdio);
	fcntl(STDIN_FILENO, F_SETFL, O_NONBLOCK);       // make the reads non-blocking
	*/


	memset(&tio, 0, sizeof(tio));
	tio.c_iflag = 0;
	tio.c_oflag = 0;
	// 8n1, see termios.h for more information
	tio.c_cflag = CS8 | CREAD | CLOCAL;           
	tio.c_lflag = 0;
	tio.c_cc[VMIN] = 1;
	tio.c_cc[VTIME] = 5;

	tty_fd = open(device, O_RDWR | O_NONBLOCK);      
	if (tty_fd < 0) {
		perror("open");
		return 1;
	}
	//Doesn't work at 115200...not sure how the speed works since its a modem
	cfsetospeed(&tio, B9600);            // 115200 baud
	//cfsetospeed(&tio,B115200);            // 115200 baud

	tcsetattr(tty_fd,TCSANOW,&tio);
	for (i = 0; i < 3; ++i) {
		printf("wrote %d\n", write(tty_fd, "~out9=1~", strlen("~out9=1~")));
		//perror("shit");
		//fsync(fd);
		sleep(1);

		printf("wrote %d\n", write(tty_fd, "~out9=0~", strlen("~out9=0~")));
		//fsync(fd);
		sleep(1);

		//if (read(tty_fd,&c,1)>0)        write(STDOUT_FILENO,&c,1);              // if new data is available on the serial port, print it out
		//if (read(STDIN_FILENO,&c,1)>0)  write(tty_fd,&c,1);                     // if new data is available on the console, send it to the serial port
	}

	close(tty_fd);
	return 0;
}

int main(void) {
	open_test();
	//termios_test();
	return 0;
}

