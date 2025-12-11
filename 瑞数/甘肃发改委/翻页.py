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
    js_code = session.get(url='https://fzgg.gansu.gov.cn' + tree.xpath('//script[2]/@src')[0], headers=headers).text

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
#url = "https://fzgg.gansu.gov.cn/common/search/b16135ef84e445dea2bfd0343dd96c4c" #[政策文件] total = 101
#url = "https://fzgg.gansu.gov.cn/common/search/0c4a5c08111c4b66b8ebfec8e563de37" #[政府定价] total =20
url = "https://fzgg.gansu.gov.cn/common/search/906fa06cf3f84ed68e030cf7cfdf7234" #[政策解读] total = 38


response = session.get(url, headers=headers)
logger.info(f'第一次访问状态：{response.status_code}')

cookies = get_cookies(response)

result = subprocess.run(['node', 'env.js'], capture_output=True, text=True)

cookies['4hP44ZykCTt5P'] = result.stdout.strip()
total = 3
for page in range(2, total + 1):
    params = {
        "sort": "",
        "_isAgg": "false",
        "_isJson": "false",
        "_pageSize": "20",
        "_template": "index",
        "_channelName": "",
        "page": str(page)
    }
    res = session.get(url, headers=headers, cookies=cookies, params=params)
    logger.info(f'第二次访问状态：{res.status_code}')
    html = res.text
    tree = etree.HTML(html)

    items = tree.xpath('//ul[@id="body"]/li')

    for li in items:
        title = li.xpath('./div[@class="title"]/a/text()')
        title = title[0].strip() if title else ""

        url_path = li.xpath('./div[@class="title"]/a/@href')
        if not url_path:
            continue

        href = url_path[0].strip()

        # ================================
        # 站外链接过滤（跳过微信/微博等）
        # ================================
        if href.startswith("http://") or href.startswith("https://"):
            # 🔥 如果不是甘肃发改委的域名 → 跳过
            if not href.startswith("https://fzgg.gansu.gov.cn"):
                print(f"跳过站外链接: {href}")
                continue
            url_full = href
        else:
            url_full = "https://fzgg.gansu.gov.cn" + href

        date = li.xpath('./div[@class="date"]/text()')
        date = date[0].strip() if date else ""

        print("\n====== 进入详情页 ======")
        print(url_full)

        # ==========================
        # 访问详情页
        # ==========================
        detail_html = session.get(url_full, headers=headers, cookies=cookies).text
        detail_tree = etree.HTML(detail_html)

        # ==========================
        # 详情正文提取
        # ==========================
        body_xpath = '//div[@class="main mt8"] | //div[@class="article"] | //div[@id="zoom"] | //div[@class="mainbox clearfix"]'

        body_elements = detail_tree.xpath(body_xpath)

        body_html = ''.join([
            etree.tostring(elem, encoding='unicode', method='html')
            for elem in body_elements
        ])

        body_text_nodes = detail_tree.xpath(f'{body_xpath}//text()')
        body_text = ''.join([
            node if isinstance(node, str) else (node.text or "")
            for node in body_text_nodes
        ]).strip()

        print({
            "title": title,
            "detail_url": url_full,
            "date": date,
            "body_text": body_text,
            "body_html": body_html
        })





