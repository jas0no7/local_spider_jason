import copy
from hashlib import md5
from json import dumps

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment

settings = get_project_settings()

policy_kafka_topic = settings.get('POLICY_KAFKA_TOPIC')


class DataSpider(CrawlSpider):
    name = 'policy_gzzfzggw'
    allowed_domains = [
        'fgw.gzz.gov.cn'
    ]

    _from = '甘孜藏族自治州发展和改革委员会'
    dupefilter_field = {
        "batch": "20241111"
    }
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "origin": "https://fgw.gzz.gov.cn",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://fgw.gzz.gov.cn/gjj/c/6870",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
    }

    infoes = [
        {
            'url': 'https://fgw.gzz.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId',
            'label': "政策解读",
            "body": {
                "columnId": "14906",
                "current": 1,
                "size": 15,
                "type": True
            },
        },
        {
            'url': 'https://fgw.gzz.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId',
            'label': "首页;政务公开;政策文件;国家级",
            "body": {
                "columnId": "6870",
                "current": 1,
                "size": 15,
                "type": False
            },
        },
        {
            'url': 'https://fgw.gzz.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId',
            'label': "首页;政务公开;政策文件;省级",
            "body": {
                "columnId": 6871,
                "current": 1,
                "size": 15,
                "type": False
            },
        },
        {
            'url': 'https://fgw.gzz.gov.cn/site-service/c/manuscript/getManuscriptListByColumnId',
            'label': "首页;政务公开;政策文件;省级",
            "body": {
                "columnId": 6872,
                "current": 1,
                "size": 15,
                "type": False
            },
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
                url=url,
                method="POST",
                headers=self.headers,
                body=dumps(body, ensure_ascii=False),
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
        try:
            result = response.json()
            data = result.get('data')
            pages = data.get('pages')
            current = data.get('current')
            datas = data.get('records')
        except:
            pass
        else:
            for da in datas:
                column_folder = da.get('columnFolder')
                _id = da.get('id')
                meta = {
                    "label": label,
                    "title": da.get('title'),
                    'publish_time': da.get('releaseTime'),
                }
                yield scrapy.Request(
                    url=f'https://fgw.gzz.gov.cn/{column_folder}/article/{_id}',
                    callback=self.parse_detail,
                    meta=copy.deepcopy(meta),
                )

            if current < pages:
                current += 1
                body.update({
                    'current': current
                })
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_item,
                    meta=copy.deepcopy({
                        'url': url,
                        'label': label,
                        "body": body,
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

        body_xpath = '//div[@id="contentBox" or @class="file_item"]'
        title = response.xpath('//meta[@name="ArticleTitle"]/@content').extract_first() or _meta.get('title')
        publish_time = _meta.get('publish_time') or \
                       response.xpath('//meta[@name="PubDate"]/@content').extract_first()

        author = response.xpath('//meta[@name="Author"]/@content').extract_first() or \
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
