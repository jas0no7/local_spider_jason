import copy
import re
import scrapy
from hashlib import md5


class HenanNewsSpider(scrapy.Spider):
    name = "policy_gxt_hunan"
    allowed_domains = ["gxt.hunan.gov.cn"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1
    }

    _from = "湖南省工业和信息化厅"

    infeos = [

        {
            "url": "https://gxt.hunan.gov.cn/gxt/xxgk_71033/zcfg/zcjd/index.html",
            "label": "政策解读",
            "detail_xpath": "//table[@class='table']/tbody/tr",
            "url_xpath": "./td[2]/a/@href",
            "title_xpath": "./td[3]/a/@title",
            "publish_time_xpath": "./td[3]/text()",
            "body_xpath": "//div[@class='tys-main']",
            "total": 18,
            "page": 1,
            "base_url": "https://gxt.hunan.gov.cn/gxt/xxgk_71033/zcfg/zcjd/index_2.html",
        },

    ]

    def start_requests(self):
        for info in self.infoes:
            yield scrapy.Request(
                url=info["url"],
                callback=self.parse_list,
                meta=copy.deepcopy(info),
                dont_filter=True
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

        for li in response.xpath(detail_xpath):

            href = li.xpath(url_xpath).get()
            if not href:
                continue

            url = response.urljoin(href)
            if url.endswith(".pdf"):
                continue

            # 修复标题逻辑
            title = li.xpath(title_xpath).get().strip()

            publish_time = li.xpath(f"string({publish_time_xpath})").get().strip()

            detail_meta = {
                "label": meta["label"],
                "title": title,
                "publish_time": publish_time,
                "body_xpath": body_xpath
            }

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(detail_meta),
                dont_filter=True
            )

        if page < total:
            page += 1
            meta["page"] = page
            next_url = base_url.format(page)

            yield scrapy.Request(
                url=next_url,
                callback=self.parse_list,
                meta=copy.deepcopy(meta),
                dont_filter=True
            )

    def parse_detail(self, response):
        meta = response.meta

        url = response.url
        title = meta["title"]

        publish_time = meta["publish_time"] or \
                       "".join(response.xpath("//publishtime/text()").getall()).strip() or \
                       "".join(re.findall(r"发布日期.*?(\d{4}-\d{2}-\d{2})", response.text))

        body_xpath = meta["body_xpath"]

        body_html = " ".join(response.xpath(body_xpath).getall())
        content = " ".join(response.xpath(f"{body_xpath}//text()").getall()).strip()

        images = [
            response.urljoin(i)
            for i in response.xpath(f"{body_xpath}//img/@src").getall()
        ]

        attachments = [
            response.urljoin(a.xpath("./@href").get())
            for a in response.xpath(
                '//a[contains(@href, ".pdf") or contains(@href, ".doc") '
                'or contains(@href, ".docx") or contains(@href, ".xls") '
                'or contains(@href, ".xlsx") or contains(@href, ".zip") '
                'or contains(@href, ".rar")]'
            )
        ]

        yield {
            "_id": md5(f"{url}{title}".encode("utf-8")).hexdigest(),
            "url": url,
            "label": meta["label"],
            "title": title,
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content,
            "images": images,
            "attachments": attachments,
            "spider_from": self._from
        }
