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
    name = "news_fgw_fujian"
    allowed_domains = ["fgw.fujian.gov.cn"]

    _from = "福建省发展和改革委员会"
    category = "新闻"
    dupefilter_field = {"batch": "20251107"}

    # ==========================================================
    # 栏目信息配置
    # ==========================================================
    infoes = [
        {
            "label": "省政府政策文件",
            "chnlid": "9374",        # 接口内参数
            "max_page": 2,           # 抓取页数
            "referer": "https://fgw.fujian.gov.cn/zwgk/fgzd/szcfg/",
        },
        {
            "label": "省发改委政策文件",
            "chnlid": "9375",  # 接口内参数
            "max_page": 4,  # 抓取页数
            "referer": "https://fgw.fujian.gov.cn/zwgk/fgzd/sfgwgfxwj/",
        },
    ]

    # ==========================================================
    # 公共 headers 与 cookies
    # ==========================================================
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://fgw.fujian.gov.cn",
        "Pragma": "no-cache",
        "Referer": "https://fgw.fujian.gov.cn/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/141.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    cookies = {
        "Secure": "",
        "BFreeDialect": "0",
        "zh_choose": "n",
        "BFreeSecret": "%7B%22code%22%3A200%2C%22sn%22%3A%2217467582006a0371%22%2C%22asr%22%3A%5B%7B%22desc%22%3A%22%E6%99%AE%E9%80%9A%E8%AF%9D%22%2C%22name%22%3A%22pth%22%2C%22proName%22%3A%22baidu%22%2C%22soundType%22%3A%221%22%7D%5D%7D",
        "_gscu_1922619767": "62508871qzg1v013",
        "_gscbrs_1922619767": "1",
        "_gscs_1922619767": "62508871xkwfp313|pv:2"
    }

    search_url = "https://fgw.fujian.gov.cn/fjdzapp/search"

    # ==========================================================
    # 起始请求（POST分页）
    # ==========================================================
    def start_requests(self):
        for info in self.infoes:
            label = info["label"]
            chnlid = info["chnlid"]
            max_page = info["max_page"]
            referer = info["referer"]

            headers = copy.deepcopy(self.headers)
            headers["Referer"] = referer

            for page in range(1, max_page + 1):
                formdata = {
                    "channelid": "229105",
                    "sortfield": "-docorder,-docreltime",
                    "classsql": f"chnlid={chnlid}",
                    "classcol": "publishyear",
                    "classnum": "100",
                    "classsort": "0",
                    "cache": "true",
                    "page": str(page),
                    "prepage": "75",
                }

                meta = {"label": label, "referer": referer}

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
    # 解析接口返回的 JSON 列表
    # ==========================================================
    def parse_list(self, response):
        meta = response.meta
        label = meta.get("label")

        try:
            data_json = json.loads(response.text)
        except Exception:
            self.logger.error(f"JSON 解析失败: {response.text[:200]}")
            return

        data_list = data_json.get("data", [])
        if not data_list:
            self.logger.warning("接口未返回 data 内容")
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
    # 解析详情页
    # ==========================================================
    def parse_detail(self, response):
        _meta = response.meta
        method = response.request.method
        body = response.request.body.decode("utf-8") if response.request.body else ""
        url = response.request.url
        title = _meta.get("title")
        publish_time = _meta.get("publish_time")
        label = _meta.get("label")

        # 正文 XPath
        body_xpath = '//div[@class="xl_con"] | //div[@class="article_component"] | //div[@class="tabs tab_base_01 rules_con1"]'
        body_html = " ".join(response.xpath(body_xpath).extract())
        content = " ".join(response.xpath(f"{body_xpath}//text()").extract())

        author = (
            response.xpath('//meta[@name="Author"]/@content').get()
            or "".join(re.findall(r'信息来源[:：]\s*(.*?)<', response.text))
        )

        # 附件
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
