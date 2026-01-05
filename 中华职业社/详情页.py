import requests
from typing import List, Dict


# =========================
# 通用配置
# =========================
LIST_URL = "https://api.91ready.com/website-boot/home/moduleResource"
DETAIL_URL = "https://api.91ready.com/website-boot/home/getWebSiteResource"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://www.zhzjs.org",
    "Referer": "https://www.zhzjs.org/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/143.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
}


# =========================
# 列表接口
# =========================
def fetch_news_list(
    page_num: int = 1,
    page_size: int = 10,
    news_type_id: str = "1067128154583007232",
    module_id: str = "1067128154562035712",
) -> List[Dict]:
    payload = {
        "appCode": "WEBSITE_PC",
        "tenantId": "647163161756909568",
        "websiteId": "1060936920410521600",
        "browserId": "debe73f358018e236867498805d4984e",
        "pageNum": page_num,
        "pageSize": page_size,
        "queryEntityDto": {"baseQueryDtoList": []},
        "newsTypeId": news_type_id,
        "fuzzySearch": "",
        "moduleId": module_id,
        "preview": 0,
    }

    resp = requests.post(
        LIST_URL,
        headers=HEADERS,
        params={"token": ""},
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()

    try:
        return resp.json()["data"][0]["retPage"]["data"]
    except Exception:
        raise RuntimeError("列表接口结构异常")


# =========================
# 详情接口
# =========================
def fetch_detail(
    website_resource_id: str,
    news_type_id: str,
    page_num: int = 1,
    page_size: int = 10,
) -> Dict:
    payload = {
        "appCode": "WEBSITE_PC",
        "tenantId": "647163161756909568",
        "websiteId": "1060936920410521600",
        "browserId": "debe73f358018e236867498805d4984e",
        "moduleType": "6",
        "websiteResourceId": website_resource_id,
        "newsId": "",
        "newsTypeId": news_type_id,
        "pageNum": str(page_num),
        "pageSize": str(page_size),
    }

    resp = requests.post(
        DETAIL_URL,
        headers=HEADERS,
        params={"token": ""},
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()

    data = resp.json().get("data")
    if not data:
        raise RuntimeError("详情接口 data 为空")

    # 正文
    body_html = data.get("content", "") or ""
    content = data.get("fuzzySearch", "") or ""

    # 附件
    attachments = []
    for att in data.get("attachmentJa", []) or []:
        file_info = att.get("file") or {}
        url = file_info.get("url")
        if url:
            attachments.append(url)

    return {
        "title": data.get("title"),
        "publish_time": data.get("publishTime"),
        "body_html": body_html,
        "content": content,
        "attachments": attachments,
    }


# =========================
# 主流程
# =========================
if __name__ == "__main__":
    news_list = fetch_news_list(page_num=1, page_size=10)

    results = []
    for item in news_list:
        try:
            detail = fetch_detail(
                website_resource_id=item.get("websiteResourceId"),
                news_type_id=item.get("newsTypeId"),
            )

            record = {
                "title": detail["title"],
                "publish_time": detail["publish_time"],
                "body_html": detail["body_html"],
                "attachments": detail["attachments"],
                "detail_page": (
                    "https://www.zhzjs.org/#/infoDetail"
                    f"?websiteResourceId={item.get('websiteResourceId')}"
                    f"&newsId={item.get('id')}"
                    f"&newsTypeId={item.get('newsTypeId')}"
                ),
            }
            print(record)

            results.append(record)


        except Exception as e:
            print("抓取失败：", item.get("title"), e)

    print(f"\n总计抓取 {len(results)} 条")
