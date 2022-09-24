#!/usr/bin/env python3

from ctypes import *
from struct import *
import io, sys, codecs
import logging, argparse, datetime

FORMAT = "%s-%s-%s %s:%s:%s"
find_MDPM = None
p_timecode = 0

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

def normalizeTimecode(timecode):
    global p_timecode, initial_timecode

#    print("tc:%d ptc:%d" % (timecode, p_timecode))
    
    if timecode < p_timecode:
        d_timecode = (2**30-1-p_timecode) + timecode
    else:
        d_timecode = timecode-p_timecode
        
    p_timecode = timecode
    return d_timecode

def decodeMDPM(mdpm):
    return  '{0[0]:02x}{0[1]:02x}'.format(mdpm.Year), '{0:02x}'.format(mdpm.Month), '{0:02x}'.format(mdpm.Day), \
            '{0:02x}'.format(mdpm.Hour), '{0:02x}'.format(mdpm.Minute), '{0:02x}'.format(mdpm.Second)

def findMDPMTag(timecode, bulk):

    global find_MDPM
    
    buffer = io.BytesIO(bulk)    

    mdpm   = MDPM()
    offset = 0

    while offset<192:

        buffer.seek(offset)
        buffer.readinto(mdpm)
        
        if mdpm.Tag[0] == 0x4d and mdpm.Tag[1] == 0x44 and mdpm.Tag[2] == 0x50 and mdpm.Tag[3] == 0x4d:

            if not find_MDPM:
                setInitialTimecode(timecode)
            find_MDPM = True
            print("%8d" % normalizeTimecode(timecode),end=" ")
            print(decodeMDPM(mdpm))
            break
        
        offset += 1

    return


def setInitialTimecode(timecode):
    global initial_timecode, p_timecode
    p_timecode = timecode

    print("initial timecode:%d" % p_timecode)
    
    return

# process each packet
def process(data):

    packet = Packet()
    
    buffer = io.BytesIO(data)
    buffer.readinto(packet)

    # Arrival Timecode consists of 30 bit
    timecode = packet.Timecode & 0x3fffffff
    findMDPMTag(timecode, packet.Bulk)
    
    return

if __name__ == '__main__':

    data = None
    with open('sample.m2ts','rb') as file:

        # for the first packet
        data = file.read(sizeof(Packet()))
        process(data)

        # the second packet and after
        while data:
            
            data = file.read(sizeof(Packet()))
            process(data)

    exit()
