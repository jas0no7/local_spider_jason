import requests
import json
import re
from hashlib import md5
from datetime import datetime
from bs4 import BeautifulSoup

# ===============================
# 基础配置
# ===============================
headers = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://cec.org.cn/menu/index.html?715",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "cookie": "JSESSIONID=56BAE96AA7F790A5BD4AC859A34C33A6;",
}

list_url = "https://cec.org.cn/ms-mcms/mcms/content/list"
detail_api = "https://cec.org.cn/ms-mcms/mcms/content/detail"

# ===============================
# 所有栏目配置
# ===============================
infoes = [
    {"label": "电力消费", "id": "823", "pageSize": 10, "total": 2},
    {"label": "电力供应", "id": "824", "pageSize": 10, "total": 2},
    {"label": "电力市场", "id": "825", "pageSize": 10, "total": 7},
    {"label": "供需报告", "id": "826", "pageSize": 10, "total": 6},
    {"label": "CEGI指数", "id": "857", "pageSize": 10, "total": 1},
    {"label": "研究成果", "id": "472", "pageSize": 10, "total": 6},
    {"label": "CECI周报", "id": "719", "pageSize": 10, "total": 47},
    {"label": "CECI指数", "id": "718", "pageSize": 10, "total": 213},
]


# ===============================
# 采集函数
# ===============================
def crawl_list_and_detail():
    all_results = []

    for info in infoes:
        label = info["label"]
        cid = info["id"]
        pageSize = int(info["pageSize"])
        total = int(info["total"])

        # 计算页数
        total_page = (total + pageSize - 1) // pageSize

        print(f"\n======== 开始采集栏目：{label}（ID={cid}），共 {total_page} 页 ========\n")

        for page in range(1, total_page + 1):
            params = {
                "id": cid,
                "pageNumber": page,
                "pageSize": pageSize
            }

            resp = requests.get(list_url, headers=headers, params=params)
            resp.raise_for_status()
            list_json = resp.json()

            if "data" not in list_json or "list" not in list_json["data"]:
                print("列表返回为空，跳过该页。")
                continue

            for item in list_json["data"]["list"]:
                title = item.get("basicTitle", "")
                article_id = item.get("articleID", "")
                ts = item.get("publicTime", 0)
                list_time = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")

                detail_params = {"id": article_id}
                detail_resp = requests.get(detail_api, headers=headers, params=detail_params)
                detail_resp.raise_for_status()
                detail_json = detail_resp.json().get("data", {})

                author = detail_json.get("articleAuthor", "")
                publish_ts = detail_json.get("publicTime", 0)
                publish_time = datetime.fromtimestamp(publish_ts / 1000).strftime("%Y-%m-%d")

                body_html = detail_json.get("articleContent", "")
                soup = BeautifulSoup(body_html, "lxml")
                content_text = soup.get_text("\n", strip=True)

                # 图片
                images = re.findall(r'<img[^>]+src="([^"]+)"', body_html)

                # 附件
                attachments = []
                pdf_url = detail_json.get("pdfUrl")
                if pdf_url:
                    attachments.append(pdf_url)

                # 构造详情页 URL
                detail_url = f"https://cec.org.cn/detail/index.html?3-{article_id}"

                # 唯一 _id
                _id = md5(f"GET{detail_url}".encode("utf-8")).hexdigest()

                # 结果结构
                doc = {
                    "_id": _id,
                    "label": label,
                    "spider_from": "中国电力企业联合会",
                    "url": detail_url,
                    "title": title,
                    "author": author,
                    "publish_time": publish_time,
                    "publicTime_list": list_time,
                    "article_id": article_id,
                    "body_html": body_html,
                    "content": content_text,
                    "images": images,
                    "attachment": attachments,
                }

                all_results.append(doc)
                print(all_results)


    return all_results


# ===============================
# 主执行
# ===============================
if __name__ == "__main__":
    data = crawl_list_and_detail()
    print("\n================== 所有数据采集完成 ==================\n")
    print(json.dumps(data, ensure_ascii=False, indent=2))
