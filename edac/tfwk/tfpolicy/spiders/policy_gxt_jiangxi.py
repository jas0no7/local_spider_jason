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
    name = "policy_gxt_jiangxi"
    allowed_domains = ["gxt.jiangxi.gov.cn"]

    _from = "江西省工业和信息化厅"
    dupefilter_field = {"batch": "20251107"}

    # ==========================================================
    # 栏目信息配置（支持四个接口）
    # ==========================================================
    infoes = [
        {
            "label": "政策文件",
            "channel_code": "zcwj",
            "max_page": 4,
            "referer": "https://gxt.jiangxi.gov.cn/jxsgyhxxht/zcwj/index.html",
        },
        {
            "label": "解读材料",
            "channel_code": "jdcl",
            "max_page": 10,
            "referer": "https://gxt.jiangxi.gov.cn/jxsgyhxxht/jdcl/index.html",
        },
        {
            "label": "规范性文件",
            "channel_code": "gfxwj",
            "max_page": 4,
            "referer": "https://gxt.jiangxi.gov.cn/jxsgyhxxht/gfxwj/index.html",
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

    # 接口 URL
    base_url = "https://gxt.jiangxi.gov.cn/queryList"

    # ==========================================================
    # 起始请求：遍历 infoes 并分页请求
    # ==========================================================
    def start_requests(self):
        for info in self.infoes:
            label = info["label"]
            channel_code = info["channel_code"]
            max_page = info["max_page"]
            referer = info["referer"]

            headers = copy.deepcopy(self.headers)
            headers["Referer"] = referer

            for page in range(1, max_page + 1):
                formdata = {
                    "current": str(page),
                    "pageSize": "15",
                    "webSiteCode[]": "jxsgyhxxht",
                    "channelCode[]": channel_code,
                    "sort": "sortNum",
                    "order": "desc",
                }

                meta = {"label": label, "referer": referer}

                yield scrapy.FormRequest(
                    url=self.base_url,
                    headers=headers,
                    formdata=formdata,
                    meta=meta,
                    callback=self.parse_list,
                    dont_filter=True,
                )

    # ==========================================================
    # 列表页解析：提取 JSON 内容
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

            # 图片提取
            image_list = []
            if source.get("images"):
                try:
                    for img in json.loads(source["images"]):
                        image_list.append(urljoin(base_domain, img["filePath"]))
                except Exception:
                    pass

            # 详情页URL
            content_url = ""
            if source.get("urls"):
                try:
                    urls_obj = json.loads(source["urls"])
                    content_url = urljoin(base_domain, urls_obj.get("pc", ""))
                except Exception:
                    pass

            # 附件
            attachment_urls = []

            # 输出 DataItem
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
                    "attachment": get_attachment(
                        attachment_urls, content_url, self._from
                    ),
                    "spider_date": get_now_date(),
                    "spider_topic": "spider-policy-jiangxi",
                }
            )
