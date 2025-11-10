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
    name = 'policy_xbnyj'
    allowed_domains = [
        'nea.gov.cn',
        'news.cn',
        'www.gov.cn',
        'www.xinhuanet.com'
    ]

    _from = '西北能源局'
    dupefilter_field = {
        "batch": "20240322"
    }

    infoes = [
        {
            'url': 'https://xbj.nea.gov.cn/xxgk/zcfg/gjfl/index.html',
            'label': "首页;信息公开;政策法规;国家法律",
            'detail_xpath': '//ul[@class="wrapper_item_con4_ul"]/li/a',
            'url_xpath': './@href',
            'title_xpath': './span[1]/text()',
            'publish_time_xpath': './span[2]/text()',
            'body_xpath': '//div[@class="article-content" or @id="detail" or @class="wrapper_detail_text" or @id="UCAP-CONTENT" or @id="content"]',
            'total': 2,
            'page': 0,
            'base_url': 'https://xbj.nea.gov.cn/xxgk/zcfg/gjfl/index_{}.html'
        },
        {
            'url': 'https://xbj.nea.gov.cn/xxgk/zcfg/xzfg/index.html',
            'label': "首页;信息公开;政策法规;行政法规",
            'detail_xpath': '//ul[@class="wrapper_item_con4_ul"]/li/a',
            'url_xpath': './@href',
            'title_xpath': './span[1]/text()',
            'publish_time_xpath': './span[2]/text()',
            'body_xpath': '//div[@class="article-content" or @id="detail" or @class="wrapper_detail_text"]',
            'total': 1,
            'page': 0,
            'base_url': 'https://xbj.nea.gov.cn/xxgk/zcfg/xzfg/index_{}.html'
        },
        {
            'url': 'https://xbj.nea.gov.cn/xxgk/zcfg/bmgz/index.html',
            'label': "首页;信息公开;政策法规;部门规章",
            'detail_xpath': '//ul[@class="wrapper_item_con4_ul"]/li/a',
            'url_xpath': './@href',
            'title_xpath': './span[1]/text()',
            'publish_time_xpath': './span[2]/text()',
            'body_xpath': '//div[@class="article-content" or @id="detail" or @class="wrapper_detail_text"]',
            'total': 1,
            'page': 0,
            'base_url': 'https://xbj.nea.gov.cn/xxgk/zcfg/bmgz/index_{}.html'
        },
        {
            'url': 'https://xbj.nea.gov.cn/xxgk/zcfg/gfxwj/index.html',
            'label': "首页;信息公开;政策法规;规范性文件",
            'detail_xpath': '//ul[@class="wrapper_item_con4_ul"]/li/a',
            'url_xpath': './@href',
            'title_xpath': './span[1]/text()',
            'publish_time_xpath': './span[2]/text()',
            'body_xpath': '//div[@class="article-content" or @id="detail" or @class="wrapper_detail_text"]',
            'total': 2,
            'page': 0,
            'base_url': 'https://xbj.nea.gov.cn/xxgk/zcfg/gfxwj/index_{}.html'
        },
        {
            'url': 'https://xbj.nea.gov.cn/xxgk/zcjd/index.html',
            'label': "首页;信息公开;政策解读",
            'detail_xpath': '//ul[@class="wrapper_item_con4_ul"]/li/a',
            'url_xpath': './@href',
            'title_xpath': './span[1]/text()',
            'publish_time_xpath': './span[2]/text()',
            'body_xpath': '//div[@class="article-content" or @id="detail" or @class="wrapper_detail_text"]',
            'total': 6,
            'page': 0,
            'base_url': 'https://xbj.nea.gov.cn/xxgk/zcjd/index_{}.html'
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
            )

        if page + 1 <= total:
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
        publish_time = _meta.get('publish_time')
        author = response.xpath('//meta[@name="Author"]/@content').extract_first() or \
            ''.join(re.findall(r'<span>来源：</span>(.*?)</div>', response.text, re.DOTALL)).strip() or \
            ''.join(re.findall(r'<span class="author">.*?来源：(.*?)</span>', response.text, re.DOTALL)).strip() or \
            ''.join(re.findall(r'<span>来源：(.*?)</span>', response.text, re.DOTALL)).strip()

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
