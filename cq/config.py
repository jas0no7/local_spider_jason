# mysql
MYSQL_211 = {
    "host": "192.168.0.181",
    "port": 1006,
    "user": "root",
    "passwd": "123456"
}

# 数据库名
SPIDER_CHARGE_DATA = "CHARGE_DATA"
# kafka topic
KAFKA_TOPIC = "YkcSichuanTemporary"
# mysql数据库表名
DB_BASIC = "root_sichuan_tld_charge_basic"
DB_DETAIL = "root_cq_charge_detail"
DB_TERMINAL = "root_cq_charge_terminal"
DB_ORIGIN_PRICE = "root_cq_charge_origin_price"
DB_NUMBER = "root_cq_charge_num"
# 特来电token
REDIS_TLD_X_TOKEN = "variable:charge_cq:tld_token"
# 龙禹快充token
REDIS_LYKC_TOKEN = "variable:charge_cq:lykc_token"
# 去重
REDIS_DUPLICATE = "duplicate:charge_cq"
# 不是重庆的站点
REDIS_FILTER = "duplicate:charge_cq_no"
# 超时
TIMEOUT = 5
# 重试
RETRY = 8
# 定时
CRON_BASE = {
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
# kafka 连接
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
# redis去重
REDIS_FILTER_181 = {
    "host": "192.168.0.181",
    "port": 1079,
    "db": 1,
    "max_connections": 50,
}
# redis 代理ip
REDIS_PROXY_181 = {
    "host": "192.168.0.181",
    "port": 1079,
    "db": 0,
    "max_connections": 50,
}
# 代理
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
# spider_api_geo是docker-compose服务中对应的经纬度转换的服务名
# FLASK_GEO_API = 'http://192.168.0.212:5000/get_address'
FLASK_GEO_API = 'http://spider_api_geo:5000/get_address'
