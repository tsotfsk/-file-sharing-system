import hashlib 
import json
import asyncio
import aiosqlite3
import os
import time
import datetime
import yaml
import chardet
# #keep alive

# daemon_do_list

#  writer.get_extra_info("sockname")
#  daemon_dict[b4.conf['name']] = {'host':sock_host, 'port':b4.conf['port'], 'time'= time.time()}
# if __name__ == "__main__":
#     pass


# async def daemon_do_list_host(writer,reader,dst):
#     #改变dst得到绝对路径dst
#     ls_dict = {}
#     with os.scandir(dst) as it: #不是异步的
#         for entry in it:
#             st = entry.stat()
#             log.debug{''}
#     data = json.dumps(ls_dist).encode("utf-8")
    
#     functools.partial(scandir,dst)

#am 注册 成员关系的维护

# rq = json.dumps('a\nb\n\n').encode('utf-8')
# rs = json.loads(rq.decode('utf-8'))
# print(rs)
# rs = rs.split('\n')
# print(rq,rs)

# a = 'a a a a a'.split(' ')
# b = json.dumps(a).encode('utf-8')
# c = json.loads(b.decode('utf-8'))

# print(a,b,c)




# 字段	定义	请求必选	应答必选	有效取值
# V	版本号		            No	        1.0
# A	认证码		            No	        SHA256( secret + I )
# I	命令本身		        No	
# E	错误代码	No		                参考HTTP错误码
# L	内容长度	No	        No	        十进制字节长度
# F 内容格式                            b or json
# C 内容本身	No	        No	




async def selectDB(execStr,value):
    result = []
    conn = await aiosqlite3.connect('catalog.db')
    print ("Opened database successfully")
    c = await conn.cursor()
    await c.execute(execStr,value)
    print("Table catalog selected successfully")
    await conn.commit()
    re = await c.fetchall()
    for lines in re:
        result.append({'filename':lines[0],'filetype':lines[1],'ctime':lines[2],'mtime':lines[3],'hostname':lines[4],'hostaddr':lines[5],'rootname':lines[6],'lAddress':lines[7]})   
    await conn.close()
    print(result)
    return result

async def insertDB(execStr,value):
    conn = await aiosqlite3.connect('catalog.db')
    print ("Opened database successfully")
    c = await conn.cursor()
    await c.execute(execStr,value)
    print("Table catalog inserted successfully")
    await conn.commit()
    await conn.close()

async def createDB():
    conn = await aiosqlite3.connect('catalog.db')
    print ("Opened database successfully")
    c = await conn.cursor()
    await c.execute('''CREATE TABLE catalog
        (
        filename        TEXT    NOT NULL,
        filetype        TEXT    NOT NULL,
           ctime        TEXT    NOT NULL,
           mtime        TEXT    NOT NULL,
        hostname        TEXT    NOT NULL,
        hostaddr        TEXT    NOT NULL,
        rootname        TEXT    NOT NULL,
        lAddress        TEXT    NOT NULL,
        PRIMARY KEY     (hostname,rootname,filename));''')
    print("Table catalog created successfully")
    await conn.commit()

async def updateDB(execStr, value):
    conn = await aiosqlite3.connect('catalog.db')
    print ("Opened database successfully")
    c = await conn.cursor()
    await c.execute(execStr, value)
    await conn.commit()
    await conn.close()
    print("Table catalog updated successfully")
    await conn.close()

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

# asyncio.run(createDB())
# filesList = []
# hostname = 'h1'
# hostaddr = '127.0.0.1:60000'
# lAddress = 'None'
# for rootname,dirs,files in os.walk('C:/Users/咸鱼/Desktop/pns/h1root'):
#     rootname = rootname.replace('\\','/')
#     for filename in dirs:
#         fpath = rootname+'/' + filename
#         ctime = getFileCreateTime(fpath)
#         mtime = getFileModifyTime(fpath)
#         filetype = 'd' 
#         filesList.append({'filename':filename,'filetype':filetype,'ctime':ctime,'mtime':mtime,'hostname':hostname,'hostaddr':hostaddr,'rootname':rootname,'lAddress':lAddress})
#     for filename in files:
#         fpath = rootname+'/' + filename
#         ctime = getFileCreateTime(fpath)
#         mtime = getFileModifyTime(fpath)
#         filetype = 'f'
#         filesList.append({'filename':filename,'filetype':filetype,'ctime':ctime,'mtime':mtime,'hostname':hostname,'hostaddr':hostaddr,'rootname':rootname,'lAddress':lAddress})
# for item in filesList:
#     print('{:>8} {:>8} {:>20} {:>20} {:>8} {:>20} {:>10} {:>10} '.format(item['filename'],item['filetype'],item['ctime'],item['mtime'],item['hostname'],item['hostaddr'],item['rootname'],item['lAddress']))    

# f= open()

# inst = ['//h2/c/d/e/c.1.txt']
# loc = inst[0].replace('//','').split('/')[1:-1]
# froot = ''
# for item in  loc:
#     froot += '/'+item
# print(froot)

os.remove('C:/Users/咸鱼/Desktop/pns/test/a/good.txt')
