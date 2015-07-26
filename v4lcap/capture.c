/*
 *  V4L2 video capture example
 *
 *  This program can be used and distributed without restrictions.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include <getopt.h>                /* getopt_long() */

#include <fcntl.h>                /* low-level i/o */
#include <unistd.h>
#include <errno.h>
#include <malloc.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/mman.h>
#include <sys/ioctl.h>

#include <asm/types.h>                /* for videodev2.h */

#include <linux/videodev2.h>

#define CLEAR(x) memset (&(x), 0, sizeof (x))

struct buffer {
    void *start;
    size_t length;
};

FILE *g_out = NULL;
    

static char *dev_name = NULL;
static int fd = -1;
struct buffer *buffers = NULL;
static unsigned int n_buffers = 0;

static void errno_exit(const char *s)
{
    fprintf(stderr, "%s error %d, %s\n", s, errno, strerror(errno));

    exit(EXIT_FAILURE);
}

static int xioctl(int fd, int request, void *arg)
{
    int r;

    do
        r = ioctl(fd, request, arg);
    while (-1 == r && EINTR == errno);

    return r;
}

#include <stdint.h>


uint32_t g_bytesPerRow = 16;
uint32_t g_bytesPerHalfRow = 8;

static unsigned int hexdumpHalfRow(const uint8_t * data, size_t size,
                                   uint32_t start)
{
    uint32_t col = 0;

    for (; col < g_bytesPerHalfRow && start + col < size; ++col) {
        uint32_t index = start + col;
        uint8_t c = data[index];

        printf("%.2X ", (unsigned int) c);
        fflush(stdout);
    }

    //pad remaining
    while (col < g_bytesPerHalfRow) {
        printf("   ");
        fflush(stdout);
        ++col;
    }

    //End pad
    printf(" ");
    fflush(stdout);

    return start + g_bytesPerHalfRow;
}

void UVDHexdumpCore(const uint8_t * data, size_t size, const char *prefix)
{
    /*
       [mcmaster@gespenst icd2prog-0.3.0]$ hexdump -C /bin/ls |head
       00000000  7f 45 4c 46 01 01 01 00  00 00 00 00 00 00 00 00  |.ELF............|
       00000010  02 00 03 00 01 00 00 00  f0 99 04 08 34 00 00 00  |............4...|
       00017380  00 00 00 00 01 00 00 00  00 00 00 00          |............|
     */

    size_t pos = 0;
    while (pos < size) {
        uint32_t row_start = pos;
        uint32_t i = 0;

        printf("%s", prefix);
        fflush(stdout);

        pos = hexdumpHalfRow(data, size, pos);
        pos = hexdumpHalfRow(data, size, pos);

        printf("|");
        fflush(stdout);

        //Char view
        for (i = row_start; i < row_start + g_bytesPerRow && i < size; ++i) {
            char c = data[i];
            if (isprint(c)) {
                printf("%c", c);
                fflush(stdout);
            } else {
                printf("%c", '.');
                fflush(stdout);
            }

        }
        for (; i < row_start + g_bytesPerRow; ++i) {
            printf(" ");
            fflush(stdout);
        }

        printf("|\n");
        fflush(stdout);
    }
    fflush(stdout);
}

void UVDHexdump(const uint8_t * data, size_t size)
{
    UVDHexdumpCore(data, size, "");
}



static void process_image(const void *data_in, size_t data_size)
{
    const uint8_t *data = (uint8_t *) data_in;
    printf("data size: %u\n", data_size);
    if (fwrite(data, 1, data_size, g_out) != data_size) {
        printf("Failed to write all data\n");
        exit(1);
    }
}

static int read_frame(void)
{
    struct v4l2_buffer buf;
    unsigned int i;
    int rc;

    rc = read(fd, buffers[0].start, buffers[0].length);
    if (-1 == rc) {
        switch (errno) {
        case EAGAIN:
            return 0;

        case EIO:
            /* Could ignore EIO, see spec. */

            /* fall through */

        default:
            errno_exit("read");
        }
    }

    process_image(buffers[0].start, rc);

    return 1;
}

static void mainloop(void)
{
    int count;
    
    printf("Looping\n");
    for (count = 0; count < 4; ++count) {
        printf("Capturing image %d\n", count);
        for (;;) {
            fd_set fds;
            struct timeval tv;
            int r;

            FD_ZERO(&fds);
            FD_SET(fd, &fds);

            /* Timeout. */
            tv.tv_sec = 5;
            tv.tv_usec = 0;

            r = select(fd + 1, &fds, NULL, NULL, &tv);

            if (-1 == r) {
                if (EINTR == errno)
                    continue;

                errno_exit("select");
            }

            if (0 == r) {
                fprintf(stderr, "select timeout\n");
                exit(EXIT_FAILURE);
            }

            if (read_frame())
                break;

            /* EAGAIN - continue select loop. */
        }
    }
}

static void stop_capturing(void)
{
}

static void start_capturing(void)
{
}

static void uninit_device(void)
{
    free(buffers[0].start);
    free(buffers);
}

