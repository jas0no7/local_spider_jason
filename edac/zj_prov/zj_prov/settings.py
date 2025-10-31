# Scrapy settings for zj_prov project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html






# !/usr/bin/env python
# _*_ coding: utf-8 _*_

import logging

# 关闭kafka的日志输出
logging.getLogger('kafka').setLevel(logging.WARNING)

BOT_NAME = "zj_prov"

SPIDER_MODULES = ["zj_prov.spiders"]
NEWSPIDER_MODULE = "zj_prov.spiders"

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
DUPEFILTER_CLASS = "zj_prov.mydefine.RFPDupeFilter"
SCHEDULER = "zj_prov.mydefine.Scheduler"
SCHEDULER_PERSIST = True
SCHEDULER_DUPEFILTER_KEY = "duplicate:zj_prov"
SCHEDULER_QUEUE_KEY = f"zj_prov:%(spider)s_requests"
SCHEDULER_FLUSH_ON_START = False
SCHEDULER_IDLE_BEFORE_CLOSE = 30
DOWNLOAD_FAIL_ON_DATALOSS = False

# kafka
NEWS_KAFKA_TOPIC = 'spider-news-zhejiang'
POLICY_KAFKA_TOPIC = 'spider-policy-zhejiang'


# Minio
BUCKET_NAME = 'zj_prov'
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
    'zj_prov.middlewares.EducationDownloaderMiddleware': 543,
    'zj_prov.middlewares.MyRetryMiddleware': 544,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None
}

# 保存管道
ITEM_PIPELINES = {
    'zj_prov.pipelines.Pipeline': 300,
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

