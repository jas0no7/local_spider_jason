import requests
import time
from lxml import etree

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Referer": "https://weixin.sogou.com/weixin",
}

cookies = {
    "SUID": "718CD4AB9654A20B0000000068622AB0",
    "SUV": "1751263921571511",
    "SNUID": "99C35667BABCFCBC09C351BABBEF214B",
}

url = "https://weixin.sogou.com/weixin"

base_params = {
    "type": "2",
    "s_from": "input",
    "query": "数说发改",
    "ie": "utf8",
    "_sug_": "n",
    "_sug_type_": ""
}

# =========================
# 翻页：第 1～10 页
# =========================
for page in range(1, 2):
    print(f"\n===== 正在抓取第 {page} 页 =====")

    params = base_params.copy()
    params["page"] = page

    resp = requests.get(
        url,
        headers=headers,
        cookies=cookies,
        params=params,
        timeout=10
    )

    resp.encoding = "utf-8"

    html = etree.HTML(resp.text)
    items = html.xpath('//ul[@class="news-list"]/li')

    # 如果这一页已经没有文章，直接停
    # if not items:
    #     print("本页无数据，结束翻页")
    #     break

    for li in items:
        title = li.xpath('string(.//h3/a)').strip()
        href = li.xpath('.//h3/a/@href')
        source = li.xpath('.//span[@class="all-time-y2"]/text()')

        source_text = source[0].strip() if source else ""

        # 只保留 浙江发改
        if source_text != "浙江发改":
            continue

        data = {
            "title": title,
            "url": "https://weixin.sogou.com" + href[0] if href else "",
            "source": source_text,
            "page": page
        }

        print(data)

    # =========================
    # 防封：每页休息 2~4 秒
    # =========================
    time.sleep(2)
