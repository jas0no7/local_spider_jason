#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
from hashlib import md5
from urllib.parse import urlparse

import requests
from loguru import logger
from lxml import etree

import scrapy
from scrapy.http import HtmlResponse
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment

settings = get_project_settings()

# ==========================
# 0. 全局请求与 Cookie 管理
# ==========================

SESSION = requests.Session()

HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

COOKIES = {}


def get_domain(url: str):
    return urlparse(url).netloc


# ==========================
# 瑞数 412 Cookie 生成模块
# ==========================

def build_cookies_from_412(response, url):
    domain = get_domain(url)
    base_url = f"https://{domain}"

    tree = etree.HTML(response.text)
    if not tree:
        raise RuntimeError("412 页面结构无法解析")

    content_str = tree.xpath('//meta[2]/@content')[0]
    script_str = tree.xpath('//script[1]/text()')[0]
    js_src = tree.xpath('//script[2]/@src')[0]

    js_url = base_url + js_src
    js_code = SESSION.get(js_url, headers=HEADERS, verify=False).text

    with open("content.js", "w", encoding="utf-8") as f:
        f.write(f'content="{content_str}";')
    with open("ts.js", "w", encoding="utf-8") as f:
        f.write(script_str)
    with open("cd.js", "w", encoding="utf-8") as f:
        f.write(js_code)

    logger.info(f"[{domain}] JS 文件写入成功")

    base_cookies = response.cookies.get_dict()

    result = subprocess.run(["node", "env.js"], capture_output=True, text=True)
    dynamic_cookie = result.stdout.strip()

    base_cookies["4hP44ZykCTt5P"] = dynamic_cookie
    return base_cookies


# ==========================
# Cookie 自动管理
# ==========================

def fetch_html_with_cookie(url, params=None):
    domain = get_domain(url)

    if domain not in COOKIES:
        COOKIES[domain] = {}

    if not COOKIES[domain]:
        r1 = SESSION.get(url, headers=HEADERS, verify=False)
        if r1.status_code == 412:
            COOKIES[domain] = build_cookies_from_412(r1, url)
        else:
            COOKIES[domain] = r1.cookies.get_dict()

    r2 = SESSION.get(url, headers=HEADERS, cookies=COOKIES[domain], params=params, verify=False)

    if r2.status_code == 412:
        r1 = SESSION.get(url, headers=HEADERS, verify=False)
        COOKIES[domain] = build_cookies_from_412(r1, url)
        r2 = SESSION.get(url, headers=HEADERS, cookies=COOKIES[domain], params=params, verify=False)

    r2.encoding = r2.apparent_encoding
    return r2.text


# ==========================
# Spider
# ==========================

class DataSpider(CrawlSpider):
    name = "news_fgw_gansu"
    allowed_domains = ["fzgg.gansu.gov.cn", "www.gansu.gov.cn"]

    _from = "甘肃省政府 & 甘肃发改委"
    category = "政策"

    infoes = [
        {
            "url": "https://www.gansu.gov.cn/common/search/77b4ad617c73434dba6491e1de8a615a",
            "label": "甘肃要闻",
            "total": 14740
        },
        {
            "url": "https://fzgg.gansu.gov.cn/common/search/71f133a9775d4075b5857b6a4c75fc8b",
            "label": "政府定价",
            "total": 840
        },
    ]

    # ============================================================
    # ★ 只采第一页（核心修改）
    # ============================================================

    def start_requests(self):
        for info in self.infoes:
            url = info["url"]
            label = info["label"]

            page_size = 20
            page = 1  # ★★★ 强制只采第一页

            params = {
                "sort": "",
                "_isAgg": "false",
                "_isJson": "false",
                "_pageSize": str(page_size),
                "_template": "index",
                "_channelName": "",
                "page": str(page),
            }

            html = fetch_html_with_cookie(url, params=params)

            fake_request = scrapy.Request(url=url, meta={
                "label": label,
                "page": page
            })

            resp = HtmlResponse(url=url, body=html, encoding="utf-8", request=fake_request)
            yield from self.parse_list(resp)

    # ============================================================
    # 列表页解析
    # ============================================================

    def parse_list(self, response):
        label = response.meta["label"]
        page = response.meta["page"]

        lis = response.xpath('//ul[@id="body"]/li')

        for li in lis:
            title = li.xpath('./div[@class="title"]/a/text()').get("").strip()
            href = li.xpath('./div[@class="title"]/a/@href').get("").strip()

            if not href:
                continue

            if href.startswith("http"):
                detail_url = href
            else:
                domain = get_domain(response.url)
                detail_url = f"https://{domain}{href}"

            date = li.xpath('./div[@class="date"]/text()').get("").strip()

            detail_html = fetch_html_with_cookie(detail_url)

            fake_req = scrapy.Request(
                url=detail_url,
                meta={"label": label, "title": title, "publish_time": date}
            )

            detail_resp = HtmlResponse(url=detail_url, body=detail_html, encoding="utf-8", request=fake_req)

            yield from self.parse_detail(detail_resp)

    # ============================================================
    # 详情页解析
    # ============================================================

    def parse_detail(self, response):
        label = response.meta["label"]
        title = response.meta["title"]
        publish_time = response.meta["publish_time"]
        url = response.url

        body_xpath = (
            '('
            '//div[@class="main"] | '
            '//div[@class="mainbox clearfix"] | '
            '//div[@class="article"] | '
            '//div[@class="main mt8"]'
            ')'
        )

        body_html = "".join(response.xpath(body_xpath).getall())
        content = "".join(response.xpath(f"{body_xpath}//text()").getall()).strip()

        images = [response.urljoin(x) for x in response.xpath(f"{body_xpath}//img/@src").getall()]

        attachment_nodes = response.xpath(
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") '
            'or contains(@href, ".xls") or contains(@href, ".zip") or contains(@href, ".rar")]'
        )
        attachments = get_attachment(attachment_nodes, url, self._from)

        item = DataItem()
        item.update({
            "_id": md5(f"{url}{title}".encode("utf-8")).hexdigest(),
            "url": url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "spider_from": self._from,
            "label": label,
            "title": title,
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content,
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category
        })

        yield item
