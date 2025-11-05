import os
import json
import re
import copy
from hashlib import md5
from datetime import datetime

import scrapy
from scrapy.spiders import CrawlSpider

from ..mydefine import get_now_date, get_attachment


class HunbNeaLocalSpider(CrawlSpider):
    custom_settings = {
        # 关闭自定义去重与调度
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter',
        'SCHEDULER': 'scrapy.core.scheduler.Scheduler',

        # 关闭所有自定义中间件，包括代理与重试逻辑
        'DOWNLOADER_MIDDLEWARES': {
            'zj_prov.middlewares.EducationDownloaderMiddleware': None,
            'zj_prov.middlewares.MyRetryMiddleware': None,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
        },

        # 不用 Kafka 管道
        'ITEM_PIPELINES': {},
        'DOWNLOAD_TIMEOUT': 15,
        'LOG_LEVEL': 'INFO',
    }
    name = 'hunb_nea_local'
    allowed_domains = ['hunb.nea.gov.cn']
    _from = '国家能源局湖南监管办公室'
    category = '新闻网站'

    # 保存路径（自动创建）
    save_dir = os.path.join(os.path.dirname(__file__), '../../output')
    os.makedirs(save_dir, exist_ok=True)

    infoes = [
        {
            'url': 'https://hunb.nea.gov.cn/xxgk/zcfg/index.html',
            'label': "政策法规",
            'detail_xpath': '//ul[@class="wrapper_item_con4_ul"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/span[1]',
            'publish_time_xpath': './a/span[2]',
            'body_xpath': '//div[@class="article-content"] | //div[@class="wrapper_deatil"]',
            'total': 4,
            'page': 1,
            'base_url': 'https://hunb.nea.gov.cn/xxgk/zcfg/index_{}.html'
        },
    ]

    def start_requests(self):
        for info in self.infoes:
            yield scrapy.Request(
                url=info.get('url'),
                callback=self.parse_item,
                meta=copy.deepcopy(info),
                dont_filter=False
            )

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

        for ex_url in response.xpath(detail_xpath):
            url = response.urljoin(ex_url.xpath(url_xpath).get())
            if not url:
                continue

            title = ''.join(ex_url.xpath(title_xpath).getall()).strip()
            publish_time = ''.join(ex_url.xpath(f'string({publish_time_xpath})').getall()).strip()

            new_meta = {
                'label': label,
                'title': title,
                'publish_time': publish_time,
                'body_xpath': body_xpath,
            }

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(new_meta),
                dont_filter=False
            )

        # 翻页逻辑
        if page < total:
            page += 1
            next_url = (
                'https://hunb.nea.gov.cn/xxgk/zcfg/index.html'
                if page == 1 else f'https://hunb.nea.gov.cn/xxgk/zcfg/index_{page - 1}.html'
            )
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
                    'page': page
                }),
                dont_filter=False
            )

    def parse_detail(self, response):
        meta = response.meta
        url = response.url
        title = meta.get('title') or response.xpath('//meta[@name="ArticleTitle"]/@content').get()
        publish_time = meta.get('publish_time')
        body_xpath = meta.get('body_xpath')

        author = (
            ''.join(re.findall(r'来源[:：]\s*(.*?)<', response.text)) or
            ''.join(response.xpath('//meta[@name="Author"]/@content').getall())
        ).strip()

        attachment_urls = response.xpath(
            '//p[contains(@class, "insertfileTag")]//a | '
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or '
            'contains(@href, ".xls") or contains(@href, ".xlsx") or contains(@href, ".wps") or '
            'contains(@href, ".zip") or contains(@href, ".rar")]'
        )

        data = {
            "_id": md5(f'GET{url}'.encode('utf-8')).hexdigest(),
            "url": url,
            'spider_from': self._from,
            'label': meta.get('label'),
            'title': title,
            'author': author,
            'publish_time': publish_time,
            'body_html': ' '.join(response.xpath(body_xpath).getall()),
            "content": ' '.join(response.xpath(f'{body_xpath}//text()').getall()),
            "images": [response.urljoin(i) for i in response.xpath(f'{body_xpath}//img/@src').getall()],
            "attachment": get_attachment(attachment_urls, url, self._from),
            "spider_date": get_now_date(),

        }

        self.save_to_local(data)

    def save_to_local(self, item):
        """保存为本地 JSON 文件"""
        date_str = datetime.now().strftime('%Y%m%d')
        save_path = os.path.join(self.save_dir, f'hunb_nea_{date_str}.json')

        with open(save_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

        print(f"已保存到本地文件：{save_path}")
