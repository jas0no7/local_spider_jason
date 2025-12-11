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
    name = "news_fgw_jiangsu"
    allowed_domains = ["fzggw.jiangsu.gov.cn"]
    category = '政府网站'

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "application/xml, text/xml, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://fzggw.jiangsu.gov.cn",
            "Pragma": "no-cache",
            "Referer": "https://fzggw.jiangsu.gov.cn/col/col282/index.html?uid=423656&pageNum=3",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
    }

    _from = "江苏省发展和改革委员会"

    infoes = [
        {
            "url": "https://fzggw.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp",
            "label": "发改要闻",
            "columnid": "282",
            "unitid": "423656",
            "webid": "3",
            "path": "/",
            "appid": "1",
            "sourceContentType": "1",
            "webname": "江苏省发展和改革委员会",
            "permissiontype": "0",
            "body_xpath": "//div[contains(@class, 'bt-content')]",
            "total_pages": 16,
            "perpage": 10,
            "page": 1
        }
    ]

    # =======================
    # 只采第一页
    # =======================
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

    # =======================
    # 列表页解析（第一页）
    # =======================
    def parse_list(self, response):
        meta = response.meta

        if b"<record><![CDATA[" not in response.body:
            self.logger.info("无数据")
            return

        try:
            root = etree.fromstring(response.text.encode('utf-8'))
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
                    url = f'https://fzggw.jiangsu.gov.cn{partial_url}'

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
            self.logger.error(f"解析列表页 XML 失败: {e}")

        # =====================
        # ❌ 删除翻页逻辑
        # =====================
        return

    # =======================
    # 详情页解析
    # =======================
    def parse_detail(self, response):
        meta = response.meta
        method = response.request.method
        body = response.request.body.decode('utf-8') if response.request.body else ''
        url = response.request.url
        title = meta["title"]

        body_xpath = meta["body_xpath"]

        body_html = " ".join(response.xpath(body_xpath).getall())
        content = " ".join(response.xpath(f"{body_xpath}//text()").getall()).strip()

        publish_time = meta.get("publish_time") or \
                       "".join(re.findall(r"(\d{4}-\d{2}-\d{2})", response.text))

        images = [response.urljoin(i) for i in response.xpath(f"{body_xpath}//img/@src").getall()]

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
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content,
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category
        })
