import time
import execjs
from curl_cffi import requests
from loguru import logger
from lxml import etree
import subprocess

cookies = {}
session = requests.Session()


def get_cookies(response):
    tree = etree.HTML(response.text)
    contentStr = tree.xpath('//meta[2]/@content')[0]
    content = f'content="{contentStr}";'
    scriptStr = tree.xpath('//script[1]/text()')[0]
    js_code = session.get(url='https://fgw.hubei.gov.cn' + tree.xpath('//script[2]/@src')[0], headers=headers).text

    with open('./content.js', 'w', encoding='utf-8') as f:
        f.write(content)
    with open('./ts.js', 'w', encoding='utf-8') as f:
        f.write(scriptStr)
    with open('./cd.js', 'w', encoding='utf-8') as f:
        f.write(js_code)

    logger.info('content/ts/js保存成功！')

    # ✅ 通用兼容写法
    try:
        # 标准 requests
        cookies = response.cookies.get_dict()
    except AttributeError:
        try:
            # 一些 curl_cffi 版本支持 items()
            cookies = dict(response.cookies.items())
        except Exception:
            # 最保险的方案：直接转字符串再解析
            cookies = {}
            for c in str(response.cookies).split(";"):
                if "=" in c:
                    k, v = c.strip().split("=", 1)
                    cookies[k] = v

    return cookies


headers = {
    "Accept": "text/html, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://fgw.hubei.gov.cn/gzjj/dtyw/fgyw/index.shtml",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
url = "https://fgw.hubei.gov.cn/gzjj/dtyw/fgyw/index.shtml"

response = session.get(url, headers=headers)
logger.info(f'第一次访问状态：{response.status_code}')

cookies = get_cookies(response)

result = subprocess.run(['node', 'env.js'], capture_output=True, text=True)

# cookies['4hP44ZykCTt5P'] = execjs.compile(open('./env.js', 'r', encoding='utf-8').read()).call('get_ck')
cookies['924omrTVcFchP'] = result.stdout.strip()
print(cookies)
res = session.get(url, headers=headers, cookies=cookies)
logger.info(f'第二次访问状态：{res.status_code}')
print(res.text)
