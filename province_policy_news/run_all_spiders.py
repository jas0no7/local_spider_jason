from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.utils.spider import iter_spider_classes
import importlib
import os

# 项目设置
settings = get_project_settings()
process = CrawlerProcess(settings)

# 遍历 spiders 目录，动态导入所有 spider 类
spiders_dir = os.path.join(os.path.dirname(__file__), 'province_policy_news', 'spiders')
for filename in os.listdir(spiders_dir):
    if filename.endswith(".py") and not filename.startswith("__"):
        module_name = f'province_policy_news.spiders.{filename[:-3]}'
        module = importlib.import_module(module_name)
        for spider_cls in iter_spider_classes(module):
            process.crawl(spider_cls)

# 启动所有 spider
process.start()

