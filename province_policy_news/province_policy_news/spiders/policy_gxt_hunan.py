import copy
import re
from hashlib import md5
from loguru import logger
import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment

settings = get_project_settings()



class DataSpider(CrawlSpider):
    name = 'policy_gxt_hunan'
    allowed_domains = ['gxt.hunan.gov.cn']

    _from = '湖南省工业和信息化厅'
    category = "政策"

    dupefilter_field = {"batch": "20240322"}

    custom_settings = {
        # 临时关闭代理中间件（调试更稳定）
        'DOWNLOADER_MIDDLEWARES': {
            'tfpolicy.middlewares.MyProxyMiddleware': None,
        }
    }

    infoes = [
        {
            'url': 'https://gxt.hunan.gov.cn/gxt/xxgk_71033/gzdt/sjfb_80675/index.html?page=1',
            'label': "工信数据",
            'detail_xpath': '//table[@id="list"]//tr[td[2]/a]',
            'url_xpath': './/td[2]/a/@href',
            'title_xpath': './/td[2]/a/text()',
            'publish_time_xpath': './/td[1]/text()',
            'body_xpath': '//div[@class="tys-main-zt"]',
            'total': 5,
            'page': 1,
            'base_url': 'https://gxt.hunan.gov.cn/gxt/xxgk_71033/gzdt/sjfb_80675/index.html?page={}'
        },
    ]

    def start_requests(self):
        for info in self.infoes:
            url = info.get('url')
            logger.info(f"启动请求：{url}")
            yield scrapy.Request(
                url=url,
                callback=self.parse_item,
                meta=copy.deepcopy(info),
                dont_filter=True
            )

    def parse_item(self, response):
        """解析列表页"""
        _meta = response.meta
        label = _meta.get('label')
        detail_xpath = _meta.get('detail_xpath')
        url_xpath = _meta.get('url_xpath')
        title_xpath = _meta.get('title_xpath')
        publish_time_xpath = _meta.get('publish_time_xpath')
        body_xpath = _meta.get('body_xpath')
        total = _meta.get('total')
        page = _meta.get('page')
        base_url = _meta.get('base_url')

        logger.info(f"正在解析列表页：{response.url}")

        rows = response.xpath(detail_xpath)
        logger.info(f"共提取到 {len(rows)} 条记录")

        for ex_url in rows:
            link = ex_url.xpath(url_xpath).get()
            if not link:
                continue
            url = response.urljoin(link)
            if url.endswith('.pdf'):
                continue

            title = ''.join(ex_url.xpath(title_xpath).getall()).strip()
            publish_time = ''.join(ex_url.xpath(publish_time_xpath).getall()).strip()

            logger.info(f"详情链接: {url} | 标题: {title} | 时间: {publish_time}")

            meta = {
                "label": label,
                "title": title,
                "publish_time": publish_time,
                "body_xpath": body_xpath,
            }

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(meta),
                dont_filter=True
            )

        # 翻页逻辑
        if False and page < total:
            page += 1
            next_page = base_url.format(page)
            logger.info(f"准备翻页 -> 第 {page} 页: {next_page}")
            yield scrapy.Request(
                url=next_page,
                callback=self.parse_item,
                meta=copy.deepcopy({
                    'label': label,
                    'detail_xpath': detail_xpath,
                    'url_xpath': url_xpath,
                    'title_xpath': title_xpath,
                    'publish_time_xpath': publish_time_xpath,
                    'body_xpath': body_xpath,
                    'total': total,
                    'page': page,
                    'base_url': base_url,
                }),
                dont_filter=True  # 必须，否则 RFPDupeFilter 会过滤掉
            )

    def parse_detail(self, response):
        """解析详情页"""
        _meta = response.meta

        method = response.request.method
        url = response.request.url
        body = response.request.body.decode('utf-8') if response.request.body else ''

        body_xpath = _meta.get('body_xpath')
        label = _meta.get("label")
        title = _meta.get('title') or response.xpath('//meta[@name="ArticleTitle"]/@content').get()
        publish_time = _meta.get('publish_time') or \
                       ''.join(response.xpath('//publishtime/text()').getall()).strip() or \
                       ''.join(re.findall(r'(\d{4}-\d{2}-\d{2})', response.text)).strip()

        author = response.xpath('//meta[@name="Author"]/@content').get() or \
                 ''.join(re.findall(r'发布机构：</strong><span>(.*?)</span></li>', response.text, re.DOTALL)).strip() or \
                 ''.join(re.findall(r'>信息来源：(.*?)</', response.text, re.DOTALL)).strip()

        attachment_urls = response.xpath(
            '//p[contains(@class, "insertfileTag")]//a | '
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or '
            'contains(@href, ".xls") or contains(@href, ".xlsx") or contains(@href, ".zip") or contains(@href, ".rar")]'
        )

        images = [response.urljoin(i) for i in response.xpath(f"{body_xpath}//img/@src").getall()]
        attachments = get_attachment(attachment_urls, url, self._from)

        item = DataItem({
            "_id": md5(f"{method}{url}{body}".encode("utf-8")).hexdigest(),
            "url": url,
            "spider_from": self._from,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "label": label,
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "body_html": " ".join(response.xpath(body_xpath).getall()),
            "content": " ".join(response.xpath(f"{body_xpath}//text()").getall()),
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category,
        })

        logger.success(f"抓取成功: {title} ({publish_time}) -> {url}")
        yield item
