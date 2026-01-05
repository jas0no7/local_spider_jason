import scrapy
from hashlib import md5
from urllib.parse import urljoin
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_attachment, get_now_date

settings = get_project_settings()


class HunanGxtSpider(scrapy.Spider):
    name = "policy_gxt2_hunan"
    allowed_domains = ["gxt.hunan.gov.cn"]
    category = '政府网站'

    _from = "湖南工业和信息化厅"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    infoes = [
        {
            "url": "https://gxt.hunan.gov.cn/gxt/xxgk_71033/zcfg/dfxfg/index.html",
            "label": "地方性法律法规",
        },
        {
            "url": "https://gxt.hunan.gov.cn/gxt/xxgk_71033/zcfg/gfxwj/index.html",
            "label": "规范性文件",
        },
        {
            "url": "https://gxt.hunan.gov.cn/gxt/xxgk_71033/zcfg/zcjd/index.html",
            "label": "政策解读",
        },
    ]

    def start_requests(self):
        """
        从 infoes 列表启动三个栏目，只采第一页
        """
        for item in self.infoes:
            yield scrapy.Request(
                url=item["url"],
                headers=self.headers,
                callback=self.parse_list,
                meta=item,
                dont_filter=True
            )

    def parse_list(self, response):
        """
        解析列表页，只采当前页，不翻页
        """
        label = response.meta["label"]

        rows = response.xpath('//table[@class="table"]/tbody/tr')

        for tr in rows:
            index_code = tr.xpath('./td[1]/text()').get(default="").strip()

            a = tr.xpath('./td[2]/a')
            title = a.xpath('./@title').get("").strip()
            href = a.xpath('./@href').get("")
            detail_url = urljoin(response.url, href)

            publish_time = tr.xpath('./td[3]/text()').get(default="").strip()

            yield scrapy.Request(
                url=detail_url,
                headers=self.headers,
                callback=self.parse_detail,
                meta={
                    "label": label,
                    "index_code": index_code,
                    "title": title,
                    "detail_url": detail_url,
                    "publish_time": publish_time,
                },
                dont_filter=True
            )

        # ❌ 取消翻页逻辑
        # 不再 yield 下一页 URL
        # 不再构造 base_url
        # 不再使用 total
        # ---- 完成当前页即可 ----

    def parse_detail(self, response):
        """
        解析详情页正文
        """
        meta = response.meta

        method = response.request.method
        body = response.request.body.decode('utf-8') if response.request.body else ''
        url = response.url

        # 正文
        body_xpath = '//div[@class="tys-main"]'
        body_html = " ".join(response.xpath(body_xpath).extract())

        content_list = response.xpath(f'{body_xpath}//text()').getall()
        content = "".join([i.strip() for i in content_list if i.strip()])

        images = [response.urljoin(i) for i in response.xpath(f'{body_xpath}//img/@src').getall()]
        attachment_nodes = response.xpath(f'{body_xpath}//a')
        attachments = get_attachment(attachment_nodes, url, self._from)

        yield DataItem({
            "_id": md5(f"{method}{url}{body}".encode('utf-8')).hexdigest(),
            "url": meta["detail_url"],
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
