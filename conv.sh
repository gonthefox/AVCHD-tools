#!/bin/sh
AVCHD_FILE=$1
MP4_FILE=$2
python avchd2srt.py -a ${AVCHD_FILE} -r recdatetime.srt -o srt
ffmpeg -i ${AVCHD_FILE} -i recdatetime.srt -map 0:v -map 0:a -map 1 -metadata:s:s:0 language=eng -c:v copy -c:a aac -c:s mov_text ${MP4_FILE}
RECDATETIME=$(python avchd2srt.py -a ${AVCHD_FILE} -r recdatetime.srt)
exiftool -CreateDate="${RECDATETIME}" -DateTimeOriginal="${RECDATETIME}" ${MP4_FILE}






    


