import requests


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a1b)XWEB/14185",
    "mini_ver": "13.1901",
    "ua": "{\"model\":\"microsoft\",\"platform\":\"windows\"}",
    "wt2": "",
    "zp_app_id": "10002",
    "content-type": "application/x-www-form-urlencoded",
    "traceid" : "F-b8ef25govX1WmhAb",
    # "traceid": "F-91b0f4pzpbKtyDFt",#"traceid": "F-990639dwsuSugKlm",
    "mpt": "93b0bda2f7fe388c8465cbdc6de87bd2",
    #       93b0bda2f7fe388c8465cbdc6de87bd2
    "scene": "1260",
    "xweb_xhr": "1",
    "x-requested-with": "XMLHttpRequest",
    "zp_product_id": "10002",
    "platform": "zhipin/windows",
    "ver": "13.1901",
    "sec-fetch-site": "cross-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": "https://servicewechat.com/wxa8da525af05281f3/584/page-frame.html",
    "accept-language": "zh-CN,zh;q=0.9",
    "priority": "u=1, i"
}
url = "https://www.zhipin.com/wapi/zpgeek/miniapp/homepage/recjoblist.json"
params = {
    "cityCode": "101210100",
    "sortType": "1",
    "page": "1",
    "pageSize": "15",
    "encryptExpectId": "cb1494e0c1011eccynU~", #"encryptExpectId": "cb1494e0c1011eccynU~",
    "districtCode": "",
    "mixExpectType": "9",
    "expectId": "-1",
    "positionLv1": "p_100000",
    "positionLv2": "p_0",
    "positionLv3": "",
    "positionType": "2",
    "appId": "10002"
}
response = requests.get(url, headers=headers, params=params)

print(response.text)
print(response)