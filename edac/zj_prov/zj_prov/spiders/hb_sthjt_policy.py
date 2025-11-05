import copy
import re
from hashlib import md5
import scrapy
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment
import copy
import re
from hashlib import md5

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment


class HBsthjt(scrapy.Spider):
    name = "hb_sthjt_policy"
    allowed_domains = ["sthjt.hubei.gov.cn"]

    _from = ''
    dupefilter_field = {
        "batch": "20240322"
    }

    infoes = [
        {
            'url': 'https://sthjt.hubei.gov.cn/fbjd/zc/gfxwj/index.shtml',
            'label': "规范性文件",
            'detail_xpath': '//*[@id="zcwjList"]/li/span[2]',
            'url_xpath': './div/a/@href',
            'title_xpath': './div/a/@title',
            'publish_time_xpath': './div/span[2]',
            'body_xpath': '//div[@class="article"]',
            'total': 3,
            'page': 1,
            'base_url': 'https://sthjt.hubei.gov.cn/fbjd/zc/gfxwj/index_{}.shtml'
        },
        {
            'url': 'https://sthjt.hubei.gov.cn/fbjd/zc/zcjd/index.shtml',
            'label': "政策解读",
            'detail_xpath': '//ul[@class="info-list"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@class="article_new"]',
            'total': 5,
            'page': 1,
            'base_url': 'https://sthjt.hubei.gov.cn/fbjd/zc/zcjd/index_{}.shtml'
        },
    ]

    def start_requests(self):
        """起始请求"""
        for info in self.infoes:
            url = info.get('url')
            yield scrapy.Request(
                url=url,
                callback=self.parse_item,
                meta=copy.deepcopy(info),
                dont_filter=True
            )

    def parse_item(self, response):
        """解析列表页，提取详情链接、标题、发布时间"""
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

        # 遍历详情页链接
        for ex_url in response.xpath(detail_xpath):
            url = response.urljoin(ex_url.xpath(url_xpath).get())
            if not url:
                continue

            title = ''.join(ex_url.xpath(title_xpath).getall()).strip()
            publish_time = ''.join(ex_url.xpath(f'string({publish_time_xpath})').getall()).strip() if publish_time_xpath else None

            meta = {
                'label': label,
                'title': title,
                'publish_time': publish_time,
                'body_xpath': body_xpath,
            }

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(meta),
                dont_filter=True
            )

        # 翻页逻辑
        if page < total:
            page += 1

            # 第1页用原始URL，后续页用base_url格式化
            if page == 1:
                next_url = _meta['url']
            else:
                next_url = base_url.format(page)

            print(f"正在抓取第 {page} 页：{next_url}")

            yield scrapy.Request(
                url=next_url,
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
                    'url': _meta['url']  # 保留原始URL
                }),
                dont_filter=True
            )

    def parse_detail(self, response):
        """解析详情页内容"""
        _meta = response.meta
        method = response.request.method
        body = response.request.body.decode('utf-8') if response.request.body else ''
        url = response.url

        title = _meta.get('title') or response.xpath('//meta[@name="ArticleTitle"]/@content').get()
        publish_time = _meta.get('publish_time')
        body_xpath = _meta.get('body_xpath')

        # 提取作者信息（来源）
        author = (
                ''.join(re.findall(r'来源[:：]\s*(.*?)<', response.text)) or
                ''.join(response.xpath('//meta[@name="Author"]/@content').getall())
        ).strip()

        #提取附件
        attachment_urls = response.xpath(
            f'{body_xpath}//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or contains(@href, ".wps")]'
        )

        yield DataItem({
            "_id": md5(f'{method}{url}{body}'.encode('utf-8')).hexdigest(),
            "url": url,
            'spider_from': self._from,
            'label': _meta.get('label'),
            'title': title,
            'author': author,
            'publish_time': publish_time,
            'body_html': ' '.join(response.xpath(body_xpath).getall()),
            "content": ' '.join(response.xpath(f'{body_xpath}//text()').getall()),
            "images": [response.urljoin(i) for i in response.xpath(f'{body_xpath}//img/@src').getall()],
            "attachment":get_attachment(attachment_urls, url, self._from),
            "spider_date": get_now_date(),
            'spider_topic': "spider-policy-hubei"
        })
