import aiosqlite3
import sqlite3
import logging
from DBUtils.PooledDB import PooledDB
from time import time

class DataBase:
    
    def __init__(self, mincached, maxcached, maxconnections, database):

        self.linkPoll = PooledDB(sqlite3, mincached=mincached, maxcached=maxcached, 
                                          maxconnections=maxconnections, blocking=True, database=database, check_same_thread=False) 
        self.create()

    def open(self):
        conn = self.linkPoll.connection(shareable=False)
        cursor = conn.cursor()
        return conn, cursor

    def close(self, conn, cursor):
        cursor.close()
        conn.commit()
        conn.close()

    def fetchall(self, sqlStr, value):
        conn, cursor = self.open()
        try:
            cursor.execute(sqlStr, value)
            result = cursor.fetchall()
        except:
            try:
                if 'insert' in sqlStr:  # 插入出错，也就是不满足完整性约束，那么就采取更新的策略
                    newSqlStr = 'update DNS set TTL = ? , RDATA = ?, TIMESTAMP = ? where Name = ? and TYPE = ? and CLASS = ? and RDATA = ?'
                    newValue = (value[3], value[4], value[5], value[0], value[1], value[2], value[4])
                    cursor.execute(newSqlStr, newValue)
                    result = cursor.fetchall()
                else:
                    result=[]
            except Exception as e:
                result = []
                logging.error(e)
        self.close(conn, cursor)
        return result
    
    def create(self):
        pass

class FileDataBase(DataBase):

    # def __init__(self, mincached, maxcached, maxconnections, database):
    #     DataBase.__init__(self, mincached, maxcached, maxconnections, database)

    # 数据库创建操作
    def create(self):
        conn, cursor = self.open()
        try:
            cursor.execute('''CREATE TABLE DNS
                (
                NAME            TEXT            NOT NULL,
                TYPE        SMALLINT            CHECK(TYPE >= 0 AND TYPE <= 65535),
                CLASS       SMALLINT            CHECK(CLASS >= 0 AND CLASS <= 65535),
                TTL              INT            CHECK(TTL >= 0),
                RDATA           TEXT            NOT NULL,
                TIMESTAMP     DOUBLE            CHECK(TIMESTAMP > 0),
                PRIMARY KEY     (NAME, TYPE, CLASS, RDATA));''')
        except Exception as e:
            logging.error(e)
    
        self.close(conn, cursor)

if __name__ == "__main__":
    database = FileDataBase(mincached=0, maxcached=0, maxconnections=10, database='catalog.db')

    