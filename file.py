import time
import os

def TimeStampToTime(timestamp):
    timeStruct = time.localtime(timestamp)
    return time.strftime('%Y-%m-%d %H:%M:%S',timeStruct)

def getFileModifyTime(filePath):
    t = os.path.getmtime(filePath)
    return TimeStampToTime(t)

def getFileCreateTime(filePath):
    t = os.path.getctime(filePath)
    return TimeStampToTime(t)

def getFileSize(filePath):
    fsize = os.path.getsize(filePath)
    return fsize