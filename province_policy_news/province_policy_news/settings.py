# !/usr/bin/env python
# _*_ coding: utf-8 _*_

import logging

# 关闭kafka的日志输出
logging.getLogger('kafka').setLevel(logging.WARNING)

BOT_NAME = 'province_policy_news'


SPIDER_MODULES = ['province_policy_news.spiders']
NEWSPIDER_MODULE = 'province_policy_news.spiders'

# 是否遵守robots
ROBOTSTXT_OBEY = False
# 在headers中使用cookie需要设置
COOKIES_ENABLED = False

# 是否开启日志
LOG_ENABLED = True
# LOG_ENABLED = False

# headers中的跳转策略
REFERRER_POLICY = "same-origin"

# 去重相关
DUPEFILTER_CLASS = "province_policy_news.mydefine.RFPDupeFilter"
SCHEDULER = "province_policy_news.mydefine.Scheduler"
SCHEDULER_PERSIST = True
SCHEDULER_DUPEFILTER_KEY = "duplicate:province_policy_news"
SCHEDULER_QUEUE_KEY = f"province_policy_news:%(spider)s_requests"
SCHEDULER_FLUSH_ON_START = False
SCHEDULER_IDLE_BEFORE_CLOSE = 30
DOWNLOAD_FAIL_ON_DATALOSS = False

spider_name_from_map = {
    # 新闻类
    'news_fgw_henan': '新闻-发展和改革委员会-河南',
    'news_fgw_jiangsu': '新闻-发展和改革委员会-江苏',
    'news_fgw_zhejiang': '新闻-发展和改革委员会-浙江',

    'news_gxt_henan': '新闻-工业和信息化厅-河南',
    'news_jxt_zhejiang': '新闻-经济和信息化厅-浙江',
    'news_nea_zhejiang': '新闻-国家能源局-浙江',

    'news_sthjt_henan': '新闻-生态环境厅-河南',
    'news_sthjt_jiangsu': '新闻-生态环境厅-江苏',

    # 政策类：发展和改革委员会
    'policy_fgw_chongqing': '政策-发展和改革委员会-重庆',
    'policy_fgw_henan': '政策-发展和改革委员会-河南',
    'policy_fgw_jiangsu': '政策-发展和改革委员会-江苏',
    'policy_fgw_shaanxi': '政策-发展和改革委员会-陕西',
    'policy_fgw_zhejiang': '政策-发展和改革委员会-浙江',

    # 工业信息化厅（简称 gxt）
    'policy_gxt1_hunan': '政策-工业和信息化厅-湖南',
    'policy_gxt2_hunan': '政策-工业和信息化厅-湖南',
    'policy_gxt_henan': '政策-工业和信息化厅-河南',
    'policy_gxt_jiangsu': '政策-工业和信息化厅-江苏',
    'policy_gxt_jiangxi': '政策-工业和信息化厅-江西',
    'policy_gxt_shaanxi': '政策-工业和信息化厅-陕西',

    # 交通运输厅（你文件名前缀 jxt）
    'policy_jxt_hubei': '政策-经济和信息化厅-湖北',
    'policy_jxt_zhejiang': '政策-经济和信息化厅-浙江',

    # 国家能源局（nea）
    'policy_nea_jiangsu': '政策-国家能源局-江苏',
    'policy_nea_zhejiang': '政策-国家能源局-浙江',

    # 生态环境厅（sthjt）
    'policy_sthjt2_zhejiang': '政策-生态环境厅-浙江',
    'policy_sthjt_henan': '政策-生态环境厅-河南',
    'policy_sthjt_hubei': '政策-生态环境厅-湖北',
    'policy_sthjt_jiangsu': '政策-生态环境厅-江苏',
    'policy_sthjt_jiangxi': '政策-生态环境厅-江西',
    'policy_sthjt_zhejiang': '政策-生态环境厅-浙江',
}

