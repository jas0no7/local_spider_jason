#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import json
import time
import subprocess
from hashlib import md5
from urllib.parse import urljoin
from datetime import datetime

from curl_cffi import requests
from lxml import etree
from loguru import logger

# ==============================================================
# 基础配置
# ==============================================================
session = requests.Session()
base_url = "https://www.gansu.gov.cn"
first_url = "https://www.gansu.gov.cn/common/search/77b4ad617c73434dba6491e1de8a615a"

headers = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://www.gansu.gov.cn/gsszf/gsyw/common_noleftlist.shtml",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    ),
}

output_dir = "./output_gansu"
os.makedirs(output_dir, exist_ok=True)


# ==============================================================
# 工具函数
# ==============================================================
def get_now_date():
    """当前时间字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_cookies(response):
    """生成瑞数 cookie 的文件"""
    tree = etree.HTML(response.text)
    content_str = tree.xpath('//meta[2]/@content')[0]
    script_str = tree.xpath('//script[1]/text()')[0]
    js_code = session.get(url=base_url + tree.xpath('//script[2]/@src')[0], headers=headers).text

    with open("./content.js", "w", encoding="utf-8") as f:
        f.write(f'content="{content_str}";')
    with open("./ts.js", "w", encoding="utf-8") as f:
        f.write(script_str)
    with open("./cd.js", "w", encoding="utf-8") as f:
        f.write(js_code)
    logger.info("content/ts/js 保存成功")

    cookies = {}
    try:
        cookies = response.cookies.get_dict()
    except Exception:
        pass
    return cookies


def get_html(url, cookies):
    """获取网页 HTML"""
    try:
        res = session.get(url, headers=headers, cookies=cookies, timeout=10)
        if res.status_code == 200:
            return res.text
        else:
            logger.warning(f"请求失败 {res.status_code} -> {url}")
            return None
    except Exception as e:
        logger.error(f"请求异常: {e}")
        return None


def get_attachment(attachment_nodes, base_url):
    """提取附件链接"""
    att_list = []
    for a in attachment_nodes:
        href = a.get("href")
        if href:
            att_list.append(urljoin(base_url, href))
    return att_list


def parse_detail(url, cookies):
    """解析详情页"""
    html = get_html(url, cookies)
    if not html:
        return None
    tree = etree.HTML(html)

    body_elem = tree.xpath('//div[@class="main"]')
    body_html = "".join([etree.tostring(e, encoding="unicode", method="html") for e in body_elem])
    content = "".join(tree.xpath('//div[@class="main"]//text()')).strip()
    author = "".join(re.findall(r"信息来源[:：]\s*(.*?)<", html, re.DOTALL)).strip()
    images = [urljoin(url, i) for i in tree.xpath('//div[@class="main"]//img/@src')]
    attachment_nodes = tree.xpath(
        '//a[contains(@href, ".pdf") or contains(@href, ".doc") or '
        'contains(@href, ".docx") or contains(@href, ".xls") or '
        'contains(@href, ".xlsx") or contains(@href, ".zip") or '
        'contains(@href, ".rar")]'
    )
    attachments = get_attachment(attachment_nodes, url)

    return {
        "author": author,
        "body_html": body_html,
        "content": content,
        "images": images,
        "attachment": attachments,
    }


def save_json(data):
    """每篇新闻保存为单独 JSON 文件"""
    file_path = os.path.join(output_dir, f"{data['_id']}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ 已保存: {file_path}")


def parse_page(html, cookies):
    """解析列表页并爬取详情"""
    tree = etree.HTML(html)
    titles = [t.strip() for t in tree.xpath('//div[@class="title"]/a/text()')]
    detail_urls = [urljoin(base_url, u) for u in tree.xpath('//div[@class="title"]/a/@href')]
    publish_times = [t.strip() for t in tree.xpath('//div[@class="date"]/text()')]

    logger.info(f"共抓取 {len(titles)} 条新闻")

    for title, detail_url, pub_time in zip(titles, detail_urls, publish_times):
        logger.info(f"正在抓取: {title} ({pub_time})")

        detail_data = parse_detail(detail_url, cookies)
        if not detail_data:
            continue

        data = {
            "_id": md5(f"GET{detail_url}".encode("utf-8")).hexdigest(),
            "url": detail_url,
            "spider_from": "甘肃省人民政府",
            "label": "甘肃要闻",
            "title": title,
            "author": detail_data["author"],
            "publish_time": pub_time,
            "body_html": detail_data["body_html"],
            "content": detail_data["content"],
            "images": detail_data["images"],
            "attachment": detail_data["attachment"],
            "spider_date": get_now_date(),
        }

        save_json(data)
        time.sleep(1.2)

    next_link = tree.xpath('//a[@class="next"]/@href')
    return urljoin(base_url, next_link[0]) if next_link else None


# ==============================================================
# 主程序入口
# ==============================================================
if __name__ == "__main__":
    logger.info("开始初始化瑞数 Cookie")
    response = session.get(first_url, headers=headers)
    cookies = get_cookies(response)

    result = subprocess.run(["node", "env.js"], capture_output=True, text=True)
    cookies["4hP44ZykCTt5P"] = result.stdout.strip()

    logger.info("开始抓取新闻列表与详情")
    page_url = first_url
    for page in range(1, 729):
        html = get_html(page_url, cookies)
        if not html:
            break
        logger.info(f"=== 第 {page} 页 ===")
        next_url = parse_page(html, cookies)
        if not next_url:
            break
        page_url = next_url
        time.sleep(3)

    logger.success(f"全部完成，结果已保存在: {os.path.abspath(output_dir)}")
