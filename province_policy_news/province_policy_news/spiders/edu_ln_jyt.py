import copy
import re
import scrapy
from hashlib import md5


class MohrssPolicySpider(scrapy.Spider):
    name = "edu_ln_jyt"
    allowed_domains = ["www.mohrss.gov.cn"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/143.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
    }

    spider_from = "人力资源社会保障部"

    info = {
        "url": "https://www.mohrss.gov.cn/SYrlzyhshbzb/rencairenshi/zcwj/jinengrencai/index.html",
        "label": "人才人事;政策文件;技能人才",
        "page": 1,
        "total": 8,
        "base_url": "https://www.mohrss.gov.cn/SYrlzyhshbzb/rencairenshi/zcwj/jinengrencai/index_{}.html",
    }

    def start_requests(self):
        yield scrapy.Request(
            url=self.info["url"],
            callback=self.parse_list,
            meta=copy.deepcopy(self.info),
            dont_filter=True,
        )

    def parse_list(self, response):
        meta = response.meta

        # =========================
        # 核心：直接抓文章链接
        # =========================
        nodes = response.xpath('//a[contains(@href, "/t20")]')
        if not nodes:
            self.logger.error("❌ 未解析到任何文章链接，请检查页面是否被改版")
            return

        for a in nodes:
            href = a.xpath("./@href").get()
            if not href:
                continue

            url = response.urljoin(href)

            # 标题：a 标签自身文本
            title = a.xpath("string(.)").get()
            title = title.strip() if title else ""

            # 发布时间：优先取相邻 span，再兜底正则
            publish_time = a.xpath(
                "string(../span | ../../span | following-sibling::span[1])"
            ).get()
            publish_time = publish_time.strip() if publish_time else None

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta={
                    "label": meta["label"],
                    "title": title,
                    "publish_time": publish_time,
                },
                dont_filter=True,
            )

        # =========================
        # 翻页
        # =========================
        page = meta["page"]
        total = meta["total"]

        if page < total:
            next_page = page + 1
            next_meta = copy.deepcopy(meta)
            next_meta["page"] = next_page

            yield scrapy.Request(
                url=meta["base_url"].format(next_page),
                callback=self.parse_list,
                meta=next_meta,
                dont_filter=True,
            )

    def parse_detail(self, response):
        meta = response.meta

        url = response.url
        title = meta.get("title", "")

        # =========================
        # 发布时间兜底
        # =========================
        publish_time = meta.get("publish_time")
        if not publish_time:
            m = re.search(r"\d{4}-\d{2}-\d{2}", response.text)
            publish_time = m.group(0) if m else None

        # =========================
        # 正文解析（人社部通用）
        # =========================
        body_nodes = response.xpath(
            '//div[@id="zoom"] | //div[contains(@class,"article")]'
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
            "spider_from": self.spider_from,
        }
