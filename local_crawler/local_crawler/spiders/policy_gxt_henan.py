import copy
import re
from hashlib import md5
import scrapy


class DataSpider(scrapy.Spider):
    name = 'policy_gxt_henan'
    allowed_domains = ['gxt.henan.gov.cn']

    _from = '河南省工业和信息化厅'

    infoes = [
        {
            'url': 'https://gxt.henan.gov.cn/xxgk/zdlygk/jsjf/',
            'label': "行政规范性文件",
            'detail_xpath': '//div[@class="zfxxgk_zdgkc"]/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './b',
            'body_xpath': '//div[@class="details-main"]',
            'total': 2,
            'page': 1,
            'base_url': 'https://gxt.henan.gov.cn/xxgk/zc/xzgfxwj/index_{}.html'
        },
        {
            'url': 'https://gxt.henan.gov.cn/xxgk/zcjd/index.html',
            'label': "政策解读",
            'detail_xpath': '//div[@class="zfxxgk_zdgkc"]/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './b',
            'body_xpath': '//div[@class="details-main"]',
            'total': 15,
            'page': 1,
            'base_url': 'https://gxt.henan.gov.cn/xxgk/zcjd/index_{}.html'
        },
        {
            'url': 'https://gxt.henan.gov.cn/xxgk/wjjb/index.html',
            'label': "政策文件",
            'detail_xpath': '//div[@class="zfxxgk_zdgkc"]/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './b',
            'body_xpath': '//div[@class="details-main"]',
            'total': 23,
            'page': 1,
            'base_url': 'https://gxt.henan.gov.cn/xxgk/wjjb/index_{}.html'
        }
    ]

    def start_requests(self):
        for info in self.infoes:
            yield scrapy.Request(
                url=info["url"],
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

            title = ''.join(li.xpath(title_xpath).getall()).strip()

            publish_time = li.xpath(f"string({publish_time_xpath})").get().strip()

            detail_meta = {
                "label": label,
                "title": title,
                "publish_time": publish_time,
                "body_xpath": body_xpath,
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
            response.urljoin(a.xpath("@href").get())
            for a in response.xpath(
                '//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or '
                'contains(@href, ".xls") or contains(@href, ".xlsx") or contains(@href, ".zip") or '
                'contains(@href, ".rar")]'
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
