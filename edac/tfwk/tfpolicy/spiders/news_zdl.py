import copy
from hashlib import md5
from time import strftime, localtime

import scrapy
from scrapy.selector import Selector
from scrapy.spiders import CrawlSpider

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment


class DataSpider(CrawlSpider):
    name = 'news_zdl'
    allowed_domains = [
        'cec.org.cn'
    ]

    dupefilter_field = {
        "batch": "20241206"
    }

    infoes = [
        {
            'url': 'https://cec.org.cn/ms-mcms/mcms/content/list?id=169&pageNumber={}&pageSize=10',
            'label': '行业要闻'
        },
    ]
    custom_settings = {
        "CONCURRENT_REQUESTS": 3,
        "DOWNLOAD_TIMEOUT": 10,
        "DOWNLOAD_DELAY": 3
    }

    def start_requests(self):
        for info in self.infoes:
            url = info.get('url')
            yield scrapy.Request(
                url=url.format(150),
                callback=self.parse_item,
                meta=copy.deepcopy({
                    "url": url,
                    "label": info.get("label"),
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
        url = _meta.get('url')

        try:
            result = response.json()
            data = result.get('data')
            total_page = data.get('totalPage')
            page_num = data.get('pageNum')
            datas = data.get('list')
        except:
            pass
        else:
            for da in datas:
                _id = da.get('articleID')
                meta = {
                    "label": label,
                    "title": da.get('basicTitle'),
                    "id": _id,
                }
                yield scrapy.Request(
                    url=f'https://cec.org.cn/ms-mcms/mcms/content/detail?id={_id}',
                    callback=self.parse_detail,
                    meta=copy.deepcopy(meta),
                )

            if page_num < total_page:
                page_num += 1
                yield scrapy.Request(
                    url=url.format(page_num),
                    callback=self.parse_item,
                    meta=copy.deepcopy({
                        'url': url,
                        'label': label,
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

        _meta = response.meta
        label = _meta.get('label')
        title = _meta.get('title')
        _id = _meta.get('id')

        try:
            result = response.json()
            data = result.get('data')
        except:
            pass
        else:
            body_html = data.get('articleContent')
            if not body_html:
                return

            html = Selector(text=body_html)
            attachment_urls = html.xpath('//a')
            _from = data.get('source')
            yield DataItem({
                "_id": md5(f'{method}{url}{body}*'.encode('utf-8')).hexdigest(),
                "url": f'https://www.cec.org.cn/detail/index.html?3-{_id}',
                'spider_from': _from,
                'label': label,
                'title': title,
                'author': data.get('articleAuthor'),
                'publish_time': self.change_time(data.get('publicTime')),
                'body_html': body_html,
                "content": ' '.join(html.xpath('//text()').extract()),
                "images": [response.urljoin(i) for i in html.xpath('//img/@src').extract()],
                "attachment": get_attachment(attachment_urls, url, _from),
                "spider_date": get_now_date(),
                "spider_topic": "spider-news-zdl-v1"
            })

    def change_time(self, _time, fmt='%Y-%m-%d %H:%M:%S'):
        """
        时间戳格式化
        :param _time:
        :param fmt: 格式化
        :return:
        """
        try:
            if len(str(_time)) > 10:
                _time = int(_time / 1000)

            if isinstance(_time, str):
                _time = int(_time)

            return strftime(fmt, localtime(_time))
        except:
            return ''
