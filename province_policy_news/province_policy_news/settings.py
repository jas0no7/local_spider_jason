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
COOKIES_ENABLED = True

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

    # ======================
    # 新闻类（更新完整）
    # ======================
    'news_fgw_fujian': '新闻-发展和改革委员会-福建',
    'news_fgw_gansu': '新闻-发展和改革委员会-甘肃',
    'news_fgw_henan': '新闻-发展和改革委员会-河南',
    'news_fgw_jiangsu': '新闻-发展和改革委员会-江苏',
    'news_fgw_zhejiang': '新闻-发展和改革委员会-浙江',

    'news_gsbnea': '新闻-国家能源局-甘肃',
    'news_gxt_jiangxi': '新闻-工业和信息化厅-江西',
    'news_gxt_jiangsu': '新闻-工业和信息化厅-江苏',

    'news_nea_fujian': '新闻-国家能源局-福建',
    'news_nea_jiangsu': '新闻-国家能源局-江苏',

    'news_scbnea': '新闻-国家能源局-四川',

    'news_sthjt_fujian': '新闻-生态环境厅-福建',
    'news_sthjt_shaanxi': '新闻-生态环境厅-陕西',
    'news_sthjt_sichuan': '新闻-生态环境厅-四川',

    'new_fgw_sichuan': '新闻-发展和改革委员会-四川',

    # ======================
    # 政策类（发展改革委 fgw）
    # ======================
    'policy_fgw_chongqing': '政策-发展和改革委员会-重庆',
    'policy_fgw_henan': '政策-发展和改革委员会-河南',
    'policy_fgw_jiangsu': '政策-发展和改革委员会-江苏',
    'policy_fgw2_jiangsu': '政策-发展和改革委员会-江苏',
    'policy_fgw_shaanxi': '政策-发展和改革委员会-陕西',
    'policy_fgw_zhejiang': '政策-发展和改革委员会-浙江',
    'policy_fgw_hunan': '政策-发展和改革委员会-湖南',
    'policy_fgw_sichuan': '政策-发展和改革委员会-四川',
    'policy_fgw_hubei': '政策-发展和改革委员会-湖北',
    'policy_fgw2_hubei': '政策-发展和改革委员会-湖北',
    'policy_fgw_jiangxi': '政策-发展和改革委员会-江西',
    'policy_fgw_gansu': '政策-发展和改革委员会-甘肃',

    # ======================
    # 政策类（gxt 工业和信息化厅）
    # ======================
    'policy_gsbnea': '政策-国家能源局-甘肃',
    'policy_gxt_fujian': '政策-工业和信息化厅-福建',
    'policy_gxt_hunan': '政策-工业和信息化厅-湖南',
    'policy_gxt_henan': '政策-工业和信息化厅-河南',
    'policy_gxt_jiangsu': '政策-工业和信息化厅-江苏',
    'policy_gxt_jiangxi': '政策-工业和信息化厅-江西',
    'policy_gxt_shaanxi': '政策-工业和信息化厅-陕西',
    'policy_gxt_gansu': '政策-工业和信息化厅-甘肃',

    # ======================
    # 政策类（能源局）
    # ======================
    'policy_hnnyfz': '政策-能源发展厅-河南',
    'policy_hunb_nea': '政策-国家能源局-湖北',

    'policy_nea_fujian': '政策-国家能源局-福建',
    'policy_nea_shaanxi': '政策-国家能源局-陕西',
    'policy_nea_jiangsu': '政策-国家能源局-江苏',
    'policy_nea_zhejiang': '政策-国家能源局-浙江',

    'policy_scbnea': '政策-国家能源局-四川',

    # ======================
    # 政策类（其他厅局）
    # ======================
    'policy_jjxxw_chongqing': '政策-经济和信息化委员会-重庆',

    'policy_jxt_sichuan': '政策-交通运输厅-四川',

    'policy_sndrc_shaanxi': '政策-发展和改革委员会-陕西（能源处）',

    # ======================
    # 生态环境厅 sthjt
    # ======================
    'policy_sthjt_chongqing': '政策-生态环境厅-重庆',
    'policy_sthjt_fujian': '政策-生态环境厅-福建',
    'policy_sthjt_hunan': '政策-生态环境厅-湖南',
    'policy_sthjt_shaanxi': '政策-生态环境厅-陕西',
    'policy_sthjt_sichuan': '政策-生态环境厅-四川',
    'policy_sthjt_jiangxi': '政策-生态环境厅-江西',
    'policy_sthjt_gansu':'政策-生态环境厅-甘肃',
    'policy_zdl': '政策-中国电力企业联合会',

}

