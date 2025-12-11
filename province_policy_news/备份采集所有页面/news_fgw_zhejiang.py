import copy
import re
import datetime
from hashlib import md5

import scrapy
from loguru import logger
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_attachment, get_now_date

settings = get_project_settings()


class EitdznewsSpider(scrapy.Spider):
    name = "news_fgw_zhejiang"
    allowed_domains = ["fzggw.zj.gov.cn"]

    _from = '浙江省发展和改革委员会'
    category = '政府网站'
    dupefilter_field = {"batch": "20240322"}

    # ⚠ 删除不存在的旧中间件
    custom_settings = {}

    infoes = [
        {
            'url': 'https://fzggw.zj.gov.cn/col/col1599562/index.html?uid=4892867&pageNum=1',
            'label': "新闻发布会;新闻发布会",
            'detail_xpath': '//*[@id="4892867"]/div/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@id="zoom" or contains(@class,"main-txt")]',
            'total': 9,
            'page': 1,
            'base_url': 'https://fzggw.zj.gov.cn/col/col1599562/index.html?uid=4892867&pageNum={}'
        },
        {
            'url': 'https://fzggw.zj.gov.cn/col/col1229318206/index.html?uid=4892867&pageNum=1',
            'label': "新闻发布会;在线访谈",
            'detail_xpath': '//*[@id="7468062"]/div/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@class="main-txt" and @id="zoom"] | //*[@id="img-content"]',
            'total': 2,
            'page': 1,
            'base_url': 'https://fzggw.zj.gov.cn/col/col1229318206/index.html?uid=4892867&pageNum={}'
        },
    ]

    # ---------------- 工具函数：当前时间 ----------------
    @staticmethod
    def get_now_date():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ---------------- 工具函数：附件提取 ----------------
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
                urls.append(base + "/" + href.lstrip("/"))
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
        logger.info(f"页面URL: {response.url}")

        xml_text = ''.join(response.xpath('//script[@type="text/xml"]/text()').getall())
        html_blocks = []

        if xml_text:
            # 新版：<record><![CDATA[...]]></record>
            html_blocks = re.findall(
                r'<record><!\[CDATA\[(.*?)\]\]></record>', xml_text, flags=re.S
            )
            if not html_blocks:
                # 兼容旧版
                html_blocks = re.findall(
                    r'<p class="lb-list">.*?</p>', xml_text, flags=re.S
                )
        else:
            logger.warning("未找到 XML 脚本块，尝试直接解析 HTML 列表")
            html_blocks = response.xpath(
                '//div[@id and contains(@class,"list")]/ul/li'
            ).getall()

        logger.info(f"匹配到 {len(html_blocks)} 条记录")

        for block in html_blocks:
            sel = scrapy.Selector(text=block)
            relative_url = sel.xpath('.//a/@href').get()
            title = sel.xpath('.//a/@title').get() or sel.xpath('.//a/text()').get()
            publish_time = sel.xpath('.//span/text()').get()

            if not relative_url:
                continue

            # 构造完整 URL
            url = response.urljoin(relative_url)
            logger.info(f"抓取链接: {url}")

            meta = {
                "label": response.meta['label'],
                "title": title.strip() if title else "",
                "publish_time": publish_time.strip() if publish_time else "",
                "body_xpath": response.meta['body_xpath'],
            }

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(meta),
                dont_filter=False
            )

        # ---------------- 翻页 ----------------
        current_page = response.meta['page']
        total_page = response.meta['total']
        base_url = response.meta['base_url']

        if current_page < total_page:
            next_page = current_page + 1
            next_url = base_url.format(next_page)
            logger.info(f"翻页至 {next_page}: {next_url}")

            next_meta = copy.deepcopy(response.meta)
            next_meta["page"] = next_page

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
        body = response.request.body.decode("utf-8") if response.request.body else ""
        url = response.url

        title = meta.get("title") or response.xpath(
            '//meta[@name="ArticleTitle"]/@content'
        ).get()

        publish_time = meta.get("publish_time")
        body_xpath = meta["body_xpath"]

        author = (
            ''.join(re.findall(r'来源[:：]\s*(.*?)<', response.text)) or
            ''.join(response.xpath('//meta[@name="Author"]/@content').getall())
        ).strip()

        # 提取附件
        attachment_nodes = response.xpath(
            f'{body_xpath}//a[contains(@href, ".pdf") or '
            f'contains(@href, ".doc") or contains(@href, ".docx") or '
            f'contains(@href, ".wps")]'
        )
        attachments = get_attachment(attachment_nodes, url, self._from)

        # 正文
        body_html = ' '.join(response.xpath(body_xpath).getall())
        content = ' '.join(
            response.xpath(f"{body_xpath}//text()").getall()
        ).strip()
        images = [
            response.urljoin(i)
            for i in response.xpath(f"{body_xpath}//img/@src").getall()
        ]

        yield DataItem({
            "_id": md5(f"{method}{url}{body}".encode("utf-8")).hexdigest(),
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
