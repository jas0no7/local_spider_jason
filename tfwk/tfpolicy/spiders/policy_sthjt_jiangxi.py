# -*- coding: utf-8 -*-
import copy
import re
from hashlib import md5
import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings
from ..items import DataItem
from ..mydefine import get_now_date, get_attachment

settings = get_project_settings()


class PolicySthjtJiangxiSpider(CrawlSpider):
    """江西省生态环境厅 - 政策法规与规范性文件"""
    name = 'policy_sthjt_jiangxi'
    allowed_domains = ['sthjt.jiangxi.gov.cn']

    _from = '江西省生态环境厅'
    dupefilter_field = {"batch": "20251107"}

    # ==============================
    # 栏目信息配置
    # ==============================
    infoes = [
        {
            'url': 'https://sthjt.jiangxi.gov.cn/jxssthjt/col/col42150/index.html?uid=380055&pageNum=1',
            'label': "政策法规框解读",
            'detail_xpath': '//ul[@class="List_list"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@class="jgz_box"]',
            'total': 30,
            'page': 1,
            'base_url': 'https://sthjt.jiangxi.gov.cn/jxssthjt/col/col42150/index.html?uid=380055&pageNum={}'
        },
        {
            'url': 'https://sthjt.jiangxi.gov.cn/jxssthjt/col/col57149/index.html?uid=380055&pageNum=1',
            'label': "规范性文件",
            'detail_xpath': '//ul[@class="List_list"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@class="jgz_box"]',
            'total': 3,
            'page': 1,
            'base_url': 'https://sthjt.jiangxi.gov.cn/jxssthjt/col/col57149/index.html?uid=380055&pageNum={}'
        },
    ]

    # ==============================
    # 禁用代理中间件（避免407错误）
    # ==============================
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
            'tfpolicy.middlewares.DownloaderMiddleware': None,
        }
    }

    # ==============================
    # 启动请求
    # ==============================
    def start_requests(self):
        for info in self.infoes:
            yield scrapy.Request(
                url=info['url'],
                callback=self.parse_item,
                meta=copy.deepcopy(info),
                dont_filter=True
            )

    # ==============================
    # 列表页解析
    # ==============================
    def parse_item(self, response):
        meta = response.meta
        label = meta.get('label')
        detail_xpath = meta.get('detail_xpath')
        url_xpath = meta.get('url_xpath')
        title_xpath = meta.get('title_xpath')
        publish_time_xpath = meta.get('publish_time_xpath')
        body_xpath = meta.get('body_xpath')
        total = meta.get('total')
        page = meta.get('page')
        base_url = meta.get('base_url')

        # 容错：匹配 List_list / list_list / List_item 等多种写法
        list_nodes = response.xpath('//ul[contains(@class,"List") or contains(@class,"list")]/li')
        count = len(list_nodes)
        self.logger.info(f"解析栏目【{label}】第 {page} 页，共匹配到 {count} 条")

        if count == 0:
            # 打印前 300 字符帮助调试
            snippet = response.text[:300]
            self.logger.warning(f"⚠️ 未匹配到列表节点，检查页面结构。HTML 片段: {snippet}")
            return

        for ex_url in list_nodes:
            url = response.urljoin(ex_url.xpath(url_xpath).get())
            if not url or url.endswith('.pdf'):
                continue

            title = ''.join(ex_url.xpath(title_xpath).getall()).strip()
            publish_time = (
                ''.join(ex_url.xpath(f'string({publish_time_xpath})').getall())
                .replace('(', '')
                .replace(')', '')
                .strip()
                if publish_time_xpath else ''
            )

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta={
                    'label': label,
                    'title': title,
                    'publish_time': publish_time,
                    'body_xpath': body_xpath,
                },
                dont_filter=True
            )

        # 翻页逻辑
        if page < total:
            next_page = page + 1
            next_url = base_url.format(next_page)
            yield scrapy.Request(
                url=next_url,
                callback=self.parse_item,
                meta=copy.deepcopy({**meta, 'page': next_page}),
                dont_filter=True
            )

    # ==============================
    # 详情页解析
    # ==============================
    def parse_detail(self, response):
        meta = response.meta
        method = response.request.method
        body = response.request.body.decode('utf-8') if response.request.body else ''
        url = response.url

        title = meta.get('title') or response.xpath('//meta[@name="ArticleTitle"]/@content').get()
        publish_time = (
            meta.get('publish_time')
            or ''.join(response.xpath('//publishtime/text()').getall()).strip()
            or ''.join(re.findall(r'发布日期.*?(\d{4}-\d{2}-\d{2})', response.text, re.DOTALL)).strip()
        )

        author = (
            response.xpath('//meta[@name="Author"]/@content').get()
            or ''.join(re.findall(r'发布机构：</strong><span>(.*?)</span>', response.text))
            or ''.join(re.findall(r'>信息来源：(.*?)</', response.text))
        ).strip()

        body_xpath = meta.get('body_xpath')

        # 附件提取
        attachment_urls = response.xpath(
            '//p[contains(@class, "insertfileTag")]//a | '
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or '
            'contains(@href, ".xls") or contains(@href, ".xlsx") or contains(@href, ".wps") or '
            'contains(@href, ".zip") or contains(@href, ".rar")]'
        )

        yield DataItem({
            "_id": md5(f'{method}{url}{body}'.encode('utf-8')).hexdigest(),
            "url": url,
            "spider_from": self._from,
            "label": meta.get('label'),
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "body_html": ' '.join(response.xpath(body_xpath).getall()),
            "content": ' '.join(response.xpath(f'{body_xpath}//text()').getall()),
            "images": [response.urljoin(i) for i in response.xpath(f'{body_xpath}//img/@src').getall()],
            "attachment": get_attachment(attachment_urls, url, self._from),
            "spider_date": get_now_date(),
            "spider_topic": "spider-policy-jiangxi"
        })
