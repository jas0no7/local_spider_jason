import copy
import re
from hashlib import md5
import scrapy
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_attachment, get_now_date

settings = get_project_settings()


class DataSpider(scrapy.Spider):
    name = 'policy_fgw_henan'
    allowed_domains = ['fgw.henan.gov.cn']
    category = '政府网站'

    _from = '河南省发展和改革委员会'

    infoes = [
        {
            'url': 'https://fgw.henan.gov.cn/zmhd/zjdc/',
            'label': "征集调查",
            'detail_xpath': '//table[@class="zmhd-table"]/tbody/tr',
            'url_xpath': './td[1]/a/@href',
            'title_xpath': 'string(./td[1]/a)',
            'publish_time_xpath': './td[4]',
            'body_xpath': '//div[@class="yMain"]',
            'total': 1,
            'page': 1,
            'base_url': 'https://fgw.henan.gov.cn/zmhd/zjdc/'
        },
        {
            'url': 'https://fgw.henan.gov.cn/zwgk/zc/xzgfxwj/index.html',
            'label': "规范性文件",
            'detail_xpath': '//div[@class="zfxxgk_zdgkc"]/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './b',
            'body_xpath': '//div[@class="yMain"]',
            'total': 2,
            'page': 1,
            'base_url': 'https://fgw.henan.gov.cn/zwgk/zc/xzgfxwj/index_{}.html'
        },
        {
            'url': 'https://fgw.henan.gov.cn/bmfw/jgjc/jgjc/gysczljg/',
            'label': "工业生产资料价格",

            # 列表结构
            'detail_xpath': '//div[@class="news-list"]/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': 'string(./a)',
            'publish_time_xpath': './span/text()',
            'body_xpath': '//div[@class="yMain"]',
            # 分页信息
            'total': 1,
            'page': 1,
            'base_url': 'https://fgw.henan.gov.cn/bmfw/jgjc/jgjc/gysczljg/index_{}.html'
        },
        {
            'url': 'https://fgw.henan.gov.cn/zwgk/sjfb/',
            'label': "数据发布",

            # 列表结构（你页面里 ul 下 li）
            'detail_xpath': '//div[@class="news-list-1200 bg-white"]/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': 'string(./a)',
            'publish_time_xpath': './span/text()',
            'body_xpath': '//div[@class="yMain"]',
            # 分页（真实结构从 pageDec 读取 pagecount=118）
            'total': 4,  # 可自动化，但你既然需要配置，这里写死即可
            'page': 1,
            # 第二页格式为：index_2.html
            'base_url': 'https://fgw.henan.gov.cn/zwgk/sjfb/index_{}.html'
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

            title = ''.join(li.xpath(title_xpath).get()).strip()

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

        if False and page < total:
            page += 1
            next_url = base_url.format(page)
            meta['page'] = page

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
        title = meta['title']

        publish_time = meta['publish_time'] or \
                       "".join(response.xpath("//publishtime/text()").getall()).strip() or \
                       "".join(re.findall(r"发布日期.*?(\d{4}-\d{2}-\d{2})", response.text))

        body_xpath = meta["body_xpath"]

        body_html = " ".join(response.xpath(body_xpath).getall())
        content = " ".join(response.xpath(f"{body_xpath}//text()").getall()).strip()

        images = [
            response.urljoin(src)
            for src in response.xpath(f"{body_xpath}//img/@src").getall()
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
