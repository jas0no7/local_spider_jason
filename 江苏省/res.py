import requests
from urllib.parse import urlencode
from time import sleep
from bs4 import BeautifulSoup
import concurrent.futures

base_url = "https://gxt.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp"

# 两个栏目的配置
configs = [
    {
        "name": "政策文件",
        "headers": {
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
        },
        "cookies": {
            "e34b3568-c02f-45db-8662-33d198d0da1b": "WyI1NjQ0Njc3NTciXQ",
            "__jsluid_s": "004e6adbcf1c6006363a34a55353707b"
        },
        "payload_template": {
            "col": 1,
            "appid": 1,
            "webid": 23,
            "path": "/",
            "columnid": 89736,
            "sourceContentType": 9,
            "unitid": 405463,
            "webname": "江苏省工业和信息化厅",
            "permissiontype": 0,
        },
        "perpage": 25,
        "total_pages": 2,
        "total_records": 756  # 用于计算最后一页的endrecord
    },
    {
        "name": "政策解读",
        "headers": {
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
        },
        "cookies": {
            "JSESSIONID": "E27B4554CCF4188AE07AB8FD97120AA3",
            "__jsluid_s": "97aa8e8d8c4555dd01573c6b0f456805",
        },
        "payload_template": {
            "col": 1,
            "appid": 1,
            "webid": 23,
            "path": "/",
            "columnid": 6197,
            "sourceContentType": 1,
            "unitid": 403981,
            "webname": "江苏省工业和信息化厅",
            "permissiontype": 0,
        },
        "perpage": 12,
        "total_pages": 2,
        "total_records": None  # 第二个脚本没有特殊的总记录数处理
    }
]


def parse_detail_page(href, headers, timeout=10):
    """解析详情页内容"""
    try:
        detail_resp = requests.get(href, headers=headers, timeout=timeout)
        detail_resp.encoding = "utf-8"
        detail_soup = BeautifulSoup(detail_resp.text, "html.parser")

        # 多模板兼容结构（顺序优先）
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

        return body_html, content_text

    except Exception as e:
        print(f"详情页请求失败：{href}, 错误：{e}")
        return "", ""


def extract_time_from_record(record_soup, config_name):
    """根据栏目类型提取发布时间"""
    if config_name == "政策文件":
        b_tag = record_soup.find('b')
        if b_tag:
            return b_tag.get('readlabel', '').strip() or b_tag.get_text(strip=True)
    elif config_name == "政策解读":
        span_tag = record_soup.find('span')
        if span_tag:
            return span_tag.get_text(strip=True)
    return ""


def crawl_single_page(config, page):
    """采集单个页面的数据"""
    extracted_data = []
    name = config["name"]
    headers = config["headers"]
    cookies = config["cookies"]
    payload_template = config["payload_template"]
    perpage = config["perpage"]

    # 计算startrecord和endrecord
    startrecord = (page - 1) * perpage + 1
    if config["total_records"] and page == config["total_pages"]:
        endrecord = config["total_records"]
    else:
        endrecord = page * perpage

    params = {
        "startrecord": startrecord,
        "endrecord": endrecord,
        "perpage": perpage,
    }

    url = f"{base_url}?{urlencode(params)}"
    print(f"[{name}] 正在抓取第 {page} 页: {url}")

    try:
        response = requests.post(url, headers=headers, cookies=cookies, data=payload_template)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, 'xml')

        records = soup.find_all('record')

        for record in records:
            cdata_content = record.get_text()
            cdata_soup = BeautifulSoup(cdata_content, 'html.parser')

            a_tag = cdata_soup.find('a')
            if not a_tag:
                continue

            href = a_tag.get('href', '').strip()
            title = a_tag.get('title', '').strip()
            publish_time = extract_time_from_record(cdata_soup, name)

            if href and not href.startswith("http"):
                href = f"https://gxt.jiangsu.gov.cn{href}"

            # 解析详情页
            body_html, content = parse_detail_page(href, headers)

            extracted_data.append({
                "label": name,
                "href": href,
                "title": title,
                "publish_time": publish_time,
                "body_html": body_html,
                "content": content
            })

            print(f"[{name}] 已采集: {title}")

        # 添加延时，避免请求过于频繁
        sleep(1)

    except Exception as e:
        print(f"[{name}] 第 {page} 页采集失败: {e}")

    return extracted_data


def crawl_single_config(config):
    """采集单个栏目的所有页面"""
    all_data = []
    name = config["name"]
    total_pages = config["total_pages"]

    print(f"\n{'=' * 50}")
    print(f"开始采集栏目: {name}")
    print(f"{'=' * 50}")

    for page in range(1, total_pages + 1):
        page_data = crawl_single_page(config, page)
        all_data.extend(page_data)
        print(f"[{name}] 第 {page} 页完成，本页采集 {len(page_data)} 条数据")

    print(f"[{name}] 采集完成，总共采集 {len(all_data)} 条数据")
    return all_data


def main():
    """主函数：同时采集两个栏目"""
    all_extracted_data = []

    # 使用线程池同时采集两个栏目
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # 提交两个栏目的采集任务
        future_to_config = {
            executor.submit(crawl_single_config, config): config["name"]
            for config in configs
        }

        # 获取结果
        for future in concurrent.futures.as_completed(future_to_config):
            config_name = future_to_config[future]
            try:
                data = future.result()
                all_extracted_data.extend(data)
                print(f"\n✅ 栏目 {config_name} 采集完成，共 {len(data)} 条数据")
            except Exception as e:
                print(f"\n❌ 栏目 {config_name} 采集失败: {e}")

    # 输出最终结果
    print(f"\n{'=' * 60}")
    print(f"全部采集完成！总共采集 {len(all_extracted_data)} 条数据")
    print(f"{'=' * 60}")

    # 按栏目统计
    for config in configs:
        name = config["name"]
        count = len([item for item in all_extracted_data if item["label"] == name])
        print(f"  {name}: {count} 条")

    # 打印前几条数据作为示例
    print(f"\n前5条数据示例:")
    for i, item in enumerate(all_extracted_data[:5]):
        print(f"  {i + 1}. [{item['label']}] {item['title']} - {item['publish_time']}")

    return all_extracted_data


if __name__ == "__main__":
    result = main()