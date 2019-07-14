import sys
import asyncio
import socket
import aiosqlite3
import os
import yaml
import json
import hashlib
import time
import datetime
import functools

#读取命令行参数
cmd = sys.argv
cmdDict={}
cmdDict['mode'] = cmd[1]
cmdDict['config'] = cmd[2]
try:
    cmdDict['inst'] = cmd[3:]
except Exception:
    print('error')

hostList = ['h1']#tracker维护一个主机列表

#配置文件记录到这个类中
class pnsConfig:
    def __init__(self):
        self.name = data['name']
        self.port = int(data['port'])
        self.address = '127.0.0.1'
        self.root = data['root']
        self.secret = str(data['secret'])
        if 'tracker' in data:
            tracker = data['tracker'].split(':')
            self.trackerAddr = tracker[0]
            self.trackerPost = int(tracker[1])
        else:
            self.trackerPost = 60000
            self.trackerAddr = '127.0.0.1'

#打包一下request包
def requestPackage(I,*C):
    header = {}
    header['V'] = '1.0'
    inst = ''
    for item in I:
        inst += item +' '
    code = pns.secret + inst
    sha256 = hashlib.sha256()
    sha256.update(code.encode('utf-8'))
    header['A'] = sha256.hexdigest()
    header['I'] = inst
    header['F'] = 'json'
    re = [header]
    try:
        content = C[0]
        re.append(content)
    except Exception:
        pass
    return  re

#打包一下response包
def responsePackage(E,*C):
    header = {}
    header['E'] = E
    header['F'] = 'json'
    re = [header]
    try:
        content = C[0]
        re.append(content)
    except Exception:
        pass
    return  re

#读配置文件
f = open(cmdDict['config'] , 'r')
cfg = f.read()
data = yaml.load(cfg)
pns = pnsConfig()

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

#数据库插入操作
async def insertDB(execStr,value):
    conn = await aiosqlite3.connect('catalog.db')
    print ("Opened database successfully")
    c = await conn.cursor()
    try:
        await c.execute(execStr,value)
        print("Table catalog inserted successfully")
        await conn.commit()
    except Exception:
        pass
    await conn.close()

#数据库创建操作
async def createDB():
    conn = await aiosqlite3.connect('catalog.db')
    print ("Opened database successfully")
    c = await conn.cursor()
    try:
        await c.execute('''CREATE TABLE catalog
            (
            filename        TEXT    NOT NULL,
            filetype        TEXT    NOT NULL,
            ctime           TEXT    NOT NULL,
            mtime           TEXT    NOT NULL,
            hostname        TEXT    NOT NULL,
            hostaddr        TEXT    NOT NULL,
            rootname        TEXT    NOT NULL,
            lAddress        TEXT    NOT NULL,
            PRIMARY KEY     (hostname,rootname,filename));''')
        print("Table catalog created successfully")
        await conn.commit()
    except Exception:
        pass


#更新数据库
async def updateDB(execStr, value):
    conn = await aiosqlite3.connect('catalog.db')
    print ("Opened database successfully")
    c = await conn.cursor()
    try:
        await c.execute(execStr, value)
        await conn.commit()
    except Exception:
        pass
    await conn.close()
    print("Table catalog updated successfully")

#删除内容
async def deleteDB(execStr, value):
    conn = await aiosqlite3.connect('catalog.db')
    print ("Opened database successfully")
    c = await conn.cursor()
    try:
        await c.execute(execStr, value)
        await conn.commit()
    except Exception:
        pass
    await conn.close()
    print("Table catalog deleted successfully")

