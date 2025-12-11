import json
import re
from hashlib import md5

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment

settings = get_project_settings()


class DataSpider(CrawlSpider):
    name = 'policy_zdl'
    allowed_domains = ['cec.org.cn']

    _from = '中国电力企业联合会'
    category = '政策类'

    list_api = "https://cec.org.cn/ms-mcms/mcms/content/list"
    detail_api = "https://cec.org.cn/ms-mcms/mcms/content/detail"

    infoes = [
        {"label": "电力消费", "id": "823", "pageSize": 10, "total": 20},
        {"label": "电力供应", "id": "824", "pageSize": 10, "total": 20},
        {"label": "电力市场", "id": "825", "pageSize": 10, "total": 70},
        {"label": "供需报告", "id": "826", "pageSize": 10, "total": 60},
        {"label": "CEGI指数", "id": "857", "pageSize": 10, "total": 10},
        {"label": "研究成果", "id": "472", "pageSize": 10, "total": 60},
        {"label": "CECI周报", "id": "719", "pageSize": 10, "total": 470},
        {"label": "CECI指数", "id": "718", "pageSize": 10, "total": 2130},
    ]

    def start_requests(self):
        """
        根据 infoes 自动构造所有 list API 请求
        """
        for info in self.infoes:
            total = int(info["total"])
            page_size = int(info["pageSize"])
            total_page = (total + page_size - 1) // page_size

            for page in range(1, total_page + 1):
                params = {
                    "id": info["id"],
                    "pageNumber": page,
                    "pageSize": page_size
                }

                yield scrapy.FormRequest(
                    url=self.list_api,
                    method="GET",
                    formdata={k: str(v) for k, v in params.items()},
                    callback=self.parse_list,
                    meta={"label": info["label"], "cid": info["id"]},
                )

    def parse_list(self, response):
        """
        列表页接口解析
        """
        label = response.meta["label"]
        data = json.loads(response.text)

        if "data" not in data or "list" not in data["data"]:
            return

        for item in data["data"]["list"]:
            article_id = item["articleID"]
            title = item["basicTitle"]
            ts = item.get("publicTime", 0)
            public_time = ""

            if ts:
                public_time = self.format_time(ts)

            # 请求详情 API
            yield scrapy.FormRequest(
                url=self.detail_api,
                method="GET",
                formdata={"id": str(article_id)},
                callback=self.parse_detail,
                meta={
                    "label": label,
                    "title": title,
                    "publish_time": public_time,
                    "article_id": article_id,
                    "body_xpath": "//div[@class='content']"  # 你可按需修改
                }
            )

    def parse_detail(self, response):
        """
        详情解析
        """
        meta = response.meta
        label = meta.get("label")
        title = meta.get("title")
        publish_time = meta.get("publish_time")
        article_id = meta.get("article_id")

        detail_json = json.loads(response.text).get("data", {})

        # 作者
        author = detail_json.get("articleAuthor", "")

        # 正文 HTML
        body_html = detail_json.get("articleContent", "")

        # 内容
        content = re.sub(r'<[^>]+>', '', body_html)

        # 图片
        images = re.findall(r'<img[^>]+src="([^"]+)"', body_html)

        # 附件
        attachments = []
        pdf_url = detail_json.get("pdfUrl")
        if pdf_url:
            attachments.append(pdf_url)

        # 构造详情页 URL（你爬虫需要）
        detail_url = f"https://cec.org.cn/detail/index.html?3-{article_id}"

        # _id 用 method + url + body
        method = "GET"
        body = ""
        _id = md5(f"{method}{detail_url}{body}".encode("utf-8")).hexdigest()

        yield DataItem({
            "_id": _id,
            "url": detail_url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "spider_from": self._from,
            "label": label,
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

    @staticmethod
    def format_time(ts):
        from datetime import datetime
        try:
            return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")
        except:
            return ""
