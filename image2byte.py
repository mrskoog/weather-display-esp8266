from PIL import Image
import sys
import math
import re

if len(sys.argv) == 1:
	print("image2byte <path> <size x> <size y> <bitsize>")
	exit()
path = sys.argv[1]
x = int(sys.argv[2])
y = int(sys.argv[3])
bitsize = int(sys.argv[4]) - 1
size = x * y

im = Image.open(path)
indata = list(im.getdata())
outdata = [0] * int(math.ceil(float(size)/float(bitsize)))
strdata = ""

for i, pixel in enumerate(indata):
	if pixel[0] == 255 and pixel[2] == 255 and pixel[2] == 255: #look for white pixels
		strdata += "-"
	else:
		pos=i%(bitsize)
		outdata[int(math.floor(i/bitsize))] |= 1<<pos
		strdata += "*"
	if i%x == (x-1):
		strdata += "\n"

print("image representation:")
print(strdata)
print("data array:")
print(outdata)

with open("imagedata.py","w") as f:
	f.write("imagedata = [")
	for i, item in enumerate(outdata):
		if i != 0:
			f.write(",")
		f.write(str(item))
	f.write("]")
print("saved to imagedata.py")


