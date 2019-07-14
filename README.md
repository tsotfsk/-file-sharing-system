# file-sharing-system
一个局域网内的文件共享系统
# 使用举例

python main.py [-s | -c server_ip] root
> DAEMON  python pns.py daemon h1.yml
> SHELL   python pns.py shell h2.yml ls //

指令说明
 ----------------ls----------------
 ls /        查看逻辑路径的/目录
 ls /movie/  查看逻辑路径下/movie/下的信息
 ls //       查看所有的主机列表
 ls //h1/    查看主机h1的物理路径/目录下的信息

 ----------------ln----------------
 ln //h3/f1  /video            链接一个物理文件or目录到 逻辑文件or目录

 ----------------md----------------
 md /video                 在逻辑路径下建立一个文件夹
 md //h3/f2                在物理路径下建立一个文件夹

 ----------------rm----------------
 rm /video                 删除一个逻辑目录or文件
 rm //h3/f2                删除本地一个物理文件

 ----------------mv----------------
 mv //h2/f2  //h3/f3   物理到物理的mv

 ----------------cp----------------
 cp //h2/f2  //h3/f3   物理到物理的cp


 请求报文
 字段   定义	    请求必选		有效取值
 V	    版本号		   YES          '1.0'
 A	    认证码		   YES          SHA256( secret + I )
 I	    命令本身	   YES
 L     内容大小        No          字节
 C     内容本身	    No	        

 应答报文
 字段   定义	    应答必选		有效取值
 E	    错误代码	   YES		    参考HTTP错误码
 L     内容大小        No          字节
 C     内容本身	    No	        	

 数据库存储
 catalog table
filename      filetype                   ctime                     mtime    hostname            hostaddr    rootname        lAddress       
   a.txt             f     2016-11-16 10:53:12       2016-11-16 10:53:12          h1     127.0.0.1:60000          /c               /
       b             d     2016-11-16 10:53:12       2016-11-16 10:53:12          h2     127.0.0.1:60001        /c/d        /moive/c
       a             d     2016-11-16 10:53:12       2016-11-16 10:53:12          h3     127.0.0.1:60002           /          /music