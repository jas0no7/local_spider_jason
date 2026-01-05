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
# 翻页
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

    for li in items:
        title = li.xpath('string(.//h3/a)').strip()
        href = li.xpath('.//h3/a/@href')
        source = li.xpath('.//span[@class="all-time-y2"]/text()')

        source_text = source[0].strip() if source else ""

        # 只保留 浙江发改
        if source_text != "浙江发改":
            continue

        detail_url = "https://weixin.sogou.com" + href[0] if href else ""

        print("标题:", title)
        print("详情页:", detail_url)

        # =========================
        # 进入详情页
        # =========================
        try:
            detail_resp = requests.get(
                detail_url,
                headers=headers,
                cookies=cookies,
                timeout=10
            )
            html = etree.HTML(detail_resp.text)

            # 正文节点
            content_nodes = html.xpath('//*[@id="js_content"]')
            if not content_nodes:
                raise RuntimeError("未获取到 js_content，可能 key/exportkey 已失效")

            content = content_nodes[0]

            # =====================================================
            # 4. 提取发布时间
            # =====================================================

            publish_time_nodes = html.xpath('//*[@id="publish_time"]/text()')
            publish_time = publish_time_nodes[0].strip() if publish_time_nodes else ""

            # =====================================================
            # 5. 提取正文图片
            # =====================================================

            img_urls = content.xpath('.//img/@data-src')

            # =====================================================
            # 6. 输出结果
            # =====================================================

            print("发布时间:", publish_time)
            print("图片数量:", len(img_urls))

            for i, u in enumerate(img_urls):
                print(i, u)
        except Exception as e:
            print("详情页解析失败:", e)

        print("-" * 60)

        # 防封
        time.sleep(2)

    time.sleep(2)
