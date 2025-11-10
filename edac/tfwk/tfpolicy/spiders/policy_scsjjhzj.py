import copy
import re
from hashlib import md5

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from edac.tfwk.tfpolicy.mydefine import get_now_date, get_attachment

settings = get_project_settings()

policy_kafka_topic = settings.get('POLICY_KAFKA_TOPIC')


class DataSpider(CrawlSpider):
    name = 'policy_scsjjhzj'
    allowed_domains = [
        'jhj.sc.gov.cn'
    ]

    _from = '四川省经济合作局'
    dupefilter_field = {
        "batch": "20240322"
    }

    infoes = [
        {
            'url': 'https://jhj.sc.gov.cn/scjhj/gfxwenjian/zfgkzclist.shtml',
            'label': "政策;行政规范性文件",
            'detail_xpath': '//div[@class="tab_zc_list"]',
            'url_xpath': './div[contains(@class,"tab_list_title")]/p/a/@href',
            'title_xpath': './div[contains(@class,"tab_list_title")]/p/a/text()',
            'publish_time_xpath': './div[contains(@class,"tab_list_fbrq")]/text()',
            'body_xpath': '//div[@class="con_list" or @class="xxgkzn_files"]',
            'total': 1,
            'page': 1,
            'base_url': ''
        },
        {
            'url': 'https://jhj.sc.gov.cn/scjhj/qtwj/zfgkzcqtlist.shtml',
            'label': '政策;其他文件',
            'detail_xpath': '//div[@class="tab_zc_list"]',
            'url_xpath': './div[contains(@class,"tab_list_title")]/p/a/@href',
            'title_xpath': './div[contains(@class,"tab_list_title")]/p/a/text()',
            'publish_time_xpath': './div[contains(@class,"tab_list_cwrq")]/text()',
            'body_xpath': '//div[@class="con_list" or @class="xxgkzn_files"]',
            'total': 1,
            'page': 1,
            'base_url': 'http://tjj.sc.gov.cn/scstjj/c105918/common_list_{}.shtml'
        },
        {
            'url': 'https://jhj.sc.gov.cn/scjhj/tzzc/tzzc_index.shtml',
            'label': "投资四川;投资政策",
            'detail_xpath': '//ul[@class="new_list_zcjd"]/li',
            'url_xpath': './/a/@href',
            'title_xpath': './/a/text()',
            'publish_time_xpath': './/a/em/text()',
            'body_xpath': '//div[@class="content_con"]',
            'total': 14,
            'page': 1,
            'base_url': 'https://jhj.sc.gov.cn/scjhj/tzzc/tzzc_index_{}.shtml'
        },
        {
            'url': 'https://jhj.sc.gov.cn/scjhj/zcjd/zcjd_index.shtml',
            'label': "投资四川;政策解读",
            'detail_xpath': '//ul[@class="new_list_zcjd"]/li',
            'url_xpath': './/a/@href',
            'title_xpath': './/a/text()',
            'publish_time_xpath': './/a/em/text()',
            'body_xpath': '//div[@class="content_con"]',
            'total': 15,
            'page': 1,
            'base_url': 'https://jhj.sc.gov.cn/scjhj/zcjd/zcjd_index_{}.shtml'
        }
    ]

    def start_requests(self):
        for info in self.infoes:
            url = info.get('url')
            yield scrapy.Request(
                url=url,
                callback=self.parse_item,
                meta=copy.deepcopy(info),
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
            }
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(meta),
            )

        if page < total:
            page += 1
            yield scrapy.Request(
                url=f'{base_url.format(page)}',
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
                       ''.join(re.findall(r'发布日期：</strong><span>(.*?)</span>', response.text, re.DOTALL)).strip() or \
                       ''.join(re.findall(r'<em>发布时间：(.*?)</em>', response.text, re.DOTALL)).strip() or \
                       ''.join(re.findall(r'<em>发布日期：(.*?)</em>', response.text, re.DOTALL)).strip()

        author = response.xpath('//meta[@name="Author"]/@content').extract_first() or \
                 ''.join(re.findall(r'发布机构：</strong><span title="(.*?)">', response.text, re.DOTALL)).strip() or \
                 ''.join(re.findall(r'<em>来源：(.*?)</em>', response.text, re.DOTALL)).strip()

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
