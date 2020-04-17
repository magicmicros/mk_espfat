# mk_espfat

## FAT Filesystem Generator for ESPxx filesystems


## Description
This small Python program will allow you to create a FAT filesystem for an ESP32 or ESP8266 of any size between 1 and 15 MB.

This filesystem can be mounted on OSX or Linux (and Windows, I assume) and files copied to it.
Then it can easily be transfered to an ESPxx with the regular esptool.

I came in the need for this, using the Arduino IDE for ESP, and swithing filesystems from SPIFFS to FAT and realizing there was no simple way create a filesystem image for FAT, as there was for SPIFFS.
I could find no tools for this, so I wrote this.


## How it works

The program creates an empty filesystem, with the necessary structures and values in place.
The size of the filesystem generated, is given at execution time and should be based off the partition size for the FAT filesystem in the ESP partitioning file.

An example of an partitioning file for the 3MB APP/9MB FATFS scheme for a 16MB ESP32 device:
```
# Name,   Type, SubType, Offset,  Size, Flags
nvs,      data, nvs,     0x9000,  0x5000,
otadata,  data, ota,     0xe000,  0x2000,
app0,     app,  ota_0,   0x10000, 0x300000,
app1,     app,  ota_1,   0x310000,0x300000,
ffat,     data, fat,     0x610000,0x9F0000,
```

This reserves 0x9F0000 bytes, starting at address 0x610000.

The value 0x610000 is passed to the mk_espfat.py program and it will create a filesystem image of this size, 
ready for mouting and copying files and/or to program onto the ESP.


## How to use it

### Create the filesystem

Simply run the python program with:
python mk_espfat.py

It will ask for the size of the partition, in which the filesystem should be located.
Use the value from the partitioning scheme you will be using.
A file, named `filesystem.img` will be created.

### Add files

(Optional)
Mount it on your main system.
On OSX, this is done with:
`hdiutil attach filesystem.img`

Then copy files as with any other disk.

### Program the ESP 

Finally program the new filesystem back onto the ESP with:

`python esptool.py -p <DEV> -b <BAUD> write_flash <PART_START+0x1000> filesystem.img`
Adjust <DEV>, <BAUD> and PART_START to your system.

Note that the filesystem is programming at partition start + 0x1000.
For more info about that, see Internals below.

That's it, reboot your ESP and all files should be accessible.


## Quick test
After creating the filesystem, copying some files onto it and uploading the filesystem to the ESPxx, load and run the FAT_test.ino program to see the partition info and a list of files on the filesystem.
Remember to set the Partition Scheme correctly to match the values used when creating the filesystem.


## Internals

The program is pretty simple, as it doesn't have to deal with the "regular" difficulties in creating a FAT filesystem.
A lot of options are predefined, and just a couple of values needs to be patched to adapt for various file system sizes.

### FAT basics

Here's some very simple FAT basics.
Note that it describes the FAT12 filesystem and is specific to the way the filesystem is configured and used on an ESP system.
The details go way deeper and for full information see the *Microsoft FAT Specification* in this repository.

FAT means File Allocation Table. 
It's a relatively simple, but effective way of working with files.
Every file has a directory index, and a pointer to an entry in the FAT table. The entry is the start of a linked list of entries, that can be used to find a part of the file in the data area.
Each part is what's called a cluster, but for simplicity, we'll just refer to sectors, as it's the same thing in a ESP FAT filesystem. 
A sector is a 4096 chunk of data. (Normally, a sector is 512 bytes, but for performance and space reasons, a sector is 4096 bytes on ESP systems).

There are 3 basic kind of FAT systems. 
FAT12, FAT16 and FAT32, the name referring to how many bits each FAT entry will use.
All ESP FAT filesystems are FAT12, meaning 12 bits or 1.5 bytes per FAT entry.

A FAT filesystem consist of 4 areas :
```
Name            #of sectors Offset              Description

Boot Sector     1           0x0000              A sector with basic information about the filesystem
FAT             1 or 2      0x1000              1 or more sectors with FAT tables 
Directory       4           0x2000 or 0x3000    Directory Entries
Data            -           0x6000 or 0x7000    Data area
```


#### The boot sector

The boot sector contains basic information about the layout of the filesystem.
Some of the fields are not used anymore, FAT goes back a long time and can be used on anything for 360k floppies to GB sized hard disks.

Here's the first 64 bytes of a bootsector. (There is ususally more, but this is all we need on the ESP):
This is taken from the "standard" 12.5 MB ESP32 filesystem.
```
00000000  eb fe 90 4d 53 44 4f 53  35 2e 30 00 10 01 01 00  |...MSDOS5.0.....|
00000010  01 00 02 d6 0b f8 02 00  3f 00 ff 00 00 00 00 00  |........?.......|
00000020  00 00 00 00 80 00 29 00  00 21 00 4e 4f 20 4e 41  |......)..!.NO NA|
00000030  4d 45 20 20 20 20 46 41  54 20 20 20 20 20 00 00  |ME    FAT     ..|
```
Here's a description of the contents and the "official" field names:

