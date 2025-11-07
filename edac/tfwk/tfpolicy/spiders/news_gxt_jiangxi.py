# -*- coding: utf-8 -*-
import copy
import json
import re
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
    dupefilter_field = {"batch": "20251107"}

    # ==========================================================
    # 栏目信息配置（保留 infoes 格式）
    # ==========================================================
    infoes = [
        {
            "label": "规划部署",
            "url": "https://gxt.jiangxi.gov.cn/queryList",
            "max_page": 4,
            "referer": "https://gxt.jiangxi.gov.cn/jxsgyhxxht/ghbs/index.html",
        },
    ]

    # ==========================================================
    # 公共 headers
    # ==========================================================
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
    # 起始请求
    # ==========================================================
    def start_requests(self):
        for info in self.infoes:
            label = info["label"]
            max_page = info["max_page"]
            url = info["url"]
            referer = info["referer"]

            headers = copy.deepcopy(self.headers)
            headers["Referer"] = referer

            for page in range(1, max_page + 1):
                formdata = {
                    "current": str(page),
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
    # 列表页解析（JSON）
    # ==========================================================
    def parse_list(self, response):
        meta = response.meta
        label = meta.get("label")

        try:
            res_json = json.loads(response.text)
            results = res_json["data"]["results"]
        except Exception as e:
            self.logger.error(f"解析JSON出错: {e}, 原文: {response.text[:200]}")
            return

        base_domain = "https://gxt.jiangxi.gov.cn"

        for item in results:
            source = item.get("source", {})
            title = source.get("title") or source.get("showTitle")
            publish_time = source.get("pubDate")
            author = json.loads(source.get("metadata", "{}")).get("author", "")
            content_html = source.get("content", {}).get("content", "")
            content_text = (
                content_html.replace("\n", "").replace("\r", "").replace("  ", "")
            )

            # ---- 图片 ----
            image_list = []
            if source.get("images"):
                try:
                    for img in json.loads(source["images"]):
                        image_list.append(urljoin(base_domain, img["filePath"]))
                except Exception:
                    pass

            # ---- 正文详情 URL ----
            content_url = ""
            if source.get("urls"):
                try:
                    urls_obj = json.loads(source["urls"])
                    content_url = urljoin(base_domain, urls_obj.get("pc", ""))
                except Exception:
                    pass

            # ---- 附件提取 ----
            attachment_urls = []  # 暂无附件字段

            # ---- 构造 DataItem ----
            yield DataItem(
                {
                    "_id": md5(f"GET{content_url}".encode("utf-8")).hexdigest(),
                    "url": content_url,
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
                    "spider_topic": "spider-news-jiangxi",
                }
            )
