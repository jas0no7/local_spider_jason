import requests
from urllib.parse import urlencode
from time import sleep
from bs4 import BeautifulSoup

base_url = "https://gxt.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp"

headers = {
    "Accept": "application/xml, text/xml, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://gxt.jiangsu.gov.cn",
    "Pragma": "no-cache",
    "Referer": "https://gxt.jiangsu.gov.cn/col/col89736/index.html?uid=405463&pageNum=1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}

cookies = {

    "e34b3568-c02f-45db-8662-33d198d0da1b": "WyI1NjQ0Njc3NTciXQ",
    "__jsluid_s": "004e6adbcf1c6006363a34a55353707b"
}

payload_template = {
    "col": 1,
    "appid": 1,
    "webid": 23,
    "path": "/",
    "columnid": 89736,
    "sourceContentType": 9,
    "unitid": 405463,
    "webname": "江苏省工业和信息化厅",
    "permissiontype": 0,
}

perpage = 25
total_pages = 2
extracted_data = []

for page in range(1, total_pages + 1):
    startrecord = (page - 1) * perpage + 1
    endrecord = page * perpage if page < total_pages else 756

    params = {
        "startrecord": startrecord,
        "endrecord": endrecord,
        "perpage": perpage,
    }

    url = f"{base_url}?{urlencode(params)}"
    print(f"正在抓取第 {page} 页: {url}")

    response = requests.post(url, headers=headers, cookies=cookies, data=payload_template)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, 'xml')

    records = soup.find_all('record')

    for record in records:
        cdata_content = record.get_text()
        cdata_soup = BeautifulSoup(cdata_content, 'html.parser')

        a_tag = cdata_soup.find('a')
        b_tag = cdata_soup.find('b')

        if not (a_tag and b_tag):
            continue

        href = a_tag.get('href', '').strip()
        title = a_tag.get('title', '').strip()
        publish_time = b_tag.get('readlabel', '').strip() or b_tag.get_text(strip=True)

        if href and not href.startswith("http"):
            href = f"https://gxt.jiangsu.gov.cn{href}"

        try:
            detail_resp = requests.get(href, headers=headers, timeout=10)
            detail_resp.encoding = "utf-8"
            detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
            content_div = detail_soup.select_one('div.scroll_main.bfr_article_content')

            if content_div:
                body_html = str(content_div)
                content = content_div.get_text(separator="\n", strip=True)
            else:
                body_html, content = "", ""
        except Exception as e:
            print(f"详情页请求失败：{href}, 错误：{e}")
            body_html, content = "", ""

        extracted_data.append({
            "label": "政策文件",
            "href": href,
            "title": title,
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content
        })
        print(extracted_data)