# -*- coding: utf-8 -*-
import copy
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
    name = "news_sthjt_fujian"
    allowed_domains = ["sthjt.fujian.gov.cn"]

    _from = "福建省生态环境厅"
    category = "新闻"
    dupefilter_field = {"batch": "20251107"}

    # ==========================================================
    # 栏目信息（infoes 替代 columns）
    # ==========================================================
    infoes = [
        {
            "label": "媒体报道",
            "chnlid": "358",
            "max_page": 77,
            "referer": "https://sthjt.fujian.gov.cn/zwgk/hbyw/",
        },
        {
            "label": "文字解读",
            "chnlid": "353",
            "max_page": 20,
            "referer": "https://sthjt.fujian.gov.cn/zwgk/sthjyw/stdt/",
        },
    ]

    # 公共请求头与 cookies
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://sthjt.fujian.gov.cn",
        "Pragma": "no-cache",
        "Referer": "https://sthjt.fujian.gov.cn/zwgk/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/141.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    cookies = {
        "Secure": "",
        "BFreeDialect": "0",
        "BFreeSecret": "%7B%22code%22%3A200%2C%22sn%22%3A%22544e417c00b40894%22%2C%22asr%22%3A%5B%7B%22desc%22%3A%22%E6%99%AE%E9%80%9A%E8%AF%9D%22%2C%22name%22%3A%22pth%22%2C%22proName%22%3A%22baidu%22%2C%22soundType%22%3A%221%22%7D%5D%7D"
    }

    search_url = "https://sthjt.fujian.gov.cn/fjdzapp/search"

    # ==========================================================
    # 起始请求：遍历 infoes → POST 搜索接口
    # ==========================================================
    def start_requests(self):
        for info in self.infoes:
            label = info["label"]
            chnlid = info["chnlid"]
            max_page = info["max_page"]
            referer = info["referer"]

            headers = copy.deepcopy(self.headers)
            headers["Referer"] = referer

            for page in [1]:
                formdata = {
                    "channelid": "229105",
                    "sortfield": "-docorderpri,-docreltime",
                    "classsql": f"chnlid={chnlid}",
                    "classcol": "publishyear",
                    "classnum": "100",
                    "classsort": "0",
                    "cache": "true",
                    "page": str(page),
                    "prepage": "75",
                }

                meta = {
                    "label": label,
                    "referer": referer,
                }

                yield scrapy.FormRequest(
                    url=self.search_url,
                    headers=headers,
                    cookies=self.cookies,
                    formdata=formdata,
                    meta=meta,
                    callback=self.parse_list,
                    dont_filter=True,
                )

    # ==========================================================
    # 列表页解析：提取 detail_url 并进入详情页
    # ==========================================================
    def parse_list(self, response):
        meta = response.meta
        label = meta.get("label")

        try:
            data_json = json.loads(response.text)
        except Exception:
            self.logger.error(f"无法解析 JSON: {response.text[:200]}")
            return

        data_list = data_json.get("data", [])
        if not data_list:
            self.logger.warning("未返回 data 字段内容")
            return

        for item in data_list:
            title = item.get("doctitle") or item.get("docpeople")
            publish_time = item.get("docreltime")
            detail_url = item.get("docpuburl") or item.get("chnldocurl")
            if not detail_url:
                continue

            meta_detail = {
                "label": label,
                "title": title,
                "publish_time": publish_time,
            }

            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail,
                meta=meta_detail,
                dont_filter=True,
            )

    # ==========================================================
    # 详情页解析：提取正文与附件
    # ==========================================================
    def parse_detail(self, response):
        _meta = response.meta
        method = response.request.method
        body = response.request.body.decode("utf-8") if response.request.body else ""
        url = response.request.url
        title = _meta.get("title")
        publish_time = _meta.get("publish_time")
        label = _meta.get("label")

        # 提取正文
        body_xpath = '//div[@class="article_component"] | //div[@class="xl-main"]'
        body_html = " ".join(response.xpath(body_xpath).extract())
        content = " ".join(response.xpath(f"{body_xpath}//text()").extract())

        author = (
            response.xpath('//meta[@name="Author"]/@content').get()
            or "".join(re.findall(r'信息来源[:：]\s*(.*?)<', response.text))
        )

        attachment_urls = response.xpath(
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") '
            'or contains(@href, ".docx") or contains(@href, ".xls") '
            'or contains(@href, ".xlsx") or contains(@href, ".wps") '
            'or contains(@href, ".zip") or contains(@href, ".rar")]'
        )

        images = [response.urljoin(i) for i in response.xpath(f"{body_xpath}//img/@src").extract()]
        attachments = get_attachment(attachment_urls, url, self._from)

        yield DataItem({
            "_id": md5(f"{method}{url}{body}".encode("utf-8")).hexdigest(),
            "url": url,
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
