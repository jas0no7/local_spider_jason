# --coding:utf-8--
import re
import requests
from lxml import etree, html
from time import sleep

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

url = "https://gxt.jiangsu.gov.cn/col/col80181/index.html"
data_list = []

for page in range(1, 9):  # 可根据需要调节页数
    print(f"正在抓取第 {page} 页...")
    params = {"uid": "403740", "pageNum": page}

    resp = requests.get(url, headers=headers, params=params, timeout=10)
    resp.encoding = "utf-8"

    tree = etree.HTML(resp.text)
    xml_text = tree.xpath('string(//script[@type="text/xml"])')
    if not xml_text:
        print("❌ 没找到 XML 数据段，跳过。")
        continue

    # 提取 CDATA 段落
    records = re.findall(r"<record><!\[CDATA\[(.*?)\]\]></record>", xml_text, re.S)
    for rec in records:
        frag = html.fromstring(rec.strip())
        title = frag.xpath("string(.//a/@title)")
        href = frag.xpath("string(.//a/@href)")
        publish_time = frag.xpath("string(.//b)")
        full_url = f"https://gxt.jiangsu.gov.cn{href}" if href.startswith("/") else href

        data_list.append({
            "label": "统计信息",
            "title": title.strip(),
            "detail_url": full_url.strip(),
            "publish_time": publish_time.strip()
        })

# ===============================
# 进入每个详情页，提取正文
# ===============================
for i, item in enumerate(data_list, 1):
    try:
        print(f"抓取正文 [{i}/{len(data_list)}]: {item['title']}")
        detail_resp = requests.get(item["detail_url"], headers=headers, timeout=10)
        detail_resp.encoding = "utf-8"
        detail_tree = etree.HTML(detail_resp.text)
        # 提取正文（包含文字与换行）
        content_list = detail_tree.xpath('//div[@id="Zoom"]//text()')
        content = "\n".join([c.strip() for c in content_list if c.strip()])
        item["content"] = content
        sleep(0.8)  # 加延时防止请求过快
    except Exception as e:
        print(f"❌ 抓取失败：{item['detail_url']}，错误：{e}")
        item["content"] = ""

# ===============================
# 打印示例结果
# ===============================
for item in data_list[:3]:
    print("=" * 60)
    print(item["title"], item["publish_time"])
    print(item["detail_url"])
    print(item["content"][:200], "...")
