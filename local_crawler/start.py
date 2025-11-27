from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

if __name__ == "__main__":
    process = CrawlerProcess(get_project_settings())

    spider_names = [
        "news_fgw_zhejiang.py",
        "news_jxt_zhejiang.py",# 有问题
        "policy_jxt_zhejiang.py",
        "policy_sthjt_zhejiang.py"# 有问题
    ]

    for spider in spider_names:
        process.crawl(spider)

    process.start()
