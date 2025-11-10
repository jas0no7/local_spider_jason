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
    js_code = session.get(url='http://www.sgcc.com.cn' + tree.xpath('//script[2]/@src')[0], headers=headers).text
    with open('./content.js', 'w', encoding='utf-8') as f:
        f.write(content)

    with open('./ts.js', 'w', encoding='utf-8') as f:
        f.write(scriptStr)

    with open('./cd.js', 'w', encoding='utf-8') as f:
        f.write(js_code)
    logger.info('content/ts/js保存成功！')

    cookies = response.cookies.get_dict()
    return cookies

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "http://www.sgcc.com.cn/html/sgcc_main/gb/xwzx/yw/index.shtml",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
}
url = "http://www.sgcc.com.cn/html/sgcc_main/gb/xwzx/yxfc/index.shtml"
response = session.get(url, headers=headers)
logger.info(f'第一次访问状态：{response.status_code}')

cookies = get_cookies(response)

result = subprocess.run(['node', 'env.js'], capture_output=True, text=True)

# cookies['4hP44ZykCTt5P'] = execjs.compile(open('./env.js', 'r', encoding='utf-8').read()).call('get_ck')
cookies['PW9ydXnjjO8XT'] = result.stdout.strip()
print(cookies)
res = session.get(url, headers=headers,cookies=cookies)
logger.info(f'第二次访问状态：{res.status_code}')
print(res.text[0:10000])