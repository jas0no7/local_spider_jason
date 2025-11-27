import scrapy
import copy
import re
from hashlib import md5
import datetime
from loguru import logger


class EitdznewsSpider(scrapy.Spider):
    name = "policy_sthjt_zhejiang"
    allowed_domains = ["sthjt.zj.gov.cn"]

    _from = '浙江省生态环境厅'
    dupefilter_field = {"batch": "20240322"}

    # ⚠ 删除不存在的中间件
    custom_settings = {}

    infoes = [
        {
            'url': 'https://sthjt.zj.gov.cn/col/col1229116546/index.html',
            'label': "政策文件及解读;上级文件",
            'detail_xpath': '//*[@id="div1229106886"]/table/tbody/tr/td/div/div[2]/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './b',
            'body_xpath': '',    # ⚠ 本网站详情页结构不同，需要自动识别
            'total': 6,
            'page': 1,
            'base_url': ''
        },
    ]

    # -------- 工具函数：当前日期 --------
    @staticmethod
    def get_now_date():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # -------- 工具函数：附件 --------
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

    # -------- 起始请求 --------
    def start_requests(self):
        for info in self.infoes:
            yield scrapy.Request(
                url=info["url"],
                callback=self.parse_item,
                meta=copy.deepcopy(info),
                dont_filter=False
            )

    # -------- 列表页 --------
    def parse_item(self, response):
        logger.info("进入 parse_item")

        meta = response.meta
        label = meta["label"]
        detail_xpath = meta["detail_xpath"]
        url_xpath = meta["url_xpath"]
        title_xpath = meta["title_xpath"]
        publish_time_xpath = meta["publish_time_xpath"]
        body_xpath = meta["body_xpath"]

        for node in response.xpath(detail_xpath):
            href = node.xpath(url_xpath).get()

            if not href:
                continue

            # 自动补全完整 URL
            if href.startswith("/"):
                url = f"https://sthjt.zj.gov.cn{href}"
            else:
                url = response.urljoin(href)

            title = ''.join(node.xpath(title_xpath).getall()).strip()
            publish_time = ''.join(node.xpath(publish_time_xpath).getall()).strip()

            logger.info(f"详情链接：{url}")

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
                dont_filter=False
            )

    # -------- 自动识别正文 XPath --------
    @staticmethod
    def detect_body_xpath(response):
        candidates = [
            '//div[@class="article-content"]',
            '//div[@class="bt-box-1170 c1"]',
            '//div[@class="wrapper_detail_text"]',
            '//div[@class="content"]',
            '//div[@class="content-con"]',
        ]
        for xp in candidates:
            if response.xpath(xp):
                return xp
        return '//body'   # 兜底（不会为空）

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
        body_xpath = meta.get("body_xpath")

        # ⚠ body_xpath 为空时自动识别
        if not body_xpath:
            body_xpath = self.detect_body_xpath(response)

        # 作者
        author = (
            ''.join(re.findall(r'来源[:：]\s*(.*?)<', response.text)) or
            ''.join(response.xpath('//meta[@name="Author"]/@content').getall())
        ).strip()

        # 附件
        attachment_nodes = response.xpath(
            f'{body_xpath}//a[contains(@href, ".pdf") or '
            'contains(@href, ".doc") or contains(@href, ".docx") or '
            'contains(@href, ".wps") or contains(@href, ".zip") or contains(@href, ".rar")]'
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
