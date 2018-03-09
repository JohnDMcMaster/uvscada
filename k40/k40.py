#!/usr/bin/env python 
'''
This script comunicated with the K40 Laser Cutter.

Copyright (C) 2017 Scorch www.scorchworks.com

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''
import usb.core
import usb.util
from egv import egv
import time
import traceback

##############################################################################

#### Status query responses ####
S_OK  = 206
# Buffer full
S_BUFF_FULL = 238
# CRC error
S_CRC_ERR = 207
S_UNK1 = 236
# after failed initialization followed by succesful initialization
S_UNK2 = 239 

#######################
PKT_STATUS   = [160]
PKT_UNLOCK  = [166,0,73,83,50,80,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,166,15]
PKT_HOME    = [166,0,73,80,80,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,166,228]
PKT_ESTOP  =  [166,0,73,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,166,130]

class K40_CLASS:
    def __init__(self):
        self.dev        = None
        self.n_timeouts = 1
        self.timeout    = 200   # Time in milliseconds
        self.write_addr = 0x2   # Write address
        self.read_addr  = 0x82  # Read address
        self.read_length= 168

    def get_status(self):
        # "get_hello"

        #255, 206, 111, 8, 19, 0
        cnt=0
        while cnt<self.n_timeouts:
            try:
                self.send_packet(PKT_STATUS)
                break
            except:
                raise
                pass
            cnt=cnt+1
        if cnt == self.n_timeouts:
            msg = "Too Many Transmission Errors (%d Status Timeouts)" %(cnt)
            raise StandardError(msg)
                
        response = None
        read_cnt = 0
        while response is None and read_cnt < 10:
            try:
                response = self.dev.read(self.read_addr,self.read_length,self.timeout)
            # Timeout
            except usb.core.USBError:
                response = None
                read_cnt = read_cnt + 1
        
        DEBUG = False
        if response != None:
            if DEBUG:
                if int(response[0]) != 255:
                    print "0: ", response[0]
                elif int(response[1]) != 206: 
                    print "1: ", response[1]
                elif int(response[2]) != 111:
                    print "2: ", response[2]
                elif int(response[3]) != 8:
                    print "3: ", response[3]
                elif int(response[4]) != 19: #Get a 3 if you try to initialize when already initialized
                    print "4: ", response[4]
                elif int(response[5]) != 0:
                    print "5: ", response[5]
                else:
                    print ".",
            
            if response[1]==S_OK          or \
               response[1]==S_BUFF_FULL or \
               response[1]==S_CRC_ERR   or \
               response[1]==S_UNK1   or \
               response[1]==S_UNK2:
                return response[1]
            else:
                return None
        else:
            return None

    
    def unlock_rail(self):
        self.send_packet(PKT_UNLOCK)

    def e_stop(self):
        self.send_packet(PKT_ESTOP)

    def home_position(self):
        self.send_packet(PKT_HOME)

    def reset_usb(self):
        self.dev.reset()

    def release_usb(self):
        if self.dev:
            usb.util.dispose_resources(self.dev)
        self.dev = None
    
    #######################################################################
    #  The one wire CRC algorithm is derived from the OneWire.cpp Library
    #  The latest version of this library may be found at:
    #  http://www.pjrc.com/teensy/td_libs_OneWire.html
    #######################################################################
    def OneWireCRC(self,line):
        crc=0
        for i in range(len(line)):
            inbyte=line[i]
            for j in range(8):
                mix = (crc ^ inbyte) & 0x01
                crc >>= 1
                if (mix):
                    crc ^= 0x8C
                inbyte >>= 1
        return crc
    #######################################################################
    def none_function(self,dummy=None):
        #Don't delete this function (used in send_data)
        pass
        print 'GUI: ', dummy 
    
    def send_data(self,data,update_gui=None,stop_calc=None,passes=1,preprocess_crc=True):
        print 'send data begin'
        if stop_calc == None:
            stop_calc=[]
            stop_calc.append(0)
        if update_gui == None:
            update_gui = self.none_function

        blank   = [166,0,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,166,0]
        packets = []
        packet  = blank[:]
        cnt=2
        len_data = len(data)
        for j in range(passes):
            if j == 0:
                istart = 0
            else:
                istart = 1
                data[-4]
            if passes > 1:
                if j == passes-1:
                    data[-4]=ord("F")
                else:
                    data[-4]=ord("@")
                
            for i in range(istart,len_data):
                if cnt > 31:
                    packet[-1] = self.OneWireCRC(packet[1:len(packet)-2])
                    if not preprocess_crc:
                        self.send_packet_w_error_checking(packet,update_gui,stop_calc)
                        update_gui("Sending Data to Laser = %.1f%%" %(100.0*float(i)/float(len_data)))
                    else:
                        packets.append(packet)
                        update_gui("Calculating CRC data and Generate Packets: %.1f%%" %(100.0*float(i)/float(len_data)))
                    packet = blank[:]
                    cnt = 2
                    
                    if stop_calc[0]==True:
                        raise StandardError("Action Stopped by User.")
                packet[cnt]=data[i]
                cnt=cnt+1
        packet[-1]=self.OneWireCRC(packet[1:len(packet)-2])
        if not preprocess_crc:
            self.send_packet_w_error_checking(packet,update_gui,stop_calc)
        else:
            packets.append(packet)
        packet_cnt = 0

        print 'send data sending'
        for line in packets:
            update_gui()
            self.send_packet_w_error_checking(line,update_gui,stop_calc)
            packet_cnt = packet_cnt+1.0
            update_gui( "Sending Data to Laser = %.1f%%" %( 100.0*packet_cnt/len(packets) ) )
        ##############################################################
        print 'send data done'


    def send_packet_w_error_checking(self,line,update_gui=None,stop_calc=None):
        print 'send w/ error start'
        timeout_cnt = 0
        crc_cnt     = 0
        while timeout_cnt < self.n_timeouts and crc_cnt < self.n_timeouts:
            try:
                self.send_packet(line)
            except:
                raise
                msg = "USB Timeout #%d" %(timeout_cnt)
                print 'USB timeout'
                update_gui(msg)
                timeout_cnt=timeout_cnt+1
                continue

            ######################################
            response = self.get_status()
            
            print 'response', response
            if response == S_BUFF_FULL:
                print 'buffer full'
                while response == S_BUFF_FULL:
                    response = self.get_status()
                break #break and move on to next packet
            elif response == S_CRC_ERR:
                msg = "Data transmission (CRC) error #%d" %(crc_cnt)               
                update_gui(msg)
                crc_cnt=crc_cnt+1
                continue
            elif response == None:
                msg = "Controller board is not responding."                
                update_gui(msg)
                break #break and move on to next packet
            else: #response == S_OK:
                break #break and move on to next packet

            #elif response == S_UNK1:
            #    msg = "Something UNKNOWN_1 happened: response=%s" %(response)
            #    break #break and move on to next packet
            #elif response == S_UNK2:
            #    msg = "Something UNKNOWN_2 happened: response=%s" %(response)
            #    break #break and move on to next packet
            #else:
            #    msg = "Something Undefined happened: response=%s" %(response)
            #    break #break and move on to next packet
            
        if crc_cnt >= self.n_timeouts:
            msg = "Too Many Transmission Errors (%d CRC Errors)" %(crc_cnt)
            update_gui(msg)
            raise StandardError(msg)
        if timeout_cnt >= self.n_timeouts:
            msg = "Too Many Transmission Errors (%d Timeouts)" %(timeout_cnt)
            update_gui(msg)
            raise StandardError(msg)
        if stop_calc[0]:
            msg="Action Stopped by User."
            update_gui(msg)
            raise StandardError(msg)
        

    def send_packet(self,line):
        print 'sending packet'
        self.dev.write(self.write_addr,line,self.timeout)
        print 'sent'

    def rapid_move(self,dxmils,dymils):
        data=[]
        egv_inst = egv(target=lambda s:data.append(s))
        egv_inst.make_move_data(dxmils,dymils)
        self.send_data(data)
    
    def initialize_device(self,verbose=False):
        try:
            self.release_usb()
        except:
            pass
            raise
        # find the device
        self.dev = usb.core.find(idVendor=0x1a86, idProduct=0x5512)
        if self.dev is None:
            raise StandardError("Laser USB Device not found.")
            #return "Laser USB Device not found."

        # set the active configuration. With no arguments, the first
        # configuration will be the active one
        try:
            self.dev.set_configuration()
        except:
            raise
            #return "Unable to set USB Device configuration."
            raise StandardError("Unable to set USB Device configuration.")

        # get an endpoint instance
        cfg = self.dev.get_active_configuration()
        intf = cfg[(0,0)]
        ep = usb.util.find_descriptor(
            intf,
            # match the first OUT endpoint
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)
        if ep == None:
            raise StandardError("Unable to match the USB 'OUT' endpoint.")
        # ?
        self.dev.ctrl_transfer(         0x40,      177,   0x0102,        0,                      0, 2000)

        #PKT_STATUS_sync()
        
    def hex2dec(self,hex_in):
        #format of "hex_in" is ["40","e7"]
        dec_out=[]
        for a in hex_in:
            dec_out.append(int(a,16))
        return dec_out
    

if __name__ == "__main__":
    k40=K40_CLASS()
    run_laser = False

    k40.initialize_device(verbose=False)

    #k40.initialize_device()
    print (k40.get_status())
    #print k40.reset_position()
    #print k40.unlock_rail()
    print ("DONE")
    
    # origin at lower left
    # this also seems to crash it...
    # also its not running the init sequence
    # hmm

    def move(self,dxmils,dymils, laser_on):
        data=[]
        print 'Making egv'
        egv_inst = egv(target=lambda s:data.append(s))
        print 'Making data'
        egv_inst.make_move_data(dxmils,dymils, laser_on=laser_on)
        print 'Sending data'
        self.send_data(data)
        print 'Data sent'

    #ON    = 68 #ord("D")=68
    #OFF   = 85 #ord("U")=85

    if 1:
        for _i in xrange(3):
            move(k40, 200,200, True)
            move(k40, -200,-200, True)
            move(k40, 200,200, False)
            move(k40, -200,-200, False)

    '''
    Each loop taking about 135-138 ms, even with the print
    Often it will stall on the very first move
    Manual has EMI note
    Possibly they 
    Additionally, a ^C causes some weird issues and doesn't actually exit
    Review their exception handling logic
    '''
    if 0:
        iters = 0
        while True:
            iters += 1
            for coords in [(200, 200), (-200, -200), (-200, 200), (200, -200)]:
                dx, dy = coords
                print
                print
                print
                print iters
                tstart = time.time()
                #move(k40, dx, dy, False)
                response = k40.get_status()
                print 'response', response
                continue
                dt = time.time() - tstart
                print 'dt: %3.3f' % dt
                if dt > 0.140:
                    raise Exception("RT failure")

    move(k40, 1, 1, False)
    move(k40, -1,-1, False)