#得到目录下的所有子目录以及文件
def getFilesList(filesList):
    hostname = pns.name
    hostaddr = '127.0.0.1'+ ':' + str(pns.port)
    lAddress = 'None'
    rootpath = str(pns.root.encode('gbk').decode())
    for root,dirs,files in os.walk(rootpath):
        root = root.replace('\\','/')
        rootname = root.replace(rootpath,'')
        for filename in dirs:
            fpath = root+'/' + filename
            ctime = getFileCreateTime(fpath)
            mtime = getFileModifyTime(fpath)
            filetype = 'd' 
            filesList.append({'filename':filename,'filetype':filetype,'ctime':ctime,'mtime':mtime,'hostname':hostname,'hostaddr':hostaddr,'rootname':rootname,'lAddress':lAddress})
        for filename in files:
            fpath = root+'/' + filename
            ctime = getFileCreateTime(fpath)
            mtime = getFileModifyTime(fpath)
            filetype = 'f'
            filesList.append({'filename':filename,'filetype':filetype,'ctime':ctime,'mtime':mtime,'hostname':hostname,'hostaddr':hostaddr,'rootname':rootname,'lAddress':lAddress})

#shell该做什么
async def shellDo():
    #从命令行读到的指令
    inst = cmdDict['inst']
    loop = asyncio.get_running_loop()
    if inst[0] == 'rg':
        filesList = []
        getFiles = functools.partial(getFilesList, filesList)
        await loop.run_in_executor(None, getFiles)
        reader, writer = await asyncio.open_connection(pns.trackerAddr, pns.trackerPost)#与服务器建立连接
        rMessage = requestPackage(inst,filesList)#打包成请求格式
        message = json.dumps(rMessage).encode('utf-8')

        #发送读到的指令给tracker
        writer.write(message)

        #从tracker读到一个反馈
        bulk = await reader.read(65536)
        bulk = json.loads(bulk.decode('utf-8')) 
        print('Received Feedback: {}'.format(bulk[0]['E']))
        print('Shell done.')
        writer.close()
        await writer.wait_closed()

    elif inst[0] in ['ls','ln','md','rm']:
        if '//' in inst[1] and inst[0] == 'rm':
            reader, writer = await asyncio.open_connection('127.0.0.1', pns.port)#与服务器建立连接
        elif '//' in inst[1] and inst[0] == 'md':
            reader,writer = await asyncio.open_connection('127.0.0.1', pns.port)#与服务器建立连接
        else:
            reader, writer = await asyncio.open_connection(pns.trackerAddr, pns.trackerPost)#与服务器建立连接
        rMessage = requestPackage(inst,'hello')#打包成请求格式
        message = json.dumps(rMessage).encode('utf-8')

        #发送读到的指令给tracker
        print(f'Shell Send Inst: {message!r}')
        writer.write(message)

        #从tracker读到一个反馈
        bulk = await reader.read(65536)
        bulk = json.loads(bulk.decode('utf-8'))

        if inst[0] == 'ls':
            if inst[1] == '//':#列出所有主机列表
                print('Received Feedback: {}'.format(bulk[1]))
            elif '//' in inst[1] or '/' in inst[1] :#列出主机某一路径下的目录
                print('Received Feedback:')
                print('{:>8} {:>8} {:>20} {:>20} {:>8} {:>20} {:>10} {:>10} '.format('filename','filetype','ctime','mtime','hostname','hostaddr','rootname','lAddress'))
                for item in bulk[1]:
                    print('{:>8} {:>8} {:>20} {:>20} {:>8} {:>20} {:>10} {:>10} '.format(item['filename'],item['filetype'],item['ctime'],item['mtime'],item['hostname'],item['hostaddr'],item['rootname'],item['lAddress']))        
            else: #指令出错            
                print('Received Feedback: {}'.format(bulk[0]['E']))
        else:
            print('Received Feedback: {}'.format(bulk[0]['E']))
        print('Shell done.')
        writer.close()
        await writer.wait_closed()     
    elif inst[0] in ['cp','mv']:
        srcHostname = '//'+ inst[1].split('//')[1].split('/')[0]
        dstHostname = '//'+ inst[2].split('//')[1].split('/')[0]
        rMessage =  requestPackage(['ls',srcHostname])
        message = json.dumps(rMessage).encode('utf-8')
        reader, writer = await asyncio.open_connection(pns.trackerAddr, pns.trackerPost)#与服务器建立连接

        #发送ls src给tracker
        print(f'Shell Send Inst: {message!r}')
        writer.write(message)
        #从tracker读到一个反馈
        srcbulk = await reader.read(65536)
        srcbulk = json.loads(srcbulk.decode('utf-8'))
        print('Received srcAddr: {}'.format(srcbulk[1][0]['hostaddr']))
        srcIp = srcbulk[1][0]['hostaddr'].split(':')[0]
        srcPost = int(srcbulk[1][0]['hostaddr'].split(':')[1])

        #发送ls dst给tracker
        rMessage =  requestPackage(['ls',dstHostname])
        message = json.dumps(rMessage).encode('utf-8')
        print(f'Shell Send Inst: {message!r}')
        writer.write(message)

        #从tracker读到一个反馈
        dstbulk = await reader.read(65536)
        dstbulk = json.loads(dstbulk.decode('utf-8'))
        print('Received srcAddr: {}'.format(dstbulk[1][0]['hostaddr']))
        dstIp = dstbulk[1][0]['hostaddr'].split(':')[0]
        dstPost = int(dstbulk[1][0]['hostaddr'].split(':')[1])

        print('Shell done.')
        writer.close()
        await writer.wait_closed()

        #两次ls得到了物理地址,接下来就进行cp操作
        reader, writer = await asyncio.open_connection(dstIp, dstPost)
        inst[1] = inst[1].replace(srcHostname,'//' + srcIp +':' + str(srcPost))
        inst[2] = inst[2].replace(dstHostname,'//' + dstIp +':' + str(dstPost))

        #将cp 发送给src  要从 dst 拿到一个数据
        rMessage = requestPackage(inst)#打包成请求格式
        message = json.dumps(rMessage).encode('utf-8')
        print(f'Shell Send Inst: {message!r}')
        writer.write(message)

        #从tracker读到一个反馈
        bulk = await reader.read(65536)
        bulk = json.loads(bulk.decode('utf-8'))
        print('Received Feedback: {}'.format(bulk))


