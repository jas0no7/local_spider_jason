import scrapy
import copy
import re
from hashlib import md5
from loguru import logger
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_attachment, get_now_date

settings = get_project_settings()


class ZjNyjnewsSpider(scrapy.Spider):
    name = "news_nea_zhejiang"
    allowed_domains = ["zjb.nea.gov.cn"]
    category = '政府网站'

    _from = '国家能源局浙江监管办公室'
    dupefilter_field = {"batch": "20240322"}

    # ======================================================
    # ✔ 强制覆盖全局 settings，禁用你的 RFPDupeFilter+Scheduler
    # ======================================================
    custom_settings = {
        "DUPEFILTER_CLASS": "scrapy.dupefilters.RFPDupeFilter",
        "SCHEDULER": "scrapy.core.scheduler.Scheduler",
        "REDIS_START_URLS": False,
        "SCHEDULER_PERSIST": False,
    }

    infoes = [
        {
            "url": "https://zjb.nea.gov.cn/dtyw/jgdt/index.html",
            "label": "政策法规",
            "detail_xpath": '//div[contains(@class,"wrapper_overview_right_list")]/ul/li/a',
            "url_xpath": "./@href",
            "title_xpath": "./span[1]/text()",
            "publish_time_xpath": "./span[2]/text()",
            "body_xpath": '//div[@class="article-content"] | //div[@class="wrapper_detail_text"]'
        }
    ]

    # ---------------- 起始请求 ----------------
    def start_requests(self):
        for info in self.infoes:
            yield scrapy.Request(
                url=info["url"],
                callback=self.parse_item,
                meta=copy.deepcopy(info),
                dont_filter=True      # ✔ 强制请求
            )

    # ---------------- 列表页 ----------------
    def parse_item(self, response):
        meta = response.meta

        label = meta["label"]
        detail_xpath = meta["detail_xpath"]
        url_xpath = meta["url_xpath"]
        title_xpath = meta["title_xpath"]
        publish_time_xpath = meta["publish_time_xpath"]
        body_xpath = meta["body_xpath"]

        logger.info(f"解析列表页：{response.url}")

        for a in response.xpath(detail_xpath):
            href = a.xpath(url_xpath).get()
            if not href:
                continue

            url = response.urljoin(href)
            title = "".join(a.xpath(title_xpath).getall()).strip()
            pub_time = "".join(a.xpath(publish_time_xpath).getall()).strip()

            detail_meta = {
                "label": label,
                "title": title,
                "publish_time": pub_time,
                "body_xpath": body_xpath,
            }

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=detail_meta,
                dont_filter=True      # ✔ 强制请求
            )

        # ---------------- 仅采第一页，不再翻页 ----------------

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

        # 作者
        author = (
            "".join(re.findall(r"来源[:：]\s*(.*?)<", response.text)) or
            "".join(response.xpath('//meta[@name="Author"]/@content').getall())
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
        images = [response.urljoin(src) for src in response.xpath(f"{body_xpath}//img/@src").getall()]

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
            "category": self.category,
        })
