import copy
import re
from hashlib import md5
import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings
from lxml import etree

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment

settings = get_project_settings()


class PolicyGxtJiangsuSpider(CrawlSpider):
    name = "policy_gxt_jiangsu"
    allowed_domains = ["gxt.jiangsu.gov.cn"]

    _from = "江苏省工业和信息化厅"
    dupefilter_field = {
        "batch": "20251123"
    }

    # 对齐模板：定义 infoes
    infoes = [
        {
            "columnid": "89736",
            "unitid": "405463",
            "label": "政策文件",
        },
        {
            "columnid": "80181",
            "unitid": "403740",
            "label": "统计信息",
        },
    ]

    # headers（与原 requests 版本一致）
    headers = {
        "Accept": "application/xml, text/xml, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://gxt.jiangsu.gov.cn",
        "Referer": "https://gxt.jiangsu.gov.cn/col/col80181/index.html",
    }

    # ------------------------------- #
    # 入口
    # ------------------------------- #
    def start_requests(self):
        for info in self.infoes:
            meta = {
                "label": info["label"],
                "columnid": info["columnid"],
                "unitid": info["unitid"],
                "page": 1
            }
            url = self.build_api_url(start=1, end=25)
            yield scrapy.FormRequest(
                url=url,
                formdata=self.build_form(info["columnid"], info["unitid"]),
                headers=self.headers,
                callback=self.parse_list,
                meta=copy.deepcopy(meta),
                dont_filter=True
            )

    # API 请求 URL
    @staticmethod
    def build_api_url(start, end):
        return f"https://gxt.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp?startrecord={start}&endrecord={end}&perpage=25"

    # API formdata
    @staticmethod
    def build_form(columnid, unitid):
        return {
            "col": "1",
            "appid": "1",
            "webid": "23",
            "path": "/",
            "columnid": columnid,
            "sourceContentType": "1",
            "unitid": unitid,
            "webname": "江苏省工业和信息化厅",
            "permissiontype": "0",
        }

    # ------------------------------- #
    # 解析列表页 XML
    # ------------------------------- #
    def parse_list(self, response):
        meta = response.meta
        label = meta["label"]
        page = meta["page"]
        columnid = meta["columnid"]
        unitid = meta["unitid"]

        text = response.text

        # 与原逻辑一致：无 record 就停止
        if "<record><![CDATA[" not in text:
            return

        # 解析 XML
        xml_tree = etree.XML(text.encode("utf-8"))
        cdata_list = xml_tree.xpath("//record/text()")

        for cdata in cdata_list:
            li_html = etree.HTML(cdata.strip())

            title = li_html.xpath("//a/@title")
            href = li_html.xpath("//a/@href")
            date = li_html.xpath("//b/text()")

            if not href:
                continue

            url = "https://gxt.jiangsu.gov.cn" + href[0]

            detail_meta = {
                "label": label,
                "title": title[0] if title else "",
                "publish_time": date[0] if date else "",
            }

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(detail_meta),
                headers=self.headers,
                dont_filter=True
            )

        # 下一页
        next_page = page + 1
        start = (next_page - 1) * 25 + 1
        end = next_page * 25
        next_url = self.build_api_url(start, end)

        meta["page"] = next_page

        yield scrapy.FormRequest(
            url=next_url,
            formdata=self.build_form(columnid, unitid),
            headers=self.headers,
            callback=self.parse_list,
            meta=copy.deepcopy(meta),
            dont_filter=True
        )

    # ------------------------------- #
    # 解析详情页
    # ------------------------------- #
    def parse_detail(self, response):
        meta = response.meta

        method = response.request.method
        body = response.request.body.decode("utf-8") if response.request.body else ""
        url = response.url

        title = meta.get("title") or response.xpath('//meta[@name="ArticleTitle"]/@content').get()

        publish_time = meta.get("publish_time") or \
                       ''.join(response.xpath('//publishtime/text()').extract()).strip() or \
                       ''.join(re.findall(r'(\d{4}-\d{2}-\d{2})', response.text))

        author = response.xpath('//meta[@name="Author"]/@content').get() or ""

        # 正文 xpath：与原逻辑保持一致，两种结构都尝试
        body_xpaths = [
            '//div[@class="scroll_main bfr_article_content"]',
            '//div[@class="article_zoom bfr_article_content"]'
        ]

        body_html = ""
        content_text = ""
        images = []

        for xp in body_xpaths:
            if response.xpath(xp):
                body_html = ''.join(response.xpath(xp).extract())
                content_text = ' '.join(response.xpath(f'{xp}//text()').extract())
                images = [response.urljoin(i) for i in response.xpath(f'{xp}//img/@src').extract()]
                break

        attachment_urls = response.xpath(
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or '
            'contains(@href, ".xls") or contains(@href, ".xlsx") or contains(@href, ".zip") or contains(@href, ".rar")]'
        )

        yield DataItem({
            "_id": md5(f"{method}{url}{body}".encode("utf-8")).hexdigest(),
            "url": url,
            "spider_from": self._from,
            "label": meta.get("label"),
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content_text,
            "images": images,
            "attachment": get_attachment(attachment_urls, url, self._from),
            "spider_date": get_now_date(),
            "spider_topic": "spider-policy-jiangsu"
        })
