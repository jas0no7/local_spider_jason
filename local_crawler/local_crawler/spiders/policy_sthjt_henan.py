import copy
import re
from hashlib import md5
import scrapy


class DataSpider(scrapy.Spider):
    name = 'policy_sthjt_henan'
    allowed_domains = ['sthjt.henan.gov.cn']

    _from = '河南省生态环境厅'

    infoes = [
        {
            'url': 'https://sthjt.henan.gov.cn/xxgk/zfxxgk/xxgkml/tcfl/hjbhtwj/index.html',
            'label': "生态环境厅文件",

            # 正确 XPath（ul > li）
            'detail_xpath': '//div[@class="newsList"]/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': 'string(./a)',
            'publish_time_xpath': './span[@class="date"]/text()',

            # 正文区域（真实页面中是 main）
            'body_xpath': '//div[contains(@class,"main")]',

            'total': 4,
            'page': 1,
            'base_url': 'https://sthjt.henan.gov.cn/xxgk/zfxxgk/xxgkml/tcfl/hjbhtwj/index_{}.html'
        }
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

            title = li.xpath(title_xpath).get().strip()
            publish_time = li.xpath(publish_time_xpath).get().strip()

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

        url = response.url
        title = meta['title']

        publish_time = meta['publish_time'] or \
            "".join(response.xpath("//publishtime/text()").getall()).strip() or \
            "".join(re.findall(r"发布日期.*?(\d{4}-\d{2}-\d{2})", response.text))

        body_xpath = meta['body_xpath']

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
