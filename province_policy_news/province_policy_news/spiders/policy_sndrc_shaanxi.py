import copy
import re
from hashlib import md5

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment

settings = get_project_settings()


class DataSpider(CrawlSpider):
    name = 'policy_sndrc_shaanxi'
    allowed_domains = [
        'sndrc.shaanxi.gov.cn'
    ]

    _from = '陕西省发展和改革委员会'
    category = "政策"
    dupefilter_field = {
        "batch": "20240322"
    }

    infoes = [
        {
            'url': 'https://sndrc.shaanxi.gov.cn/zfxxgk/zc/fgwj/sfzggwwj/2025/index.html',
            'label': "省发展改革委文件",
            'detail_xpath': '//ul[@class="rightList"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/text()',
            'publish_time_xpath': '',
            'body_xpath': '//div[@class="main"]',
            'total': 3,
            'page': 1,
            'base_url': 'https://sndrc.shaanxi.gov.cn/zfxxgk/zc/fgwj/sfzggwwj/2025/index_{}.html'
        },
        {
            'url': 'https://sndrc.shaanxi.gov.cn/zfxxgk/zc/fgwj/xzgfxwj/index.html',
            'label': "行政规范文件",
            'detail_xpath': '//ul[@class="rightList"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/text()',
            'publish_time_xpath': './span/text()',
            'body_xpath': '//div[@class="main"]',
            'total': 5,
            'page': 1,
            'base_url': 'https://sndrc.shaanxi.gov.cn/zfxxgk/zc/fgwj/xzgfxwj/index_{}.html'
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

        if False and page < total:
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
        body = response.request.body.decode('utf-8') if response.request.body else ''
        url = response.request.url

        body_xpath = _meta.get('body_xpath')
        title = _meta.get('title') or response.xpath('//meta[@name="ArticleTitle"]/@content').extract_first()
        publish_time = _meta.get('publish_time') or \
                       ''.join(response.xpath('//publishtime/text()').extract()).strip() or \
                       ''.join(re.findall(r'发布日期.*?(\d{4}-\d{2}-\d{2})', response.text, re.DOTALL)).strip()
        label = _meta.get('label')

        author = response.xpath('//meta[@name="Author"]/@content').extract_first() or \
                 ''.join(re.findall(r'发布机构：</strong><span>(.*?)</span></li>', response.text, re.DOTALL)).strip() or \
                 ''.join(re.findall(r'>信息来源：(.*?)</', response.text, re.DOTALL)).strip()

        attachment_urls = response.xpath(
            '//p[contains(@class, "insertfileTag")]//a | '
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or '
            'contains(@href, ".xls") or contains(@href, ".xlsx") or contains(@href, ".wps") or '
            'contains(@href, ".zip") or contains(@href, ".rar")]'
        )

        images = [response.urljoin(i) for i in response.xpath(f'{body_xpath}//img/@src').extract()]
        attachments = get_attachment(attachment_urls, url, self._from)

        yield DataItem({
            "_id": md5(f'{method}{url}{body}'.encode('utf-8')).hexdigest(),
            "url": url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            'spider_from': self._from,
            'label': label,
            'title': title,
            'author': author,
            'publish_time': publish_time,
            'body_html': ' '.join(response.xpath(body_xpath).extract()),
            "content": ' '.join(response.xpath(f'{body_xpath}//text()').extract()),
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category
        })
