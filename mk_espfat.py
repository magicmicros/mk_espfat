
"""

FAT Filesystem Generator for ESPxx filesystems
----------------------------------------------

Generates empty FAT filesystems from 1 to 15 MB.
These can then be mounted on Linux and OSX (and possibly Windows) systems,
files copied in and they can then be programmed onto the ESP flash with esptool.


Looking at the ESP partition schemes (the FAT based ones) in tools/partitions
you will see a line like:
   ffat,     data, fat,     0x410000,0xBF0000,
This indicates a FAT filesystem, starting at 0x410000, length 0xBF0000 bytes

This is the entry for a 12.5MB FAT filesystem
To generate a file for this, simply run this program and enter 0xBF0000 for
partition size and a filesystem will be generated.
A filesystem of any size between 1 and 15 MB can be created.

To mount the image in OSX:
  hdiutil attach filesystem.img


To program the filesystem to the ESP, use this command:
  python esptool.py -p <DEV> -b <BAUD> write_flash <PART_START+0x1000> filesystem.img
Adjust <DEV>, <BAUD> and PART_START to your system.

NOTE! The filesystem is programmed at partition start + 0x1000

Example:
  python esptool.py -p /dev/tty.usbserial-ANZ1TFY5 -b 460800 write_flash 0x411000 filesystem.img


Have fun!


Author: Jesper Hansen
Date: 2020-04-17
Updated: 2022-07-03, Phil Hilger (PeerGum)

"""


import uuid

# DOS/FAT Boot sector start
fsheader = [0xeb, 0xfe, 0x90, 0x4d, 0x53, 0x44, 0x4f, 0x53, 0x35, 0x2e, 0x30, 0x00, 0x10, 0x01, 0x01, 0x00,
            0x01, 0x00, 0x02, 0xd6, 0x0b, 0xf8, 0x02, 0x00, 0x3f, 0x00, 0xff, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x80, 0x00, 0x29, 0x00, 0x00, 0x21, 0x00, 0x4e, 0x4f, 0x20, 0x4e, 0x41,
            0x4d, 0x45, 0x20, 0x20, 0x20, 0x20, 0x46, 0x41, 0x54, 0x20, 0x20, 0x20, 0x20, 0x20, 0x00, 0x00]

bootsector = bytearray(fsheader) + bytearray([0] * (0x1000-64))     # bootsector filler to 0x1000
zerosector = bytearray([0] * 0x1000)                                # 0x1000 of 0x00
fatsector = bytearray([0] * 0x1000)                                 # 0x1000 of ox00, which will be patched later
ffsector = bytearray([255] * 0x1000)                                # 0x1000 of 0xFF

# say hello
print("\nFAT Filesystem Generator for ESP\n")
print("Enter partition size (in hex or decimal) :")
size = input()
if size[0:2] == "0x":
	fssize = int(size,16)
else:
	fssize = int(size)

# sensibility check
if fssize < (1*1024*1024) or fssize > (15*1024*1024):
    print("Come on, be serious!")
    exit();

print("\nGenerating filesystem")

# number of sectors
max_sectors = int(fssize/0x1000)

# sectors for BOOT, FAT, DIR e.t.c.
if max_sectors > 2730:  # 2730 = number of FAT12 entries in 4096 bytes
  res_sectors = 8
  bootsector[22] = 2    # patch in # of sectors per FAT
else:
  res_sectors = 7
  bootsector[22] = 1    # patch in # of sectors per FAT

# adjust max sectors
max_sectors -= res_sectors

# generate a unique ID for this disk
id = uuid.uuid4().int & 0xFFFFFFFF
id1 = id

# patch in at offset 39, VOL_ID
for i in range(4):
    bootsector[39+i] = id & 255
    id >>= 8

# patch in boot sector signature
bootsector[510] = 0x55
bootsector[511] = 0xAA

# patch in FAT start
fatsector[0] = 0xF8
fatsector[1] = 0xFF
fatsector[2] = 0xFF


# patch in this at offset 19
bootsector[19] = max_sectors & 255
bootsector[20] = (max_sectors >> 8) & 255

# show some info
print("Size    : " + str(fssize) + " bytes")
print("Sectors : " + str(max_sectors))
print("Serial  : " + str(id1))

# create new file
f = open('filesystem.img', 'wb')

# write out bootsector to file
f.write(bootsector)

# write out first FAT sector to file
f.write(fatsector)

# write out remaining FAT and DIR sectors
for i in range(res_sectors-3):
    f.write(zerosector)

# fill rest of filesystem with FF
for i in range(max_sectors):
    f.write(ffsector)

# that's all folks
f.close()
