import copy
from hashlib import md5
import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.linkextractors import LinkExtractor
from ..items import DataItem
from ..mydefine import get_now_date, get_attachment
# -*- coding: utf-8 -*-
import copy
import json
import re
from hashlib import md5

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings
from ..items import DataItem
from ..mydefine import get_now_date, get_attachment
settings = get_project_settings()


class GansuGovSpider(CrawlSpider):
    name = 'news_fgw_gansu'
    allowed_domains = ['gansu.gov.cn']

    _from = '甘肃省人民政府门户网'

    dupefilter_field = {
        "batch": "20251107"
    }

    infoes = [
        {
            'url': 'https://www.gansu.gov.cn/gsszf/c100002/ywdt.shtml',
            'label': '首页;甘肃要闻'
        },
        {
            'url': 'https://fzgg.gansu.gov.cn/fzgg/c106090/list.shtml',
            'label': '首页;发改视点'
        }
    ]

    def start_requests(self):
        for info in self.infoes:
            url = info.get('url')
            yield scrapy.Request(
                url=url,
                callback=self.parse_item,
                meta=copy.deepcopy({
                    "label": info.get('label'),
                }),
                dont_filter=True
            )

    def parse_item(self, response):
        """
        列表页解析
        """
        label = response.meta.get('label')

        # === 提取每条新闻 ===
        links = response.xpath('//ul[@id="list"]/li')
        for ex in links:
            url = response.urljoin(ex.xpath('./a/@href').get())
            title = ex.xpath('./a/@title').get()
            publish_time = ex.xpath('./span[@class="date"]/text()').get()

            meta = {
                "label": label,
                "title": title,
                "publish_time": publish_time
            }

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(meta)
            )

        # === 下一页逻辑（如果有） ===
        next_links = LinkExtractor(restrict_xpaths='//a[@class="jzgd"]').extract_links(response)
        for link in next_links:
            yield scrapy.Request(
                url=link.url,
                callback=self.parse_item,
                meta={"label": label}
            )

    def parse_detail(self, response):
        """
        详情页解析
        """
        _meta = response.meta
        method = response.request.method
        body = response.request.body.decode('utf-8') if response.request.body else ''
        url = response.request.url

        # 详情正文区域
        body_xpath = '//div[@class="main"] '

        title = _meta.get('title') or response.xpath('//meta[@name="ArticleTitle"]/@content').extract_first()
        publish_time = _meta.get('publish_time') or \
                       ''.join(response.xpath('//publishtime/text()').extract()).strip() or \
                       ''.join(re.findall(r'发布日期.*?(\d{4}-\d{2}-\d{2})', response.text, re.DOTALL)).strip()

        author = response.xpath('//meta[@name="Author"]/@content').extract_first() or \
                 ''.join(re.findall(r'发布机构：</strong><span>(.*?)</span></li>', response.text, re.DOTALL)).strip() or \
                 ''.join(re.findall(r'>信息来源：(.*?)</', response.text, re.DOTALL)).strip()

        attachment_urls = response.xpath(
            '//p[contains(@class, "insertfileTag")]//a | '
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or '
            'contains(@href, ".xls") or contains(@href, ".xlsx") or contains(@href, ".wps") or '
            'contains(@href, ".zip") or contains(@href, ".rar")]'
        )

        yield DataItem({
            "_id": md5(f"{method}{url}{body}".encode('utf-8')).hexdigest(),
            "url": url,
            "spider_from": self._from,
            "label": _meta.get('label'),
            "title": title,
            "publish_time": publish_time,
            "body_html": ' '.join(response.xpath(body_xpath).extract()),
            "content": ' '.join(response.xpath(f'{body_xpath}//text()').extract()),
            "images": [response.urljoin(i) for i in response.xpath(f'{body_xpath}//img/@src').extract()],
            "attachment": get_attachment(attachment_urls, url, self._from),
            "spider_date": get_now_date(),
            "spider_topic": "",
        })
