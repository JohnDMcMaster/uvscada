//Based on: http://cdn.teledynelecroy.com/files/manuals/8901aman.pdf

/*
Purpose: Functions to control the CAMAC bus via an 8901A or 6010,
from an IBM PC using National Instruments PC-II GPIB Card.
Language: C
Note: These functions were created for a novice user, although they assume
the basic knowledge of ‘C’, GPIB, and CAMAC.
They are not optimized for speed but for ease of understanding.
MUST link the National Instruments gpib.obj file, Microsoft ‘C’
versions are labeld MCIBx.OBJ file, (x=C,S,M,L).
*/
/* ———————————————————————————————————— */
#include "camgpib.h"
#include "ib.h"

/* status word
*/
/* GPIB error code
*/
/* number of bytes sent */
int gpibBd = -1;
/* device descriptor for the controller board */
char pcTalk[] = "@!";        /* Talk 0 List 1 */
char pcList[] = "A";        /* List 0 Talk 1 */
int ccType = 0;
/* Type of controller, 8901 or 6010 */
int qxRet;

/* status last camac command */
#define DEF6010 "DUMB ON;CDMA OFF;CFMT OFF,WORD,BINARY;CORD LOFIRST;CAMAC 2"
#define DEFCNT  59

/*
Initialize the GPIB routines and the camac controller.
This function MUST be performed to setup CAMAC access!
If GPIB board cannot be opened this function will exit(1) your program.
*/
void caminit(
        int addr,   //GPIB Address of controller
        int type) { //C8901 or C6010
    /* if gpib board was never opened, open it */
    if (gpibBd < 0) {
        if ((gpibBd = ibfind("GPIB0")) < 0)
            return;
    }
    if (addr > 0 && addr < 29) {
        pcTalk[1] = 0x20 + addr;
        pcList[1] = 0x40 + addr;
    }
    /* do an interface clear */
    ibsic(gpibBd);
    /* set timeout, 3 sec */
    ibtmo(gpibBd, 12);
    /* set type of controller */
    ccType = type;
    if (type == 6010) {
        /* address 6010 to listen */
        ibcmd(gpibBd, pcTalk, 2);
        /* send command string to the 6010 */
        ibwrt(gpibBd, DEF6010, DEFCNT);
    }
}