# kafka
KAFKA_TOPIC = {

    # ======================
    # 新闻类
    # ======================
    'news_fgw_fujian': 'spider-news-fujian',
    'news_fgw_gansu': 'spider-news-gansu',
    'news_fgw_henan': 'spider-news-henan',
    'news_fgw_jiangsu': 'spider-news-jiangsu',
    'news_fgw_zhejiang': 'spider-news-zhejiang',

    'news_gsbnea': 'spider-news-gansu',
    'news_gxt_jiangxi': 'spider-news-jiangxi',
    'news_nea_fujian': 'spider-news-fujian',
    'news_nea_jiangsu': 'spider-news-jiangsu',
    'news_scbnea': 'spider-news-sichuan',

    'news_sthjt_fujian': 'spider-news-fujian',
    'news_sthjt_shaanxi': 'spider-news-shaanxi',
    'news_sthjt_sichuan': 'spider-news-sichuan',

    'new_fgw_sichuan': 'spider-news-sichuan',
    'news_gxt_jiangsu': 'spider-news-jiangsu',

    # ======================
    # 政策类（发展改革委）
    # ======================
    'policy_fgw_chongqing': 'spider-policy-chongqing',
    'policy_fgw_henan': 'spider-policy-henan',
    'policy_fgw_jiangsu': 'spider-policy-jiangsu',
    'policy_fgw2_jiangsu': 'spider-policy-jiangsu',
    'policy_fgw_shaanxi': 'spider-policy-shaanxi',
    'policy_fgw_zhejiang': 'spider-policy-zhejiang',
    'policy_fgw_hunan': 'spider-policy-hunan',
    'policy_fgw_sichuan': 'spider-policy-sichuan',
    'policy_fgw_hubei': 'spider-policy-hubei',
    'policy_fgw2_hubei': 'spider-policy-hubei',
    'policy_fgw_jiangxi': 'spider-policy-jiangxi',
    'policy_fgw_gansu': 'spider-policy-gansu',

    # ======================
    # 工信厅 gxt
    # ======================
    'policy_gsbnea': 'spider-policy-gansu',
    'policy_gxt_fujian': 'spider-policy-fujian',
    'policy_gxt_hunan': 'spider-policy-hunan',
    'policy_gxt_henan': 'spider-policy-henan',
    'policy_gxt_jiangsu': 'spider-policy-jiangsu',
    'policy_gxt_jiangxi': 'spider-policy-jiangxi',
    'policy_gxt_shaanxi': 'spider-policy-shaanxi',
    'policy_gxt_gansu': 'spider-policy-gansu',

    # ======================
    # 能源局（nea）
    # ======================
    'policy_hnnyfz': 'spider-policy-henan',
    'policy_hunb_nea': 'spider-policy-hubei',

    'policy_nea_fujian': 'spider-policy-fujian',
    'policy_nea_shaanxi': 'spider-policy-shaanxi',
    'policy_nea_jiangsu': 'spider-policy-jiangsu',
    'policy_nea_zhejiang': 'spider-policy-zhejiang',

    'policy_scbnea': 'spider-policy-sichuan',

    # ======================
    # 其他厅局
    # ======================
    'policy_jjxxw_chongqing': 'spider-policy-chongqing',
    'policy_jxt_sichuan': 'spider-policy-sichuan',
    'policy_sndrc_shaanxi': 'spider-policy-shaanxi',

    # ======================
    # 生态环境厅 sthjt
    # ======================
    'policy_sthjt_chongqing': 'spider-policy-chongqing',
    'policy_sthjt_fujian': 'spider-policy-fujian',
    'policy_sthjt_hunan': 'spider-policy-hunan',
    'policy_sthjt_shaanxi': 'spider-policy-shaanxi',
    'policy_sthjt_sichuan': 'spider-policy-sichuan',
    'policy_sthjt_jiangxi': 'spider-policy-jiangxi',
    'policy_sthjt_gansu':'spider-policy-gansu',
    'policy_zdl': 'spider_policy_zdl',
}

# Minio
BUCKET_NAME = 'province-policy-news'
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
    'province_policy_news.middlewares.EducationSpiderMiddleware': 543,
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
    "user": "d1806922442",
    "passwd": "x8ykeboz",
    "key": "o8k668bte7v9357aw4lp",
    "orderid": "956527168580692",
    "signature": "z76vps1cl157lceesyyp4wo3fja8jpvl"
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
