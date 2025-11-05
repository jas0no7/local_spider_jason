import copy
import re
from hashlib import md5

import scrapy
from scrapy.spiders import CrawlSpider

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment


class DataSpider(CrawlSpider):
    name = 'news_cpc'
    allowed_domains = [
        'cpc.people.com.cn'
    ]

    _from = '中国共产党新闻网'
    dupefilter_field = {
        "batch": "20240603"
    }

    infoes = [
        {
            'url': 'http://cpc.people.com.cn/GB/64192/105996/352007/index{}.html',
            'label': '讲话'
        },
        {
            'url': 'http://cpc.people.com.cn/GB/64192/105996/352002/index{}.html',
            'label': '出席会议'
        }
    ]
    total = 7

    def start_requests(self):
        for info in self.infoes:
            url = info.get('url')
            yield scrapy.Request(
                url=url.format(1),
                callback=self.parse_item,
                meta=copy.deepcopy({
                    "page": 1,
                    "base_url": url,
                    "label": info.get("label")
                }),
                dont_filter=True
            )

    def parse_item(self, response):
        """
        详情和下一页url
        :param response:
        :return:
        """

        _meta = response.meta
        label = _meta.get('label')
        page = _meta.get('page')
        base_url = _meta.get('base_url')

        for ex_url in response.xpath('//div[@class="fl"]/ul/li'):
            detail_url = ex_url.xpath('./a/@href').extract_first()
            if not detail_url:
                continue

            url = response.urljoin(detail_url)
            title = ''.join(ex_url.xpath('./a//text()').extract())
            publish_time = ex_url.xpath('substring(./i/text(), 2, 11)').extract_first()

            meta = {
                "label": label,
                "title": title,
                'publish_time': publish_time,
            }
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(meta)
            )

        if page < self.total:
            page += 1
            yield scrapy.Request(
                url=base_url.format(page),
                callback=self.parse_item,
                meta=copy.deepcopy({
                    'label': label,
                    'page': page,
                    'base_url': base_url
                })
            )

    def parse_detail(self, response):
        """
        详情
        :param response:
        :return:
        """
        _meta = response.meta

        method = response.request.method
        body = response.request.body.decode('utf-8')
        url = response.request.url

        body_xpath = '//div[@class="show_text" or @class="edit" or contains(@class, "rm_txt_con")]'
        attachment_urls = response.xpath(f'{body_xpath}//a')

        title = _meta.get('title')
        publish_time = _meta.get('publish_time') or \
            response.xpath('substring(//p[@class="sou"]/text(), 0, 17)').extract_first()

        _author = response.xpath('//div[contains(@class, "edit")]//text()').extract_first()
        if not _author:
            _author = ''
        author = re.sub(r'.*责编[:：](.+?)\).*', r'\1', _author) or \
            ';'.join(response.xpath('//p[@class="sou"]/a//text()').extract())

        yield DataItem({
            "_id": md5(f'{method}{url}{body}'.encode('utf-8')).hexdigest(),
            "url": url,
            'spider_from': self._from,
            'label': _meta.get('label'),
            'title': title,
            'author': author,
            'publish_time': publish_time,
            'body_html': ' '.join(response.xpath(body_xpath).extract()),
            "content": ' '.join(response.xpath(f'{body_xpath}//text()').extract()),
            "images": [response.urljoin(i) for i in response.xpath(f'{body_xpath}//img/@src').extract()],
            "attachment": get_attachment(attachment_urls, url, self._from),
            "spider_date": get_now_date(),
        })
