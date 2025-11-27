import scrapy
import copy
import re
from hashlib import md5
import datetime
from loguru import logger


class ZjNyjnewsSpider(scrapy.Spider):
    name = "news_nea_zhejiang"
    allowed_domains = ["zjb.nea.gov.cn"]

    _from = '国家能源局浙江监管办公室'
    dupefilter_field = {"batch": "20240322"}

    infoes = [
        {
            'url': 'https://zjb.nea.gov.cn/dtyw/jgdt/index.html',
            'label': "政策法规",
            'detail_xpath': '//div[contains(@class,"wrapper_overview_right_list")]/ul/li/a',
            'url_xpath': './@href',
            'title_xpath': './span[1]/text()',
            'publish_time_xpath': './span[2]/text()',
            'body_xpath': '//div[@class="article-content"] | //div[@class="wrapper_detail_text"]',
            'total': 88,
            'page': 1,
            'base_url': 'https://zjb.nea.gov.cn/dtyw/jgdt/index_{}.shtml'
        },
    ]

    # ---------------- 内置：当前日期 ----------------
    @staticmethod
    def get_now_date():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ---------------- 内置：附件处理 ----------------
    @staticmethod
    def get_attachment(a_nodes, page_url):
        urls = []
        for a in a_nodes:
            href = a.xpath("./@href").get()
            if not href:
                continue
            # 拼接绝对 URL
            if href.startswith("http"):
                urls.append(href)
            else:
                base = page_url.rsplit("/", 1)[0]
                urls.append(base + "/" + href.lstrip("/"))
        return urls

    # ---------------- 起始请求 ----------------
    def start_requests(self):
        for info in self.infoes:
            yield scrapy.Request(
                url=info['url'],
                callback=self.parse_item,
                meta=copy.deepcopy(info),
                dont_filter=False
            )

    # ---------------- 列表页 ----------------
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

        for ex_url in response.xpath(detail_xpath):
            href = ex_url.xpath(url_xpath).get()
            if not href:
                continue

            url = response.urljoin(href)
            title = ''.join(ex_url.xpath(title_xpath).getall()).strip()
            publish_time = ''.join(
                ex_url.xpath(f"string({publish_time_xpath})").getall()
            ).strip() if publish_time_xpath else None

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

        # ---------------- 翻页 ----------------
        if page < total:
            next_page = page + 1

            if next_page == 1:
                next_url = 'https://zjb.nea.gov.cn/dtyw/jgdt/index.html'
            else:
                next_url = f'https://zjb.nea.gov.cn/dtyw/jgdt/index_{next_page - 1}.shtml'

            logger.info(f"翻页 {next_page} : {next_url}")

            next_meta = {
                'label': label,
                'detail_xpath': detail_xpath,
                'url_xpath': url_xpath,
                'title_xpath': title_xpath,
                'publish_time_xpath': publish_time_xpath,
                'body_xpath': body_xpath,
                'total': total,
                'page': next_page
            }

            yield scrapy.Request(
                url=next_url,
                callback=self.parse_item,
                meta=next_meta,
                dont_filter=False
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
        body_xpath = meta['body_xpath']

        # 作者
        author = (
                ''.join(re.findall(r'来源[:：]\s*(.*?)<', response.text)) or
                ''.join(response.xpath('//meta[@name="Author"]/@content').getall())
        ).strip()

        # 附件
        attachment_nodes = response.xpath(
            f'{body_xpath}//a[contains(@href, ".pdf") or '
            f'contains(@href, ".doc") or contains(@href, ".docx") or '
            f'contains(@href, ".wps")]'
        )
        attachments = self.get_attachment(attachment_nodes, url)

        # 正文
        body_html = ' '.join(response.xpath(body_xpath).getall())
        content = ' '.join(response.xpath(f"{body_xpath}//text()").getall()).strip()
        images = [
            response.urljoin(src)
            for src in response.xpath(f"{body_xpath}//img/@src").getall()
        ]

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
