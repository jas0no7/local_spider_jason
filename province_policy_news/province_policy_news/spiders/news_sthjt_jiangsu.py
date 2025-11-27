# --coding:utf-8--
import copy
import re
import scrapy
from hashlib import md5
from lxml import etree
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_attachment, get_now_date

settings = get_project_settings()


class JiangsuEnvSpider(scrapy.Spider):
    name = "news_sthjt_jiangsu"
    allowed_domains = ["sthjt.jiangsu.gov.cn"]
    category = '政府网站'

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "application/xml, text/xml, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Origin": "https://sthjt.jiangsu.gov.cn",
            "Referer": "https://sthjt.jiangsu.gov.cn/col/col84025/index.html?uid=402134&pageNum=1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
    }

    _from = "江苏省生态环境厅"

    infoes = [
        {
            "url": "https://sthjt.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp",
            "label": "公示公告",
            "columnid": "84025",
            "unitid": "402134",
            "webid": "14",
            "path": "/",
            "appid": "1",
            "sourceContentType": "1",
            "webname": "江苏省生态环境厅",
            "permissiontype": "0",
            "body_xpath": "//div[@class='zoom']",
            "total_pages": 688,
            "perpage": 15,
            "page": 1
        }
    ]

    def start_requests(self):
        for info in self.infoes:
            start = (info["page"] - 1) * info["perpage"] + 1
            end = info["page"] * info["perpage"]

            formdata = {
                "col": "1",
                "appid": info["appid"],
                "webid": info["webid"],
                "path": info["path"],
                "columnid": info["columnid"],
                "sourceContentType": info["sourceContentType"],
                "unitid": info["unitid"],
                "webname": info["webname"],
                "permissiontype": info["permissiontype"],
                "startrecord": str(start),
                "endrecord": str(end),
                "perpage": str(info["perpage"])
            }

            yield scrapy.FormRequest(
                url=info["url"],
                formdata=formdata,
                callback=self.parse_list,
                meta=copy.deepcopy(info),
                dont_filter=True
            )

    def parse_list(self, response):
        meta = response.meta
        page = meta["page"]
        total_pages = meta["total_pages"]
        perpage = meta["perpage"]

        if b"<record><![CDATA[" not in response.body:
            self.logger.info("无更多数据，停止循环")
            return

        try:
            xml_text = response.text
            root = etree.fromstring(xml_text.encode('utf-8'))
            records = root.xpath('//record')

            for record in records:
                cdata_content = record.text
                if not cdata_content:
                    continue

                html_element = etree.fromstring(cdata_content)

                a_tag = html_element.xpath('.//a')[0]
                title = a_tag.get('title')
                partial_url = a_tag.get('href')

                span_tag = html_element.xpath('.//span')[0]
                publish_time = span_tag.text

                if not partial_url:
                    continue

                if partial_url.startswith("http"):
                    url = partial_url
                else:
                    url = f'https://sthjt.jiangsu.gov.cn{partial_url}'

                if url.lower().endswith(".pdf"):
                    continue

                detail_meta = {
                    "label": meta["label"],
                    "title": title,
                    "publish_time": publish_time,
                    "body_xpath": meta["body_xpath"]
                }

                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                    meta=detail_meta,
                    dont_filter=True
                )

        except Exception as e:
            self.logger.error(f"解析列表页XML 失败: {e}")

        if page < total_pages:
            page += 1
            meta["page"] = page

            start = (page - 1) * perpage + 1
            end = page * perpage

            formdata = {
                "col": "1",
                "appid": meta["appid"],
                "webid": meta["webid"],
                "path": meta["path"],
                "columnid": meta["columnid"],
                "sourceContentType": meta["sourceContentType"],
                "unitid": meta["unitid"],
                "webname": meta["webname"],
                "permissiontype": meta["permissiontype"],
                "startrecord": str(start),
                "endrecord": str(end),
                "perpage": str(perpage)
            }

            yield scrapy.FormRequest(
                url=meta["url"],
                formdata=formdata,
                callback=self.parse_list,
                meta=copy.deepcopy(meta),
                dont_filter=True
            )

    def parse_detail(self, response):
        meta = response.meta
        method = response.request.method
        body = response.request.body.decode('utf-8') if response.request.body else ''
        url = response.request.url
        title = meta["title"]

        publish_time = meta.get("publish_time")
        if not publish_time:
            publish_time = "".join(response.xpath("//publishtime/text()").getall()).strip() or \
                           "".join(re.findall(r"发布日期.*?(\d{4}-\d{2}-\d{2})", response.text))

        body_xpath = meta["body_xpath"]
        body_html = " ".join(response.xpath(body_xpath).getall())
        content = " ".join(response.xpath(f"{body_xpath}//text()").getall()).strip()
        images = [
            response.urljoin(i)
            for i in response.xpath(f"{body_xpath}//img/@src").getall()
        ]

        attachment_nodes = response.xpath(
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") '
            'or contains(@href, ".docx") or contains(@href, ".xls") '
            'or contains(@href, ".xlsx") or contains(@href, ".zip") '
            'or contains(@href, ".rar")]'
        )
        attachments = get_attachment(attachment_nodes, url, self._from)

        yield DataItem({
            "_id": md5(f"{method}{url}{body}".encode("utf-8")).hexdigest(),
            "url": url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "spider_from": self._from,
            "label": meta["label"],
            "title": title,
            "author": "",
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content,
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category
        })
