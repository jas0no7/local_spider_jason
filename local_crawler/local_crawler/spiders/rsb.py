import requests
from bs4 import BeautifulSoup

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://www.mohrss.gov.cn/xxgk2020/fdzdgknr/index_iframe.html",
    "Sec-Fetch-Dest": "iframe",
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
    "__tst_status": "775671185#",
    "EO_Bot_Ssid": "4286644224",
    "turingcross": "%7B%22distinct_id%22%3A%2219b2b81aae2d97-07fb34b48a999f-26061a51-1440000-19b2b81aae31900%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219b2b81aae2d97-07fb34b48a999f-26061a51-1440000-19b2b81aae31900%22%7D",
    "Hm_lvt_64e46e3f389bd47c0981fa5e4b9f2405": "1765960189,1766462458",
    "HMACCOUNT": "87F8838732B4A041",
    "arialoadData": "false",
    "ariauseGraymode": "false",
    "Hm_lpvt_64e46e3f389bd47c0981fa5e4b9f2405": "1766567461"
}
url = "https://www.mohrss.gov.cn/xxgk2020/fdzdgknr/index_iframe_1.html"
response = requests.get(url, headers=headers, cookies=cookies)
response.encoding='utf-8'

print(response.text)
print(response)