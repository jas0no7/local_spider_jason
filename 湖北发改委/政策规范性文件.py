import json

import requests

headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://fgw.hubei.gov.cn/fbjd/zc/gfwj/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
cookies = {
    "dataHide2": "33533906-1820-4452-be37-1f54bdcde486",
    "enable_924omrTVcFch": "true",
    "Hm_lvt_26e401b5926a8e2f986da47f23068edc": "1764056241,1764557361",
    "HMACCOUNT": "87F8838732B4A041",
    "Hm_lvt_b29a0fc8cf9f88dc79677b5ad985798b": "1764056241,1764557361",
    "mozi-assist": "{%22show%22:true%2C%22audio%22:false%2C%22speed%22:%22middle%22%2C%22zomm%22:1%2C%22cursor%22:false%2C%22pointer%22:false%2C%22bigtext%22:false%2C%22overead%22:false}",
    "Hm_lpvt_26e401b5926a8e2f986da47f23068edc": "1764557388",
    "Hm_lpvt_b29a0fc8cf9f88dc79677b5ad985798b": "1764557388",
    "924omrTVcFchP": "0Vh_Ld.m_bfqFpxICJRMpHFngp7u5pX_woccrRybBt0uyNJY1_sowPzOZpGuv6JDynYY395kuhvTrXtt7hIOVnOX5NK8OsGNeQCslTt9J606XKqXAXKv7KOpfh1tBH3DJPf_c.6Tgka5Tft16maZmxch1YBzrvUd7mMWKxrNppeZnPebfAGZdyXnRlt7e4RN49sSh5OhFhu1h4cmEBzrgdC6500wSIRqsYMT0bTYU1n8_eU605Ugvy1ePFamT6vs25VMmXz70eqb3.6U3DtCg5SfNP8Gos8T25AIhuaS4chiGK8LTic3d1oUakzai1tExyG2kphYFR1VoFBCxNIs0BCabRVUKqhJocHF2OXCtTB7"
}
url = "https://fgw.hubei.gov.cn/fbjd/zc/gfwj/wj/gfxwj.json"
params = {
    "6LDjm9Ls": "0KuTTFalqEo91_ieQrBXJmNEcqC.mgLlX9YuAdMyanvad1UKNY0uIAhKoJSKFNa6A_WhBrqr.9dhMKj1XmdsL0PwAlIlNwtqEzdydZ7V5b9UaYR1dmLCSSMm415snzKrknna5vDHhjEq"
}
response = requests.get(url, headers=headers, cookies=cookies, params=params)

index_data = json.loads(response.text)
all_data = []

# 遍历所有数据项
for item in index_data["data"]:
    data_item = {
        "deatil_url": item["URL"],
        "title": item["FILENAME"],
        "publish_time": item["DOCRELTIME"]
    }
    all_data.append(data_item)
    print(all_data)
