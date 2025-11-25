import time
import subprocess
from curl_cffi import requests
from lxml import etree
from loguru import logger

# ======================
# 初始化会话与头部
# ======================
session = requests.Session()
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://ticket.sxhm.com/quickticket/index.html",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090a1b) XWEB/14185 Flue",
}


# ======================
# 提取 cookie + JS 文件
# ======================
def get_cookies(response):
    tree = etree.HTML(response.text)
    contentStr = tree.xpath('//meta[2]/@content')[0]
    scriptStr = tree.xpath('//script[1]/text()')[0]
    js_code = session.get(url='https://ticket.sxhm.com' + tree.xpath('//script[2]/@src')[0], headers=headers).text

    with open('./content.js', 'w', encoding='utf-8') as f:
        f.write(f'content="{contentStr}";')
    with open('./ts.js', 'w', encoding='utf-8') as f:
        f.write(scriptStr)
    with open('./cd.js', 'w', encoding='utf-8') as f:
        f.write(js_code)

    logger.info('✅ content/ts/js 保存成功！')

    try:
        return response.cookies.get_dict()
    except Exception:
        return {}


# ======================
# 第一次访问
# ======================
url = "https://ticket.sxhm.com/quickticket/index.html"
response = session.get(url, headers=headers)
logger.info(f'第一次访问状态：{response.status_code}')

# 提取 cookies
cookies = get_cookies(response)

# ======================
# 手动补入你的 cookie 值
# ======================
# （这部分就是你第一个脚本里定义的）
manual_cookies = {
    "yrLQQyDMDE1ZO": "60Ywmfm8mn_yaXxbeOUWdZjJIdigqhp3kFLepq2ZFBQPFHbdXiSTpAQOegZKL0g5jsXv9WsI0bMk5jYEnQji1yOtQZ9NfIeYTWZTqMYQ4Q1za",
    "yrLQQyDMDE1ZP": "0LFR8WgAIzflZEBGnIeJOOu2DjEzD9A1Twk8xrZ4wGOERknxnqDXwWzeY4mW1_cK9HVNOlXJzhyrEmC1d0vWQvdVqGs2zDXLIrf20nashKcZvojUMN3K6fvFkZNdBXohpNwfny0Tfxo.QRQAWaTlataVD0KdhkZ3vWmtcaGIQPCsNbUcykO_BEly1u_XNr8ADhwbnfFYBR8PT.QLiJxxdpf._2wOmzSiBUooctVipU48KLmw6JFBnW23XoaaZe9Te3s9EzIujLd67qpb93unZYlwoRMONs6rDKakAascYq6Zb.EME3HIxytrSZbI6Jqv3j4f76cBuLERvklXiXeFIge8ZRUz78c0e31M6.nyvI6tNWeOC6sl32i9SK..Z2I5T6i7YLz5tVK1XMkcyAWEfPxn9bWZafTpkbLrLC1gfQr5lnmSx._hl7i0n8dpchJ6bQwEvEHuVkqM.bc_MWdEeCA"
}

# 合并 cookie
cookies.update(manual_cookies)

# ======================
# 运行 env.js 生成动态 cookie（如果有）
# ======================
result = subprocess.run(['node', 'env.js'], capture_output=True, text=True)
ck_value = result.stdout.strip()
if ck_value:
    cookies["yrLQQyDMDE1ZP"] = ck_value
    logger.info("✅ 使用 Node 生成的 cookie 覆盖成功")

logger.info(f"当前 cookies：{cookies}")

# ======================
# 第二次访问
# ======================
res = session.get(url, headers=headers, cookies=cookies)
logger.info(f'第二次访问状态：{res.status_code}')
print(res.text[:500])  # 打印前 500 字符预览 HTML 内容
