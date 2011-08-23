/**
	@file decode.cpp
	@author Andrew D. Zonenberg
	@brief AmScope camera data decoder, v0.1
	
	This file is dual licensed under GPL v3+ and a BSD-style license (included below for clarity).
	
	Copyright (c) 2011 Andrew D. Zonenberg
	All rights reserved.
	
	Redistribution and use in source and binary forms, with or without modifi-
	cation, are permitted provided that the following conditions are met:
	
	   * Redistributions of source code must retain the above copyright notice
	     this list of conditions and the following disclaimer.
	
	   * Redistributions in binary form must reproduce the above copyright
	     notice, this list of conditions and the following disclaimer in the
	     documentation and/or other materials provided with the distribution.
	
	   * Neither the name of the author nor the names of any contributors may be
	     used to endorse or promote products derived from this software without
	     specific prior written permission.
	
	THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR IMPLIED
	WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
	MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN
	NO EVENT SHALL THE AUTHOR BE HELD LIABLE FOR ANY DIRECT, INDIRECT,
	INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
	NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
	DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
	THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
	(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
	THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include <stdio.h>

#define IMG_BUFFER_SIZE 1000*1024
//#define IMG_BUFFER_SIZE 900*1024
#define BUFFER_SIZE 1024
#define IMG_WIDTH 640lu
#define IMG_HEIGHT 480lu
#define FRAME_SIZE (IMG_WIDTH*IMG_HEIGHT)

struct pixel
{
	unsigned char r;
	unsigned char g;
	unsigned char b;
};

float crosscorrelation(unsigned char* a, unsigned char* b, int size);

int main(int argc, char* argv[])
{
	if(argc < 2)
	{
		printf("usage: decode file.bin\n");
		return 0;
	}
	
	//Read the file
	FILE* fp = fopen(argv[1], "rb");
	if(!fp)
	{
		printf("Failed to open %s\n", argv[1]);
		return -1;
	}
	unsigned char* buf = new unsigned char[IMG_BUFFER_SIZE * sizeof(pixel)];
	for(int i=0; i<IMG_BUFFER_SIZE; i += BUFFER_SIZE)
	{
		if(BUFFER_SIZE != fread(buf+(i*sizeof(pixel)), sizeof(pixel), BUFFER_SIZE, fp))
		{
			printf("fread error\n");
			return -1;
		}
	}
	fclose(fp);
	pixel* pixels = new pixel[FRAME_SIZE];
		
	//Each frame is 307200 pixels
	//these start positions are for rgb_wire
	int framestarts[]=
	{
		  -1407,		//incomplete, not processed
		 305793,		//clean but dark
		 612993,		//clean
		 920193,		//dropped data, middle section lost sync
		1226881,		//dropped data but looks good otherwise
		1534593,
	/*	1842049,
		2144385,
		2452609,
		2758273,*/
	};
	
	//Decode the image
	for(unsigned int iframe=2; iframe < (sizeof(framestarts) / sizeof(framestarts[0])); iframe++)
	{
		printf("processing frame %u\n", iframe);
		if(framestarts[iframe] < 0)
		{
			printf("skipping frame (negative start pos)\n");
			continue;
		}
			
		float miny = 255, maxy = 0;
			
		unsigned char* image = buf + framestarts[iframe];
		unsigned char* last_scanline = image;
		int last_shift = 0; 
		int total_shift = 0;
		for(unsigned int y=0; y<IMG_HEIGHT; y+=2)
		{
			pixel* row = pixels + (y*IMG_WIDTH);
			pixel* row2 = row + IMG_WIDTH;
			unsigned char* scanline = image + total_shift + y*IMG_WIDTH;
			unsigned char* scanline2 = scanline + IMG_WIDTH;			
				
			//Only check for shifts if we didn't just have some
			bool dropped = false;
			int offset = 0;
			if( ((y - last_shift) > 5) && (y < IMG_HEIGHT - 5) )
			{
				//all shifts seem to be multiples of 64 so only check these
				float mc = 0;
				for(unsigned int k=0; k<IMG_WIDTH; k += 2)
				{
					float c = crosscorrelation(last_scanline, scanline+k, IMG_WIDTH*2);
					if(c > mc)
					{
						mc = c;
						offset = k;
					}
				}
				
				if(offset != 0)
				{
					//offset += 2*IMG_WIDTH + 1;
					
					//TODO: insert padding
				
					printf("detected %d bad bytes in frame %d at scanline %d\n", offset, iframe, y);
					total_shift += offset;
					//scanline += offset;
					last_shift = y;
					dropped = true;
				}
			}
			
			//save this scanline for reference
			last_scanline = scanline;
			
			//Process the pixels
			for(unsigned int x=0; x<IMG_WIDTH; x += 2)
			{
				//Black out if this line got corrupted
				//TODO: attempt recovery
				if(dropped)
				{
					row[x].r = 0;
					row[x].g = 0;
					row[x].b = 0;
					
					row[x+1].r = 0;
					row[x+1].g = 0;
					row[x+1].b = 0;
					
					row2[x].r = 0;
					row2[x].g = 0;
					row2[x].b = 0;
					
					row2[x+1].r = 0;
					row2[x+1].g = 0;
					row2[x+1].b = 0;
				}
				else
				{
					//Decode color values (Bayer filter, GBRG)
					int r = scanline2[x];
					int b = scanline[x+1];
					int g = scanline[x];
					int g2 = scanline2[x+1];
					
					//White balance so (136, 171, 129) becomes neutral
					//This is just a random background pixel chosen from a typical decoded frame, automatic or manual balancing
					//would be good here!
					r *= 0.941176471;
					g *= 0.748538012;
					b *= 0.992248062;
					
					//Store min/max pixel values for leveling (standard NTSC weights)
					float y = r*0.2989 + g*0.5870 + b*0.1140;
					if(miny > y) miny = y;
					if(maxy < y) maxy = y;
									
					//TODO: better demosaicing algorithm?
					row[x].r = row[x+1].r = row2[x].r = row2[x+1].r = r;
					row[x].b = row[x+1].b = row2[x].b = row2[x+1].b = b;
					row[x].g = row[x+1].g = g;
					row2[x].g = row2[x+1].g = g2;
				}
			}
		}
		
		//Once the entire image is done, normalize intensities to full range
		//This should be done more properly by adjusting exposure on the camera etc
		//but it will help for now
		float dy = maxy - miny;
		float yscale = 255 / dy;
		for(unsigned int y=0; y<IMG_HEIGHT; y++)
		{
			pixel* row = pixels + (y*IMG_WIDTH);
			for(unsigned int x=0; x<IMG_WIDTH; x ++)
			{
				pixel& pix = row[x];
				
				float r = (pix.r - miny) * yscale;
				float g = (pix.g - miny) * yscale;
				float b = (pix.b - miny) * yscale;
				
				if(r < 0) r = 0;
				if(g < 0) g = 0;
				if(b < 0) b = 0;
				if(r > 255) r = 255;
				if(g > 255) g = 255;
				if(b > 255) b = 255;
				
				pix.r = r;
				pix.g = g;
				pix.b = b;
			}
		}
		
		//Save output
		char fname[1024];
		snprintf(fname, 1023, "testdata/out_%d.ppm", iframe);
		fp = fopen(fname, "wb");
		if(!fp)
		{
			printf("Failed to open PPM file %s for writing", fname);
			return -1;
		}
		fprintf(fp, "P6 %lu %lu %d\n", IMG_WIDTH, IMG_HEIGHT, 255);
		fwrite(pixels, sizeof(pixel), FRAME_SIZE, fp);
		fclose(fp);
		
		break;
	}
		
	//clean up
	delete[] pixels;
	delete[] buf;
}

/**
	@brief computes normalized cross-correlation between two scanlines
 */
float crosscorrelation(unsigned char* a, unsigned char* b, int size)
{
	float result = 0;
	for(int i=0; i<size; i++)
	{
		float na = a[i];
		float nb = b[i];
		na /= 255;
		nb /= 255;
		
		result += na*nb;
	}
	return result;
}
