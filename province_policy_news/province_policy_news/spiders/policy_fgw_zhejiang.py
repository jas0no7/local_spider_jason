import scrapy
import copy
import re
import datetime
from hashlib import md5
from loguru import logger
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_attachment, get_now_date

settings = get_project_settings()


class EitdznewsSpider(scrapy.Spider):
    name = "policy_fgw_zhejiang"
    allowed_domains = ["fzggw.zj.gov.cn"]
    category = '政府网站'

    _from = '浙江省发展和改革委员会'
    dupefilter_field = {"batch": "20240322"}

    # ⚠ 移除旧项目无效中间件
    custom_settings = {}

    # 全局 URL 去重
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.visited_urls = set()

    infoes = [
        {
            'url': 'https://fzggw.zj.gov.cn/col/col1229565788/index.html?uid=4892867&pageNum=1',
            'label': "政策文件;行政规范性文件",
            'detail_xpath': '//*[@id="4892867"]/div/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@id="zoom" or contains(@class,"main-txt")]',
            'total': 26,
            'page': 1,
            'base_url': 'https://fzggw.zj.gov.cn/col/col1229565788/index.html?uid=4892867&pageNum={}'
        },
        {
            'url': 'https://fzggw.zj.gov.cn/col/col1229603564/index.html?uid=7468062&pageNum=1',
            'label': "政策文件;政策解读;规划解读",
            'detail_xpath': '//*[@id="7468062"]/div/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@class="main-txt" and @id="zoom"]',
            'total': 6,
            'page': 1,
            'base_url': 'https://fzggw.zj.gov.cn/col/col1229603564/index.html?uid=7468062&pageNum={}'
        },
        {
            'url': 'https://fzggw.zj.gov.cn/col/col1229603565/index.html?uid=7468062&pageNum=1',
            'label': "政策文件;政策解读;其他解读",
            'detail_xpath': '//*[@id="7468062"]/div/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@class="main-txt" and @id="zoom"]',
            'total': 6,
            'page': 1,
            'base_url': 'https://fzggw.zj.gov.cn/col/col1229603565/index.html?uid=7468062&pageNum={}'
        },
        {
            'url': 'https://fzggw.zj.gov.cn/col/col1599544/index.html?uid=4892867&pageNum=1',
            'label': "政策文件;通知公告",
            'detail_xpath': '//*[@id="4892867"]/div/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@class="main-txt" and @id="zoom"]',
            'total': 182,
            'page': 1,
            'base_url': 'https://fzggw.zj.gov.cn/col/col1599544/index.html?uid=4892867&pageNum={}'
        },
    ]

    # ---------------- 工具函数 ----------------
    @staticmethod
    def get_now_date():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def get_attachment(a_nodes, page_url):
        urls = []
        for a in a_nodes:
            href = a.xpath("./@href").get()
            if not href:
                continue
            if href.startswith("http"):
                urls.append(href)
            else:
                base = page_url.rsplit("/", 1)[0]
                urls.append(base + "/" + href.lstrip("/"))
        return urls

    # ---------------- Start ----------------
    def start_requests(self):
        for info in self.infoes:
            yield scrapy.Request(
                url=info["url"],
                callback=self.parse_item,
                meta=copy.deepcopy(info),
                dont_filter=True
            )

    # ---------------- 列表页 ----------------
    def parse_item(self, response):
        logger.info(f"页面URL: {response.url}")

        xml_text = ''.join(response.xpath('//script[@type="text/xml"]/text()').getall())
        html_blocks = []

        if xml_text:
            html_blocks = re.findall(
                r'<record><!\[CDATA\[(.*?)\]\]></record>', xml_text, flags=re.S
            )
            if not html_blocks:
                html_blocks = re.findall(
                    r'<p class="lb-list">.*?</p>', xml_text, flags=re.S
                )
        else:
            logger.warning("未找到 XML 数据，开始解析 HTML 列表结构")
            html_blocks = response.xpath(
                '//div[@id and contains(@class,"list")]/ul/li'
            ).getall()

        logger.info(f"匹配到 {len(html_blocks)} 条记录")

        for block in html_blocks:
            sel = scrapy.Selector(text=block)

            relative_url = sel.xpath('.//a/@href').get()
            if not relative_url:
                continue

            url = response.urljoin(relative_url).replace("http://", "https://")

            # 全局 URL 去重
            if url in self.visited_urls:
                logger.debug(f"重复URL跳过: {url}")
                continue
            self.visited_urls.add(url)

            title = sel.xpath('.//a/@title').get() or sel.xpath('.//a/text()').get()
            publish_time = sel.xpath('.//span/text()').get()

            meta = {
                "label": response.meta["label"],
                "title": title.strip() if title else "",
                "publish_time": publish_time.strip() if publish_time else "",
                "body_xpath": response.meta["body_xpath"],
            }

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(meta),
                dont_filter=True
            )

        # ---------------- 分页 ----------------
        current_page = response.meta['page']
        total_page = response.meta['total']
        base_url = response.meta['base_url']

        if current_page < total_page:
            next_page = current_page + 1
            next_url = base_url.format(next_page)
            logger.info(f"翻页至第 {next_page} 页: {next_url}")

            next_meta = copy.deepcopy(response.meta)
            next_meta["page"] = next_page

            yield scrapy.Request(
                url=next_url,
                callback=self.parse_item,
                meta=next_meta,
                dont_filter=True
            )

    # ---------------- 详情页 ----------------
    def parse_detail(self, response):
        meta = response.meta

        method = response.request.method
        body = response.request.body.decode("utf-8") if response.request.body else ""
        url = response.url

        title = meta.get("title") or response.xpath(
            '//meta[@name="ArticleTitle"]/@content'
        ).get()
        publish_time = meta.get("publish_time")
        body_xpath = meta["body_xpath"]

        author = (
                ''.join(re.findall(r'来源[:：]\s*(.*?)<', response.text))
                or ''.join(response.xpath('//meta[@name="Author"]/@content').getall())
        ).strip()

        # 附件
        attachment_nodes = response.xpath(
            f'{body_xpath}//a[contains(@href, ".pdf") or contains(@href, ".doc") or '
            f'contains(@href, ".docx") or contains(@href, ".wps")]'
        )
        attachments = get_attachment(attachment_nodes, url, self._from)

        # 正文
        body_html = ' '.join(response.xpath(body_xpath).getall())
        content = ' '.join(response.xpath(f"{body_xpath}//text()").getall()).strip()
        images = [
            response.urljoin(i)
            for i in response.xpath(f"{body_xpath}//img/@src").getall()
        ]

        yield DataItem({
            "_id": md5(f"{method}{url}{body}".encode("utf-8")).hexdigest(),
            "url": url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "spider_from": self._from,
            "label": meta["label"],
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content,
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category
        })
