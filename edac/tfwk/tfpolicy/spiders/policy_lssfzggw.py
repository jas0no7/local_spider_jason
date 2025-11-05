import copy
import json
import re
from hashlib import md5
from xml import etree

import requests
import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment

settings = get_project_settings()

policy_kafka_topic = settings.get('POLICY_KAFKA_TOPIC')


class DataSpider(CrawlSpider):
    name = 'policy_lssfzggw'
    allowed_domains = [
        'sfgw.leshan.gov.cn'
    ]

    _from = '乐山市发展和改革委员会'
    dupefilter_field = {
        "batch": "20250509"
    }
    use_playwright = True
    custom_settings = {
        "CONCURRENT_REQUESTS": 3,
        "DOWNLOAD_TIMEOUT": 10,
        "DOWNLOAD_DELAY": 3
    }

    infoes = [
        {
            'url': 'https://sfgw.leshan.gov.cn/govinfo2/channel/index/33',
            'label': "政策文件",
            'detail_xpath': '//tbody[@id="dataList"]/tr',
            'url_xpath': './td[2]/a/@href',
            'title_xpath': './td[2]/a/@title',
            'publish_time_xpath': './td[3]/text()',
            'body_xpath': '//div[@class="xxgk_content_info"]',
            'total': 1,
            'page': 1,
            'base_url': ''
        },
    ]

    def start_requests(self):
        for info in self.infoes:
            _meta = {
                **info,
                "use_playwright": self.use_playwright
            }
            url = info.get('url')
            yield scrapy.Request(
                url=url,
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
        page = _meta.get('page')
        self.regionid = re.findall('var regionid = "(\d+)"', response.text)[0]
        deptId = re.findall('var deptId = "(\d+)"', response.text)[0]
        chId = re.findall('var chId = "(\d+)"', response.text)[0]
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "https://sfgw.leshan.gov.cn/govinfo2/channel/index/33",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
        }
        for i in range(0, page):
            data = {
                "regionid": str(self.regionid),
                "deptId": str(deptId),
                "channelId": str(chId),
                "pageNo": f"{i + 1}",
                "pageSize": "15"
            }
            response = requests.post(url = "https://sfgw.leshan.gov.cn/open-information/document/list.do", headers = headers, data=data)
            response.encoding = 'utf-8'
            datasa = json.loads(response.text)['data']['dataList']
            for ex_url in datasa:
                id = ex_url.get('id')
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Referer": "https://sfgw.leshan.gov.cn/govinfo2/channel/index/33",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
                }
                yield scrapy.FormRequest(
                    url='https://sfgw.leshan.gov.cn/open-information/document/info.do',
                    formdata={'id': id},
                    headers=headers,
                    callback=self.parse_detail,
                    meta={'meta_data': ex_url},  # 你可以传原始数据进去
                    dont_filter=True
                )



    def parse_detail(self, response):
        data = json.loads(response.text)['data']
        title = data['publicDocument']['title']
        author = ''
        publish_time = data['template01']['cataloguingTime']
        body_html = data['template01']['content']  # 纯 HTML 字符串
        id = data['publicDocument']['id']
        url = f'https://sfgw.leshan.gov.cn/fgwa/xxgkcontent/list_xxgkcontent.shtml?id={id}'
        'https://sfgw.leshan.gov.cn/fgwa/xxgkcontent/Articles/90053490/2024/05/10/20240510094805-587731.docx'
        # 使用 Scrapy Selector 解析 HTML 内容
        selector = scrapy.Selector(text=body_html)

        content = ' '.join(selector.xpath('//text()').getall()).replace('语音播报：', '')
        images = [response.urljoin(i) for i in selector.xpath('//img/@src').getall()]

        attachment_urls = []
        for f in data.get('files', []):
            if f:
                relPath = f.get('relPath')
                attachment_urls.append('https://sfgw.leshan.gov.cn/fgwa/xxgkcontent/'+f'{relPath}'+f['fileName'])# 自己根据数据结构调整
        if attachment_urls:
            attachment_urls = ("<a>" +i+"</a>" for i in attachment_urls)
        else:
            attachment_urls = set()

        yield DataItem({
            "_id": md5(f'{id}'.encode('utf-8')).hexdigest(),
            "url": url,
            'spider_from': self._from,
            'label': "政策文件",
            'title': title,
            'author': author,
            'publish_time': publish_time,
            'body_html': body_html,
            "content": content,
            "images": images,
            "attachment": get_attachment(attachment_urls, url, self._from),
            "spider_date": get_now_date(),
            'spider_topic': policy_kafka_topic
        })
