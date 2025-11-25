from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

if __name__ == "__main__":
    process = CrawlerProcess(get_project_settings())

    spider_names = [
        "policy_fgw_henan",
        "policy_gxt_henan",
        "policy_sthjt_henan",
        "news_gxt_henan",
        "news_sthjt_henan",
    ]

    for spider in spider_names:
        process.crawl(spider)

    process.start()
