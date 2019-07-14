import asyncio

async def lnDo():
    '''将本地文件链接到server存储的逻辑视图中
    
    比如 ln //music/song.mp3   /test 表示将本地文件链接到server根目录下的test目录下
    这里支持一个文件的多次链接
    '''
    pass

async def mdDo():
    '''在server逻辑视图下创建一个目录
    
    比如 md /test 就是在server逻辑视图根目录下创建一个test目录，如果存在则会报错
    '''
    pass

async def mvDo():
    '''将一个逻辑视图下的文件移动到另一个逻辑视图或用户目录下

    比如 mv /test //music 就是讲server逻辑视图中的/test目录移动到本机的//music中
    '''
    pass

async def rmDo():
    '''删除一个逻辑视图下的文件

    比如 rm /test 就是将逻辑视图下的test文件递归的删除
    '''
    pass

async def lsDo():
    '''列出当前逻辑视图下的文件

    比如 ls /test/music 就是将逻辑视图下的test/music目录中文件列举出来
    '''
    pass


async def main():
    inst = 'ls'
    await globals()[inst + 'Do']()

if __name__ == "__main__":
    asyncio.run(main())