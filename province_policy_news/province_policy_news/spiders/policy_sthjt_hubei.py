import copy
import re
import scrapy
from hashlib import md5
from loguru import logger
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_attachment, get_now_date

settings = get_project_settings()


class HenanNewsSpider(scrapy.Spider):
    name = "policy_sthjt_hubei"
    allowed_domains = ["sthjt.hubei.gov.cn"]
    category = '政府网站'

    handle_httpstatus_list = [412, 404]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1
    }

    _from = "湖北省生态环境厅"

    infoes = [
        {
            "url": "https://sthjt.hubei.gov.cn/fbjd/zc/gfxwj/index.shtml",
            "label": "规范性文件",
            "detail_xpath": "//ul[@id='zcwjList']/li",
            "url_xpath": ".//a[1]/@href",
            "title_xpath": "string(.//a[1])",
            "publish_time_xpath": ".//div[@class='info']/span[contains(text(),'发布日期')]",
            "body_xpath": "//div[@class='article'] | //div[@class='grid'] ",
            "total": 3,
            "page": 0,
            "base_url": "https://sthjt.hubei.gov.cn/fbjd/zc/gfxwj/index_{}.shtml",
        },
        {
            "url": "https://sthjt.hubei.gov.cn/fbjd/zc/zcjd/index.shtml",
            "label": "政策解读",
            "detail_xpath": "//ul[@class='info-list']/li",
            "url_xpath": "./a/@href",
            "title_xpath": "string(./a)",
            "publish_time_xpath": "./span",
            "body_xpath": "//div[@class='article_box'] ",
            "total": 12,
            "page": 0,
            "base_url": "https://sthjt.hubei.gov.cn/fbjd/zc/zcjd/index_{}.shtml",
        }
    ]

    def start_requests(self):
        for info in self.infoes:
            yield scrapy.Request(
                url=info["url"],
                callback=self.parse_list,
                meta=copy.deepcopy(info),
                dont_filter=True,
            )

    def parse_list(self, response):
        meta = response.meta

        for li in response.xpath(meta["detail_xpath"]):
            href = li.xpath(meta["url_xpath"]).get()
            if not href:
                continue

            detail_url = response.urljoin(href)

            if detail_url.endswith(".pdf"):
                continue

            title = li.xpath(meta["title_xpath"]).get("") or ""
            title = title.strip()

            publish_time = li.xpath(meta["publish_time_xpath"] + "/text()").get("") or ""
            publish_time = publish_time.replace("发布日期：", "").strip()

            detail_meta = {
                "label": meta["label"],
                "title": title,
                "publish_time": publish_time,
                "body_xpath": meta["body_xpath"],
                "referer": response.url,
            }

            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail,
                meta=detail_meta,
                dont_filter=True,
            )

        if meta["page"] < meta["total"]:
            meta["page"] += 1
            next_url = meta["base_url"].format(meta["page"])

            yield scrapy.Request(
                next_url,
                callback=self.parse_list,
                meta=meta,
                dont_filter=True,
            )

    def parse_detail(self, response):
        meta = response.meta
        body_xpath = meta["body_xpath"]

        method = response.request.method
        body = response.request.body.decode('utf-8') if response.request.body else ''
        url = response.request.url

        body_html = " ".join(response.xpath(body_xpath).getall())
        content = " ".join(response.xpath(f"{body_xpath}//text()").getall()).strip()

        images = [
            response.urljoin(i)
            for i in response.xpath(f"{body_xpath}//img/@src").getall()
        ]

        attachment_nodes = response.xpath(
            "//a["
            "contains(@href,'.pdf') or contains(@href,'.doc') or "
            "contains(@href,'.docx') or contains(@href,'.xls') or "
            "contains(@href,'.xlsx') or contains(@href,'.zip') or "
            "contains(@href,'.rar')]"
        )
        attachments = get_attachment(attachment_nodes, url, self._from)

        yield DataItem({
            "_id": md5(f"{method}{url}{body}".encode("utf-8")).hexdigest(),
            "url": url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "spider_from": self._from,
            "label": meta["label"],
            "title": meta["title"],
            "author": "",
            "publish_time": meta["publish_time"],
            "body_html": body_html,
            "content": content,
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category
        })