async def rgDo(reader,writer,inst,files):
    for file in files:
        execStr = 'insert into catalog values (?,?,?,?,?,?,?,?)'
        value = (file['filename'],file['filetype'],file['ctime'],file['mtime'],file['hostname'],file['hostaddr'],file['rootname'],file['lAddress'])
        await insertDB(execStr,value)
    bulk = responsePackage('200') 
    bulk = json.dumps(bulk).encode('utf-8')
    writer.write(bulk)      

#ls操作
async def lsDo(reader,writer,inst):
    if inst[0] == '//':#列出所有主机列表
        bulk = responsePackage('200',hostList)
        print(f'Send: {hostList!r}')
    elif '//' in inst[0]:#列出主机某一路径下的目录
        p1 = inst[0].split('//')[1]
        p2 = p1.split('/')
        hname = p2[0]
        rname = ''
        rList = p2[1:]
        for item in rList:
            rname += '/'+ item
        execStr,value = 'select * from catalog where hostname = ? and rootname = ?',(hname,rname)
        re = await selectDB(execStr,value)
        bulk = responsePackage('200',re)
    elif inst[0] == '/':
        execStr,value = 'select * from catalog where lAddress != ?',('None',)
        re = await selectDB(execStr,value)
        bulk = responsePackage('200',re)        
    elif '/' in inst[0]: #列出某个逻辑目录下的内容     
        execStr,value = 'select * from catalog where lAddress = ?',(inst[0],)
        re = await selectDB(execStr,value)
        bulk = responsePackage('200',re)
    else: #指令出错
        bulk = responsePackage('400')
    bulk = json.dumps(bulk).encode('utf-8')
    writer.write(bulk)

