//Based on: http://cdn.teledynelecroy.com/files/manuals/8901aman.pdf

/*
/TEXT
Purpose: Header file for all files that use functions from camgpib.c
Language: C
/CODE
*/
/* ———————————————————————————————————— */
extern void caminit(int addr, int type);
extern void camo(int n, int f, int a, long d);
extern long cami(int n, int f, int a);
extern int camibk16(int n, int f, int a, int count, int *buffer);
extern int qxResp(void);

