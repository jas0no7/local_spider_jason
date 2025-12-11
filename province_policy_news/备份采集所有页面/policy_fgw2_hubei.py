import copy
import re
import json
import subprocess
from hashlib import md5
from urllib.parse import urljoin

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment

from loguru import logger
from lxml import etree
from curl_cffi import requests as curl_requests
import requests

settings = get_project_settings()

# =====================================================================
#  自动生成湖北发改委 Cookie（封装成函数，让 Scrapy 可以调用）
# =====================================================================
def get_valid_cookies(start_url):
    logger.info("开始执行动态 Cookie 获取流程...")

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Referer": "https://fgw.hubei.gov.cn/fbjd/zc/gfwj/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    # -------- 1. curl_cffi 绕过 JS 反爬 -----------
    first_resp = curl_requests.get(start_url, headers=headers)
    first_tree = etree.HTML(first_resp.text)

    contentStr = first_tree.xpath('//meta[2]/@content')[0]
    scriptStr = first_tree.xpath('//script[1]/text()')[0]
    js_url = first_tree.xpath('//script[2]/@src')[0]

    open("content.js", "w", encoding="utf-8").write(f'content="{contentStr}";')
    open("ts.js", "w", encoding="utf-8").write(scriptStr)
    open("cd.js", "w", encoding="utf-8").write(
        curl_requests.get(urljoin("https://fgw.hubei.gov.cn", js_url)).text
    )

    logger.info("content.js / ts.js / cd.js 保存成功")

    # -------- 2. node env.js 生成 cookie -----------
    result = subprocess.run(["node", "env.js"], capture_output=True, text=True)
    dynamic_cookie = result.stdout.strip()

    base_cookies = dict(first_resp.cookies)
    base_cookies["924omrTVcFchP"] = dynamic_cookie

    logger.info(f"动态 Cookie 已生成：{base_cookies}")
    return base_cookies


# =====================================================================
# Scrapy Spider
# =====================================================================
class DataSpider(CrawlSpider):
    name = 'policy_fgw2_hubei'
    allowed_domains = ['fgw.hubei.gov.cn']
    _from = '湖北发改委'
    category = "政策"

    # ========== ★ JSON 列表接口 =============================
    list_api = "https://fgw.hubei.gov.cn/fbjd/zc/gfwj/wj/gfxwj.json"

    # ========== 首页地址（用于生成 Cookie）==================
    cookie_home = "https://fgw.hubei.gov.cn/fbjd/zc/gfwj/"

    # ==========================================================
    # Scrapy 初始化时只执行一次：生成 Cookie
    # ==========================================================
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        logger.info("Scrapy 正在初始化湖北发改委动态 Cookie ...")
        self.base_cookie = get_valid_cookies(self.cookie_home)
        logger.info(f"Cookie 初始化完成：{self.base_cookie}")

    # ==========================================================
    # 1. 直接请求 JSON 列表接口
    # ==========================================================
    def start_requests(self):
        yield scrapy.Request(
            url=self.list_api,
            cookies=self.base_cookie,
            callback=self.parse_json,
            dont_filter=True
        )

    # ==========================================================
    # 2. 解析 JSON 列表，分发详情页请求
    # ==========================================================
    def parse_json(self, response):
        data = json.loads(response.text)

        BASE = "https://fgw.hubei.gov.cn/"

        for item in data["data"]:
            detail_url = urljoin(BASE, item["URL"])

            meta = {
                "title": item["FILENAME"],
                "publish_time": item["DOCRELTIME"]
            }

            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail,
                cookies=self.base_cookie,
                meta=meta,
                dont_filter=True
            )

    # ==========================================================
    # 3. 详情页解析（UTF-8 强制解码 + 多模板 XPATH）
    # ==========================================================
    def parse_detail(self, response):
        meta = response.meta

        # Scrapy 的 response.body 是 bytes → 强制 decode，避免乱码
        html = response.body.decode("utf-8", errors="ignore")
        tree = etree.HTML(html)

        # 常见正文结构
        xpaths = [
            '//div[@class="article"]//text()',
            '//div[@class="article-content"]//text()',
            '//div[@class="TRS_Editor"]//text()',
            '//div[@class="zfxxgk_zw_content"]//text()',
        ]

        content = ""
        for xp in xpaths:
            part = tree.xpath(xp)
            if part:
                content = "".join([x.strip() for x in part if x.strip()])
                break

        images = tree.xpath('//div[@class="article"]//img/@src')
        images = [response.urljoin(x) for x in images]

        attachment_urls = tree.xpath(
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".xlsx")]'
        )
        attachments = get_attachment(attachment_urls, response.url, self._from)

        yield DataItem({
            "_id": md5(response.url.encode("utf-8")).hexdigest(),
            "url": response.url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "spider_from": self._from,
            "label": "政策规范性文件",
            "title": meta["title"],
            "author": "",
            "publish_time": meta["publish_time"],
            "body_html": html,
            "content": content,
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category
        })
