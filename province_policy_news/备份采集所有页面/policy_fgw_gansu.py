#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
from hashlib import md5

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
# 1. 全局请求配置（瑞数 + requests）
# ==========================

SESSION = requests.Session()

HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://www.gansu.gov.cn/gsszf/gsyw/common_noleftlist.shtml",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}

COOKIES = {}   # 全局 cookie 缓存


def build_cookies_from_412(response):
    """
    从 412 返回的页面中提取 content/meta + script，写入 content.js / ts.js / cd.js，
    然后调用 node env.js 生成 4hP44ZykCTt5P，最终返回完整 cookies。
    """
    tree = etree.HTML(response.text)
    if tree is None:
        raise RuntimeError("无法解析 412 页面 HTML")

    content_str_list = tree.xpath('//meta[2]/@content')
    script_str_list = tree.xpath('//script[1]/text()')
    js_src_list = tree.xpath('//script[2]/@src')

    if not (content_str_list and script_str_list and js_src_list):
        raise RuntimeError("412 页面结构变化，无法找到 meta/script 节点")

    content_str = content_str_list[0]
    script_str = script_str_list[0]
    js_url = "https://fzgg.gansu.gov.cn" + js_src_list[0]

    js_code = SESSION.get(js_url, headers=HEADERS, verify=False).text

    with open("content.js", "w", encoding="utf-8") as f:
        f.write(f'content="{content_str}";')
    with open("ts.js", "w", encoding="utf-8") as f:
        f.write(script_str)
    with open("cd.js", "w", encoding="utf-8") as f:
        f.write(js_code)

    logger.info("content.js / ts.js / cd.js 写入成功")

    # 先拿基础 cookie
    try:
        base_cookies = response.cookies.get_dict()
    except AttributeError:
        base_cookies = {}
        for c in str(response.cookies).split(";"):
            if "=" in c:
                k, v = c.strip().split("=", 1)
                base_cookies[k] = v

    # 调用 node env.js 生成 4hP44ZykCTt5P
    result = subprocess.run(["node", "env.js"], capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(result.stderr)
        raise RuntimeError("env.js 执行失败")

    dynamic_cookie = result.stdout.strip()
    if not dynamic_cookie:
        raise RuntimeError("env.js 未返回 4hP44ZykCTt5P 值")

    base_cookies["4hP44ZykCTt5P"] = dynamic_cookie
    logger.info(f"生成 4hP44ZykCTt5P: {dynamic_cookie[:16]}...")

    return base_cookies


def fetch_html_with_cookie(url, params=None):
    """
    统一入口：
    - 第一次访问会 412 -> 构建 cookie
    - 之后访问复用 COOKIES
    - 如果再次 412，自动刷新 cookie 一次
    """
    global COOKIES

    if not COOKIES:
        logger.info(f"[初始化 cookie] 访问 {url}")
        r1 = SESSION.get(url, headers=HEADERS, verify=False)
        logger.info(f"第一次访问状态码: {r1.status_code}")
        if r1.status_code == 412:
            COOKIES = build_cookies_from_412(r1)
        else:
            COOKIES = r1.cookies.get_dict()

    r2 = SESSION.get(url, headers=HEADERS, cookies=COOKIES, params=params, verify=False)
    logger.info(f"访问 {url} 状态码: {r2.status_code}")

    # 如果 cookie 过期，再刷新一次
    if r2.status_code == 412:
        logger.warning("cookie 失效，重新生成中...")
        r1 = SESSION.get(url, headers=HEADERS, verify=False)
        COOKIES = build_cookies_from_412(r1)
        r2 = SESSION.get(url, headers=HEADERS, cookies=COOKIES, params=params, verify=False)
        logger.info(f"重试访问 {url} 状态码: {r2.status_code}")

    r2.encoding = r2.apparent_encoding
    return r2.text


# ==========================
# 2. Scrapy Spider
# ==========================

class DataSpider(CrawlSpider):
    name = "policy_fgw_gansu"
    allowed_domains = ["fzgg.gansu.gov.cn"]

    _from = "甘肃发改委"
    category = "政策"

    infoes = [
        {
            "url": "https://fzgg.gansu.gov.cn/common/search/b16135ef84e445dea2bfd0343dd96c4c",
            "label": "政策文件",
            "total": 2020,
        },
        {
            "url": "https://fzgg.gansu.gov.cn/common/search/0c4a5c08111c4b66b8ebfec8e563de37",
            "label": "政府定价",
            "total": 400,
        },
        {
            "url": "https://fzgg.gansu.gov.cn/common/search/906fa06cf3f84ed68e030cf7cfdf7234",
            "label": "政策解读",
            "total": 753,
        },
    ]

    def start_requests(self):
        """
        不用 Scrapy 自己发请求，而是用 fetch_html_with_cookie 拿到 HTML，
        然后构造 HtmlResponse 喂给 parse_list，这样可以完全复用你瑞数的 cookie 逻辑。
        """
        for info in self.infoes:
            url = info["url"]
            label = info["label"]
            total = info["total"]
            page_size = 20
            page_count = (total + page_size - 1) // page_size

            for page in range(1, page_count + 1):
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

                fake_request = scrapy.Request(url=url, meta={"label": label, "page": page})
                response = HtmlResponse(
                    url=url,
                    body=html,
                    encoding="utf-8",
                    request=fake_request,
                )
                yield from self.parse_list(response)

    def parse_list(self, response):
        """
        解析列表页：提取 title / url / date，
        跳过站外链接（如微信）。
        """
        label = response.meta["label"]
        page = response.meta["page"]

        lis = response.xpath('//ul[@id="body"]/li')
        logger.info(f"[{label}] 第 {page} 页，解析到 {len(lis)} 条")

        for li in lis:
            title = li.xpath('./div[@class="title"]/a/text()').get("")
            title = title.strip()

            href = li.xpath('./div[@class="title"]/a/@href').get("")
            href = href.strip()

            if not href:
                continue

            # 站外链接过滤（微信 / 微博 / 其他域名）
            if href.startswith("http://") or href.startswith("https://"):
                if not href.startswith("https://fzgg.gansu.gov.cn"):
                    logger.info(f"跳过站外链接: {href}")
                    continue
                detail_url = href
            else:
                detail_url = "https://fzgg.gansu.gov.cn" + href

            date = li.xpath('./div[@class="date"]/text()').get("")
            date = date.strip()

            # 直接用 requests + cookie 获取详情页 HTML（不走 Scrapy Downloader）
            detail_html = fetch_html_with_cookie(detail_url)
            fake_request = scrapy.Request(
                url=detail_url,
                meta={
                    "label": label,
                    "title": title,
                    "publish_time": date,
                },
            )
            detail_response = HtmlResponse(
                url=detail_url,
                body=detail_html,
                encoding="utf-8",
                request=fake_request,
            )
            yield from self.parse_detail(detail_response)

    def parse_detail(self, response):
        """
        详情页解析：
        - 正文：//div[@class="main mt8"] | //div[@class="article"] | //div[@id="zoom"] | //div[@class="mainbox clearfix"]
        - 附件：各种后缀
        - 图片：正文里的 img
        """
        label = response.meta["label"]
        title = response.meta["title"]
        publish_time = response.meta["publish_time"]
        url = response.url

        # 正文 XPath 合并
        body_xpath = (
            '('
            '//div[@class="main mt8"]'
            ' | //div[@class="article"]'
            ' | //div[@id="zoom"]'
            ' | //div[@class="mainbox clearfix"]'
            ')'
        )

        # HTML 正文
        body_html = "".join(response.xpath(body_xpath).getall())

        # 纯文本
        content = "".join(response.xpath(f"{body_xpath}//text()").getall()).strip()

        # 图片（不会再出现 HTML 被当成 src 的问题）
        image_srcs = response.xpath(f"{body_xpath}//img/@src").getall()
        images = [response.urljoin(src) for src in image_srcs]

        # 附件
        attachment_nodes = response.xpath(
            '//p[contains(@class, "insertfileTag")]//a | '
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or '
            'contains(@href, ".xls") or contains(@href, ".xlsx") or contains(@href, ".wps") or '
            'contains(@href, ".zip") or contains(@href, ".rar")]'
        )
        attachments = get_attachment(attachment_nodes, url, self._from)

        # 图片
        image_srcs = response.xpath(f"{body_xpath}//img/@src").getall()
        images = [response.urljoin(src) for src in image_srcs]

        item = DataItem()
        item.update({
            "_id": md5(f"{url}{title}".encode("utf-8")).hexdigest(),
            "url": url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "spider_from": self._from,
            "label": label,
            "title": title,
            "author": "",                       # 页面上如果有需要你再加 XPath
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content,
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category,
        })

        yield item