async def lnDo(reader,writer,inst):
    if inst[1][0] == '/' and '//' not in inst[1]:#src 符合格式要求
        if '//' in inst[0]:#dst 符合格式要求
            p1 = inst[0].split('//')[1]
            p2 = p1.split('/')
            lAddr = inst[1]
            hname = p2[0]
            fname = p2[-1]
            rList = p2[1:-1]
            rname = ''
            for item in rList:
                rname += '/'+ item
            execStr, value = 'update catalog set lAddress = ? where hostname = ? and rootname = ? and filename = ?',(lAddr,hname,rname,fname)
            print(execStr, value)
            await updateDB(execStr,value) 
            bulk = responsePackage('200') 
    else:
        bulk = responsePackage('400')
    bulk = json.dumps(bulk).encode('utf-8')
    writer.write(bulk)        
        
async def mdDo(reader,writer,inst):
    if '//' in inst[0]:#在当前主机下新建一个目录
        fpath = pns.root
        loc = inst[0].replace('//','').split('/')[1:]
        fdir = ''
        for item in loc:
            fdir += '/' +item  
        os.mkdir((fpath + fdir).encode('gbk'))
        bulk = responsePackage('200')  
    elif '/' in inst[0]: #列出某个逻辑目录下的内容
        p1 = inst[0].split('/')[1:]
        hname = 'None'
        rname = 'None'
        fname = p1[-1]
        ftype = 'd'
        ctime = TimeStampToTime(time.time())
        mtime = TimeStampToTime(time.time())
        haddr = 'None'
        lAddr = ''
        lList = p1[0:-1]
        for item in lList:
            lAddr += '/'+ item
        execStr = 'insert into catalog values (?,?,?,?,?,?,?,?)'
        value = (fname,ftype,ctime,mtime,hname,haddr,rname,lAddr)
        await insertDB(execStr,value)
        bulk = responsePackage('200')    
    else:
        bulk = responsePackage('400') 
    bulk = json.dumps(bulk).encode('utf-8')
    writer.write(bulk) 

async def rmDo(reader,writer,inst):
    if '//' in inst[0]:#是本主机下的目录
        fpath = pns.root
        loc = inst[0].replace('//','').split('/')[1:]
        fdir = ''
        for item in loc:
            fdir += '/' +item  
        try:
            os.remove((fpath + fdir).encode('gbk'))
        except Exception:
            try:
                os.rmdir((fpath + fdir).encode('gbk'))
            except Exception:
                pass
        
        #删除数据库中对应文件
        filereader,filewriter = await asyncio.open_connection(pns.trackerAddr, pns.trackerPost)   
        rMessage = requestPackage(['test','//'],{'delete':inst[0],'hostname':pns.name})
        message = json.dumps(rMessage).encode('utf-8')
        filewriter.write(message)

        #读到的文件
        bulk = await filereader.read(100)
        bulk = json.loads(bulk.decode('utf-8'))
        print('Received File: {}'.format(bulk))

        filewriter.close()
        await filewriter.wait_closed()

        bulk = responsePackage('200') 
    elif '/' in inst[0]: #逻辑目录
        p1 = inst[0].split('/')[1:]
        fname = p1[-1]
        lAddr = ''
        lList = p1[0:-1]
        for item in lList:
            lAddr += '/'+ item
        execStr = 'update catalog set lAddress = ? where lAddress like ? and filename = ?'
        value = ('None',lAddr,fname)
        await updateDB(execStr,value)
        execStr = 'update catalog set lAddress = ? where lAddress like ?'
        value = ('None','/' + fname + lAddr+'%')
        await updateDB(execStr,value)
        bulk = responsePackage('200')    
    else:
        pass
    bulk = json.dumps(bulk).encode('utf-8')
    writer.write(bulk) 

