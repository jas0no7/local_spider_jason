# -*- coding: utf-8 -*-
import copy
import json
from hashlib import md5
from urllib.parse import urljoin

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment

settings = get_project_settings()


class DataSpider(CrawlSpider):
    name = "news_gxt_jiangxi"
    allowed_domains = ["gxt.jiangxi.gov.cn"]

    _from = "江西省工业和信息化厅"
    category = "新闻"
    dupefilter_field = {"batch": "20251107"}

    # ==========================================================
    # 栏目配置（已保留 max_page 但不再使用它）
    # ==========================================================
    infoes = [
        {
            "label": "规划部署",
            "url": "https://gxt.jiangxi.gov.cn/queryList",
            "max_page": 4,  # 不再使用，只采第一页
            "referer": "https://gxt.jiangxi.gov.cn/jxsgyhxxht/ghbs/index.html",
        },
    ]

    headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://gxt.jiangxi.gov.cn",
        "Pragma": "no-cache",
        "Referer": "https://gxt.jiangxi.gov.cn/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/141.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    # ==========================================================
    # 起始请求（已改为只请求第一页）
    # ==========================================================
    def start_requests(self):
        for info in self.infoes:
            label = info["label"]
            url = info["url"]
            referer = info["referer"]

            headers = copy.deepcopy(self.headers)
            headers["Referer"] = referer

            # ★★★ 只采第一页，不再循环 max_page ★★★
            formdata = {
                "current": "1",
                "pageSize": "15",
                "webSiteCode[]": "jxsgyhxxht",
                "channelCode[]": "ghbs",
                "sort": "sortNum",
                "order": "desc",
            }

            meta = {"label": label, "referer": referer}

            yield scrapy.FormRequest(
                url=url,
                headers=headers,
                formdata=formdata,
                meta=meta,
                callback=self.parse_list,
                dont_filter=True,
            )

    # ==========================================================
    # JSON 列表解析
    # ==========================================================
    def parse_list(self, response):
        meta = response.meta
        label = meta.get("label")
        method = response.request.method
        body = response.request.body.decode("utf-8") if response.request.body else ""

        try:
            res_json = json.loads(response.text)
            results = res_json["data"]["results"]
        except Exception as e:
            self.logger.error(f"解析JSON异常: {e}, 原文: {response.text[:200]}")
            return

        base_domain = "https://gxt.jiangxi.gov.cn"

        for item in results:
            source = item.get("source", {})
            title = source.get("title") or source.get("showTitle")
            publish_time = source.get("pubDate")
            author = ""

            # 元数据解析
            try:
                metadata = json.loads(source.get("metadata", "{}"))
                author = metadata.get("author", "")
            except Exception:
                pass

            # 正文 HTML
            content_html = source.get("content", {}).get("content", "")
            content_text = content_html.replace("\n", "").replace("\r", "").replace("  ", "")

            # 图片解析
            image_list = []
            try:
                if source.get("images"):
                    for img in json.loads(source["images"]):
                        image_list.append(urljoin(base_domain, img["filePath"]))
            except Exception:
                pass

            # 内容页 URL
            content_url = ""
            try:
                if source.get("urls"):
                    urls_obj = json.loads(source["urls"])
                    content_url = urljoin(base_domain, urls_obj.get("pc", ""))
            except Exception:
                pass

            # 附件（暂不提供字段）
            attachment_urls = []

            yield DataItem({
                "_id": md5(f"{method}{content_url}{body}".encode("utf-8")).hexdigest(),
                "url": content_url,
                "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
                "spider_from": self._from,
                "label": label,
                "title": title,
                "author": author,
                "publish_time": publish_time,
                "body_html": content_html,
                "content": content_text,
                "images": image_list,
                "attachment": get_attachment(attachment_urls, content_url, self._from),
                "spider_date": get_now_date(),
                "category": self.category,
            })
