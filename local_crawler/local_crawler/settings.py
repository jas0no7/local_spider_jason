# Scrapy settings for local_crawler project

BOT_NAME = "local_crawler"

SPIDER_MODULES = ["local_crawler.spiders"]
NEWSPIDER_MODULE = "local_crawler.spiders"

ADDONS = {}

ROBOTSTXT_OBEY = False


CONCURRENT_REQUESTS_PER_DOMAIN = 1


FEED_EXPORT_ENCODING = "utf-8"

# ---------------------------------------------
# 输出数据到本地 JSON 文件
# 每次 crawl 命令运行都会生成 output.json
# ---------------------------------------------
FEEDS = {
    r"D:\项目文件夹\政策大脑_json\%(name)s.json": {
        "format": "json",
        "encoding": "utf-8",
        "indent": 2,
    }
}



# 如不需要可删
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# 你可以根据需要启用中间件或管道
# SPIDER_MIDDLEWARES = {
#     "local_crawler.middlewares.LocalCrawlerSpiderMiddleware": 543,
# }

DOWNLOADER_MIDDLEWARES = {
    "local_crawler.middlewares.LocalCrawlerDownloaderMiddleware": 500,
}

# ITEM_PIPELINES = {
#     "local_crawler.pipelines.LocalCrawlerPipeline": 300,
# }
DOWNLOAD_DELAY = 1.0