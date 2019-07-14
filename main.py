import asyncio
import aiosqlite3
import logging
import argparse
import os
import json
import functools

'''
    项目实现需求分析:
    1.起初在思考是使用面向对象和面向过程，个人觉得面向对象更易于修改和拓展，而且更易于项目编写
    2.cs架构:一个主server存储逻辑视图，然后一人共享文件，可供多人查看下载，多人之间下载也是p2p
    3.支持直接p2p传文件:这个方便在两人之间传文件，省去了启动server的过程
    4.自行设计了通信协议，不过是json实现的，但提供了接口，改成字节形式的协议也很方便，这里主要是纠结使用哪个更合适一些
    5.代码编写风格依据google的python项目规范
'''

class Error(Exception):
    pass

class MessageMixin():

    '''是协议的内容,每个报文都要包含此内容
    
    V	版本号		必有
    
    A	认证码		必有

    I	命令	    请求包必有

    E	错误码	    回复包必有

    L	内容长度	必有

    C   内容本身	可选
    '''

    # def __init__(self, version='1.0', aCode='', inst='', eCode='', content=''):

    #     self.version = version
    #     self.aCode = aCode
    #     self.inst = inst
    #     self.eCode = eCode
    #     self.content = content

    def encode(self, message):
        return json.dumps(message).encode('utf-8')

    def decode(self, message):
        return json.loads(message.decode('utf-8')) 


class Transport(MessageMixin):
    '''通信类，负责通信和根据协议的拆解包

    '''
    
    def __init__(self):
        self.writer = None
        self.reader = None

    async def send(self, message):
        self.writer.write(self.encode(message))
        await self.writer.drain()

    async def recv(self):
        try:
            rdata = await self.reader.read(1024)
            return self.decode(rdata)
        except:
            raise Error('recv error')

class Tracker(Transport):
    '''tracker是存储逻辑视图的节点，负责响应各种请求

    tracker可以收到daemon的请求，去查询数据库中的逻辑视图，以及在传文件时让两个用户进行p2p连接
    '''
    def __init__(self):
        pass

    async def setup(self):
        '''启动时要做的事情

        支持重载'''
        pass

    async def finish(self):
        '''结束时要做的事情

        支持重载'''
        pass

class Daemon(Transport):
    '''daemon负责在本地运行，响应shell命令和trakcer发来的报文

    daemon接收到shell的命令后转发给tracker去处理，同样tracker处理完转发给daemon，daemon通知shell处理结果
    '''
    def __init__(self):
        pass

    async def setup(self):
        '''启动时要做的事情

        支持重载'''
        pass

    async def finish(self):
        '''结束时要做的事情

        支持重载'''
        pass

class Shell(Transport):
    '''shell负责处理用户操作，向daemon发送请求以及接受daemon的响应结果

    shell主要包含ln,ls,rm,md,mv这五个基本指令
    '''

    def __init__(self, inst):
        
        self.inst = inst
        self.reader = None
        self.writer = None

    async def run(self):

        await self.setup()
        try:
            await self.handle()
        finally:
            await self.finish()

    async def setup(self):

        self.reader, self.writer = await asyncio.open_connection('127.0.0.1', 9001, local_addr=('127.0.0.1', 9002))
        await self.handle()

    async def handle(self):

        # 发送shell请求
        await self.send(self.inst)

        # 等待回复
        while True:
            data = await self.recv()

    async def finish(self):

        self.writer.close()
        await self.writer.wait_closed()

def getOpt():

    # 获取命令行参数
    parser = argparse.ArgumentParser(prog="file-sharing-system", usage='[-h] fileRoot [-t | -d trackerAddr | -s [S [S ...]]]')
    parser.add_argument('fileRoot', nargs=1, help='指定的共享文件目录')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-t', action='store_true', help='作为tracker启动，文件逻辑视图存储节点')
    group.add_argument('-d', nargs=1, help='作为daemon启动，连接tracker和shell')
    group.add_argument('-s', nargs='*', help='作为shell启动与daemon交互')
    # 得到参数字典
    args = parser.parse_args()
    args_dict = vars(args)
    return args_dict

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - [line:%(lineno)d]- %(levelname)s: %(message)s')
    args_dict = getOpt()
    if args_dict.get('t'):  # tracker
        role = Tracker()
    elif args_dict.get('d'):  # daemon
        role = Daemon()
    elif args_dict.get('s'):  # shell
        role = Shell(args_dict['s'])
    asyncio.run(role.run())