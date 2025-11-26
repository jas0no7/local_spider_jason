# MySQL 连接配置
MYSQL = {
    "host": "192.168.0.181",
    "port": 1006,
    "user": "root",
    "passwd": "123456",
    "db": "CHARGE_DATA"
}

# 表名
# 站点详情表（站信息）
DB_DETAIL = "xinjiang_charge_detail"

# 枪表（充电枪列表）
DB_TERMINAL = "xinjiang_charge_gun"

# 主费率表（站点当前费率总览：freeNum/totalNum/currentPhase）
DB_RATE_MAIN = "xinjiang_charge_rate"

# 分时费率明细表（rateList 内每一条）
DB_RATE_DETAIL = "xinjiang_charge_rate_detail"


# Redis 去重（可选）
REDIS = {
    "host": "192.168.0.181",
    "port": 1079,
    "db": 1,
    "max_connections": 5,
}
REDIS_DUP_KEY = "dup:single_station"

# 请求配置
TIMEOUT = 5
RETRY = 3
