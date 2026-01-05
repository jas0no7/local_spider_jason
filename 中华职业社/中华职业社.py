import requests
from loguru import logger

URL = "https://api.91ready.com/website-boot/home/moduleResource"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
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


def fetch_news_list(
    page_num=1,
    page_size=10,
    news_type_id="1067128154583007232",
    module_id="1067128154562035712",
):
    payload = {
        "appCode": "WEBSITE_PC",
        "tenantId": "647163161756909568",
        "websiteId": "1060936920410521600",
        "browserId": "debe73f358018e236867498805d4984e",
        "pageNum": page_num,
        "pageSize": page_size,
        "queryEntityDto": {
            "baseQueryDtoList": []
        },
        "newsTypeId": news_type_id,
        "fuzzySearch": "",
        "moduleId": module_id,
        "preview": 0,
    }

    resp = requests.post(
        URL,
        headers=HEADERS,
        params={"token": ""},
        json=payload,
        timeout=10,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"请求失败，status={resp.status_code}")

    data = resp.json()

    try:
        return data["data"][0]["retPage"]["data"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("返回结构异常，无法解析列表数据")


def build_detail_url(item):
    return (
        "https://www.zhzjs.org/#/infoDetail"
        f"?lightIndex=0"
        f"&websiteResourceId={item.get('websiteResourceId')}"
        f"&newsId={item.get('id')}"
        f"&newsTypeId={item.get('newsTypeId')}"
        f"&preview=0"
        f"&currentPage=1"
        f"&pageSize=10"
        f"&moduleType=6"
    )


if __name__ == "__main__":
    news_list = fetch_news_list(page_num=1, page_size=10)

    for item in news_list:
        title = item.get("title")
        publish_time = item.get("publishTime")
        website_resource_id = item.get("websiteResourceId")
        news_id = item.get("id")
        news_type_id = item.get("newsTypeId")

        detail_url = build_detail_url(item)


        item = {
            "title": title,
            "publish_time": publish_time,
            "detail_url": detail_url,
        }
        logger.info(item)
