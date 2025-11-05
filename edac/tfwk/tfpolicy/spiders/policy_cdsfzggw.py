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
    name = 'policy_cdsfzggw'
    allowed_domains = [
        'cddrc.chengdu.gov.cn'
    ]

    _from = '成都市发展和改革委员会'
    dupefilter_field = {
        "batch": "20240322"
    }
    use_playwright = True
    custom_settings = {
        "CONCURRENT_REQUESTS": 3,
        "DOWNLOAD_TIMEOUT": 30,
        "DOWNLOAD_DELAY": 3
    }

    infoes = [
        {
            'url': 'https://cddrc.chengdu.gov.cn/cdfgw/c112453/list_3.shtml',
            'label': "首页;政务公开;最新信息公开",
            'detail_xpath': '//div[@class="more-list"]/ul/li/a',
            'url_xpath': './@href',
            'title_xpath': './@title',
            'publish_time_xpath': './span[@class="date"]/text()',
            'body_xpath': '//div[@class="content-area"]',
            'total': 4,
            'page': 1,
            'base_url': 'https://cddrc.chengdu.gov.cn/cdfgw/c112453/list_3_{}.shtml'
        },
        {
            'url': 'https://cddrc.chengdu.gov.cn/cdfgw/jkhqdata001/jksj_list.shtml?classId=1580116519959474177',
            'label': "首页;政务公开;部门文件;行政规范性文件",
            'detail_xpath': '//div[@class="more-list"]/ul/li/a',
            'url_xpath': './@href',
            'title_xpath': './@title',
            'publish_time_xpath': './span[@class="date"]/text()',
            'body_xpath': '//div[@class="content-area"]',
            'total': 1,
            'page': 1,
            'base_url': 'https://cddrc.chengdu.gov.cn/cdfgw/jkhqdata001/jksj_list.shtml?classId=1580116519959474177&pageNum={}'
        },
        {
            'url': 'https://cddrc.chengdu.gov.cn/cdfgw/jkhqdata001/jksj_list.shtml?classId=1588371990657957890',
            'label': "首页;政务公开;部门文件;其他文件",
            'detail_xpath': '//div[@class="more-list"]/ul/li/a',
            'url_xpath': './@href',
            'title_xpath': './@title',
            'publish_time_xpath': './span[@class="date"]/text()',
            'body_xpath': '//div[@class="content-area"]',
            'total': 20,
            'page': 1,
            'base_url': 'https://cddrc.chengdu.gov.cn/cdfgw/jkhqdata001/jksj_list.shtml?classId=1588371990657957890&pageNum={}'
        },
        {
            'url': 'https://cddrc.chengdu.gov.cn/cdfgw/c112462/jksj_list.shtml?classId=1583411220128514049',
            'label': "首页;政务公开;政策解读和热点回应",
            'detail_xpath': '//div[@class="more-list"]/ul/li/a',
            'url_xpath': './@href',
            'title_xpath': './@title',
            'publish_time_xpath': './span[@class="date"]/text()',
            'body_xpath': '//div[@class="content-area"]',
            'total': 7,
            'page': 1,
            'base_url': 'https://cddrc.chengdu.gov.cn/cdfgw/c112462/jksj_list.shtml?classId=1583411220128514049&pageNum={}'
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

            title = ''.join(ex_url.xpath(title_xpath).extract())
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
        title = _meta.get('title') or response.xpath('//meta[@name="ArticleTitle"]/@content').extract_first()
        publish_time = _meta.get('publish_time') or \
                       response.xpath('//meta[@name="PubDate"]/@content').extract_first()

        author = ''.join(re.findall(r'<span class="date">.*?来源：(.*?)</span>', response.text, re.DOTALL))

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
            "content": ' '.join(response.xpath(f'{body_xpath}//text()').extract()),
            "images": [response.urljoin(i) for i in response.xpath(f'{body_xpath}//img/@src').extract()],
            "attachment": get_attachment(attachment_urls, url, self._from),
            "spider_date": get_now_date(),
            'spider_topic': policy_kafka_topic
        })