/*
Do a 24 bit camac write cycle, W1-W24.
*/
void camo(
        int n,      //slot number of module
        int f,      //funtion code
        int a,      //address code
        long d) {   //data value to send
    char rw[40];
    
    /* init qxResp return value */
    qxRet = 0;
    if (ccType == 8901) {
        /* address 8901 to listen */
        ibcmd(gpibBd, pcTalk, 2);
        /* send 24 bit normal mode command to 8901A (decimal 100) */
        ibwrt(gpibBd, "d", 1);
        /* MUST make the 8901A unlisten, send unlisten & untalk */
        25 ibcmd(gpibBd, "? _", 2);
        /* build command string with 3 bytes of data (CAMAC W1-W24) */
        rw[0] = (char) f;
        rw[1] = (char) a;
        rw[2] = (char) n;
        rw[3] = (char) (d & 0xFFL);
        rw[4] = (char) ((d & 0xFF00L) >> 8);
        rw[5] = (char) ((d & 0xFF0000L) >> 16);
        /* address 8901A to listen */
        ibcmd(gpibBd, pcTalk, 2);
        /* send command string to the 8901A (F, A, N, D1, D2, D3) */
        ibwrt(gpibBd, rw, 6);
        /* address 8901A to talk to execute the CAMAC cycle */
        ibcmd(gpibBd, pcList, 2);
        /* read data from the 8901A to update the Q and X status */
        ibrd(gpibBd, rw, 10);
        /* 1st byte=R1-R8, 2nd byte=R9-R16, 3rd byte=R17-R24, 4th byte=Q&X */
        if (ibcnt == 4)
            qxRet = (int) (rw[3] & 3);
        } else if (ccType == 6010) {
        /* build command string with 3 bytes of data (CAMAC W1-W24) */
        sprintf(rw, "n = %2 d;
                f = %2 d;
                a = %2 d;
                w = %10l d;
                rqx", n, f, a, d);
        /* address 6010 to listen */
        ibcmd(gpibBd, pcTalk, 2);
        /* send command string to the 6010 */
        ibwrt(gpibBd, rw, 31);
        /* address 6010 to talk */
        ibcmd(gpibBd, pcList, 2);
        /* read data from the 6010 to update the Q and X status */
        ibrd(gpibBd, rw, 10);
        /* 1st byte=R1-R8, 2nd byte=R9-R16, 3rd byte=R17-R24, 4th byte=Q&X */
        if (ibcnt == 4)
            qxRet = (int) (rw[3] & 3);
    }
}

/*
Do a 24 bit camac read cycle.
Returns: long (R1-R24) value of data read.
*/
long cami(
        int n,      //slot number of module
        int f,      //funtion code
        int a) {    //address code
    long d, d1, d2, d3;
    char rw[40];
    
    /* init return data value and qxResp return value */
    d = 0L;
    qxRet = 0;
    if (ccType == 8901) {
        /* address 8901 to listen */
        ibcmd(gpibBd, pcTalk, 2);
        /* send 24 bit normal mode command to 8901A (decimal 100) */
        ibwrt(gpibBd, "d", 1);
        /* MUST make the 8901A unlisten, send unlisten & untalk */
        ibcmd(gpibBd, "? _", 2);
        /* build command string with 3 bytes of data (CAMAC W1-W24) */
        rw[0] = (char) f;
        rw[1] = (char) a;
        rw[2] = (char) n;
        rw[3] = (char) 0;
        rw[4] = (char) 0;
        rw[5] = (char) 0;
        /* address 8901A to listen */
        ibcmd(gpibBd, pcTalk, 2);
        /* send command string to the 8901A (F, A, N, D1, D2, D3) */
        ibwrt(gpibBd, rw, 6);
        /* address 8901A to talk to execute the CAMAC cycle */
        ibcmd(gpibBd, pcList, 2);
        /* read data from the 8901A to update the Q and X status */
        ibrd(gpibBd, rw, 10);
        /* 1st byte=R1-R8, 2nd byte=R9-R16, 3rd byte=R17-R24, 4th byte=Q&X */
        if (ibcnt == 4) {
            d3 = (long) rw[2];
            d3 = d3 & 0xFF;
            d2 = (long) rw[1];
            d2 = d2 & 0xFF;
            d1 = (long) rw[0];
            d1 = d1 & 0xFF;
            d = (d3 << 16) + (d2 << 8) + d1;
            qxRet = (int) (rw[3] & 3);
        }
    } else if (ccType == 6010) {
        /* build command string with 0 data (CAMAC W1-W24) */
        sprintf(rw, "n = %2 d;
                f = %2 d;
                a = %2 d;
                w = 0;
                rqx", n, f, a);
        /* address 6010 to listen */
        ibcmd(gpibBd, pcTalk, 2);
        /* send command string to the 6010 */
        ibwrt(gpibBd, rw, 22);
        /* address 6010 to talk */
        ibcmd(gpibBd, pcList, 2);
        /* read data from the 6010 to update the Q and X status */
        ibrd(gpibBd, rw, 10);
        /* 1st byte=R1-R8, 2nd byte=R9-R16, 3rd byte=R17-R24, 4th byte=Q&X */
        if (ibcnt == 4) {
            d3 = (long) rw[2];
            d3 = d3 & 0xFF;
            d2 = (long) rw[1];
            d2 = d2 & 0xFF;
            d1 = (long) rw[0];
            d1 = d1 & 0xFF;
            d = (d3 << 16) + (d2 << 8) + d1;
            qxRet = (int) (rw[3] & 3);
        }
    }
    return (d);
}

/*
Do a 16 bit block read cycle.
Return: number of data values read.
*/
int camibk16(
        int n,          //slot number of module
        int f,          //funtion code
        int a,          //address code
        int count,      //number of data values to read
        int *buffer) {  //array to store data into
    int retval;
    char rw[40];
    
    /* init return data count value */
    retval = 0;
    /* block xfer mode is set in bytes */
    count = count * 2;
    if (ccType == 8901) {
        /* address 8901 to listen */
        ibcmd(gpibBd, pcTalk, 2);
        /* send 16 bit high speed mode command to 8901A (decimal 106) */
        ibwrt(gpibBd, "j", 1);
        /* MUST make the 8901A unlisten, send unlisten & untalk */
        ibcmd(gpibBd, "? _", 2);
        /* build command string with 3 bytes of data (CAMAC W1-W24) */
        rw[0] = (char) f;
        rw[1] = (char) a;
        rw[2] = (char) n;
        rw[3] = (char) 0;
        rw[4] = (char) 0;
        rw[5] = (char) 0;
        /* address 8901A to listen */
        ibcmd(gpibBd, pcTalk, 2);
        /* send command string to the 8901A (F, A, N, D1, D2, D3) */
        ibwrt(gpibBd, rw, 6);
        /* address 8901A to talk to execute the CAMAC cycle */
        ibcmd(gpibBd, pcList, 2);
        /* read a block of data from the 8901A */
        ibrd(gpibBd, (char *) buffer, count);
        /* number of 16 bit values read */
        retval = ibcnt / 2;
    } else if (ccType == 6010) {
        /* 6010 max of 8192 bytes it can block transfer */
        if (count > 8192)
            count = 8192;
        /* build command string to perform block read (CAMAC W1-W16) */
        sprintf(rw, "n = %2 d;
                f = %2 d;
                a = %2 d;
                cbls = %4 d;
                rb", n, f, a, count);
        /* address 6010 to listen */
        ibcmd(gpibBd, pcTalk, 2);
        /* send command string to the 6010 */
        ibwrt(gpibBd, rw, 27);
        /* address 6010 to talk */
        ibcmd(gpibBd, pcList, 2);
        /* read a block of data from the 6010 */
        ibrd(gpibBd, (char *) buffer, count);
        /* number of 16 bit values read */
        retval = ibcnt / 2;
    }
    return (retval);
}

/*
Purpose: Returns the CAMAC Q and X response from the last camo or cami functions.
Returns: Q response in bit 1, X response in bit 0
*/
int qxResp(void) {
    return qxRet;
}

