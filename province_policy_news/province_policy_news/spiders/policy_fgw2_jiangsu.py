import scrapy
import json
import re
from hashlib import md5
from lxml import etree
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_attachment, get_now_date

settings = get_project_settings()


class JiangsuEnvSpider(scrapy.Spider):
    name = "policy_fgw2_jiangsu"
    allowed_domains = ["fzggw.jiangsu.gov.cn"]
    category = '政府网站'
    _from = "江苏省发展改革委"

    list_api = "https://fzggw.jiangsu.gov.cn/module/jslib/zcjd/right.jsp"
    domain = "https://fzggw.jiangsu.gov.cn"

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "https://fzggw.jiangsu.gov.cn/module/jslib/zcjd/zcjd.htm",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }
    cookies = {
        "JSESSIONID": "AB0C590C6B0F4DB6A6CD0B6879154CDD",
        "__jsluid_s": "2a972ed8b0d1135bbd7905ce23af19c8",
        "zh_choose_3": "s"
    }

    page_size = 10
    max_page = 1  # 总页数

    # =========================================
    # 1) start_requests：请求每一页列表
    # =========================================
    def start_requests(self):
        for page in range(1, self.max_page + 1):
            formdata = {
                "name": "",
                "keytype": "",
                "year": "",
                "ztflid": "",
                "fwlbbm": "",
                "pageSize": str(self.page_size),
                "pageNo": str(page)
            }

            yield scrapy.FormRequest(
                url=self.list_api,
                method="POST",
                headers=self.headers,
                cookies=self.cookies,
                formdata=formdata,
                callback=self.parse_list,
                meta={"page": page},
                dont_filter=True
            )

    # =========================================
    # 2) parse_list：解析列表页
    # =========================================
    def parse_list(self, response):
        try:
            data = json.loads(response.text)
        except Exception:
            self.logger.error("列表解析失败")
            return

        for item in data.get("data", []):
            vc_title = item.get("vc_title", "")
            deploy_time = item.get("c_deploytime", "")
            detail_url = self.domain + item.get("url", "")

            yield scrapy.Request(
                url=detail_url,
                method="GET",
                headers=self.headers,
                cookies=self.cookies,
                callback=self.parse_detail,
                meta={
                    "title": vc_title,
                    "publish_time": deploy_time,
                },
                dont_filter=True
            )

    # =========================================
    # 3) parse_detail：解析详情页
    # =========================================
    def parse_detail(self, response):

        # ------- 元数据 -------
        meta = response.meta
        title = meta["title"]
        publish_time = meta["publish_time"]

        # ------- 强制 UTF-8 解码 -------
        detail_html = response.body.decode("utf-8", errors="ignore")


        # ------- 使用 lxml 获取内容 -------
        tree = etree.HTML(response.text)
        content_nodes = tree.xpath('//div[@class="bt-content zoom clearfix"]')

        if content_nodes:
            body_html = etree.tostring(content_nodes[0], encoding="utf-8").decode("utf-8")
            body_text = content_nodes[0].xpath("string(.)").strip()
        else:
            body_html = ""
            body_text = ""

        # ------- 图片 -------
        images = [
            response.urljoin(src)
            for src in response.xpath('//div[@class="bt-content zoom clearfix"]//img/@src').getall()
        ]

        # ------- 附件 -------
        attachment_nodes = response.xpath(
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") '
            'or contains(@href, ".docx") or contains(@href, ".xls") '
            'or contains(@href, ".xlsx") or contains(@href, ".zip") '
            'or contains(@href, ".rar")]'
        )
        attachments = get_attachment(attachment_nodes, response.url, self._from)

        # ------- 唯一 _id -------
        method = response.request.method
        body = response.request.body.decode("utf-8") if response.request.body else ""
        _id = md5(f"{method}{response.url}{body}".encode("utf-8")).hexdigest()

        yield DataItem({
            "_id": _id,
            "url": response.url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "spider_from": self._from,
            "label": "政策解读",
            "title": title,
            "author": "",
            "publish_time": publish_time,
            "body_html": body_html,
            "content": body_text,
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category
        })
