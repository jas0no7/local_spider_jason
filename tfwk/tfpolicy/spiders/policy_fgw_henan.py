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
    name = 'policy_fgw_henan'
    allowed_domains = [
        'fgw.henan.gov.cn'
    ]

    _from = '河南省发展和改革委员会'
    dupefilter_field = {
        "batch": "20240322"
    }

    infoes = [
        {
            'url': 'https://fgw.henan.gov.cn/zmhd/zjdc/',
            'label': "征集调查",
            'detail_xpath': '//table[@class="zmhd-table"]/tbody/tr',
            'url_xpath': './td[1]/a/@href',
            'title_xpath': './td[1]/a/@title',
            'publish_time_xpath': './td[4]',
            'body_xpath': '//div[@class="yMain"]',
            'total': 1,
            'page': 1,
            'base_url': 'https://fgw.henan.gov.cn/zmhd/zjdc/'
        },
        {
            'url': 'https://fgw.henan.gov.cn/zwgk/zc/xzgfxwj/index.html',
            'label': "规范性文件",
            'detail_xpath': '//div[@class="zfxxgk_zdgkc"]/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './b',
            'body_xpath': '//div[@class="yMain"]',
            'total': 2,
            'page': 1,
            'base_url': 'https://fgw.henan.gov.cn/zwgk/zc/xzgfxwj/index_{}.html'
        },


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
                publish_time = ''.join(ex_url.xpath(f'string({publish_time_xpath})').extract()).replace('(', '').replace(')', '').strip()
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
                dont_filter=True
            )

        if page < total:
            page += 1
            if page == 1:
                next_url = _meta['url']
            else:
                next_url = base_url.format(page)
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
            'spider_topic': "spider-policy-henan"
        })

