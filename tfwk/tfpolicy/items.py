# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DataItem(scrapy.Item):
    _id = scrapy.Field()
    url = scrapy.Field()
    spider_topic = scrapy.Field()
    spider_from = scrapy.Field()
    label = scrapy.Field()
    title = scrapy.Field()
    author = scrapy.Field()
    publish_time = scrapy.Field()
    body_html = scrapy.Field()
    content = scrapy.Field()
    images = scrapy.Field()
    attachment = scrapy.Field()
    spider_date = scrapy.Field()
    category = scrapy.Field()
    publish_agency = scrapy.Field()
    report_period = scrapy.Field()
    theme = scrapy.Field()

