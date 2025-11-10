import copy
import json
from hashlib import md5

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from edac.tfwk.tfpolicy.mydefine import get_now_date, get_attachment

settings = get_project_settings()

policy_kafka_topic = settings.get('POLICY_KAFKA_TOPIC')


class DataSpider(CrawlSpider):
    name = 'policy_cdsrmzf'
    allowed_domains = [
        'www.chengdu.gov.cn'
    ]

    _from = '成都市人民政府'
    dupefilter_field = {
        "batch": "20240322"
    }
    use_playwright = True
    custom_settings = {
        "CONCURRENT_REQUESTS": 3,
        "DOWNLOAD_TIMEOUT": 25,
        "DOWNLOAD_DELAY": 3
    }

    infoes_ajax = [
        {
            'url': 'https://www.chengdu.gov.cn/gkml/api/policyLibrary/listPage?deptTypeId=1564154428109889538&current={}&size=20',
            'label': "首页;政务公开;政府信息公开专栏;政策;列表;市政府",
            'page': 1,
        },
        {
            'url': 'https://www.chengdu.gov.cn/gkml/api/policyLibrary/listPage?deptId=1607625235320909825&current={}&size=20',
            'label': "首页;政务公开;政府信息公开专栏;政策;市级部门政府;市政府办公厅",
            'page': 1,
        }
    ]

    def start_requests(self):
        for info in self.infoes_ajax:
            _meta = {
                **info,
                "use_playwright": self.use_playwright
            }
            url = info.get('url')
            yield scrapy.Request(
                url=url.format(1),
                callback=self.parse_item_ajax,
                meta=copy.deepcopy(_meta),
                dont_filter=True
            )

    def parse_item_ajax(self, response):
        """
        详情和下一页url
        :param response:
        :return:
        """

        _meta = response.meta
        label = _meta.get('label')
        start_url = _meta.get('url')
        page = _meta.get('page')

        try:
            result = json.loads(response.xpath('//text()').extract_first())
            result = result.get('data')
            datas = result.get('records', [])
            pages = result.get('pages', 1)
        except:
            pass
        else:
            for data in datas:
                url = data.get('detailInfoUrl')
                if not url:
                    continue

                meta = {
                    "label": label,
                    "title": data.get('name'),
                    "author": data.get('fullName'),
                    'publish_time': data.get('checkTime', '')[:10],
                    "use_playwright": self.use_playwright
                }
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                    meta=copy.deepcopy(meta)
                )

            if page < pages:
                page += 1
                yield scrapy.Request(
                    url=start_url.format(page),
                    callback=self.parse_item_ajax,
                    meta=copy.deepcopy({
                        'url': start_url,
                        'label': label,
                        'page': page,
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

        body_xpath = '//div[@class="content" or @id="content"]'

        title = _meta.get('title') or response.xpath('//meta[@name="ArticleTitle"]/@content').extract_first()
        publish_time = _meta.get('publish_time') or \
                       response.xpath('//meta[@name="PubDate"]/@content').extract_first()

        author = _meta.get('author') or \
                 response.xpath('//meta[@name="Author"]/@content').extract_first() or \
                 response.xpath('//meta[@name="ContentSource"]/@content').extract_first()
        author = author.replace('责任单位：', '') if author else None

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
