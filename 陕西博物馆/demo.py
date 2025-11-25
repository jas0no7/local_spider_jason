import time
import subprocess
from curl_cffi import requests
from loguru import logger
from lxml import etree

session = requests.Session()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090a1b)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
}

url = "https://ticket.sxhm.com/quickticket/index.html"


def parse_rs6_scripts(html):
    tree = etree.HTML(html)

    metas = tree.xpath('//meta[@id]/@content')
    if not metas:
        raise Exception("RS6 meta 未找到")
    contentStr = metas[0]

    # 找 inline 的 TS
    scripts = tree.xpath('//script[@r="m"]/text()')
    if not scripts:
        raise Exception("RS6 ts 未找到")
    ts_js = scripts[0]

    # 找 cd.js
    cd_src = tree.xpath('//script[@r="m"]/@src')
    if not cd_src:
        raise Exception("RS6 cd.js 未找到")
    cd_js = session.get("https://ticket.sxhm.com" + cd_src[0], headers=headers).text

    with open("content.js", "w", encoding="utf-8") as f:
        f.write(f'content="{contentStr}";')
    with open("ts.js", "w", encoding="utf-8") as f:
        f.write(ts_js)
    with open("cd.js", "w", encoding="utf-8") as f:
        f.write(cd_js)

    logger.info("RS6 三件套保存完毕！")


def extract_cookie_from_envjs_output(output):
    for line in output.splitlines():
        if "yrLQQyDMDE1ZP" in line:
            kv = line.split("yrLQQyDMDE1ZP=")[1]
            return kv.split(";")[0]

    raise Exception("env.js 中未找到 yrLQQyDMDE1ZP")


# 第一步：访问页面，拿到 JS
resp = session.get(url, headers=headers)
parse_rs6_scripts(resp.text)

# 第二步：执行 env.js 生成 Cookie
result = subprocess.run(["node", "env.js"], text=True, capture_output=True)
cookie_value = extract_cookie_from_envjs_output(result.stdout)

session.cookies.set("yrLQQyDMDE1ZP", cookie_value, domain="ticket.sxhm.com")

logger.info("Cookie 写入成功！")

# 第三步：真正访问页面
res2 = session.get(url, headers=headers)
print("第二次访问状态：", res2.status_code)
print(res2.text)
