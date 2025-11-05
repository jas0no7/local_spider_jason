import copy
from hashlib import md5
from json import dumps

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings
from urllib.parse import urlencode
from ..items import DataItem
from ..mydefine import get_now_date, get_attachment

settings = get_project_settings()

policy_kafka_topic = settings.get('POLICY_KAFKA_TOPIC')


class DataSpider(CrawlSpider):
    name = 'policy_dzsfzggw'
    allowed_domains = [
        'fgw.dazhou.gov.cn'
    ]

    _from = '达州市发展和改革委员会'
    dupefilter_field = {
        "batch": "20241111"
    }
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://fgw.dazhou.gov.cn",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://fgw.dazhou.gov.cn/news-list-zhengcejiedu.html",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
        "x-requested-with": "XMLHttpRequest"
    }
    page_size = 20

    infoes = [
        {
            'url': 'https://fgw.dazhou.gov.cn/api-ajax_list-{}.html',
            'label': "政策解读",
            "body": 'ajax_type%5B%5D=3_news&ajax_type%5B%5D=47&ajax_type%5B%5D=3&ajax_type%5B%5D=news&ajax_type%5B%5D=Y-m-d&ajax_type%5B%5D=40&ajax_type%5B%5D=20&ajax_type%5B%5D=0&ajax_type%5B8%5D=&is_ds=1',
            'page': 1
        },
        {
            'url': 'https://fgw.dazhou.gov.cn/api-ajax_list-{}.html',
            'label': "政策文件",
            "body": 'ajax_type%5B%5D=3_news&ajax_type%5B%5D=46&ajax_type%5B%5D=3&ajax_type%5B%5D=news&ajax_type%5B%5D=Y-m-d&ajax_type%5B%5D=40&ajax_type%5B%5D=20&ajax_type%5B%5D=0&ajax_type%5B8%5D=&is_ds=1',
            'page': 1
        }
    ]

    def start_requests(self):
        for info in self.infoes:
            _meta = {
                **info,
            }
            url = info.get('url')
            body = info.get('body')
            yield scrapy.Request(
                url=url.format(1),
                method="POST",
                headers=self.headers,
                body=body,
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
        url = _meta.get('url')
        body = _meta.get('body')
        page = _meta.get('page')
        try:
            result = response.json()
            datas = result.get('data')
            total = result.get('total')
        except:
            pass
        else:
            for da in datas:
                column_folder = da.get('columnFolder')
                _id = da.get('id')
                meta = {
                    "label": label,
                    "title": da.get('title'),
                    'publish_time': da.get('inputtime'),
                    'author': da.get('zuozhe')
                }
                yield scrapy.Request(
                    url=da.get('url'),
                    callback=self.parse_detail,
                    meta=copy.deepcopy(meta),
                )

            if page * self.page_size < total:
                page += 1
                yield scrapy.Request(
                    url=url.format(page),
                    callback=self.parse_item,
                    meta=copy.deepcopy({
                        'url': url,
                        'label': label,
                        "body": body,
                        'page': page
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

        body_xpath = '//div[@class="content"]'

        title = response.xpath('//meta[@name="ArticleTitle"]/@content').extract_first() or _meta.get('title')
        publish_time = _meta.get('publish_time') or \
                       response.xpath('//meta[@name="PubDate"]/@content').extract_first()

        author = _meta.get('author') or \
                 response.xpath('//meta[@name="Author"]/@content').extract_first() or \
                 response.xpath('//meta[@name="ContentSource"]/@content').extract_first()

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
