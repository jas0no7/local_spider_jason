import json

import requests

url = "https://api.hunan.gov.cn/search/common/search/80675"

headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://gxt.hunan.gov.cn",
    "Pragma": "no-cache",
    "Referer": "https://gxt.hunan.gov.cn/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}
for page in range(1,71):
    data = {
        "datas[0][key]": "status",
        "datas[0][value]": "4",
        "datas[0][join]": "and",
        "datas[0][queryType]": "term",

        "datas[1][key]": "publishedTime",
        "datas[1][sort]": "true",
        "datas[1][order]": "desc",
        "datas[1][queryType]": "term",

        "page": page,
        "_pageSize": "20",
        "_isAgg": "true"
    }

    response = requests.post(url, headers=headers, data=data)

    resp_json = json.loads(response.text)

    items = []

    # 安全地取出 results 列表
    results = resp_json.get("data", {}).get("results", [])

    for r in results:
        title = r.get("title", "")
        content = r.get("content", "")
        publish_time = r.get("publishedTimeStr", "")

        items.append({
            "label": "工信数据",
            "title": title,
            "content": content,
            "publish_time": publish_time,
        })
        print(items)





