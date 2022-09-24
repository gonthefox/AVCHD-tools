#!/usr/bin/env python3

from ctypes import *
from struct import *
import io, sys, codecs
import logging, argparse, datetime

FORMAT = "%s-%s-%s %s:%s:%s"
p_timecode = 0
p_diff  = 0
ip_diff = 0


class Packet(BigEndianStructure):
    _fields_ = (
        ('Timecode', c_uint32),
        ('Bulk',c_ubyte * 188))

class MDPM(BigEndianStructure):
    _fields_ = (
        ('Tag', c_ubyte * 4),
        ('Unknown1', c_ubyte),
        ('Year_and_Month_tag', c_ubyte),
        ('Unknown2', c_ubyte),                
        ('Year',  c_uint8 * 2),
        ('Month', c_uint8),
        ('Day_and_Time_tag', c_ubyte),
        ('Day', c_uint8),
        ('Hour', c_uint8),
        ('Minute', c_uint8),
        ('Second', c_uint8)
    )

def findMDPMTag(timecode, buffer):

    packet = Packet()
    mdpm   = MDPM()
    
    buffer.seek(packet.Timecode)
    buffer.readinto(mdpm)

    offset = 0
    global p_timecode
    global ip_diff
    global p_diff
    
    while offset<192:

        buffer.seek(offset)
        buffer.readinto(mdpm)
        
        if mdpm.Tag[0] == 0x4d and mdpm.Tag[1] == 0x44 and mdpm.Tag[2] == 0x50 and mdpm.Tag[3] == 0x4d:

            diff = timecode - p_timecode
            if diff < 0:
                diff = 1073741823 - p_timecode + timecode

            ip_diff = ip_diff+p_diff
            it_diff  = ip_diff/27000000.0*1000

            second  = int(it_diff/1000)%60
            minute = int(it_diff/60000)%60
            hour = int(it_diff/3600000)%24
            msec = int(it_diff)%1000
            
#            print("%d %d %d" % (timecode, p_timecode, diff),end="")
            print("%8d %02d:%02d:%02d,%03d" % (it_diff,hour,minute,second,msec),end="")            
#            print(" %02x%02x %02x%02x" % (mdpm.Tag[0],mdpm.Tag[1],mdpm.Tag[2],mdpm.Tag[3]),end="")
#            print(" (%03d)" % offset,end="")

            print(" %02x%02x" % (mdpm.Year[0],mdpm.Year[1]),end="")
            print("-%02x" % (mdpm.Month),end="")
            print("-%02x" % (mdpm.Day),end="")            
            print(" %02x" % (mdpm.Hour),end="")
            print(":%02x" % (mdpm.Minute),end="")
            print(":%02x" % (mdpm.Second),end="")            
            print()
            p_timecode=timecode
            p_diff = diff
            break
        
        offset += 1

    return

# process each packet
def process(data):

    packet = Packet()
    
    buffer = io.BytesIO(data)
    buffer.readinto(packet)

    # Arrival Timecode consists of 30 bit
    timecode = packet.Timecode & 0x3fffffff
    findMDPMTag(timecode, buffer)
    
    return

if __name__ == '__main__':

    data = None
    with open('sample.m2ts','rb') as file:

        data = file.read(sizeof(Packet()))        
        while data:
            
            data = file.read(sizeof(Packet()))
            process(data)

    exit()