static void init_read(unsigned int buffer_size)
{
    printf("Allocating size %d\n", buffer_size);
    buffers = calloc(1, sizeof(*buffers));

    if (!buffers) {
        fprintf(stderr, "Out of memory\n");
        exit(EXIT_FAILURE);
    }

    buffers[0].length = buffer_size;
    buffers[0].start = malloc(buffer_size);

    if (!buffers[0].start) {
        fprintf(stderr, "Out of memory\n");
        exit(EXIT_FAILURE);
    }
}

static void init_device(void)
{
    struct v4l2_capability cap;
    struct v4l2_cropcap cropcap;
    struct v4l2_crop crop;
    struct v4l2_format fmt;
    unsigned int min;

    if (-1 == xioctl(fd, VIDIOC_QUERYCAP, &cap)) {
        if (EINVAL == errno) {
            fprintf(stderr, "%s is no V4L2 device\n", dev_name);
            exit(EXIT_FAILURE);
        } else {
            errno_exit("VIDIOC_QUERYCAP");
        }
    }

    if (!(cap.capabilities & V4L2_CAP_VIDEO_CAPTURE)) {
        fprintf(stderr, "%s is no video capture device\n", dev_name);
        exit(EXIT_FAILURE);
    }

    if (!(cap.capabilities & V4L2_CAP_READWRITE)) {
        fprintf(stderr, "%s does not support read i/o\n", dev_name);
        exit(EXIT_FAILURE);
    }


    /* Select video input, video standard and tune here. */


    CLEAR(cropcap);

    cropcap.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

    if (0 == xioctl(fd, VIDIOC_CROPCAP, &cropcap)) {
        crop.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        crop.c = cropcap.defrect;        /* reset to default */

        if (-1 == xioctl(fd, VIDIOC_S_CROP, &crop)) {
            switch (errno) {
            case EINVAL:
                /* Cropping not supported. */
                break;
            default:
                /* Errors ignored. */
                break;
            }
        }
    } else {
        /* Errors ignored. */
    }

    /*
    If it was going to force size during set why did it not give it during get?
    Got format, type: 1
    Suggested width: 0
    Suggested height: 0
    Bytes per line: 0
    Image size: 0
    Requested width: 3264
    Requested height: 2448
    Final width: 1600
    Final height: 1200
    Final image size: 1920000
    Allocating size 1920000
    */

    CLEAR(fmt);

    //Must be either this or V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE
    fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    if (-1 == xioctl(fd, VIDIOC_G_FMT, &fmt))
        errno_exit("VIDIOC_G_FMT");
    printf("Got format, type: %d\n", fmt.type);

    CLEAR(fmt);

    printf("Suggested width: %d\n", fmt.fmt.pix.width);
    printf("Suggested height: %d\n", fmt.fmt.pix.height);
    printf("Bytes per line: %d\n", fmt.fmt.pix.bytesperline);
    printf("Image size: %d\n", fmt.fmt.pix.sizeimage);

    fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    fmt.fmt.pix.width = 1600;
    fmt.fmt.pix.height = 1200;
    fmt.fmt.pix.width = 3264;
    fmt.fmt.pix.height = 2448;
    
    printf("Requested width: %d\n", fmt.fmt.pix.width);
    printf("Requested height: %d\n", fmt.fmt.pix.height);
    fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_YUYV;
    fmt.fmt.pix.field = V4L2_FIELD_INTERLACED;

    if (-1 == xioctl(fd, VIDIOC_S_FMT, &fmt))
        errno_exit("VIDIOC_S_FMT");

    /* Note VIDIOC_S_FMT may change width and height. */
    
    printf("Final width: %d\n", fmt.fmt.pix.width);
    printf("Final height: %d\n", fmt.fmt.pix.height);
    printf("Final image size: %d\n", fmt.fmt.pix.sizeimage);
    init_read(fmt.fmt.pix.sizeimage);
}

static void close_device(void)
{
    if (-1 == close(fd))
        errno_exit("close");

    fd = -1;
}

static void open_device(void)
{
    struct stat st;

    if (-1 == stat(dev_name, &st)) {
        fprintf(stderr, "Cannot identify '%s': %d, %s\n",
                dev_name, errno, strerror(errno));
        exit(EXIT_FAILURE);
    }

    if (!S_ISCHR(st.st_mode)) {
        fprintf(stderr, "%s is no device\n", dev_name);
        exit(EXIT_FAILURE);
    }

    fd = open(dev_name, O_RDWR /* required */  | O_NONBLOCK, 0);

    if (-1 == fd) {
        fprintf(stderr, "Cannot open '%s': %d, %s\n",
                dev_name, errno, strerror(errno));
        exit(EXIT_FAILURE);
    }
}

int main(int argc, char **argv)
{
    g_out = fopen("out.bin", "w");
    if (g_out == NULL) {
        perror("open out");
        return 1;
    }
    
    dev_name = "/dev/video0";

    open_device();
    init_device();
    start_capturing();
    mainloop();
    stop_capturing();
    uninit_device();
    close_device();

    return 0;
}
