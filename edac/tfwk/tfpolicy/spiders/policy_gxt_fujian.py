# -*- coding: utf-8 -*-
import copy
import json
import re
from hashlib import md5

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings
from ..items import DataItem
from edac.tfwk.tfpolicy.mydefine import get_now_date, get_attachment

settings = get_project_settings()


class DataSpider(CrawlSpider):
    name = "policy_gxt_fujian"
    allowed_domains = ["gxt.fujian.gov.cn"]

    _from = "福建省工业和信息化厅"
    dupefilter_field = {"batch": "20251107"}

    # ==========================================================
    # 栏目信息配置
    # ==========================================================
    infoes = [
        {
            "label": "省级政策法规",
            "chnlid": "32377",  # 接口内参数
            "max_page": 5,
            "referer": "https://gxt.fujian.gov.cn/jdhy/zxzcfg/sjzcfg/",
        },
    ]

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://gxt.fujian.gov.cn",
        "Pragma": "no-cache",
        "Referer": "https://gxt.fujian.gov.cn/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/141.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    cookies = {
        "BFreeDialect": "0",
        "zh_choose": "n",
    }

    search_url = "https://gxt.fujian.gov.cn/fjdzapp/search"

    # ==========================================================
    # 起始请求：按栏目分页 POST 请求接口
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
    # 列表页解析：提取标题、时间、详情链接
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
            self.logger.warning("未返回 data 内容")
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
    # 详情页解析：提取正文内容
    # ==========================================================
    def parse_detail(self, response):
        _meta = response.meta
        url = response.url
        title = _meta.get("title")
        publish_time = _meta.get("publish_time")
        label = _meta.get("label")

        # 正文 xpath
        body_xpath = '//div[@class="article_component"]'
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

        yield DataItem(
            {
                "_id": md5(f"GET{url}".encode("utf-8")).hexdigest(),
                "url": url,
                "spider_from": self._from,
                "label": label,
                "title": title,
                "author": author,
                "publish_time": publish_time,
                "body_html": body_html,
                "content": content,
                "images": [response.urljoin(i) for i in response.xpath(f"{body_xpath}//img/@src").extract()],
                "attachment": get_attachment(attachment_urls, url, self._from),
                "spider_date": get_now_date(),
                "spider_topic": "spider-policy-fujian",
            }
        )
