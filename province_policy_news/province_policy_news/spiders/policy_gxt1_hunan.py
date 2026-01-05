import json
import scrapy
from hashlib import md5
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_attachment, get_now_date

settings = get_project_settings()


class HunanGxtSpider(scrapy.Spider):
    name = "policy_gxt1_hunan"
    allowed_domains = ["api.hunan.gov.cn"]
    category = '政府网站'

    _from = "湖南工业和信息化厅"

    api_url = "https://api.hunan.gov.cn/search/common/search/80675"

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://gxt.hunan.gov.cn",
        "Referer": "https://gxt.hunan.gov.cn/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    def start_requests(self):
        """
        向 API 发送 1-70 页请求
        """
        for page in [1]:
            data = {
                "datas[0][key]": "status",
                "datas[0][value]": "4",
                "datas[0][join]": "and",
                "datas[0][queryType]": "term",

                "datas[1][key]": "publishedTime",
                "datas[1][sort]": "true",
                "datas[1][order]": "desc",
                "datas[1][queryType]": "term",

                "page": str(page),
                "_pageSize": "20",
                "_isAgg": "true"
            }

            yield scrapy.FormRequest(
                url=self.api_url,
                headers=self.headers,
                formdata=data,
                callback=self.parse_api
            )

    def parse_api(self, response):
        """
        解析 API 返回 JSON
        """
        resp_json = json.loads(response.text)
        results = resp_json.get("data", {}).get("results", [])
        method = response.request.method
        body = response.request.body.decode('utf-8') if response.request.body else ''

        for r in results:
            title = r.get("title", "")
            body_html = r.get("content", "")
            content = body_html
            publish_time = r.get("publishedTimeStr", "")
            detail_path = r.get("url", "")
            if detail_path.startswith("http"):
                url = detail_path
            else:
                url = f"https://gxt.hunan.gov.cn{detail_path}" if detail_path else ""

            attachments = get_attachment([], url, self._from)

            yield DataItem({
                "_id": md5(f"{method}{url}{body}".encode("utf-8")).hexdigest(),
                "url": url,
                "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
                "spider_from": self._from,
                "label": "工信数据",
                "title": title,
                "author": "",
                "publish_time": publish_time,
                "body_html": body_html,
                "content": content,
                "images": [],
                "attachment": attachments,
                "spider_date": get_now_date(),
                "category": self.category
            })
