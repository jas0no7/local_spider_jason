import requests
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from time import sleep

base_url = "https://gxt.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp"

headers = {
    "Accept": "application/xml, text/xml, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://gxt.jiangsu.gov.cn",
    "Pragma": "no-cache",
    "Referer": "https://gxt.jiangsu.gov.cn/col/col6197/index.html?uid=403981&pageNum=1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}

cookies = {
    "JSESSIONID": "E27B4554CCF4188AE07AB8FD97120AA3",
    "__jsluid_s": "97aa8e8d8c4555dd01573c6b0f456805",
}

payload_template = {
    "col": 1,
    "appid": 1,
    "webid": 23,
    "path": "/",
    "columnid": 6197,
    "sourceContentType": 1,
    "unitid": 403981,
    "webname": "江苏省工业和信息化厅",
    "permissiontype": 0,
}

perpage = 12
total_pages = 2
extracted_data = []

for page in range(1, total_pages + 1):
    startrecord = (page - 1) * perpage + 1
    endrecord = page * perpage

    params = {
        "startrecord": startrecord,
        "endrecord": endrecord,
        "perpage": perpage,
    }

    url = f"{base_url}?{urlencode(params)}"
    print(f"正在抓取第 {page} 页: {url}")

    response = requests.post(url, headers=headers, cookies=cookies, data=payload_template)
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "xml")
    records = soup.find_all("record")

    for record in records:
        cdata_html = record.get_text()
        inner = BeautifulSoup(cdata_html, "html.parser")

        a_tag = inner.find("a")
        span_tag = inner.find("span")

        if not a_tag:
            continue

        href = a_tag.get("href", "").strip()
        title = a_tag.get("title", "").strip()
        publish_time = span_tag.get_text(strip=True) if span_tag else ""

        if href and not href.startswith("http"):
            href = f"https://gxt.jiangsu.gov.cn{href}"

        # 详情页解析
        try:
            detail_resp = requests.get(href, headers=headers, timeout=10)
            detail_resp.encoding = "utf-8"
            detail_soup = BeautifulSoup(detail_resp.text, "html.parser")

            # ✅ 多模板兼容结构（顺序优先）
            content_div = (
                detail_soup.select_one("div.article_zoom.bfr_article_content") or
                detail_soup.select_one("div.article_zoom") or
                detail_soup.select_one("div.scroll_main.bfr_article_content") or
                detail_soup.select_one("div#zoom") or
                detail_soup.select_one("div.TRS_Editor") or
                detail_soup.select_one("div.content") or
                detail_soup.select_one("div.ccontent.center") or
                detail_soup.select_one("div.artile_zw") or
                detail_soup.select_one("div.w980.center.cmain")
            )

            if content_div:
                body_html = str(content_div)
                content_text = content_div.get_text(separator="\n", strip=True)
            else:
                body_html, content_text = "", ""

        except Exception as e:
            print(f"详情页出错：{href}, 错误：{e}")
            body_html, content_text = "", ""

        extracted_data.append({
            "label": "政策解读",
            "href": href,
            "title": title,
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content_text
        })
        print(extracted_data)