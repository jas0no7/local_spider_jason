import copy
import re
from hashlib import md5

import scrapy
from scrapy.spiders import CrawlSpider
import datetime
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_attachment, get_now_date

settings = get_project_settings()


class PolicyFgwChongqingSpider(CrawlSpider):
    name = 'policy_fgw_chongqing'
    allowed_domains = ['fzggw.cq.gov.cn']
    category = '政府网站'

    _from = '重庆市发展和改革委员会'

    infoes = [
        {
            'url': 'https://fzggw.cq.gov.cn/zwgk/zfxxgkml/zcwj/xzgfxwj/',
            'label': "行政规范文件",
            'detail_xpath': '//div[@class="gkm-cr glw-c"]/div/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span/text()',
            'body_xpath': '//div[@class="zcwjk-xlcon"] | //div[@class="zwxl-main"]',
            'total': 1,
            'page': 1,
            'base_url': 'https://fzggw.cq.gov.cn/zwgk/zfxxgkml/zcwj/xzgfxwj/'
        },
        {
            'url': 'https://fzggw.cq.gov.cn/zwgk/zfxxgkml/zcwj/qtwj/index.html',
            'label': "其他文件",
            'detail_xpath': '//div[@class="gkm-cr glw-c"]/div/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span/text()',
            'body_xpath': '//div[@class="zcwjk-xlcon"] | //div[@class="zwxl-main"]',
            'total': 185,
            'page': 1,
            'base_url': 'https://fzggw.cq.gov.cn/zwgk/zfxxgkml/zcwj/qtwj/index_{}.html'
        },
        {
            'url': 'https://fzggw.cq.gov.cn/zwgk/zfxxgkml/jgxx/jgzc/index.html',
            'label': "价格政策",
            'detail_xpath': '//ul[@class="xhy-c1item underlines overflows xhy-item1 gl-ul"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span/text()',
            'body_xpath': '//div[@class="zwxl-content"] | //div[@class="zwxl-main"]',
            'total': 203,
            'page': 1,
            'base_url': 'https://fzggw.cq.gov.cn/zwgk/zfxxgkml/jgxx/jgzc/index_{}.html'
        },
    ]

    # ---------- 工具函数：当前时间 ----------
    @staticmethod
    def get_now_date():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ---------- 工具函数：附件处理 ----------
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

    # ---------- 列表页入口 ----------
    def start_requests(self):
        for info in self.infoes:
            yield scrapy.Request(
                url=info['url'],
                callback=self.parse_item,
                meta=copy.deepcopy(info),
                dont_filter=True
            )

    # ---------- 列表页 ----------
    def parse_item(self, response):
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

        for li in response.xpath(detail_xpath):
            href = li.xpath(url_xpath).get()
            if not href:
                continue

            url = response.urljoin(href)
            if url.endswith(".pdf"):
                continue

            title = ''.join(li.xpath(title_xpath).getall()).strip()

            if publish_time_xpath:
                publish_time = ''.join(
                    li.xpath(f"string({publish_time_xpath})").getall()
                ).replace("(", "").replace(")", "").strip()
            else:
                publish_time = None

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

        # ---------- 下一页 ----------
        if False and page < total:
            next_page = page + 1
            next_url = (
                meta['url'] if next_page == 1 else base_url.format(next_page)
            )

            next_meta = {
                'label': label,
                'detail_xpath': detail_xpath,
                'url_xpath': url_xpath,
                'title_xpath': title_xpath,
                'publish_time_xpath': publish_time_xpath,
                'body_xpath': body_xpath,
                'total': total,
                'page': next_page,
                'base_url': base_url,
            }

            yield scrapy.Request(
                url=next_url,
                callback=self.parse_item,
                meta=copy.deepcopy(next_meta),
                dont_filter=True
            )

    # ---------- 详情页 ----------
    def parse_detail(self, response):
        meta = response.meta

        method = response.request.method
        body = response.request.body.decode('utf-8') if response.request.body else ""
        url = response.url

        body_xpath = meta['body_xpath']

        title = meta.get("title") or response.xpath(
            '//meta[@name="ArticleTitle"]/@content'
        ).get()

        publish_time = meta.get('publish_time') or \
                       ''.join(response.xpath("//publishtime/text()").getall()).strip() or \
                       ''.join(re.findall(r'发布日期.*?(\d{4}-\d{2}-\d{2})', response.text, re.DOTALL)).strip()

        author = response.xpath('//meta[@name="Author"]/@content').get() or \
                 ''.join(re.findall(r'发布机构：</strong><span>(.*?)</span></li>', response.text, re.DOTALL)).strip() or \
                 ''.join(re.findall(r'>信息来源：(.*?)</', response.text, re.DOTALL)).strip()

        # ---------- 附件 ----------
        attachment_nodes = response.xpath(
            '//p[contains(@class, "insertfileTag")]//a | '
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or '
            'contains(@href, ".xls") or contains(@href, ".xlsx") or contains(@href, ".wps") or '
            'contains(@href, ".zip") or contains(@href, ".rar")]'
        )
        attachments = get_attachment(attachment_nodes, url, self._from)

        body_html = ' '.join(response.xpath(body_xpath).getall())
        content = ' '.join(response.xpath(f"{body_xpath}//text()").getall()).strip()
        images = [response.urljoin(i) for i in response.xpath(f"{body_xpath}//img/@src").getall()]

        yield DataItem({
            "_id": md5(f'{method}{url}{body}'.encode('utf-8')).hexdigest(),
            "url": url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "spider_from": self._from,
            "label": meta['label'],
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
