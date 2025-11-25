import time
from hashlib import md5

import execjs
from curl_cffi import requests
from loguru import logger
from lxml import etree
import subprocess
from urllib.parse import urljoin



session = requests.Session()

headers = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://www.gansu.gov.cn/gsszf/gsyw/common_noleftlist.shtml",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}

base_url = "https://www.gansu.gov.cn"
first_url = "https://www.gansu.gov.cn/common/search/77b4ad617c73434dba6491e1de8a615a"


def get_cookies(response):
    """瑞数cookie生成部分"""
    tree = etree.HTML(response.text)
    contentStr = tree.xpath('//meta[2]/@content')[0]
    scriptStr = tree.xpath('//script[1]/text()')[0]
    js_code = session.get(url=base_url + tree.xpath('//script[2]/@src')[0], headers=headers).text

    with open('./content.js', 'w', encoding='utf-8') as f:
        f.write(f'content="{contentStr}";')
    with open('./ts.js', 'w', encoding='utf-8') as f:
        f.write(scriptStr)
    with open('./cd.js', 'w', encoding='utf-8') as f:
        f.write(js_code)

    logger.info('content/ts/js保存成功！')

    cookies = {}
    try:
        cookies = response.cookies.get_dict()
    except Exception:
        pass
    return cookies


def get_html(url, cookies):
    """发请求获取 HTML"""
    try:
        res = session.get(url, headers=headers, cookies=cookies, timeout=10)
        if res.status_code == 200:
            return res.text
        else:
            logger.error(f"请求失败 {res.status_code} -> {url}")
            return None
    except Exception as e:
        logger.error(f"请求异常: {e}")
        return None


def parse_detail(url, cookies):
    """进入详情页，解析正文"""
    html = get_html(url, cookies)
    if not html:
        return ""
    tree = etree.HTML(html)
    # 提取正文（可能有多个段落）
    content_list = tree.xpath('//div[@class="main"]//text()')
    content = "".join([c.strip() for c in content_list if c.strip()])
    return content


def parse_page(html, cookies):
    """解析文章列表并爬取详情"""
    tree = etree.HTML(html)
    titles = [t.strip() for t in tree.xpath('//div[@class="title"]/a/text()')]
    detail_urls = [urljoin(base_url, u) for u in tree.xpath('//div[@class="title"]/a/@href')]
    publish_times = [t.strip() for t in tree.xpath('//div[@class="date"]/text()')]

    logger.info(f"共抓取 {len(titles)} 条新闻")

    for title, detail_url, pub_time in zip(titles, detail_urls, publish_times):
        logger.info(f"正在抓取: {title} ({pub_time})")
        content = parse_detail(detail_url, cookies)
        data_list = {
            "_id": md5(f'{detail_url}-{content}'.encode('utf-8')).hexdigest(),
            ""
            "title": title,
            "url": detail_url,
            "publish_time": pub_time,
            "content": content,

        }
        print(data_list)
        time.sleep(1.5)

    # 提取下一页链接
    next_link = tree.xpath('//a[@class="next"]/@href')
    if next_link:
        next_url = urljoin(base_url, next_link[0])
        return next_url
    return None


if __name__ == "__main__":
    # 第一次访问，触发瑞数保护
    response = session.get(first_url, headers=headers)
    cookies = get_cookies(response)

    # 调用 node 脚本生成瑞数 cookie 值
    result = subprocess.run(['node', 'env.js'], capture_output=True, text=True)
    cookies['4hP44ZykCTt5P'] = result.stdout.strip()

    logger.info("开始爬取分页与详情内容")

    page_url = first_url
    for page in range(1, 3):  # 示例只抓前2页
        html = get_html(page_url, cookies)
        if not html:
            break
        print(f"\n=== 第 {page} 页 ===")
        next_url = parse_page(html, cookies)
        if not next_url:
            break
        time.sleep(3)
        page_url = next_url
