import copy
import re
from hashlib import md5
from lxml import html

import scrapy
from loguru import logger
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_attachment, get_now_date

settings = get_project_settings()


class EitdznewsSpider(scrapy.Spider):
    name = "news_jxt_zhejiang"
    allowed_domains = ["jxt.zj.gov.cn"]

    _from = "浙江省经济和信息化厅"
    category = "政府网站"
    dupefilter_field = {"batch": "20240322"}

    custom_settings = {
        "DUPEFILTER_CLASS": "scrapy.dupefilters.RFPDupeFilter",
    }

    infoes = [
        {
            "url": "https://jxt.zj.gov.cn/col/col1659217/index.html?uid=5031616&pageNum=1",
            "label": "政策法规",

            # 注意：列表并不在 HTML，而是在 script 的 CDATA 中
            "body_xpath": (
                '//div[@class="bt-box-1170 c1"] | '
                '//div[@class="wrapper_detail_text"] | '
                '//div[@class="article-content"]'
            ),

            "total": 6,
            "page": 1,
            "base_url": "https://jxt.zj.gov.cn/col/col1659217/index.html?uid=5031616&pageNum={}"
        },
    ]

    def start_requests(self):
        for info in self.infoes:
            yield scrapy.Request(
                url=info["url"],
                callback=self.parse_item,
                meta=copy.deepcopy(info),
                dont_filter=True
            )

    # --------------------------------------------------------
    # ⭐ 关键：解析 <script type="text/xml"> 里的 CDATA 列表
    # --------------------------------------------------------
    def parse_item(self, response):
        logger.info("进入 parse_item")

        meta = response.meta
        page = meta["page"]
        total = meta["total"]

        # 1) 拿到 script 里的 XML
        xml_text = response.xpath('//div[@id="5031616"]/script/text()').get()
        if not xml_text:
            logger.error("❌ 未找到 script XML 内容")
            return

        # 2) 抽取 CDATA 内的 HTML 段落
        records = re.findall(r'<!\[CDATA\[(.*?)\]\]>', xml_text, re.S)
        if not records:
            logger.error("❌ XML 中未找到 record CDATA 内容")
            return

        records_html = "".join(records)

        # 3) 转成 DOM 树
        doc = html.fromstring(records_html)

        # 4) 每段实际结构：<p class="lb-list"><a ...>标题</a><span>日期</span></p>
        for p in doc.xpath('//p[@class="lb-list"]'):
            relative_url = p.xpath('./a/@href')
            if not relative_url:
                continue

            detail_url = response.urljoin(relative_url[0])
            title = "".join(p.xpath('./a/text()')).strip()
            publish_time = "".join(p.xpath('./span/text()')).strip()

            logger.info(f"发现文章：{title} | {detail_url}")

            detail_meta = {
                "label": meta["label"],
                "title": title,
                "publish_time": publish_time,
                "body_xpath": meta["body_xpath"]
            }

            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail,
                meta=copy.deepcopy(detail_meta),
                dont_filter=True
            )

        # --------------------------------------------------------
        # 🔄 翻页逻辑
        # --------------------------------------------------------
        if False and page < total:
            next_page = page + 1
            next_url = meta["base_url"].format(next_page)

            logger.info(f"抓取第 {next_page} 页：{next_url}")

            next_meta = copy.deepcopy(meta)
            next_meta["page"] = next_page

            yield scrapy.Request(
                url=next_url,
                callback=self.parse_item,
                meta=next_meta,
                dont_filter=True
            )

    # --------------------------------------------------------
    # ⭐ 详情页解析
    # --------------------------------------------------------
    def parse_detail(self, response):
        meta = response.meta

        method = response.request.method
        body = response.request.body.decode("utf-8") if response.request.body else ""
        url = response.url

        title = meta["title"] or response.xpath(
            '//meta[@name="ArticleTitle"]/@content'
        ).get()

        publish_time = meta["publish_time"]
        body_xpath = meta["body_xpath"]

        # 提取作者
        author = (
            "".join(re.findall(r"来源[:：]\s*(.*?)<", response.text))
            or "".join(response.xpath('//meta[@name="Author"]/@content').getall())
        ).strip()

        # 附件
        attachment_nodes = response.xpath(
            f'{body_xpath}//a[contains(@href, ".pdf") or contains(@href, ".doc") '
            'or contains(@href, ".docx") or contains(@href, ".wps")]'
        )
        attachments = get_attachment(attachment_nodes, url, self._from)

        # 内容解析
        body_html = " ".join(response.xpath(body_xpath).extract())
        content = " ".join(response.xpath(f"{body_xpath}//text()").extract()).strip()
        images = [response.urljoin(i) for i in response.xpath(f"{body_xpath}//img/@src").extract()]

        yield DataItem({
            "_id": md5(f"{method}{url}{body}".encode("utf-8")).hexdigest(),
            "url": url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "spider_from": self._from,
            "label": meta["label"],
            "category": self.category,

            "title": title,
            "author": author,
            "publish_time": publish_time,

            "body_html": body_html,
            "content": content,
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
        })
