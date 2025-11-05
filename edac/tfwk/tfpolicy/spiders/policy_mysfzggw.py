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
    name = 'policy_mysfzggw'
    allowed_domains = [
        'fgw.my.gov.cn'
    ]

    _from = '绵阳市发展和改革委员会'
    dupefilter_field = {
        "batch": "20241111"
    }
    headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Host": "fgw.my.gov.cn",
        "Pragma": "no-cache",
        "Referer": "https://fgw.my.gov.cn/mysfgw/c100289/list.shtml",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
        "X-Requested-With": "XMLHttpRequest",
    }

    infoes = [
        {
            'url': 'https://fgw.my.gov.cn/common/search/843b17cc25584632b77b56a6f583722b?_isAgg=true&_isJson=true&_pageSize=18&_template=index&_rangeTimeGte=&_channelName=&page={}',
            'label': "首页;政务公开;政策文件与解读",
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
                headers=self.headers,
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
        try:
            result = response.json()
            data = result.get('data')
            total = data.get('total')
            rows = data.get('rows')
            page = data.get('page')
            datas = data.get('results')
        except:
            pass
        else:
            for da in datas:
                column_folder = da.get('columnFolder')
                _id = da.get('id')
                meta = {
                    "label": label,
                    "title": da.get('title'),
                    'publish_time': da.get('publishedTimeStr'),
                    'author': da.get('zuozhe')
                }
                yield scrapy.Request(
                    url=f'https://fgw.my.gov.cn{da.get("url")}',
                    callback=self.parse_detail,
                    meta=copy.deepcopy(meta),
                )

            if page * rows < total:
                page += 1
                yield scrapy.Request(
                    url=url.format(page),
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

        body_xpath = '//div[@id="zoom"]'

        title = response.xpath('//meta[@name="ArticleTitle"]/@content').extract_first() or _meta.get('title')
        publish_time = _meta.get('publish_time') or \
                       response.xpath('//meta[@name="PubDate"]/@content').extract_first()

        author = _meta.get('author') or \
                 ''.join(re.findall(r'<span>作者：(.*?)</span>', response.text, re.DOTALL)) or \
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
