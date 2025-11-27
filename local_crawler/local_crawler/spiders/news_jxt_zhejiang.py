import scrapy
import copy
from hashlib import md5
import re
import datetime
from loguru import logger


class EitdznewsSpider(scrapy.Spider):
    name = "news_jxt_zhejiang"
    allowed_domains = ["jxt.zj.gov.cn"]

    _from = '浙江省经济和信息化厅'
    dupefilter_field = {"batch": "20240322"}

    # ⚠ 删除不存在的中间件，避免报错
    custom_settings = {}

    infoes = [
        {
            'url': 'https://jxt.zj.gov.cn/col/col1659217/index.html?uid=5031616&pageNum=1',
            'label': "政策法规",
            'detail_xpath': '//*[@id="5031616"]/div/p',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': (
                '//div[@class="bt-box-1170 c1"] | '
                '//div[@class="wrapper_detail_text"] | '
                '//div[@class="article-content"]'
            ),
            'total': 6,
            'page': 1,
            'base_url': 'https://jxt.zj.gov.cn/col/col1659217/index.html?uid=5031616&pageNum={}'
        },
    ]

    # -------- 工具函数：当前日期 --------
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
            url = info['url']
            yield scrapy.Request(
                url=url,
                callback=self.parse_item,
                meta=copy.deepcopy(info),
                dont_filter=False
            )

    # -------- 列表页 --------
    def parse_item(self, response):
        logger.info("进入 parse_item")

        meta = response.meta

        label = meta['label']
        detail_xpath = meta['detail_xpath']
        url_xpath = meta['url_xpath']
        title_xpath = meta['title_xpath']
        publish_time_xpath = meta['publish_time_xpath']
        body_xpath = meta['body_xpath']
        total = meta['total']
        page = meta['page']
        base_url = meta['base_url']

        for node in response.xpath(detail_xpath):
            relative_url = node.xpath(url_xpath).get()
            logger.info(f"relative_url = {relative_url}")

            if not relative_url:
                continue

            # 补全 URL
            if relative_url.startswith("/"):
                url = "https://jxt.zj.gov.cn" + relative_url
            else:
                url = response.urljoin(relative_url)

            title = ''.join(node.xpath(title_xpath).getall()).strip()
            publish_time = ''.join(node.xpath(f'string({publish_time_xpath})').getall()).strip()

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

        # -------- 下一页 --------
        if page < total:
            next_page = page + 1
            next_url = base_url.format(next_page)

            logger.info(f"抓取第 {next_page} 页：{next_url}")

            next_meta = {
                "label": label,
                "detail_xpath": detail_xpath,
                "url_xpath": url_xpath,
                "title_xpath": title_xpath,
                "publish_time_xpath": publish_time_xpath,
                "body_xpath": body_xpath,
                "total": total,
                "page": next_page,
                "base_url": base_url
            }

            yield scrapy.Request(
                url=next_url,
                callback=self.parse_item,
                meta=copy.deepcopy(next_meta),
                dont_filter=False
            )

    # -------- 详情页 --------
    def parse_detail(self, response):
        meta = response.meta

        method = response.request.method
        body = response.request.body.decode('utf-8') if response.request.body else ""
        url = response.url

        title = meta.get("title") or response.xpath(
            '//meta[@name="ArticleTitle"]/@content'
        ).get()

        publish_time = meta.get("publish_time")
        body_xpath = meta["body_xpath"]

        # 作者
        author = (
            ''.join(re.findall(r'来源[:：]\s*(.*?)<', response.text)) or
            ''.join(response.xpath('//meta[@name="Author"]/@content').getall())
        ).strip()

        # 附件
        attachment_nodes = response.xpath(
            f'{body_xpath}//a[contains(@href, ".pdf") or contains(@href, ".doc") or '
            'contains(@href, ".docx") or contains(@href, ".wps")]'
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
