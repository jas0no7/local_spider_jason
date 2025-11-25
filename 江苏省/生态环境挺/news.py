import requests
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from time import sleep
from loguru import logger

# ==================================
# ==================================
base_url = "https://sthjt.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp"

headers = {
    "Accept": "application/xml, text/xml, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://sthjt.jiangsu.gov.cn",
    "Pragma": "no-cache",
    "Referer": "https://sthjt.jiangsu.gov.cn/col/col84025/index.html?uid=402134&pageNum=1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}

cookies = {
    "JSESSIONID": "E5CE90EE12ADD4DF55D8FEFA20061063",
    "__jsluid_s": "3a7706b8264b4000ab582f8996e70e23"
}

# 固定表单参数
payload = {
    "col": "1",
    "appid": "1",
    "webid": "14",
    "path": "/",
    "columnid": "84025",
    "sourceContentType": "1",
    "unitid": "402134",
    "webname": "江苏省生态环境厅",
    "permissiontype": "0",
}

# ==================================
# 分页逻辑
# ==================================
total_pages = 685
per_page = 15
total_records = 10266

results = []  # 存储结果

def parse_detail_page(url):
    """解析详情页正文"""
    try:
        # 加强 headers，加入动态 Referer
        local_headers = headers.copy()
        local_headers["Referer"] = url

        resp = requests.get(url, headers=local_headers, cookies=cookies, timeout=10)
        resp.encoding = "utf-8"

        # 安全检查：防止防爬页面
        if resp.status_code != 200 or len(resp.text) < 500:
            logger.warning(f"⚠️ 详情页内容疑似异常 (len={len(resp.text)})：{url}")
            return "", ""

        detail_soup = BeautifulSoup(resp.text, "html.parser")

        # 多模板兼容结构（顺序优先）
        content_div = (
            detail_soup.select_one("div.article_zoom.bfr_article_content")
            or detail_soup.select_one("div.article_zoom")
            or detail_soup.select_one("div.scroll_main.bfr_article_content")
            or detail_soup.select_one("div#zoom")
            or detail_soup.select_one("div.TRS_Editor")
            or detail_soup.select_one("div.content")
            or detail_soup.select_one("div.ccontent.center")
            or detail_soup.select_one("div.artile_zw")
            or detail_soup.select_one("div.w980.center.cmain")
            or detail_soup.select_one("div#article")
            or detail_soup.select_one("article")
            or detail_soup.select_one("div.main")
        )

        if content_div:
            body_html = str(content_div)
            content_text = content_div.get_text(separator="\n", strip=True)
        else:
            # 打印页面片段用于调试
            snippet = resp.text[:500].replace("\n", "")
            logger.warning(f"❌ 未找到正文节点: {url}\n片段预览: {snippet[:200]}")
            body_html, content_text = "", ""

        return body_html, content_text

    except Exception as e:
        logger.warning(f"详情页解析失败：{url}, 错误：{e}")
        return "", ""


# ==================================
# 主循环
# ==================================
for page in range(1, total_pages + 1):
    startrecord = (page - 1) * per_page + 1
    endrecord = min(page * per_page, total_records)
    query_params = {
        "startrecord": startrecord,
        "endrecord": endrecord,
        "perpage": per_page,
    }

    url = f"{base_url}?{urlencode(query_params)}"
    logger.info(f"正在抓取第 {page} 页: {url}")

    try:
        resp = requests.post(url, headers=headers, cookies=cookies, data=payload, timeout=10)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "xml")

        # 遍历每条 record
        for record in soup.find_all("record"):
            html = record.get_text()
            sub = BeautifulSoup(html, "html.parser")

            a_tag = sub.find("a")
            span_tag = sub.find("span")

            if not a_tag:
                continue

            title = a_tag.get("title") or a_tag.text.strip()
            href = a_tag.get("href", "").strip()
            publish_time = span_tag.get_text(strip=True) if span_tag else ""

            # 修正相对路径
            if href and not href.startswith("http"):
                href = f"https://sthjt.jiangsu.gov.cn{href}"

            # 解析详情页内容
            body_html, content_text = parse_detail_page(href)
            sleep(0.3)

            data = {
                "label":"省内新闻",
                "publish_time": publish_time,
                "title": title,
                "href": href,
                "body_html": body_html,
                "content": content_text
            }

            results.append(data)
            logger.info(results)

        logger.info(f"第 {page} 页提取完毕，共 {len(soup.find_all('record'))} 条")
        sleep(0.8)

    except Exception as e:
        logger.exception(f"第 {page} 页出错: {e}")

