import copy
import re
from hashlib import md5
import scrapy
from scrapy.spiders import CrawlSpider
from lxml import etree
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_attachment, get_now_date

settings = get_project_settings()


class PolicyGxtJiangsuSpider(CrawlSpider):
    name = "policy_gxt_jiangsu"
    allowed_domains = ["gxt.jiangsu.gov.cn"]
    handle_httpstatus_list = [403]
    category = '政府网站'

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
        {
            "columnid": "6179",
            "unitid": "403981",
            "label": "政策解读",
        },
        {
            "columnid": "83658",
            "unitid": "403981",
            "label": "省级政策",
        },
        {
            "columnid": "6285",
            "unitid": "405449",
            "label": "数据统计;统计信息",
        },
    ]

    headers = {
        "Accept": "application/xml, text/xml, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://gxt.jiangsu.gov.cn",
        "Pragma": "no-cache",
        "Referer": "https://gxt.jiangsu.gov.cn/col/col80181/index.html?uid=403740&pageNum=3",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "cookie": 'JSESSIONID=D5A1F5D49BBB67A1784450859E7DAB55; __jsluid_s=6adbbfed425abed2a58140d4b6204a37; e34b3568-c02f-45db-8662-33d198d0da1b=WyI1NjQ0Njc3NTciXQ',
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

        attachments = get_attachment(attachment_nodes, url, self._from)

        yield DataItem({
            "_id": md5(f"{method}{url}{body}".encode("utf-8")).hexdigest(),
            "url": url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "spider_from": self._from,
            "label": meta.get("label"),
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content_text,
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category
        })
