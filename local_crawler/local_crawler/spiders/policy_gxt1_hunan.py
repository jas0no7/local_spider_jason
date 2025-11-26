import json
import scrapy
from hashlib import md5


class HunanGxtSpider(scrapy.Spider):
    name = "policy_gxt1_hunan"
    allowed_domains = ["api.hunan.gov.cn"]

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
        for page in range(1, 71):
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

        for r in results:
            title = r.get("title", "")
            content = r.get("content", "")
            publish_time = r.get("publishedTimeStr", "")

            yield {
                "_id": md5(f"{title}{publish_time}".encode("utf-8")).hexdigest(),
                "label": "工信数据",
                "title": title,
                "content": content,
                "publish_time": publish_time,
                "spider_from": self._from,
            }
