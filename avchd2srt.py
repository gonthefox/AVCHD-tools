#!/usr/bin/env python3

from ctypes import *
from struct import *
import io, sys, codecs
import logging, argparse, datetime

FORMAT  = "%02s:%02s:%02s,%03s --> %02s:%02s:%02s,%03s"
FORMAT2 = "%04s-%02s-%02s %02s:%02s:%02s"
find_MDPM = None
p_timecode = 0
p_recdatetime = 0
normalizedTimecode = 0

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

def changeDetect(recdatetime):
    global p_recdatetime

    if recdatetime == 0:
        return True
    
    if recdatetime != p_recdatetime:
        p_recdatetime = recdatetime
        return True
    else:
        return None


def decodeTimecode(normTimecode):

    hour   = int(normTimecode/(27000000*60*60))
    minute = int((normTimecode-hour*27000000*60*60)/(27000000*60))
    second = int((normTimecode-hour*27000000*60*60-minute*60*27000000)/(27000000))
    msec   = int((normTimecode-hour*27000000*60*60-minute*60*27000000-second*27000000)/27000)

    check  = hour*27000000*3600+minute*27000000*60+second*27000000+msec*27000
    
    return '{0:02d}'.format(hour),'{0:02d}'.format(minute),\
        '{0:02d}'.format(second),'{0:03d}'.format(msec)


def timecodeInteg(timecodeDiff):
    global normalizedTimecode
    
    normalizedTimecode += timecodeDiff 

    return normalizedTimecode
    
def timecodeDiff(timecode):

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


            recdatetime = decodeMDPM(mdpm)

            if changeDetect(recdatetime):
                dtimecode = decodeTimecode(timecodeInteg(timecodeDiff(timecode)))
                return dtimecode,recdatetime

            break
        
        offset += 1

    return


def setInitialTimecode(timecode):
    global initial_timecode, p_timecode
    p_timecode = timecode

#    print("initial timecode:%d" % p_timecode)
    
    return

# process each packet
def process(data):

    packet = Packet()
    
    buffer = io.BytesIO(data)
    buffer.readinto(packet)

    # Arrival Timecode consists of 30 bit
    timecode = packet.Timecode & 0x3fffffff
    retval = findMDPMTag(timecode, packet.Bulk)
    if retval:
        return retval
    else:
        return None


if __name__ == '__main__':

    data = None
    dtimecode = "('00', '00', '00', '000')"
    ddatetime = None
    index = 0
    with open('sample.m2ts','rb') as file:

        # for the first packet
        data = file.read(sizeof(Packet()))
        process(data)

        # the second packet and after
        while data:
            data = file.read(sizeof(Packet()))
            retval = process(data)
            if retval:
                timecode, datetime = retval
                if ddatetime:
                    index = index+1
#                    print(dtimecode,timecode,ddatetime)
                    dhh,dmm,dss,dms = dtimecode
                    hh,  mm, ss, ms = timecode
                    year,month,day,hour,minute,second = ddatetime
                    print("%d" % index)
                    print(FORMAT  % (dhh,dmm,dss,dms,hh,mm,ss,ms))
                    print(FORMAT2 % (year,month,day,hour,minute,second))
                    print()
                dtimecode = timecode
                ddatetime = datetime
            
    exit()
