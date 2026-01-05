# !/usr/bin/env python
# _*_ coding: utf-8 _*_

# kafka配置
kafka = {
    "charge": "spider-charge",
}
# 数据库配置
database = {
    "redis_key": {
        # 已经完成的
        "first": "duplicate",
        "charge": "charge",
        # 变量
        "variable": "variable",
    },
    "db_name": {
        "chrage_basic": "root_sc_charge_basic",
        "chrage_detail": "root_sc_charge_detail",
        "chrage_terminal": "root_sc_charge_terminal",
        "chrage_origin_price": "root_sc_charge_origin_price",
    }
}
# 超时重试
proxytimeout = {
    "charge": {
        "timeout": 5,
        "retry": 10
    }
}
# 定时任务配置
cron = {
    "trigger": "cron",
    "year": "*",
    "month": "*",
    "week": "*",
    "day_of_week": "*",
    "misfire_grace_time": 100,
    "max_instances": 10,
    "day": "*",
    "hour": "*",
    "minute": "00,30",
    "second": "00",
}
cron_token = {
    "trigger": "cron",
    "year": "*",
    "month": "*",
    "week": "*",
    "day_of_week": "*",
    "misfire_grace_time": 100,
    "max_instances": 10,
    "day": "*",
    "hour": "*",
    "minute": "*/19",
    "second": "15",
}

KAFKA = {
    "bootstrap_servers": [
        '192.168.0.220:9092',
        '192.168.0.221:9092',
        '192.168.0.222:9092',
        '192.168.0.223:9092'
    ],
    "api_version": (2, 7),
    "group_id": "spider",
    "client_id": "consumer_spider"
}

REDIS_FILTER_181 = {
    "host": "192.168.0.181",
    "port": 1079,
    "db": 1,
    "max_connections": 50,
}

REDIS_PROXY_181 = {
    "host": "192.168.0.181",
    "port": 1079,
    "db": 0,
    "max_connections": 50,
}

# PROXY = {
#     "user": "895047059",
#     "passwd": "eq0ar8ui",
#     "key": "kuai_proxy",
#     "orderid": "913834400555444",
#     "signature": "g0hmiauijvrtd3gvpnu01cr93fk68m06"
# }
PROXY = {
    "user": "d1806922442",
    "passwd": "x8ykeboz",
    "key": "o8k668bte7v9357aw4lp",
    "orderid": "956527168580692",
    "signature": "z76vps1cl157lceesyyp4wo3fja8jpvl"
}
