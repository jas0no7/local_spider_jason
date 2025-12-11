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
    name = 'news_fgw_sichuan'
    allowed_domains = [
        'fgw.sc.gov.cn'
    ]

    _from = '四川发改委'
    category = "新闻"
    dupefilter_field = {
        "batch": "20240322"
    }

    infoes = [
        {
            'url': 'https://fgw.sc.gov.cn/sfgw/fgyw/common_list.shtml',
            'label': "发改动态",
            'detail_xpath': '//ul[@class="list"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/text()',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@class="detail"]',
            'total': 43,
            'page': 1,
            'base_url': 'https://fgw.sc.gov.cn/sfgw/fgyw/common_list_{}.shtml'
        },
        {
            'url': 'https://fgw.sc.gov.cn/sfgw/xwfb/common_list.shtml',
            'label': "新闻发布",
            'detail_xpath': '//ul[@class="list"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/text()',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@class="detail"]',
            'total': 10,
            'page': 1,
            'base_url': 'https://fgw.sc.gov.cn/sfgw/xwfb/common_list_{}.shtml'
        },
    ]

    # ===============================
    # 1. 请求每个栏目的第一页
    # ===============================
    def start_requests(self):
        for info in self.infoes:
            url = info.get('url')
            yield scrapy.Request(
                url=url,
                callback=self.parse_item,
                meta=copy.deepcopy(info),
                dont_filter=True
            )

    # ===============================
    # 2. 解析列表页（只采第一页）
    # ===============================
    def parse_item(self, response):
        """
        列表页 → 提取详情页 URL（只采第一页）
        """
        _meta = response.meta
        label = _meta.get('label')
        detail_xpath = _meta.get('detail_xpath')
        url_xpath = _meta.get('url_xpath')
        title_xpath = _meta.get('title_xpath')
        publish_time_xpath = _meta.get('publish_time_xpath')
        body_xpath = _meta.get('body_xpath')

        # ----------- 只采第一页的文章链接 -----------
        for ex_url in response.xpath(detail_xpath):
            url = response.urljoin(ex_url.xpath(url_xpath).extract_first())
            if url.endswith('.pdf'):
                continue

            title = ''.join(ex_url.xpath(title_xpath).extract())
            if publish_time_xpath:
                publish_time = ''.join(
                    ex_url.xpath(f'string({publish_time_xpath})').extract()
                ).replace('(', '').replace(')', '').strip()
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

        # ----------- 禁止翻页（删除分页逻辑）-----------
        return

    # ===============================
    # 3. 解析详情页内容
    # ===============================
    def parse_detail(self, response):
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
