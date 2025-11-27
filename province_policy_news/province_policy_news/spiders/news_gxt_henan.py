import copy
import re
from hashlib import md5
import scrapy
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_attachment, get_now_date

settings = get_project_settings()


class DataSpider(scrapy.Spider):
    name = 'news_gxt_henan'
    allowed_domains = ['gxt.henan.gov.cn']
    category = '政府网站'

    _from = '河南省工业和信息化厅'

    infoes = [
        {
            'url': 'https://gxt.henan.gov.cn/xxgk/zdlygk/jsjf/',
            'label': "减税降费信息公开",
            'detail_xpath': '//div[@class="zfxxgk_zdgkc"]/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': 'string(./a)',  # 修复 title
            'publish_time_xpath': './b',
            'body_xpath': '//div[@class="details-main"]',
            'total': 1,
            'page': 1,
            'base_url': 'https://gxt.henan.gov.cn/xxgk/zdlygk/jsjf/'
        },
        {
            'url': 'https://gxt.henan.gov.cn/xxgk/fzgh/',
            'label': "发展规划",
            'detail_xpath': '//div[@class="zfxxgk_zdgkc"]/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': 'string(./a)',  # 修复 title
            'publish_time_xpath': './b',
            'body_xpath': '//div[@class="details-main"]',
            'total': 1,
            'page': 1,
            'base_url': 'https://gxt.henan.gov.cn/xxgk/fzgh/'
        },
    ]

    def start_requests(self):
        for info in self.infoes:
            yield scrapy.Request(
                url=info['url'],
                callback=self.parse_item,
                meta=copy.deepcopy(info),
                dont_filter=True
            )

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

        for li in response.xpath(detail_xpath):
            href = li.xpath(url_xpath).get()
            if not href:
                continue

            url = response.urljoin(href)
            if url.endswith('.pdf'):
                continue

            # 修复 title
            title = li.xpath(title_xpath).get().strip()

            if publish_time_xpath:
                publish_time = li.xpath(f"string({publish_time_xpath})").get().strip()
            else:
                publish_time = ""

            detail_meta = {
                "label": label,
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
            meta['page'] = page
            next_url = base_url.format(page)

            yield scrapy.Request(
                url=next_url,
                callback=self.parse_item,
                meta=copy.deepcopy(meta),
                dont_filter=True
            )

    def parse_detail(self, response):

        meta = response.meta

        method = response.request.method
        body = response.request.body.decode('utf-8') if response.request.body else ''
        url = response.request.url
        title = meta.get("title") or ""

        publish_time = meta["publish_time"] or \
            "".join(response.xpath("//publishtime/text()").getall()).strip() or \
            "".join(re.findall(r"发布日期.*?(\d{4}-\d{2}-\d{2})", response.text))

        body_xpath = meta['body_xpath']

        body_html = " ".join(response.xpath(body_xpath).getall())
        content = " ".join(response.xpath(f"{body_xpath}//text()").getall()).strip()

        images = [
            response.urljoin(img)
            for img in response.xpath(f"{body_xpath}//img/@src").getall()
        ]

        attachment_nodes = response.xpath(
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or '
            'contains(@href, ".xls") or contains(@href, ".xlsx") or contains(@href, ".zip") or '
            'contains(@href, ".rar")]'
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
