import scrapy
import copy
import re
from hashlib import md5
import datetime
from loguru import logger


class EitdznewsSpider(scrapy.Spider):
    name = "policy_jxt_zhejiang"
    allowed_domains = ["jxt.zj.gov.cn"]

    _from = '浙江省经济和信息化厅'
    dupefilter_field = {"batch": "20240322"}

    # ⚠ 移除不存在的中间件，避免报错
    custom_settings = {}

    infoes = [
        {
            'url': 'https://jxt.zj.gov.cn/col/col1229895084/index.html?uid=5024951&pageNum=1',
            'label': "统计分析;统计信息",
            'detail_xpath': '//*[@id="5024951"]/div/p',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': (
                '//div[@class="bt-box-1170 c1"] | '
                '//div[@class="wrapper_detail_text"] | '
                '//div[@class="article-content"]'
            ),
            'total': 5,
            'page': 1,
            'base_url': 'https://jxt.zj.gov.cn/col/col1229895084/index.html?uid=5024951&pageNum={}'
        },
        {
            'url': 'https://jxt.zj.gov.cn/col/col1229895085/index.html?uid=5024951&pageNum=1',
            'label': "统计分析;监测分析",
            'detail_xpath': '//*[@id="5024951"]/div/p',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': (
                '//div[@class="bt-box-1170 c1"] | '
                '//div[@class="wrapper_detail_text"] | '
                '//div[@class="article-content"]'
            ),
            'total': 5,
            'page': 1,
            'base_url': 'https://jxt.zj.gov.cn/col/col1229895085/index.html?uid=5024951&pageNum={}'
        },
    ]

    # -------- 工具函数：当前时间 --------
    @staticmethod
    def get_now_date():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # -------- 工具函数：附件提取 --------
    @staticmethod
    def get_attachment(a_nodes, page_url):
        urls = []
        for a in a_nodes:
            href = a.xpath("./@href").get()
            if href:
                if href.startswith("http"):
                    urls.append(href)
                else:
                    base = page_url.rsplit("/", 1)[0]
                    urls.append(base + "/" + href.lstrip("/"))
        return urls

    # -------- 起始请求 --------
    def start_requests(self):
        for info in self.infoes:
            yield scrapy.Request(
                url=info['url'],
                callback=self.parse_item,
                meta=copy.deepcopy(info),
                dont_filter=False
            )

    # -------- 列表页（解析 XML） --------
    def parse_item(self, response):
        logger.info(f"当前页面 URL：{response.url}")

        xml_text = ''.join(response.xpath('//script[@type="text/xml"]/text()').getall())
        if not xml_text:
            logger.warning("⚠ 未找到 <script type='text/xml'> 内容")
            return

        html_blocks = re.findall(r'<p class="lb-list">.*?</p>', xml_text, flags=re.S)
        logger.info(f"匹配到 {len(html_blocks)} 条记录")

        body_xpath = response.meta['body_xpath']
        label = response.meta['label']

        for block in html_blocks:
            sel = scrapy.Selector(text=block)

            relative_url = sel.xpath('//a/@href').get()
            title = sel.xpath('//a/text()').get()
            publish_time = sel.xpath('//span/text()').get()

            if not relative_url:
                continue

            # → 自动补全 URL
            if relative_url.startswith("/"):
                url = f"https://jxt.zj.gov.cn{relative_url}"
            else:
                url = relative_url

            logger.info(f"详情链接：{url}")

            meta = {
                "label": label,
                "title": title.strip() if title else "",
                "publish_time": publish_time.strip() if publish_time else "",
                "body_xpath": body_xpath,
            }

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(meta),
                dont_filter=False
            )

    # -------- 详情页 --------
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

        # 作者提取
        author = (
            ''.join(re.findall(r'来源[:：]\s*(.*?)<', response.text)) or
            ''.join(response.xpath('//meta[@name="Author"]/@content').getall())
        ).strip()

        # 附件
        attachment_nodes = response.xpath(
            f'{body_xpath}//a[contains(@href, ".pdf") or '
            'contains(@href, ".doc") or contains(@href, ".docx") or '
            'contains(@href, ".wps")]'
        )
        attachments = self.get_attachment(attachment_nodes, url)

        # 正文
        body_html = ' '.join(response.xpath(body_xpath).getall())
        content = ' '.join(response.xpath(f"{body_xpath}//text()").getall()).strip()
        images = [response.urljoin(i) for i in response.xpath(f"{body_xpath}//img/@src").getall()]

        yield {
            "_id": md5(f"{method}{url}{body}".encode("utf-8")).hexdigest(),
            "url": url,
            "spider_from": self._from,
            "label": meta["label"],
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content,
            "images": images,
            "attachment": attachments,
            "spider_date": self.get_now_date(),

        }
