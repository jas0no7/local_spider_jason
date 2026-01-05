import copy
import re
import json
import subprocess
import os
from hashlib import md5
from urllib.parse import urljoin

import scrapy
import requests
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment

from loguru import logger
from lxml import etree

settings = get_project_settings()


# ==========================================================
#  工具：保证临时目录存在
# ==========================================================
TMP_DIR = "."
os.makedirs(TMP_DIR, exist_ok=True)


# ==========================================================
#  动态 Cookie 生成（湖北发改委专用）
# ==========================================================
def get_valid_cookies(start_url):
    logger.info("开始执行湖北发改委 Cookie 动态生成流程...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://fgw.hubei.gov.cn/fbjd/zc/gfwj/",
    }

    # 使用 requests 获取首页（替代 curl_cffi）
    resp = requests.get(start_url, headers=headers, timeout=10)
    tree = etree.HTML(resp.text)

    contentStr = tree.xpath('//meta[2]/@content')[0]
    scriptStr = tree.xpath('//script[1]/text()')[0]
    js_url = tree.xpath('//script[2]/@src')[0]

    # 下载 JS 文件
    js_full = requests.get(urljoin("https://fgw.hubei.gov.cn", js_url)).text

    # 写入临时文件
    open(f"{TMP_DIR}/content.js", "w", encoding="utf-8").write(f'content="{contentStr}";')
    open(f"{TMP_DIR}/ts.js", "w", encoding="utf-8").write(scriptStr)
    open(f"{TMP_DIR}/cd.js", "w", encoding="utf-8").write(js_full)

    logger.info("已生成 content.js、ts.js、cd.js")

    # env.js 会 require 前 3 个文件
    env_js_path = f"{TMP_DIR}/env.js"
    open(env_js_path, "w", encoding="utf-8").write("""
require('./content.js');
require('./ts.js');
require('./cd.js');
console.log(getEncryptedCookie(content));
""")

    # 调用 node 生成 cookie
    result = subprocess.run(["node", env_js_path], capture_output=True, text=True)
    dynamic_cookie = result.stdout.strip()

    base_cookies = dict(resp.cookies)
    base_cookies["924omrTVcFchP"] = dynamic_cookie

    logger.info(f"动态 Cookie 生成成功：{base_cookies}")
    return base_cookies


# ==========================================================
#  Scrapy Spider
# ==========================================================
class DataSpider(CrawlSpider):
    name = 'policy_fgw2_hubei'
    allowed_domains = ['fgw.hubei.gov.cn']
    _from = '湖北发改委'
    category = "政策"

    list_api = "https://fgw.hubei.gov.cn/fbjd/zc/gfwj/wj/gfxwj.json"
    cookie_home = "https://fgw.hubei.gov.cn/fbjd/zc/gfwj/"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("正在初始化湖北发改委 Cookie ...")
        self.base_cookie = get_valid_cookies(self.cookie_home)

    # ===================== 1. JSON 列表接口 ====================
    def start_requests(self):
        yield scrapy.Request(
            url=self.list_api,
            cookies=self.base_cookie,
            callback=self.parse_json,
            dont_filter=True
        )

    # ===================== 2. 解析列表 JSON ====================
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
                cookies=self.base_cookie,
                callback=self.parse_detail,
                meta=meta,
                dont_filter=True
            )

    # ===================== 3. 解析详情页 ====================
    def parse_detail(self, response):
        meta = response.meta
        html = response.text
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
            nodes = tree.xpath(xp)
            if nodes:
                content = "".join(x.strip() for x in nodes if x.strip())
                break

        images = [response.urljoin(i) for i in tree.xpath('//img/@src')]
        attachment_nodes = tree.xpath(
            '//a[contains(@href,".pdf") or contains(@href,".doc") or contains(@href,".xlsx")]'
        )
        attachments = get_attachment(attachment_nodes, response.url, self._from)

        yield DataItem({
            "_id": md5(response.url.encode()).hexdigest(),
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
