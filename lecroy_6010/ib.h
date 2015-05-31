/*
http://www.interface.co.jp/catalog/prdchelp/English/gpf4301n/488.1/ibfind.html

The ibfind function opens and initializes the board. 
   
When the opening the device is successfully completed, return the device handle. 
Otherwise, this function returns INVALID_HANDLE_VALUE(-1). 
*/
int ibfind(
        //Specifies the board to open and initialize. For board name and RSW1 value, refer to the "5.1.7 Board Name and RSW1 Value."        
        char *board);

/*
http://www.interface.co.jp/catalog/prdchelp/English/gpf4301n/488.1/ibonl.html

The ibonl function closes or initializes the board or device. 
*/
int ibonl(
        //Specifies the board  handle or device handle obtained by the ibfind  or ibdev function. 
        int 	ud,
        //Specifies the board or device to initialize or close as follows. 
	    int 	option);

/*
http://www.interface.co.jp/catalog/prdchelp/English/gpf4301n/488.1/ibtmo.html

The ibtmo function changes or disables the time-out period. 
*/
int ibtmo(
        //Specifies the board handle or device handle obtained by the ibfind or ibdev function.
        int 	ud,
	    //Specifies the time-out period.
	    int 	value);

/*
http://www.interface.co.jp/catalog/prdchelp/English/gpf4301n/488.1/ibsic.html

The ibsic function asserts the IFC line for 100 µs and more.
   
To call this function, the specified board must be System Controller. 
*/
int ibsic(
        //Specifies the board handle obtained by the ibfind function.    
        int ud);

/*
http://www.interface.co.jp/catalog/prdchelp/English/gpf4301n/488.1/ibcmd.html

The ibcmd function sends the GP-IB commands (multiline interface message). 
The size of the transferred command bytes is returned to global variable, ibcntl.
  
GP-IB commands are used for GP-IB state configuration. 
This function does not send the command for the device. For the command, use the ibwrt function.
*/
int ibcmd(
        //Specifies the device handle obtained by the ibfind function.
	    int     ud,
	    //Points to a variable to store the command to send.
	    //void    *buffer,
	    char    *buffer,
	    //Specifies the size of command to send. 
	    int     count);

/*
http://www.interface.co.jp/catalog/prdchelp/English/gpf4301n/488.1/ibwrt.html

The ibwrt function sends the data to the specified device.
    
The size of the actual send data is returned to the global variable, ibcntl.  
*/
int ibwrt(
        /*
        Specifies the board handle or device handle obtained by the ibfind or ibdev function. 
        The operation depends on the type of handle.
	    <Board Handle>
	    To call this function, addressing for the specified device needs beforehand. 
       	
	    <Device Handle>
	    Addressing for the specified device need not to call this function. 
	    This function recognized board as Listener and device as Talker.
        */
	    int 	ud,
	    //Points to a buffer to send the data.
	    //void 	*buffer,
	    char 	*buffer,
	    //Specifies the size of send data. 
	    int 	count);


/*
http://www.interface.co.jp/catalog/prdchelp/English/gpf4301n/488.1/ibrd.html

The ibrd function receives the data from the specified device.
     
The process is successfully completed when the receive data reaches the specified size the data or END is received. 
Actual size of the receive data is returned to global variable, ibcnt.  
*/
int ibrd(
        /*
        Specifies the device handle or board handle obtained by the ibdev or ibfind function. The operation depends on the type of handle.
	    <Board Handle>
        To call the ibrd function, addressing for the specified device needs beforehand.
	        <Device Handle>
        Addressing for the specified device need not to call the ibrd function. The ibrd function recognized board as Listener and device as Talker.
        */
        int ud,
        //Points to a buffer to store the received data.
        //void     	*buffer,
        char *buffer,
        //Specifies the size of the received data. 
        int count);

//N/A
extern int ibsta;

//N/A
extern int iberr;

//N/A
extern int ibcnt;

