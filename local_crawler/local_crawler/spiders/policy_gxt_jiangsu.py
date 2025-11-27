import copy
import re
from hashlib import md5
import scrapy
from scrapy.spiders import CrawlSpider
from lxml import etree


class PolicyGxtJiangsuSpider(CrawlSpider):
    name = "policy_gxt_jiangsu"
    allowed_domains = ["gxt.jiangsu.gov.cn"]
    handle_httpstatus_list = [403]

    _from = "江苏省工业和信息化厅"

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

    headers = {
        "Accept": "application/xml, text/xml, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://gxt.jiangsu.gov.cn",
        "Referer": "https://gxt.jiangsu.gov.cn/col/col80181/index.html",
        "cookie":"__jsluid_s=6adbbfed425abed2a58140d4b6204a37; e34b3568-c02f-45db-8662-33d198d0da1b=WyIyNzE4Nzk4NjkwIl0"
    }

    # ---------- 工具函数：内部实现 get_attachment ----------
    @staticmethod
    def _get_attachment(a_tags, page_url):
        """把附件的 <a> 标签转换成绝对 URL 列表"""
        attachments = []
        for a in a_tags:
            href = a.xpath("./@href").get()
            if href:
                attachments.append(
                    a.root.base_url + href if href.startswith("/") else href
                )
        return attachments

    # ---------- 工具函数：当前日期 ----------
    @staticmethod
    def _now():
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ---------- API 入口 ----------
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

    @staticmethod
    def build_api_url(start, end):
        return f"https://gxt.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp?startrecord={start}&endrecord={end}&perpage=25"

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

    # ---------- 列表页 ----------
    def parse_list(self, response):
        meta = response.meta
        page = meta["page"]
        columnid = meta["columnid"]
        unitid = meta["unitid"]
        label = meta["label"]

        text = response.text
        if "<record><![CDATA[" not in text:
            return

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
                dont_filter=True,
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

    # ---------- 详情页 ----------
    def parse_detail(self, response):
        meta = response.meta

        method = response.request.method
        body = response.request.body.decode("utf-8") if response.request.body else ""
        url = response.url

        title = meta.get("title") or response.xpath(
            '//meta[@name="ArticleTitle"]/@content').get()

        publish_time = meta.get("publish_time") or \
                       ''.join(response.xpath('//publishtime/text()').getall()).strip() or \
                       ''.join(re.findall(r'(\d{4}-\d{2}-\d{2})', response.text))

        author = response.xpath(
            '//meta[@name="Author"]/@content').get() or ""

        body_xpaths = [
            '//div[@class="scroll_main bfr_article_content"]',
            '//div[@class="article_zoom bfr_article_content"]'
        ]

        body_html = ""
        content_text = ""
        images = []

        for xp in body_xpaths:
            if response.xpath(xp):
                body_html = ''.join(response.xpath(xp).getall())
                content_text = ' '.join(response.xpath(f'{xp}//text()').getall()).strip()
                images = [response.urljoin(i) for i in response.xpath(f'{xp}//img/@src').getall()]
                break

        attachment_nodes = response.xpath(
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or '
            'contains(@href, ".xls") or contains(@href, ".xlsx") or contains(@href, ".zip") or contains(@href, ".rar")]'
        )

        attachment_urls = [response.urljoin(a.xpath("./@href").get()) for a in attachment_nodes]

        yield {
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
            "attachments": attachment_urls,
            "spider_date": self._now(),
        }
