import copy
import re
from hashlib import md5

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment

settings = get_project_settings()

policy_kafka_topic = settings.get('POLICY_KAFKA_TOPIC')


class DataSpider(CrawlSpider):
    name = 'policy_bzsfzggw'
    allowed_domains = [
        'fzggw.cnbz.gov.cn'
    ]

    _from = '巴中市发展和改革委员会'
    dupefilter_field = {
        "batch": "20241111"
    }
    use_playwright = True
    custom_settings = {
        "CONCURRENT_REQUESTS": 3,
        "DOWNLOAD_TIMEOUT": 30,
        "DOWNLOAD_DELAY": 3
    }

    infoes = [
        {
            'url': 'https://fzggw.cnbz.gov.cn/xxgk/zcfg/index.html',
            'label': "首页;信息公开;政策文件",
            'detail_xpath': '//ul[contains(@class, "doc_list")]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span/text()',
            'body_xpath': '//div[contains(@class, "j-fontContent")]',
            'total': 1,
            'page': 1,
            'base_url': ''
        },
        {
            'url': 'https://fzggw.cnbz.gov.cn/xxgk/zcjd/index.html',
            'label': "首页;信息公开;政策解读",
            'detail_xpath': '//ul[contains(@class, "doc_list")]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span/text()',
            'body_xpath': '//div[contains(@class, "j-fontContent")]',
            'total': 2,
            'page': 1,
            'base_url': 'https://fzggw.cnbz.gov.cn/content/column/6814881?pageIndex={}'
        }
    ]

    def start_requests(self):
        for info in self.infoes:
            _meta = {
                **info,
                "use_playwright": self.use_playwright
            }
            url = info.get('url')
            yield scrapy.Request(
                url=url,
                callback=self.parse_item,
                meta=copy.deepcopy(_meta),
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
        detail_xpath = _meta.get('detail_xpath')
        url_xpath = _meta.get('url_xpath')
        title_xpath = _meta.get('title_xpath')
        publish_time_xpath = _meta.get('publish_time_xpath')
        body_xpath = _meta.get('body_xpath')
        total = _meta.get('total')
        page = _meta.get('page')
        base_url = _meta.get('base_url')

        for ex_url in response.xpath(detail_xpath):
            url = response.urljoin(ex_url.xpath(url_xpath).extract_first())
            if url.endswith('.pdf'):
                continue

            if title_xpath:
                title = ''.join(ex_url.xpath(title_xpath).extract())
            else:
                title = None

            if publish_time_xpath:
                publish_time = ''.join(ex_url.xpath(f'string({publish_time_xpath})').extract()).strip()
            else:
                publish_time = None

            meta = {
                "label": label,
                "title": title,
                'publish_time': publish_time,
                'body_xpath': body_xpath,
                "use_playwright": self.use_playwright
            }
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(meta)
            )

        if page < total:
            page += 1
            yield scrapy.Request(
                url=base_url.format(page),
                callback=self.parse_item,
                meta=copy.deepcopy({
                    'label': label,
                    'detail_xpath': detail_xpath,
                    'url_xpath': url_xpath,
                    'title_xpath': title_xpath,
                    'publish_time_xpath': publish_time_xpath,
                    'body_xpath': body_xpath,
                    'total': total,
                    'page': page,
                    'base_url': base_url,
                    "use_playwright": self.use_playwright
                }),
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

        body_xpath = _meta.get('body_xpath')
        title = response.xpath('//meta[@name="ArticleTitle"]/@content').extract_first() or _meta.get('title')
        publish_time = _meta.get('publish_time') or \
                       response.xpath('//meta[@name="PubDate"]/@content').extract_first()

        author = response.xpath('//meta[@name="Author"]/@content').extract_first() or \
                  ''.join(re.findall(r'<span class="date">.*?来源：(.*?)</span>', response.text, re.DOTALL))

        attachment_urls = response.xpath(f'{body_xpath}//a')

        yield DataItem({
            "_id": md5(f'{method}{url}{body}'.encode('utf-8')).hexdigest(),
            "url": url,
            'spider_from': self._from,
            'label': _meta.get('label'),
            'title': title,
            'author': author,
            'publish_time': publish_time,
            'body_html': ' '.join(response.xpath(body_xpath).extract()),
            "content": ' '.join(response.xpath(f'{body_xpath}//text()').extract()).replace('语音播报：', ''),
            "images": [response.urljoin(i) for i in response.xpath(f'{body_xpath}//img/@src').extract()],
            "attachment": get_attachment(attachment_urls, url, self._from),
            "spider_date": get_now_date(),
            'spider_topic': policy_kafka_topic
        })
