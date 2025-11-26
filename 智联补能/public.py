# --coding:utf-8--

import pymysql
import requests
from redis import Redis, ConnectionPool
from hashlib import md5
from datetime import datetime
from zoneinfo import ZoneInfo
from random import choice

import config


# =========================
#   User-Agent
# =========================
class UserAgent:
    """
    随机 UA（可选）
    """
    uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1",
    ]

    def random(self):
        return choice(self.uas)


ua = UserAgent()


# =========================
#   MySQL 封装
# =========================
class MyMySQL:
    def __init__(self, conf):
        self.conf = conf

    def _connect(self):
        conn = pymysql.connect(
            host=self.conf["host"],
            port=self.conf["port"],
            user=self.conf["user"],
            passwd=self.conf["passwd"],
            db=self.conf["db"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn, conn.cursor()

    def execute(self, sql, params=None):
        conn, cursor = self._connect()
        cursor.execute(sql, params)
        conn.commit()
        conn.close()

    def select(self, sql):
        conn, cursor = self._connect()
        cursor.execute(sql)
        data = cursor.fetchall()
        conn.close()
        return data

    def insert(self, table, item: dict):
        keys = ", ".join(f"`{k}`" for k in item.keys())
        placeholders = ", ".join(["%s"] * len(item))
        sql = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
        self.execute(sql, list(item.values()))


mysql = MyMySQL(config.MYSQL)


# =========================
#   Redis 去重（可选）
# =========================
class MyRedis:
    def __init__(self, conf):
        pool = ConnectionPool(
            host=conf["host"],
            port=conf["port"],
            db=conf["db"],
            max_connections=conf["max_connections"],
            decode_responses=True
        )
        self.redis = Redis(connection_pool=pool)

    def exist_or_add(self, key, value):
        """
        简单去重：存在→True，不存在→写入→False
        """
        sign = md5(value.encode()).hexdigest()
        if self.redis.sismember(key, sign):
            return True
        self.redis.sadd(key, sign)
        return False


myredis = MyRedis(config.REDIS)


# =========================
#   工具函数
# =========================
def now(fmt='%Y-%m-%d %H:%M:%S'):
    return datetime.now(ZoneInfo("PRC")).strftime(fmt)
