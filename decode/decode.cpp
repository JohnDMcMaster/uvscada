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
int maximize_crosscorrelation(unsigned char* a, unsigned char* b, int size, int minshift, int maxshift);

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
		  -1407,		//skipped, not processed
		 305793,		//clean but dark
		 612993,		//clean
		 918273,		//dropped data from here on
		1227521,
		1534593,
		1842049,
		2144385,
		2452609,
		2758273,
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
			
		unsigned char* image = buf + framestarts[iframe];
		unsigned char* last_scanline = image;
		//int last_shift = 0; 
		int total_shift = 0;
		for(unsigned int y=0; y<IMG_HEIGHT; y+=2)
		{
			pixel* row = pixels + (y*IMG_WIDTH);
			pixel* row2 = row + IMG_WIDTH;
			unsigned char* scanline = image + total_shift + y*IMG_WIDTH;
			unsigned char* scanline2 = scanline + IMG_WIDTH;			
				
			/*
			//Only check for shifts if we didn't just have some
			//Most of the boundary numbers here are totally random but seem to work
			//TODO: fix this - it gets a lot more complex now that we're reading color data!
			bool dropped = false;
			int offset = 0;
			if( ((y - last_shift) > 5) && (y < IMG_HEIGHT - 5) )
			{
				//Detect dropped data
				offset = maximize_crosscorrelation(last_scanline, scanline, IMG_WIDTH*2, 5, IMG_WIDTH - 64);
				if(offset != 0)
				{
					printf("detected %d bad bytes in frame %d at scanline %d, interpolating from previous scanline\n", offset, iframe, y);
					
					//Print out the bad data
					printf("Missing data: \n");
					for(int k=0; k<offset; k++)
					{
						printf("%02x ", scanline[k] & 0xff);
						if( (k % 16) == 15)
							printf("\n");
					}
					printf("\n");
					
					
					total_shift += offset;
				//	scanline += total_shift;
					last_shift = y;
					dropped = true;
				}
			}
			*/	
			
			//nope, all is good - decode the pixels (2D bayer filter)
			for(unsigned int x=0; x<IMG_WIDTH; x += 2)
			{
				int r = scanline2[x];
				int b = scanline[x];
				int g1 = scanline[x+1];
				int g2 = scanline2[x+1];		
				
				//TODO: better demosaicing algorithm for G interpolation?
				row[x].r = row[x+1].r = row2[x].r = row2[x+1].r = r;
				row[x].b = row[x+1].b = row2[x].b = row2[x+1].b = b;
				row[x].g = row[x+1].g = g1;
				row2[x].g = row2[x+1].g = g2;
			}
			
			//save this scanline for reference
			last_scanline = scanline;
		}
		
		//Save output
		char fname[1024];
		snprintf(fname, 1023, "out_%d.ppm", iframe);
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

int maximize_crosscorrelation(unsigned char* a, unsigned char* b, int size, int minshift, int maxshift)
{
	float mc = 0;
	int mv = 0;
	for(int i=0; i<maxshift; i++)
	{
		float c = crosscorrelation(a, b+i, size);
		if(c > mc)
		{
			mc = c;
			mv = i;
		}
	}
	
	//todo: figure out why we have high correlation in first few
	if(mv < minshift)
		return 0;
	
	return mv;
}
