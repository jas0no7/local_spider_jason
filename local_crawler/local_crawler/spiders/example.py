import scrapy


class ExampleSpider(scrapy.Spider):
    name = "example"
    allowed_domains = ["sthjt.jiangxi.gov.cn"]
    start_urls = ["https://sthjt.jiangxi.gov.cn"]

    def parse(self, response):
        pass
