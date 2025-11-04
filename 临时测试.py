import requests


headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
cookies = {
    "_trs_uv": "mhkcqgt2_2997_6ior",
    "_trs_ua_s_1": "mhkcqgt2_2997_2nn9",
    "_trs_gv": "g_mhkcqgt2_2997_6ior",
    "dataHide2": "256a69aa-1bbb-44de-b1af-a4f627d4170a",
    "Hm_lvt_b6564ffd7a04bf8cb06eea91adfbce21": "1762247644",
    "HMACCOUNT": "8F1962303CCAC654",
    "Hm_lpvt_b6564ffd7a04bf8cb06eea91adfbce21": "1762249632"
}
url = "https://jxt.hubei.gov.cn/fbjd/zc/zcjd/"
response = requests.get(url, headers=headers, cookies=cookies)

print(response.text)
print(response)