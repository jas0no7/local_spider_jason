import requests
import json
import time
import csv
import random
import os
import re
from urllib.parse import unquote

# --- 请确保以下信息是你最新抓包获取的 ---
URL = "https://mp.weixin.qq.com/cgi-bin/appmsgpublish"

HEADERS = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=77&createType=8&token=237409963&lang=zh_CN&timestamp=1767508830006",
    "sec-ch-ua": "\"Microsoft Edge\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
    "x-requested-with": "XMLHttpRequest"
}

# 复制你刚才代码里的完整 cookies
COOKIES = {
    "RK": "4n+Q7DkbR9",
    "ptcz": "06e610245ea18abb2595ee44c7d0c0450dbb48a7fae61bbe2abcac5360ccb6be",
    "eas_sid": "D17774J9Z1l781e8l0L168N4B0",
    "pgv_pvid": "6344216056",
    "fqm_pvqid": "6050f84b-b1c3-4bfa-bede-f3e200232741",
    "_qimei_uuid42": "19a0d09073b1001f4c22c7617089ea6dbba6c68348",
    "_qimei_fingerprint": "0b0d42084c6cb29bed570ad51ec3b7d1",
    "_qimei_q36": "",
    "_qimei_h38": "a4fa7af74c22c7617089ea6d0200000bc19a0d",
    "ua_id": "3CFB2Iz0DlqKspPgAAAAAG2Ivt-ZgQCXnR1dn7nS6P0=",
    "_clck": "yi6308|1|g2f|0",
    "wxuin": "67508769800339",
    "mm_lang": "zh_CN",
    "uuid": "f05f01c118e1d92ed01b467205237a2d",
    "rand_info": "CAESIPcdrhgNGR/zyjvvqqRZEF6cDsa0Ml3SJZjmwf40jHoo",
    "slave_bizuin": "3576963203",
    "data_bizuin": "3576963203",
    "bizuin": "3576963203",
    "data_ticket": "woNCu5BCMyNC/vKvNnglk1QEtuL4xZyAKR3iB8WLZHnkCn2jv4AVu1o4mZPNnIvN",
    "slave_sid": "NHUwMEMwVHNrNXFDN09SME9fZGpHUVpIS2g5eEtWNlN4eEZxNkdSbGR6UlVJbTZjTU9lbTRHaWJ6WkIyaUhQRkhpUWpjZFlTUV91Zm9aYUNSeDRjdWJZRFBUOVB5cEI0S0Y3M2UyVkV2Q2JrNnhaVnZoTHdsQTU5NWsyODJZTEhqRjI4dHptMmtwTHg1bkxs",
    "slave_user": "gh_3bc6203573ae",
    "xid": "7206fef30475299c424024bd48d83d5e",
    "_clsk": "1hhcnx6|1767508833730|4|1|mp.weixin.qq.com/weheat-agent/payload/record"
}

# 基础请求参数
BASE_PARAMS = {
    "sub": "list",
    "search_field": "null",
    "count": "5",  # 每次抓5篇
    "query": "",
    "fakeid": "MzU5NTEzODg0NQ==",
    "type": "101_1",
    "free_publish_type": "1",
    "sub_action": "list_ex",
    "token": "237409963",  # 你的 Token
    "lang": "zh_CN",
    "f": "json",
    "ajax": "1"
}

# ====== 新增：详情页抓取与保存 ======
ARTICLES_DIR = "articles_html"
os.makedirs(ARTICLES_DIR, exist_ok=True)

DETAIL_HEADERS = {
    "user-agent": HEADERS["user-agent"],
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "zh-CN,zh;q=0.9",
    "referer": "https://mp.weixin.qq.com/",
}


def safe_filename(s: str, max_len: int = 80) -> str:
    """把标题变成安全文件名"""
    s = s or "untitled"
    s = re.sub(r"[\\/:*?\"<>|]", "_", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:max_len]


def fetch_article_html(url: str, timeout: int = 15, retries: int = 2):
    """
    抓取公众号文章详情页 HTML
    大多数文章是公开的，通常不需要 COOKIES；如遇到 403/风控，再考虑加 cookies（但不建议默认加）。
    """
    if not url:
        return None, "empty_url"

    # 有些 link 可能含有转义/编码，顺手处理下
    url = unquote(url)

    last_err = None
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=DETAIL_HEADERS, timeout=timeout, allow_redirects=True)
            r.raise_for_status()
            # 微信文章一般是 utf-8，requests 会自动处理；这里直接返回 text
            return r.text, None
        except Exception as e:
            last_err = str(e)
            # 小退避
            time.sleep(random.uniform(1.0, 2.5))
    return None, last_err


def save_html(update_time: str, title: str, html: str) -> str:
    """保存 HTML 到本地文件，返回文件路径"""
    ts = update_time.replace(":", "-").replace(" ", "_")
    name = safe_filename(title)
    path = os.path.join(ARTICLES_DIR, f"{ts}__{name}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


# ====== 新增结束 ======


def parse_and_save(json_data, csv_writer):
    """解析嵌套的 JSON 并写入 CSV，同时抓取详情页 HTML"""
    try:
        publish_page_str = json_data.get("publish_page", "{}")
        publish_page_dict = json.loads(publish_page_str)

        publish_list = publish_page_dict.get("publish_list", [])
        if not publish_list:
            return False

        for item in publish_list:
            publish_info_str = item.get("publish_info", "{}")
            publish_info_dict = json.loads(publish_info_str)

            articles = publish_info_dict.get("appmsgex", [])
            for article in articles:
                title = article.get("title")
                link = article.get("link")

                ts = article.get("update_time")
                update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

                print(f"[{update_time}] 抓取到: {title}")
                print(f"详情页: {link}")

                # ====== 新增：抓取详情页 HTML 并保存 ======
                html_path = ""
                html_len = 0
                err = ""

                html, err = fetch_article_html(link)
                if html:
                    html_len = len(html)
                    html_path = save_html(update_time, title, html)
                    print(f"  ✅ 已保存 HTML: {html_path} (len={html_len})")
                else:
                    print(f"  ❌ 抓取 HTML 失败: {err}")
                # ====== 新增结束 ======

                # CSV 多写两列：HTML文件路径、HTML长度/错误
                csv_writer.writerow([update_time, title, link, html_path, html_len, err])

                # 每篇文章之间也稍微歇一下，更稳
                time.sleep(random.uniform(1.5, 3.0))

        return True
    except Exception as e:
        print(f"解析出错: {e}")
        return False


def main():
    # 创建 CSV 文件
    with open('wechat_articles.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        # 增加列：HTML路径 / HTML长度 / 错误信息
        writer.writerow(['发布时间', '文章标题', '文章链接', 'HTML文件路径', 'HTML长度', '错误信息'])

        begin = 0
        while True:
            params = BASE_PARAMS.copy()
            params["begin"] = str(begin)

            print(f"\n--- 正在请求 begin={begin} 的数据 ---")

            try:
                response = requests.get(URL, headers=HEADERS, cookies=COOKIES, params=params, timeout=10)
                data = response.json()

                if data.get("base_resp", {}).get("ret") == 200013:
                    print("!!! 触发频率限制，请停止脚本，稍后再试，或更换 Cookie !!!")
                    break

                has_data = parse_and_save(data, writer)
                if not has_data:
                    print("没有更多数据了，抓取结束。")
                    break

                begin += 5

                sleep_time = random.uniform(5, 10)
                print(f"休眠 {sleep_time:.2f} 秒...")
                time.sleep(sleep_time)

            except Exception as e:
                print(f"请求发生错误: {e}")
                break


if __name__ == "__main__":
    main()