async def mvDo(reader,writer,inst):
    if len(inst) == 1: #说明是接受指令的,那么就需要查找所要文件,然后发送.. 
        addr = inst[0].replace('//','').split('/')[1:]
        fdir = ''
        for item in addr:
            fdir += '/' +item 
        fpath = pns.root
        f = open((fpath + fdir).encode('gbk'),'r')
        data = f.read()
        bulk = responsePackage('200',data)
        bulk = json.dumps(bulk).encode('utf-8')
        writer.write(bulk) 

    elif len(inst) == 2: #说明是未来要发送指令的
        addr = inst[0].replace('//','').split('/')[0].split(':')
        dstIp = addr[0]
        dstPost = addr[1]
        fname =  inst[0].replace('//','').split('/')[-1]

        fpath = pns.root
        loc = inst[1].replace('//','').split('/')[1:]
        fdir = ''
        for item in loc:
            fdir += '/' +item
        print(fpath + fdir + '/'+fname)
        f = open((fpath + fdir + '/'+fname).encode('gbk'),'wb')
        f.close()

        #索要文件
        filereader,filewriter = await asyncio.open_connection(dstIp, dstPost)   
        rMessage = requestPackage(['cp',inst[0]])
        message = json.dumps(rMessage).encode('utf-8')
        filewriter.write(message)

        #读到的文件
        bulk = await filereader.read(65536)
        bulk = json.loads(bulk.decode('utf-8'))
        f = open((fpath + fdir + '/'+fname).encode('gbk'),'wb')
        print('Received File: {}'.format(bulk))
        f.write(bulk[1].encode('utf-8'))
        f.close()

        #删除文件
        rMessage = requestPackage(['rm',inst[0]])
        message = json.dumps(rMessage).encode('utf-8')
        filewriter.write(message)

        #读到回复
        bulk = await filereader.read(65536)
        bulk = json.loads(bulk.decode('utf-8'))
        print('Received Feedback: {}'.format(bulk))

        filewriter.close()
        await filewriter.wait_closed()

        #返回shell ok
        bulk = responsePackage('200')
        bulk = json.dumps(bulk).encode('utf-8')
        writer.write(bulk)

async def cpDo(reader,writer,inst):
    if len(inst) == 1: #说明是接受指令的,那么就需要查找所要文件,然后发送.. 
        addr = inst[0].replace('//','').split('/')[1:]
        fdir = ''
        for item in addr:
            fdir += '/' +item 
        fpath = pns.root
        f = open((fpath + fdir).encode('gbk'),'r')
        data = f.read()
        bulk = responsePackage('200',data)
        bulk = json.dumps(bulk).encode('utf-8')
        writer.write(bulk) 

    elif len(inst) == 2: #说明是未来要发送指令的
        addr = inst[0].replace('//','').split('/')[0].split(':')
        dstIp = addr[0]
        dstPost = addr[1]
        fname =  inst[0].replace('//','').split('/')[-1]

        fpath = pns.root
        loc = inst[1].replace('//','').split('/')[1:]
        fdir = ''
        for item in loc:
            fdir += '/' +item
        print(fpath + fdir + '/'+fname)
        f = open((fpath + fdir + '/'+fname).encode('gbk'),'wb')
        f.close()
        filereader,filewriter = await asyncio.open_connection(dstIp, dstPost)   
        rMessage = requestPackage(['cp',inst[0]])
        message = json.dumps(rMessage).encode('utf-8')
        filewriter.write(message)

        #读到的文件
        bulk = await filereader.read(65536)
        bulk = json.loads(bulk.decode('utf-8'))
        f = open((fpath + fdir + '/'+fname).encode('gbk'),'wb')
        print('Received File: {}'.format(bulk))
        f.write(bulk[1].encode('utf-8'))
        f.close()
        filewriter.close()
        await filewriter.wait_closed()

        #返回shell ok
        bulk = responsePackage('200')
        bulk = json.dumps(bulk).encode('utf-8')
        writer.write(bulk)

