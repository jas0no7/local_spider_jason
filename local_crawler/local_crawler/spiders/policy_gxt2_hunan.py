import scrapy
from hashlib import md5
from urllib.parse import urljoin


class HunanGxtSpider(scrapy.Spider):
    name = "policy_gxt2_hunan"
    allowed_domains = ["gxt.hunan.gov.cn"]

    _from = "湖南工业和信息化厅"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    infoes = [
        {
            "url": "https://gxt.hunan.gov.cn/gxt/xxgk_71033/zcfg/dfxfg/index.html",
            "label": "地方性法律法规",
            "total": 3,
            "base_url": "https://gxt.hunan.gov.cn/gxt/xxgk_71033/zcfg/dfxfg/index_{}.html"
        },
        {
            "url": "https://gxt.hunan.gov.cn/gxt/xxgk_71033/zcfg/gfxwj/index.html",
            "label": "规范性文件",
            "total": 6,
            "base_url": "https://gxt.hunan.gov.cn/gxt/xxgk_71033/zcfg/gfxwj/index_{}.html"
        },
        {
            "url": "https://gxt.hunan.gov.cn/gxt/xxgk_71033/zcfg/zcjd/index.html",
            "label": "政策解读",
            "total": 18,
            "base_url": "https://gxt.hunan.gov.cn/gxt/xxgk_71033/zcfg/zcjd/index_{}.html"
        },
    ]

    def start_requests(self):
        """
        从 infoes 列表启动三个栏目
        """
        for item in self.infoes:
            yield scrapy.Request(
                url=item["url"],
                headers=self.headers,
                callback=self.parse_list,
                meta=item
            )

    def parse_list(self, response):
        """
        解析列表页，提取 index_code, title, url, publish_time
        """
        label = response.meta["label"]
        total = response.meta["total"]
        base_url = response.meta["base_url"]

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
                }
            )

        # 下一页
        current_url = response.url
        # index.html、index_2.html、index_3.html...
        for p in range(2, total + 1):
            next_url = base_url.format(p)
            yield scrapy.Request(
                url=next_url,
                headers=self.headers,
                callback=self.parse_list,
                meta=response.meta
            )

    def parse_detail(self, response):
        """
        解析详情页正文
        """
        meta = response.meta

        # 提取正文
        content_list = response.xpath('//div[@class="tys-main"]//text()').getall()
        content = "".join([i.strip() for i in content_list if i.strip()])

        yield {
            "_id": md5(f"{meta['detail_url']}{meta['title']}".encode("utf-8")).hexdigest(),
            "url": meta["detail_url"],
            "label": meta["label"],
            "index_code": meta["index_code"],
            "title": meta["title"],
            "publish_time": meta["publish_time"],
            "content": content,
            "spider_from": self._from,
        }