# kafka
KAFKA_TOPIC = {

    # ======================
    # 新闻类
    # ======================
    'news_fgw_henan': 'spider-news-henan',
    'news_fgw_jiangsu': 'spider-news-jiangsu',
    'news_fgw_zhejiang': 'spider-news-zhejiang',

    'news_gxt_henan': 'spider-news-henan',
    'news_jxt_zhejiang': 'spider-news-zhejiang',
    'news_nea_zhejiang': 'spider-news-zhejiang',

    'news_sthjt_henan': 'spider-news-henan',
    'news_sthjt_jiangsu': 'spider-news-jiangsu',

    # ======================
    # 政策类（统一 spider-policy-省份）
    # ======================
    'policy_fgw_chongqing': 'spider-policy-chongqing',
    'policy_fgw_henan': 'spider-policy-henan',
    'policy_fgw_jiangsu': 'spider-policy-jiangsu',
    'policy_fgw_shaanxi': 'spider-policy-shaanxi',
    'policy_fgw_zhejiang': 'spider-policy-zhejiang',

    'policy_gxt1_hunan': 'spider-policy-hunan',
    'policy_gxt2_hunan': 'spider-policy-hunan',
    'policy_gxt_henan': 'spider-policy-henan',
    'policy_gxt_jiangsu': 'spider-policy-jiangsu',
    'policy_gxt_jiangxi': 'spider-policy-jiangxi',
    'policy_gxt_shaanxi': 'spider-policy-shaanxi',

    'policy_jxt_hubei': 'spider-policy-hubei',
    'policy_jxt_zhejiang': 'spider-policy-zhejiang',

    'policy_nea_jiangsu': 'spider-policy-jiangsu',
    'policy_nea_zhejiang': 'spider-policy-zhejiang',

    'policy_sthjt2_zhejiang': 'spider-policy-zhejiang',
    'policy_sthjt_henan': 'spider-policy-henan',
    'policy_sthjt_hubei': 'spider-policy-hubei',
    'policy_sthjt_jiangsu': 'spider-policy-jiangsu',
    'policy_sthjt_jiangxi': 'spider-policy-jiangxi',
    'policy_sthjt_zhejiang': 'spider-policy-zhejiang',
}



# Minio
BUCKET_NAME = 'province_policy_news'
MINIO_DOMAIN = "http://fd.edachr.com/"

# playwright ip
PLAYWRIGHT_IP = '192.168.0.206'
# playwright_api
PLAYWRIGHT_URL = f'http://{PLAYWRIGHT_IP}:5000/get_data_async?url='

# 满足下面后缀名的附件下载
ATTACHMENT_SUFFIX = [
    '.doc', '.docx', '.docm', '.dotm', '.dot', '.xps', '.rtf', '.odt', '.dotx',
    '.xls', '.xlsx', '.xlsm', '.xlsb', '.csv', '.xltx', '.prn', '.xml', '.dif', '.slk', '.xlam', '.xla', '.ods',
    '.ppt', '.pptx', '.pptm', '.potx', '.potm', '.pot', '.thmx', '.ppsx', '.ppsm', '.pps', '.ppam', '.ppa', '.emf', '.odp',
    '.pdf', '.ofd', '.wps', '.txt', '.et', '.md',
    '.rar', '.zip', '.7z', '.tar', '.gzip', '.bzip2', '.xz'
]

# 重试
RETRY_ENABLED = True
RETRY_TIMES = 5

# 下面几个状态码才重试
RETRY_HTTP_CODES = [502, 403, 449, 503, 440, 500, 452, 521, 454, 458]
HTTPERROR_ALLOWED_CODES = [502, 302, 301, 449, 304, 500, 452, 521, 400]
TELNETCONSOLE_PORT = None

MEDIA_ALLOW_REDIRECTS = False
# 超时
DOWNLOAD_TIMEOUT = 10
# 下载响应 随机间隔
RANDOMIZE_DOWNLOAD_DELAY = True
# 间隔
DOWNLOAD_DELAY = 0.5
# 请求并发数
CONCURRENT_REQUESTS = 12

# 下载中间件
DOWNLOADER_MIDDLEWARES = {
    'province_policy_news.middlewares.EducationDownloaderMiddleware': None,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
}


# 保存管道
ITEM_PIPELINES = {
    'province_policy_news.pipelines.EducationPipeline': 300,
}

# 默认的ua
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.62'

# 定时任务
cron = {
    "trigger": "cron",
    "year": "*",
    "month": "*",
    "week": "*",
    "day_of_week": "*",
    "day": "*",
    "misfire_grace_time": 100,
    "max_instances": 5
}

# redis
REDIS_181 = {
    "host": "192.168.0.181",
    "port": 1079,
    "max_connections": 50,
}
# REDIS_PROXY_DB 代理
REDIS_PROXY_DB = 0
# REDIS_FILTER_DB 过期
REDIS_FILTER_DB = 1
# 代理
PROXY = {
    "user": "895047059",
    "passwd": "eq0ar8ui",
    "key": "kuai_proxy",
    "orderid": "913834400555444",
    "signature": "g0hmiauijvrtd3gvpnu01cr93fk68m06"
}
# kafka
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