async def daemonDo(reader, writer):
    thisName = ''
    while(True):
        #收到的命令
        try:
            bulk = await reader.read(65536)           
        except Exception:
            try:
                hostList.remove(thisName)
            except Exception:
                pass
            writer.close()
            await writer.wait_closed()
            break
        
        if bulk:#有数据
            client = writer.get_extra_info('peername')  # 返回套接字连接的远程地址
            print('Received from {}'.format(client))  # 在控制台打印查询记录
            #下面以后会被数据库替代
            bulk = json.loads(bulk.decode('utf-8'))

            #keepalive
            try:
                thisName = bulk[1]['keepalive']
                if thisName not in hostList:
                    hostList.append(thisName)
            except Exception:
                pass

            #其他主机操作后要去服务器更新数据库
            try:
                if 'delete' in bulk[1]:
                    hname = bulk[1]['hostname']
                    fdir = bulk[1]['delete']
                    fname = fdir.replace('//','').split('/')[-1]
                    loc = fdir.replace('//','').split('/')[1:-1]
                    froot = ''
                    for item in  loc:
                        froot += '/'+item
                    execStr = 'delete from catalog where hostname = ? and rootname = ? and filename = ? '
                    value = (hname,froot,fname)
                    await deleteDB(execStr,value)

                    bulk = responsePackage('200')
                    bulk = json.dumps(bulk).encode('utf-8')
                    writer.write(bulk)
                    break
            except Exception:
                pass
            
            if 'V' in bulk[0]:#请求报文
                inst = bulk[0]['I'].split(' ')
                while '' in inst:
                    inst.remove('')
                cmdToDo = inst[0]
                await asyncio.sleep(0.5)
                print(f'Receive Inst: {inst!r}')
                if cmdToDo == 'rg':
                    task = asyncio.create_task(rgDo(reader,writer,inst[1:],bulk[1]))
                    await task
                elif cmdToDo == 'ls':#列出指令
                    task = asyncio.create_task(lsDo(reader,writer,inst[1:]))
                    await task
                elif cmdToDo == 'ln':
                    task = asyncio.create_task(lnDo(reader,writer,inst[1:]))
                    await task
                elif cmdToDo == 'md':
                    task = asyncio.create_task(mdDo(reader,writer,inst[1:]))
                    await task
                elif cmdToDo == 'rm':
                    task = asyncio.create_task(rmDo(reader,writer,inst[1:]))
                    await task                    
                elif cmdToDo == 'cp':
                    task = asyncio.create_task(cpDo(reader,writer,inst[1:]))
                    await task  
                elif cmdToDo == 'mv':
                    task = asyncio.create_task(mvDo(reader,writer,inst[1:]))
                    await task                      
                else:  
                    pass
            else:#应答报文
                print('Receive FeedBack: {}'.format(bulk[0]['E']))
        else:
            break

async def startServer(loop):
    server = await asyncio.start_server(daemonDo, pns.address, pns.port, loop = loop) 
    for socket in server.sockets:
        print("serving on {}".format(socket.getsockname()))
    async with server:
        await server.serve_forever()

async def keepalive(reader, writer):
    while(True):
        #每过1s发一个ls包
        await asyncio.sleep(1)
        keeplist = ['ls','//']
        rMessage = requestPackage(keeplist,{'keepalive':pns.name})#打包成请求格式
        keepJson = json.dumps(rMessage )
        inst = keepJson.encode('utf-8')
        print(f'Send Keepalive Package: {keeplist!r}')
        writer.write(inst)

        #收到就ok
        bulk = await reader.read(100)
        bulk = json.loads(bulk.decode('utf-8'))
        print('Receive FeedBack: {}'.format(bulk[0]['E']))

async def daemon():  
    loop = asyncio.get_event_loop()
    #如果运行的是tracketr就启动一个服务器
    if pns.name == 'h1':
        task = asyncio.create_task(createDB())
        await task
        startServerTask = asyncio.create_task(startServer(loop))
        await startServerTask
    #运行的是普通daemon 要在启动一个服务器的同时加入一个keepalive
    else:
        reader,writer = await asyncio.open_connection(pns.trackerAddr, pns.trackerPost, loop=loop)
        await asyncio.gather(
            startServer(loop),
            keepalive(reader,writer))

if __name__ == '__main__':
    if cmdDict['mode'] == 'daemon':
        asyncio.run(daemon())
    if cmdDict['mode'] == 'shell':
        asyncio.run(shellDo())