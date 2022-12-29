#!/usr/bin/env python
import os, argparse,re
import glob
import avchd2srt as avchd
import datetime
from PIL import Image, ExifTags

FFMPEG = """
ffmpeg -i %s -i recdatetime.srt -map 0:v -map 0:a -map 1 -metadata:s:s:0 language=eng -c:v copy -c:a aac -c:s mov_text %s
"""

EXIFTOOL = 'exiftool -CreateDate="%s" -DateTimeOriginal="%s" %s -overwrite_original_in_place'

DateTimeOriginal = 36867

def getDateTimeOriginal(dict):
    return dict.get(DateTimeOriginal)

def getDateTimeDirname(dict):
    return re.sub(r'([0-9]{4}):([0-9]{2}):([0-9]{2}).+$',r'\1-\2-\3',getDateTimeOriginal(dict))

if __name__ == '__main__':

    parser= argparse.ArgumentParser(description="AVCHDTOOL")

    parser.add_argument('-i', '--indir',    help='directory which AVCHD files are contained')
    parser.add_argument('-o', '--outdir',   help='directory which MP4 files are generated in')
    parser.add_argument('-t', '--title',    help='title of the clip')
    args = parser.parse_args()

    if not os.path.exists(args.indir):
        raise Exception("Input directory not found.")


    avchdfiles = []
    dup = 0
    for dirpath, dirname, filenames in os.walk(args.indir, topdown=True):
        print(dirpath)
        for filename in [f for f in filenames if os.path.splitext(f)[1].casefold() in {".m2ts"}]:
            print(filename)
            if re.search(r'\(\d\)',filename):
                dup = dup+1
                print("duplicate found at %s" % filename)
            else:
                avchdfiles.append(dirpath+"/"+filename)

    total = len(avchdfiles)

    print("%d avchdfiles to be processed. %d duplicates removed." % (len(avchdfiles),dup))

    for index, avchdfile in enumerate(avchdfiles):
        now = datetime.datetime.now()
        print(now.strftime("%Y-%m-%d %H:%M:%S"))

        
        # AVCHD fileを開く
        recdatetime = None
        print("%d/%d %s" % (index+1, total, avchdfile))
        with open(avchdfile,'rb') as file:
            data = file.read()
            recdatetime = avchd.getRecdatetime(data, 0)

        print("RECDATETIME: %s" % recdatetime)
        
        # 撮影日付時刻を取得しMP4ファイルが存在するか確認する
        year    = recdatetime[0:4]
        month   = recdatetime[5:7]
        day     = recdatetime[8:10]

        print("%s-%s-%s" % (year,month,day))

        filepath = args.outdir+year+"-"+month+"-"+day+"/"
        mp4file = filepath+os.path.splitext(os.path.basename(avchdfile))[0]+".mp4"        

        print("%s" % mp4file)

        # MP4ファイルが存在していれば変換処理済みなのでスキップ
        # MP4ファイルが存在していなければ、未処理なので変換を実行
        if not os.path.exists(mp4file):

            if not os.path.exists(filepath):
                os.makedirs(filepath)
            
            avchd.rdfile = open("recdatetime.srt",'w')
            avchd.process(data, 0)
            avchd.rdfile.close()
            
            os.system(FFMPEG % (avchdfile, mp4file))
            print(recdatetime)
            os.system(EXIFTOOL % (recdatetime, recdatetime, mp4file))
#            os.system('rm %s' % mp4file+"_original")
        else:
            print("file exists: %s. skipped." % mp4file)
