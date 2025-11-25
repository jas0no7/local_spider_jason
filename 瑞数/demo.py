#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
甘肃省政府网站瑞数防护绕过 + 翻页抓取示例
1️⃣ 第一次访问生成 JS 环境
2️⃣ 运行 Node 获取加密 cookie
3️⃣ 访问新闻列表页 (200)
4️⃣ 循环调用分页接口 /common/search/
"""

import time
import subprocess
from curl_cffi import requests
from loguru import logger
from lxml import etree

# ===============================
# 全局 Session 与 headers
# ===============================
session = requests.Session()

headers_html = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://www.gansu.gov.cn/gsszf/gsyw/common_noleftlist.shtml",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
}


# ===============================
# 1️⃣ 第一次访问，提取 cookie + 加密 JS
# ===============================
def get_cookies_and_js():
    url = "https://www.gansu.gov.cn/gsszf/gsyw/common_noleftlist.shtml"
    resp = session.get(url, headers=headers_html)
    logger.info(f"第一次访问状态：{resp.status_code}")

    tree = etree.HTML(resp.text)
    contentStr = tree.xpath('//meta[2]/@content')[0]
    content = f'content="{contentStr}";'
    scriptStr = tree.xpath('//script[1]/text()')[0]
    js_url = 'https://www.gansu.gov.cn' + tree.xpath('//script[2]/@src')[0]
    js_code = session.get(js_url, headers=headers_html).text

    # 写入本地 JS 文件
    with open('./content.js', 'w', encoding='utf-8') as f:
        f.write(content)
    with open('./ts.js', 'w', encoding='utf-8') as f:
        f.write(scriptStr)
    with open('./cd.js', 'w', encoding='utf-8') as f:
        f.write(js_code)
    logger.info("content.js / ts.js / cd.js 保存成功")

    # 提取 cookie
    try:
        cookies = resp.cookies.get_dict()
    except AttributeError:
        try:
            cookies = dict(resp.cookies.items())
        except Exception:
            cookies = {}
            for c in str(resp.cookies).split(";"):
                if "=" in c:
                    k, v = c.strip().split("=", 1)
                    cookies[k] = v
    return cookies


# ===============================
# 2️⃣ 生成瑞数加密 cookie
# ===============================
def get_rs_cookie():
    result = subprocess.run(['node', 'env.js'], capture_output=True, text=True)
    ck = result.stdout.strip()
    return ck


# ===============================
# 3️⃣ 第二次访问主页面（确认200）
# ===============================
def access_main_page(cookies):
    url = "https://www.gansu.gov.cn/gsszf/gsyw/common_noleftlist.shtml"
    res = session.get(url, headers=headers_html, cookies=cookies)
    logger.info(f"第二次访问状态：{res.status_code}")
    return res


# ===============================
# 4️⃣ 翻页接口抓取
# ===============================
def crawl_pages(cookies):
    base_url = "https://www.gansu.gov.cn/common/search/77b4ad617c73434dba6491e1de8a615a"
    headers_ajax = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Referer": "https://www.gansu.gov.cn/gsszf/gsyw/common_noleftlist.shtml",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    for page in range(1, 6):  # 翻5页
        sign = get_rs_cookie()  # 每页生成新的加密签名
        params = {"UAta9QfS": sign, "pageIndex": page}
        res = session.get(base_url, headers=headers_ajax, cookies=cookies, params=params)
        logger.info(f"第{page}页 状态：{res.status_code}")
        print(res.text[:400])  # 预览前400字符
        time.sleep(1)


# ===============================
# 主执行逻辑
# ===============================
if __name__ == "__main__":
    cookies = get_cookies_and_js()

    main_page = access_main_page(cookies)
    if main_page.status_code == 200:
        crawl_pages(cookies)
