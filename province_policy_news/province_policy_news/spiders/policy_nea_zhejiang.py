import scrapy
import copy
import re
from hashlib import md5
import datetime
from loguru import logger
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_attachment, get_now_date

settings = get_project_settings()


class ZjNyjpolicySpider(scrapy.Spider):
    name = "policy_nea_zhejiang"
    allowed_domains = ["zjb.nea.gov.cn"]
    category = '政府网站'

    _from = '国家能源局浙江监管办公室'
    dupefilter_field = {"batch": "20240322"}

    infoes = [
        {
            'url': 'https://zjb.nea.gov.cn/xxgk/zcfg/index.html',
            'label': "政策法规",
            'detail_xpath': '//div[contains(@class,"wrapper_item_content")]/ul/li/a',
            'url_xpath': './@href',
            'title_xpath': './span[1]/text()',
            'publish_time_xpath': './span[2]/text()',
            'body_xpath': '//div[@class="article-content"] | //div[@class="wrapper_detail_text"]',
            'total': 10,
            'page': 1,
            'base_url': 'https://zjb.nea.gov.cn/xxgk/zcfg/index_{}.shtml'
        },
        {
            'url': 'https://zjb.nea.gov.cn/xxgk/zcjd/index.html',
            'label': "政策解读",
            'detail_xpath': '//div[contains(@class,"wrapper_item_content")]/ul/li/a',
            'url_xpath': './@href',
            'title_xpath': './span[1]/text()',
            'publish_time_xpath': './span[2]/text()',
            'body_xpath': '//div[@class="article-content"] | //div[@class="wrapper_detail_text"]',
            'total': 10,
            'page': 1,
            'base_url': 'https://zjb.nea.gov.cn/xxgk/zcjd/index_{}.shtml'
        },
    ]

    # ---------------- 工具函数 ----------------
    @staticmethod
    def get_now_date():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def get_attachment(a_nodes, page_url):
        urls = []
        for a in a_nodes:
            href = a.xpath("./@href").get()
            if not href:
                continue

            if href.startswith("http"):
                urls.append(href)
            else:
                base = page_url.rsplit("/", 1)[0]
                urls.append(f"{base}/{href.lstrip('/')}")
        return urls

    # ---------------- 起始请求 ----------------
    def start_requests(self):
        for info in self.infoes:
            yield scrapy.Request(
                url=info['url'],
                callback=self.parse_item,
                meta=copy.deepcopy(info),
                dont_filter=False
            )

    # ---------------- 列表页 ----------------
    def parse_item(self, response):
        meta = response.meta

        label = meta['label']
        detail_xpath = meta['detail_xpath']
        url_xpath = meta['url_xpath']
        title_xpath = meta['title_xpath']
        publish_time_xpath = meta['publish_time_xpath']
        body_xpath = meta['body_xpath']
        page = meta['page']
        total = meta['total']
        base_url = meta['base_url']

        for ex in response.xpath(detail_xpath):
            href = ex.xpath(url_xpath).get()
            if not href:
                continue

            url = response.urljoin(href)
            title = ''.join(ex.xpath(title_xpath).getall()).strip()
            publish_time = ''.join(
                ex.xpath(f"string({publish_time_xpath})").getall()
            ).strip()

            detail_meta = {
                "label": label,
                "title": title,
                "publish_time": publish_time,
                "body_xpath": body_xpath,
            }

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(detail_meta),
                dont_filter=False
            )

        # -------- 翻页，不再使用错误的 zcjd 固定链接 --------
        if False and page < total:
            next_page = page + 1
            next_url = base_url.format(next_page)

            logger.info(f"翻页 {next_page}: {next_url}")

            next_meta = {
                'label': label,
                'detail_xpath': detail_xpath,
                'url_xpath': url_xpath,
                'title_xpath': title_xpath,
                'publish_time_xpath': publish_time_xpath,
                'body_xpath': body_xpath,
                'total': total,
                'page': next_page,
                'base_url': base_url
            }

            yield scrapy.Request(
                url=next_url,
                callback=self.parse_item,
                meta=next_meta,
                dont_filter=False
            )

    # ---------------- 详情页 ----------------
    def parse_detail(self, response):
        meta = response.meta

        method = response.request.method
        body_raw = response.request.body.decode('utf-8') if response.request.body else ""
        url = response.url

        title = meta.get("title") or response.xpath(
            '//meta[@name="ArticleTitle"]/@content'
        ).get()

        publish_time = meta.get("publish_time")
        body_xpath = meta['body_xpath']

        author = (
            ''.join(re.findall(r'来源[:：]\s*(.*?)<', response.text))
            or ''.join(response.xpath('//meta[@name="Author"]/@content').getall())
        ).strip()

        # 附件
        attachment_nodes = response.xpath(
            f'{body_xpath}//a[contains(@href, ".pdf") or '
            f'contains(@href, ".doc") or contains(@href, ".docx") or '
            f'contains(@href, ".wps")]'
        )
        attachments = get_attachment(attachment_nodes, url, self._from)

        # 正文
        body_html = " ".join(response.xpath(body_xpath).getall())
        content = " ".join(response.xpath(f"{body_xpath}//text()").getall()).strip()
        images = [
            response.urljoin(i)
            for i in response.xpath(f"{body_xpath}//img/@src").getall()
        ]

        yield DataItem({
            "_id": md5(f"{method}{url}{body_raw}".encode("utf-8")).hexdigest(),
            "url": url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "spider_from": self._from,
            "label": meta["label"],
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content,
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category
        })