```
BS_jmpBoot      0       3   Jump instruction to boot code.
BS_OEMName      3       8   OEM Name Identifier. Can be set by a FAT implementation to any desired value.
BPB_BytsPerSec  11      2   Count of bytes per sector. (512, 1024, 2048 or 4096).
BPB_SecPerClus  13      1   Number of sectors per allocation unit.(1, 2, 4, 8, 16, 32, 64, or 128).
BPB_RsvdSecCnt  14      2   Number of reserved sectors in the reserved region
BPB_NumFATs     16      1   The count of file allocation tables (FATs) on the volume (1 or 2).
BPB_RootEntCnt  17      2   The count of 32-byte directory entries in the root directory.
BPB_TotSec16    19      2   (OLD) Total count of sectors on the volume.
BPB_Media       21      1   0xF8 is the standard value for “fixed” (nonremovable) media.
BPB_FATSz16     22      2   Count of sectors occupied by one FAT.
BPB_SecPerTrk   24      2   Sectors per track for interrupt 0x13.
BPB_NumHeads    26      2   Number of heads for interrupt 0x13.
BPB_HiddSec     28      4   Count of hidden sectors preceding the partition that contains this FAT volume.
BPB_TotSec32    32      4   (NEW) 32-bit total count of sectors on the volume.
BS_DrvNum       36      1   Interrupt 0x13 drive number (0x80 or 0).
BS_Reserved1    37      1   Reserved. Set value to 0x0.
BS_BootSig      38      1   Extended boot signature. Set value to 0x29.
BS_VolID        39      4   Volume serial number.
BS_VolLab       43      11  Volume label.
BS_FilSysType   54      8   One of the strings “FAT12 ”, “FAT16 ”, or “FAT”.
-               62      448 Set to 0x00
Signature_word  510     2   Set to 0x55 (@ offset 510) and 0xAA (@ offset 511)
-               512     All remaining bytes in sector set to 0x00 (for sectors > 512 bytes).
```

And finally, here are the corresponding values from the 64 bytes above:
```
BS_jmpBoot      0       3   EB FE 90
BS_OEMName      3       8   "MSDOS5.0"
BPB_BytsPerSec  11      2   4096
BPB_SecPerClus  13      1   1
BPB_RsvdSecCnt  14      2   1
BPB_NumFATs     16      1   1
BPB_RootEntCnt  17      2   512
BPB_TotSec16    19      2   3030
BPB_Media       21      1   0xF8
BPB_FATSz16     22      2   2           (2, because there is > 2730 sectors)
BPB_SecPerTrk   24      2   63
BPB_NumHeads    26      2   255
BPB_HiddSec     28      4   0
BPB_TotSec32    32      4   0
BS_DrvNum       36      1   0x80
BS_Reserved1    37      1   0
BS_BootSig      38      1   0x29
BS_VolID        39      4   0x00210000
BS_VolLab       43      11  "NO NAME    "
BS_FilSysType   54      8   "FAT     "
-               62      448 0
Signature_word  510     2   0x55, 0xAA
-               512     0
```

#### The FAT

The FAT is simple a translation table, or index table that tells where to find the file data.
On the ESP filesystems it's pretty simple, as each entry (or rather, it's location in the table) refers to a sector within the data area, containing a 4k block of the file.
At the same time, the entry also links to the next FAT entry (and corresponding data). Finally the last entry is marked by a special value.
Here's the most important values:

`0x000  indicates a free entry.`
`0x002 to MAX indicates an allocated entry. The value of the entry is the number of the next entry in the chain.`
`0xFF8 to 0xFFE are reserved values.`
`0xFFF indicates an allocated entry and also the end of a chain.`

The first entries of an empty FAT is always  (the rest is filled with zeroes):
`f8 ff ff 00 00 00 00 00 00 00 00 00 00 00 00 00`

On a FAT12 filesystem, this means there are two (reserved) entries (enties 0 and 1) (3 bytes) and they are 0xFF8 and 0xFFF.
This explains why FAT numbers start at 2.
If a file was now created that was 6kB long, the FAT would be updated to this :
`f8 ff ff 03 0F FF 00 00 00 00 00 00 00 00 00 00`

This show:
1. That the first sector of the file is at an offset into the data area of (0x002 - 2)*4096 bytes.
2. That the next FAT entry is 0x003
3. That the second sector of the file is at an offset into the data area of (0x003 - 2)*4096 bytes.
4. That the second sector is the last sector of the file.



#### The Directory

This is a complex matter, especially when long filenames are involved.
But it's not really of importance to this program so, refer to the  *Microsoft FAT Specification* for details.

#### The data area

Simply the area where filedata is stored.
Again, refer to the  *Microsoft FAT Specification* for details.


