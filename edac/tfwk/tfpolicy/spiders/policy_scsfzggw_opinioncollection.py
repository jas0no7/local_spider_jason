import json
from hashlib import md5
import scrapy
from scrapy.utils.project import get_project_settings
from edac.tfwk.tfpolicy.mydefine import get_now_date, get_attachment  # 修改：新增 get_attachment 导入

from lxml import etree  # 修改：新增 etree，用于构造 fake <a> 标签列表

settings = get_project_settings()
policy_kafka_topic = settings.get('POLICY_KAFKA_TOPIC')


class OpinionCollectionSpider(scrapy.Spider):
    name = 'policy_scsfzggw_opinioncollection'
    allowed_domains = ['fgw.sc.gov.cn']

    _from = '四川省发展改革委'
    dupefilter_field = {
        "batch": "20240322"
    }

    api_url = "https://fgw.sc.gov.cn/communication/api-collect/frontArticle/pageList"
    file_api_url = "https://fgw.sc.gov.cn/communication/api-collect/frontArticle/fileLoad"
    file_download_prefix = "https://fgw.sc.gov.cn/communication/api-common/file/download?path="

    detail_url_template = (
        "https://fgw.sc.gov.cn/hd/yjzj_details?"
        "siteCode=5100000018&site=sfgw&url=/sfgw/yjzj/newyjzj_detail.shtml&id={id}"
    )

    def start_requests(self):
        payload = {
            "pageNum": 1,
            "pageSize": 10,
            "sortMap": {"startTime": "desc"},
            "params": {
                "deptId": "2cf9d7a6fa3a465b83c166778a79ccdf",
                "siteNo": "",
                "siteUrl": ""
            }
        }
        yield scrapy.Request(
            url=self.api_url,
            method="POST",
            body=json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest"
            },
            callback=self.parse_list,
            meta={"page": 1, "use_proxy": False},
            dont_filter=True
        )

    def parse_list(self, response):
        page = response.meta["page"]
        data = json.loads(response.text)
        rows = data.get("data", {}).get("rows", [])
        total = data.get("data", {}).get("total", 0)
        page_size = data.get("data", {}).get("pageSize", 10)

        for row in rows:
            rec_id = row["id"]
            title = row.get("title")
            publish_time = row.get("startTime")
            content_snippet = row.get("content")
            author = row.get("siteName")
            label = "首页;互动交流;意见征集"

            detail_url = self.detail_url_template.format(id=rec_id)

            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail,
                meta={
                    "rec_id": rec_id,
                    "title": title,
                    "publish_time": publish_time,
                    "summary": content_snippet,
                    "author": author,
                    "label": label,
                    "use_proxy": False,
                }
            )

        total_pages = (total + page_size - 1) // page_size
        if page < total_pages:
            next_page = page + 1
            payload = {
                "pageNum": next_page,
                "pageSize": page_size,
                "sortMap": {"startTime": "desc"},
                "params": {
                    "deptId": "2cf9d7a6fa3a465b83c166778a79ccdf",
                    "siteNo": "",
                    "siteUrl": ""
                }
            }
            yield scrapy.Request(
                url=self.api_url,
                method="POST",
                body=json.dumps(payload),
                headers={
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest"
                },
                callback=self.parse_list,
                meta={"page": next_page, "use_proxy": False},
                dont_filter=True
            )

    def parse_detail(self, response):
        meta = response.meta

        rec_id = meta["rec_id"]
        title = meta["title"]
        publish_time = meta["publish_time"]
        author = meta["author"]
        label = meta["label"]

        content_texts = response.xpath('//*[@id="container"]/div/div/div[2]/div[2]').getall()
        content = " ".join([t.strip() for t in content_texts if t.strip()])

        yield scrapy.FormRequest(
            url=self.file_api_url,
            method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest",
            },
            formdata={"id": rec_id},
            callback=self.parse_fileLoad,
            meta={
                "rec_id": rec_id,
                "title": title,
                "publish_time": publish_time,
                "author": author,
                "label": label,
                "original_url": response.url,
                "content_detail": content,
                "body_html_detail": response.text,
                "summary": meta.get("summary"),
            },
            dont_filter=True
        )

    def parse_fileLoad(self, response):
        meta = response.meta

        try:
            data = json.loads(response.text)
        except Exception as e:
            self.logger.error(f"附件接口解析失败: {e}")
            data = {}

        # 修改：构造伪 a 标签结构，统一交给 get_attachment 处理
        a_tags_html = ""
        seen_paths = set()
        for it in data.get("data", []):
            name = (it.get("fileName") or it.get("name") or "附件").strip()
            path = it.get("path")
            if path and path not in seen_paths:
                seen_paths.add(path)
                url = f"{self.file_download_prefix}{path}"
                a_tags_html += f'<a href="{url}">{name}</a>'

        fake_html = etree.HTML(a_tags_html)
        attachment_elements = fake_html.xpath('//a')

        # 修改：使用统一 get_attachment 上传并返回结果
        attachment = get_attachment(attachment_elements, meta["original_url"], self._from)

        yield {
            "_id": md5((meta["rec_id"] + meta["title"]).encode("utf-8")).hexdigest(),
            "url": meta["original_url"],
            "spider_from": self._from,
            "title": meta["title"],
            "label": meta["label"],
            "author": meta["author"],
            "publish_time": meta["publish_time"],
            "content": meta["content_detail"],
            "body_html": meta["body_html_detail"],
            "attachment": attachment,
            "images": [],
            "spider_date": get_now_date(),
            "spider_topic": policy_kafka_topic,
        }
