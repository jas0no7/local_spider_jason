import copy
import re
import scrapy
from hashlib import md5
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_attachment, get_now_date

settings = get_project_settings()


class HenanNewsSpider(scrapy.Spider):
    name = "policy_fgw_shaanxi"
    allowed_domains = ["sndrc.shaanxi.gov.cn"]
    category = '政府网站'

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1
    }

    _from = "陕西省发展和改革委员会"

    infoes = [
        {
            'url': 'https://sndrc.shaanxi.gov.cn/sy/xwxx/jjxsfx/index.html',
            'label': "经济形势分析",
            'detail_xpath': '//ul[@class="rightList"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/text()',
            'publish_time_xpath': './span/text()',
            'body_xpath': '//div[@class="tyxlCenter"]',
            'total': 6,
            'page': 1,
            'base_url': 'https://sndrc.shaanxi.gov.cn/sy/xwxx/jjxsfx/index_{}.html'
        },
        {
            'url': 'https://sndrc.shaanxi.gov.cn/sy/xwxx/mtfg/index.html',
            'label': "媒体发改",
            'detail_xpath': '//ul[@class="rightList"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/text()',
            'publish_time_xpath': './span/text()',
            'body_xpath': '//div[@class="tyxlCenter"]',
            'total': 5,
            'page': 1,
            'base_url': 'https://sndrc.shaanxi.gov.cn/sy/xwxx/mtfg/index_{}.html'
        },
        {
            'url': 'https://sndrc.shaanxi.gov.cn/sy/xwxx/wndt/index.html',
            'label': "委内动态",
            'detail_xpath': '//ul[@class="rightList"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/text()',
            'publish_time_xpath': './span/text()',
            'body_xpath': '//div[@class="tyxlCenter"]',
            'total': 5,
            'page': 1,
            'base_url': 'https://sndrc.shaanxi.gov.cn/sy/xwxx/wndt/index_4.html'
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

        method = response.request.method
        body = response.request.body.decode('utf-8') if response.request.body else ''
        url = response.request.url
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

        attachment_nodes = response.xpath(
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") '
            'or contains(@href, ".docx") or contains(@href, ".xls") '
            'or contains(@href, ".xlsx") or contains(@href, ".zip") '
            'or contains(@href, ".rar")]'
        )
        attachments = get_attachment(attachment_nodes, url, self._from)

        yield DataItem({
            "_id": md5(f"{method}{url}{body}".encode("utf-8")).hexdigest(),
            "url": url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "spider_from": self._from,
            "label": meta["label"],
            "title": title,
            "author": "",
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content,
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category
        })
