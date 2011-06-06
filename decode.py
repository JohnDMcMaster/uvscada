import Image
import sys
import time

width = 640
height = 480

f = open("image.bin", "r")
image = Image.new("RGB", (width, height), "White")

for y in range(0, height):
	for x in range(0, width):
		# putpixel(self, (x, y), (R, G, B))
		R = ord(f.read(1))
		G = ord(f.read(1))
		B = ord(f.read(1))
		image.putpixel((x, y), (R, G, B))

image.show()
time.sleep(3)


