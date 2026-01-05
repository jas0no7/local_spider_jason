import requests
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from hashlib import md5

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://www.mohrss.gov.cn/SYrlzyhshbzb/rencairenshi/zcwj/jinengrencai/index_1.html",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}

cookies = {
    "path": "/",
    "__tst_status": "1065405420#",
    "EO_Bot_Ssid": "1706819584",
    "turingcross": "%7B%22distinct_id%22%3A%2219b2b81aae2d97-07fb34b48a999f-26061a51-1440000-19b2b81aae31900%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219b2b81aae2d97-07fb34b48a999f-26061a51-1440000-19b2b81aae31900%22%7D",
    "Hm_lvt_64e46e3f389bd47c0981fa5e4b9f2405": "1765960189,1766462458",
    "HMACCOUNT": "87F8838732B4A041",
    "arialoadData": "false",
    "ariauseGraymode": "false",
    "Hm_lpvt_64e46e3f389bd47c0981fa5e4b9f2405": "1766481191"
}

BASE_URL = "https://www.mohrss.gov.cn"
LIST_URL = "https://www.mohrss.gov.cn/SYrlzyhshbzb/rencairenshi/zcwj/jinengrencai/index{}.html"
TOTAL_PAGE = 8


def fetch(url):
    r = requests.get(url, headers=headers, cookies=cookies, timeout=20)
    r.encoding = "utf-8"
    return r.text


def parse_list(html):
    soup = BeautifulSoup(html, "html.parser")
    data_list = []

    items = soup.find_all("div", class_="organGeneralNewListConType")

    for item in items:
        a = item.find("a")
        if not a:
            continue

        title = a.get_text(strip=True)
        href = a.get("href", "").strip()
        full_link = urljoin(BASE_URL + "/", href)

        date = ""
        date_div = item.find("div", class_="organGeneralNewListTxtConTime")
        if date_div:
            span = date_div.find("span")
            if span:
                date = span.get_text(strip=True)

        if title and full_link:
            data_list.append({
                "title": title,
                "url": full_link,
                "publish_time": date
            })

    return data_list


def parse_detail(url, meta):
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    body_div = soup.find("div", class_="clearboth")

    body_html = body_div.decode() if body_div else ""
    content = body_div.get_text(strip=True) if body_div else ""

    if not meta["publish_time"]:
        m = re.search(r"\d{4}-\d{2}-\d{2}", html)
        meta["publish_time"] = m.group(0) if m else ""

    return {
        "_id": md5((url + meta["title"]).encode("utf-8")).hexdigest(),
        "url": url,
        "title": meta["title"],
        "publish_time": meta["publish_time"],
        "body_html": body_html,
        "content": content,
        "spider_from": "人力资源社会保障部",
        "label": "人才人事;政策文件;技能人才"
    }


def get_list_url(page):
    if page == 1:
        return LIST_URL.format("")
    return LIST_URL.format(f"_{page}")


def main():
    for page in range(1, TOTAL_PAGE + 1):
        list_url = get_list_url(page)
        html = fetch(list_url)
        items = parse_list(html)

        for item in items:
            data = parse_detail(item["url"], item)
            print(data)
            time.sleep(1)


if __name__ == "__main__":
    main()
