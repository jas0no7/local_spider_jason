import requests
from lxml import etree
import time

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://jyt.zj.gov.cn/col/col1229266336/index.html",
    "X-Requested-With": "XMLHttpRequest",
}

url = "https://jyt.zj.gov.cn/module/jpage/dataproxy.jsp"

params = {
    "startrecord": "1",
    "endrecord": "15",
    "perpage": "15"
}

data = {
    "col": "1",
    "appid": "1",
    "webid": "3099",
    "path": "/",
    "columnid": "1229266336",
    "sourceContentType": "1",
    "unitid": "6258453",
    "webname": "浙江省教育厅",
    "permissiontype": "0"
}

resp = requests.post(url, headers=headers, params=params, data=data, timeout=15)
resp.encoding = "utf-8"

xml_root = etree.XML(resp.text.encode("utf-8"))

records = xml_root.xpath("//record")

results = []

for idx, rec in enumerate(records, 1):
    html_str = rec.text
    if not html_str:
        continue

    html = etree.HTML(html_str)

    title = html.xpath("//a/@title")
    detail_url = html.xpath("//a/@href")
    pub_date = html.xpath("//span/text()")

    title = title[0].strip() if title else ""
    detail_url = detail_url[0].strip() if detail_url else ""
    publish_date = pub_date[0].strip() if pub_date else ""

    print(f"\n[{idx}] 进入详情页: {title}")
    print(detail_url)

    if not detail_url:
        continue

    try:
        detail_resp = requests.get(detail_url, headers=headers, timeout=15)
        detail_resp.encoding = "utf-8"
    except Exception as e:
        print("详情页请求失败:", e)
        continue

    detail_tree = etree.HTML(detail_resp.text)

    main_nodes = detail_tree.xpath('//div[@class="main"]')

    if not main_nodes:
        print("未找到 div.main")
        continue

    main_node = main_nodes[0]

    body_html = etree.tostring(
        main_node,
        encoding="unicode",
        method="html"
    )

    content_text = "".join(
        main_node.xpath('.//text()')
    ).strip()

    item = {
        "label":"公告公示",
        "title": title,
        "detail_url": detail_url,
        "publish_date": publish_date,
        "body_html": body_html,
        "content": content_text,
    }
    print(item)

    results.append(item)

    time.sleep(0.5)
