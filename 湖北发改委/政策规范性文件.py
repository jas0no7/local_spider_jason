import json
import subprocess
from lxml import etree
from urllib.parse import urljoin

import requests  # 正常 requests（必须保留）
from curl_cffi import requests as curl_requests  # 第一次访问绕过 JS
from loguru import logger

# -------------------------------------------------------
# 1) 第一次访问（curl_cffi 绕过 JS-Cookie 反爬）
# -------------------------------------------------------

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

start_url = "https://fgw.hubei.gov.cn/fbjd/zc/gfwj/"

logger.info("第一次访问，用 curl_cffi 绕过 JS 验证")
first_resp = curl_requests.get(start_url, headers=headers)
first_tree = etree.HTML(first_resp.text)

# ---- 解析网站生成 JS cookie 所需的三个文件 ----
contentStr = first_tree.xpath('//meta[2]/@content')[0]
scriptStr = first_tree.xpath('//script[1]/text()')[0]
js_url = first_tree.xpath('//script[2]/@src')[0]

open("content.js", "w", encoding="utf-8").write(f'content="{contentStr}";')
open("ts.js", "w", encoding="utf-8").write(scriptStr)
open("cd.js", "w", encoding="utf-8").write(
    curl_requests.get(urljoin("https://fgw.hubei.gov.cn", js_url)).text
)

logger.info("content/ts/js 保存成功")

# ---- 调用 node 运行 env.js 获取动态 cookie ----
result = subprocess.run(["node", "env.js"], capture_output=True, text=True)
dynamic_cookie = result.stdout.strip()

# ---- curl_cffi cookies 正确使用方式 ----
base_cookies = dict(first_resp.cookies)
base_cookies["924omrTVcFchP"] = dynamic_cookie

logger.info(f"第一次访问 cookies：{base_cookies}")

# -------------------------------------------------------
# 2) 第二次访问（requests 正常通过 JS 验证）
# -------------------------------------------------------

session = requests.Session()
session.headers.update(headers)

logger.info("第二次访问，正常请求验证页面")
home2 = session.get(start_url, cookies=base_cookies)
logger.info(f"状态码：{home2.status_code}")

# -------------------------------------------------------
# 3) 请求 JSON 列表接口
# -------------------------------------------------------

json_url = "https://fgw.hubei.gov.cn/fbjd/zc/gfwj/wj/gfxwj.json"
resp_json = session.get(json_url, cookies=base_cookies)
data = json.loads(resp_json.text)

all_data = []
BASE = "https://fgw.hubei.gov.cn/"


# -------------------------------------------------------
# 4) 抓取详情页内容（含 UTF-8 强制解码，解决乱码）
# -------------------------------------------------------

for item in data["data"]:
    detail_url_raw = item["URL"]
    detail_url = urljoin(BASE, detail_url_raw)

    print(f"进入详情页：{detail_url}")

    # 请求详情页
    resp_detail = session.get(detail_url, cookies=base_cookies)

    # ---- 修复乱码的关键代码（必须用 content）-----
    html = resp_detail.content.decode("utf-8", errors="ignore")

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

    data_item = {
        "detail_url": detail_url,
        "title": item["FILENAME"],
        "publish_time": item["DOCRELTIME"],
        "content": content
    }
    all_data.append(data_item)

    print(data_item)


