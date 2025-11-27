import copy
import re
import scrapy
from hashlib import md5


class HenanNewsSpider(scrapy.Spider):
    name = "policy_nea_jiangsu"
    allowed_domains = ["jsb.nea.gov.cn"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1
    }

    _from = "国家能源局江苏监管办公室"

    infoes = [
        {
            "url": "https://jsb.nea.gov.cn/dtyw/tz/index.html",
            "label": "通知",
            "detail_xpath": '//div[@class="wrapper_overview_right_list"]/ul/li/a',
            "url_xpath": "./@href",
            "title_xpath": "./span[1]/text()",  # 修正标题
            "publish_time_xpath": "./span[2]/text()",

            "body_xpath": '//div[@class="wrapper_deatil"]',
            "total": 14,
            "page": 1,
            "base_url": "https://jsb.nea.gov.cn/dtyw/tz/index_{}.html"
        },
        {
            "url": "https://jsb.nea.gov.cn/xxgk/zcfg/index.html",
            "label": "政策法规",
            "detail_xpath": '//div[@class="wrapper_item_content active_con"]/ul/li/a',
            "url_xpath": "./@href",
            "title_xpath": "./span[1]/text()",  # 修正标题
            "publish_time_xpath": "./span[2]/text()",

            "body_xpath": '//div[@class="wrapper_deatil"]',
            "total": 4,
            "page": 1,
            "base_url": "https://jsb.nea.gov.cn/xxgk/zcfg/index_{}.html"
        },
        {
            "url": "https://jsb.nea.gov.cn/xxgk/zcjd/index.html",
            "label": "政策解读",
            "detail_xpath": '//div[@class="wrapper_item_content five_con active_con"]/ul/li/a',
            "url_xpath": "./@href",
            "title_xpath": "./span[1]/text()",  # 修正标题
            "publish_time_xpath": "./span[2]/text()",

            "body_xpath": '//div[@class="channel-page"]',
            "total": 4,
            "page": 1,
            "base_url": "https://jsb.nea.gov.cn/xxgk/zcjd/index_{}.html"
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
