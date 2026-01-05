import copy
import re
import scrapy
from hashlib import md5


class HenanNewsSpider(scrapy.Spider):
    name = "edu_ln_jyt"
    allowed_domains = ["www.mohrss.gov.cn"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
    }

    _from = "人力资源社会保障部"

    infoes = [
        {
            "url": "https://www.mohrss.gov.cn/SYrlzyhshbzb/rencairenshi/zcwj/jinengrencai/index.html",
            "label": "人才人事;政策文件;技能人才",

            # ===== 列表页（mohrss.gov.cn 模板）=====
            "detail_xpath": '//ul[contains(@class,"list")]//li',
            "url_xpath": './/a/@href',
            "title_xpath": './/a/text()',
            "publish_time_xpath": './/span[contains(@class,"time")]/text()',

            # ===== 详情页正文 =====
            "body_xpath": '//div[@id="zoom"]',

            "total": 8,
            "page": 1,
            "base_url": "https://www.mohrss.gov.cn/SYrlzyhshbzb/rencairenshi/zcwj/jinengrencai/index_{}.html",
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

        detail_xpath = meta["detail_xpath"]
        url_xpath = meta["url_xpath"]
        title_xpath = meta["title_xpath"]
        publish_time_xpath = meta["publish_time_xpath"]

        body_xpath = meta["body_xpath"]
        page = meta["page"]
        total = meta["total"]
        base_url = meta["base_url"]

        nodes = response.xpath(detail_xpath)
        if not nodes:
            self.logger.warning(f"列表页未解析到节点: {response.url}")

        for li in nodes:
            href = li.xpath(url_xpath).get()
            if not href:
                continue

            url = response.urljoin(href)
            if url.endswith(".pdf"):
                continue

            title = li.xpath(title_xpath).get()
            title = title.strip() if title else ""

            publish_time = li.xpath(publish_time_xpath).get()
            publish_time = publish_time.strip() if publish_time else ""

            detail_meta = {
                "label": meta["label"],
                "title": title,
                "publish_time": publish_time,
                "body_xpath": body_xpath,
            }

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(detail_meta),
                dont_filter=True,
            )

        # ===== 翻页 =====
        if page < total:
            next_page = page + 1
            next_url = base_url.format(next_page)

            next_meta = copy.deepcopy(meta)
            next_meta["page"] = next_page

            yield scrapy.Request(
                url=next_url,
                callback=self.parse_list,
                meta=next_meta,
                dont_filter=True,
            )

    def parse_detail(self, response):
        meta = response.meta

        url = response.url
        title = meta.get("title", "")
        body_xpath = meta.get("body_xpath")

        # ===== 发布时间兜底 =====
        publish_time = meta.get("publish_time") or ""
        if not publish_time:
            publish_time = "".join(
                re.findall(r"(\d{4}-\d{2}-\d{2})", response.text)
            )

        # ===== 正文解析（主 XPath + 兜底）=====
        body_nodes = response.xpath(body_xpath)
        if not body_nodes:
            body_nodes = response.xpath(
                '//div[contains(@class,"article")] | //div[contains(@class,"content")]'
            )

        body_html = " ".join(body_nodes.getall()).strip()
        content = " ".join(body_nodes.xpath(".//text()").getall()).strip()

        images = [
            response.urljoin(i)
            for i in body_nodes.xpath(".//img/@src").getall()
        ]

        attachments = [
            response.urljoin(a)
            for a in response.xpath(
                '//a[contains(@href, ".pdf") or contains(@href, ".doc") '
                'or contains(@href, ".docx") or contains(@href, ".xls") '
                'or contains(@href, ".xlsx") or contains(@href, ".zip") '
                'or contains(@href, ".rar")]/@href'
            ).getall()
        ]

        yield {
            "_id": md5(f"{url}{title}".encode("utf-8")).hexdigest(),
            "url": url,
            "label": meta.get("label"),
            "title": title,
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content,
            "images": images,
            "attachments": attachments,
            "spider_from": self._from,
        }
