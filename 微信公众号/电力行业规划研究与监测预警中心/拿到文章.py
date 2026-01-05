import requests
import json
import time
import random
import os
import re
from urllib.parse import unquote
from bs4 import BeautifulSoup


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

BASE_PARAMS = {
    "sub": "list",
    "search_field": "null",
    "count": "5",
    "query": "",
    "fakeid": "MzU5NDg1OTc5MQ==",
    "type": "101_1",
    "free_publish_type": "1",
    "sub_action": "list_ex",
    "token": "237409963",
    "lang": "zh_CN",
    "f": "json",
    "ajax": "1"
}

# ====== 保存 HTML（可选） ======
ARTICLES_DIR = "articles_html"
os.makedirs(ARTICLES_DIR, exist_ok=True)

DETAIL_HEADERS = {
    "user-agent": HEADERS["user-agent"],
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "zh-CN,zh;q=0.9",
    "referer": "https://mp.weixin.qq.com/",
}

def safe_filename(s: str, max_len: int = 80) -> str:
    s = s or "untitled"
    s = re.sub(r"[\\/:*?\"<>|]", "_", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:max_len]

def save_html(update_time: str, title: str, html: str) -> str:
    ts = update_time.replace(":", "-").replace(" ", "_") if update_time else "unknown_time"
    name = safe_filename(title)
    path = os.path.join(ARTICLES_DIR, f"{ts}__{name}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


# ====== 新增：统一重试请求（解决你超时直接退出的问题） ======
def request_with_retry(
    session: requests.Session,
    method: str,
    url: str,
    *,
    headers=None,
    cookies=None,
    params=None,
    timeout=25,
    retries=4,
    backoff_base=1.8,
    allow_redirects=True,
):
    """
    - 对 ReadTimeout / ConnectionError / 5xx 做重试
    - 指数退避 + 抖动
    """
    last_err = None
    for i in range(retries + 1):
        try:
            resp = session.request(
                method=method,
                url=url,
                headers=headers,
                cookies=cookies,
                params=params,
                timeout=timeout,
                allow_redirects=allow_redirects,
            )
            # 5xx 也重试
            if 500 <= resp.status_code < 600:
                raise requests.HTTPError(f"server_error {resp.status_code}")
            return resp, None
        except (requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ConnectionError,
                requests.HTTPError) as e:
            last_err = str(e)
            if i == retries:
                break
            sleep_s = (backoff_base ** i) + random.uniform(0.3, 1.2)
            print(f"  ⚠️ 请求失败({e})，{sleep_s:.2f}s 后重试 {i+1}/{retries} ...")
            time.sleep(sleep_s)
        except Exception as e:
            # 其它异常通常没必要重试太多
            last_err = str(e)
            break
    return None, last_err


def fetch_article_html(session: requests.Session, url: str):
    if not url:
        return None, "empty_url"
    url = unquote(url)
    resp, err = request_with_retry(
        session,
        "GET",
        url,
        headers=DETAIL_HEADERS,
        timeout=25,   # 详情页也调大点
        retries=3,
        allow_redirects=True
    )
    if not resp:
        return None, err
    try:
        resp.raise_for_status()
    except Exception as e:
        return None, str(e)
    return resp.text, None


# ====== 解析微信正文/图片 ======
def _get_meta_content(soup: BeautifulSoup, prop: str):
    tag = soup.find("meta", attrs={"property": prop})
    return tag.get("content") if tag and tag.get("content") else None

def parse_wechat_article(html: str, fallback_url: str = "", fallback_title: str = "", fallback_publish_time: str = ""):
    soup = BeautifulSoup(html, "lxml")

    url = _get_meta_content(soup, "og:url") or fallback_url
    title = _get_meta_content(soup, "og:title") or fallback_title

    publish_time = fallback_publish_time
    pt = soup.find(id="publish_time")
    if pt:
        publish_time = pt.get_text(strip=True) or publish_time

    js_content = soup.find(id="js_content") or soup.select_one(".rich_media_content")

    body_html, content_text, images = "", "", []
    if js_content:
        body_html = js_content.decode_contents()
        content_text = js_content.get_text("\n", strip=True)

        for img in js_content.find_all("img"):
            cand = (
                img.get("data-croporisrc")
                or img.get("data-src")
                or img.get("data-original")
                or img.get("src")
            )
            if cand:
                images.append(cand)

    # 去重保持顺序
    seen, images_unique = set(), []
    for u in images:
        if u not in seen:
            seen.add(u)
            images_unique.append(u)

    return {
        "url": url,
        "title": title,
        "publish_time": publish_time,
        "body_html": body_html,
        "content": content_text,
        "images": images_unique,
    }


def parse_list_and_process(session: requests.Session, json_data, jsonl_fp):
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
                title = article.get("title") or ""
                link = article.get("link") or ""

                ts = article.get("update_time")
                update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)) if ts else ""

                print(f"[{update_time}] 抓取到: {title}")
                print(f"详情页: {link}")

                html, err = fetch_article_html(session, link)
                if not html:
                    print(f"  ❌ 抓取 HTML 失败: {err}")
                    obj = {
                        "url": link,
                        "title": title,
                        "publish_time": update_time,
                        "body_html": "",
                        "content": "",
                        "images": [],
                        "error": err,
                    }
                    jsonl_fp.write(json.dumps(obj, ensure_ascii=False) + "\n")
                    time.sleep(random.uniform(1.5, 3.0))
                    continue

                # 可选保存
                save_html(update_time, title, html)

                parsed = parse_wechat_article(
                    html=html,
                    fallback_url=link,
                    fallback_title=title,
                    fallback_publish_time=update_time,
                )
                jsonl_fp.write(json.dumps(parsed, ensure_ascii=False) + "\n")

                print(f"  ✅ 解析完成：正文长度={len(parsed.get('content',''))}，图片数={len(parsed.get('images',[]))}")
                time.sleep(random.uniform(1.5, 3.0))

        return True
    except Exception as e:
        print(f"解析列表/处理文章出错: {e}")
        return False


def main():
    # Session 复用连接
    session = requests.Session()

    with open("wechat_articles.jsonl", "w", encoding="utf-8") as jsonl_fp:
        begin = 0
        while True:
            params = BASE_PARAMS.copy()
            params["begin"] = str(begin)

            print(f"\n--- 正在请求 begin={begin} 的数据 ---")

            resp, err = request_with_retry(
                session,
                "GET",
                URL,
                headers=HEADERS,
                cookies=COOKIES,
                params=params,
                timeout=25,   # ✅ 列表接口 timeout 调大
                retries=4
            )
            if not resp:
                print(f"!!! 列表接口彻底失败: {err}")
                # 不直接退出：你可以选择 break，也可以继续下一轮
                break

            try:
                data = resp.json()
            except Exception as e:
                print(f"!!! JSON 解析失败: {e}")
                break

            if data.get("base_resp", {}).get("ret") == 200013:
                print("!!! 触发频率限制，请停止脚本，稍后再试，或更换 Cookie !!!")
                break

            has_data = parse_list_and_process(session, data, jsonl_fp)
            if not has_data:
                print("没有更多数据了，抓取结束。")
                break

            begin += 5
            sleep_time = random.uniform(6, 12)
            print(f"休眠 {sleep_time:.2f} 秒...")
            time.sleep(sleep_time)


if __name__ == "__main__":
    main()
