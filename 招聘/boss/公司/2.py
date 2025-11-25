import requests


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a1b)XWEB/14185",
    "mini_ver": "13.2000",
    "ua": "{\"model\":\"microsoft\",\"platform\":\"windows\"}",
    "wt2": "",
    "zp_app_id": "10002",
    "Content-Type": "application/x-www-form-urlencoded",
    "Traceid": "F-1e1d81Lf3eQyyapr",
    "mpt": "93fbbe218851c0664c1efd1de1acf90c",
    "scene": "1145",
    "xweb_xhr": "1",
    "x-requested-with": "XMLHttpRequest",
    "zp_product_id": "10002",
    "platform": "zhipin/windows",
    "ver": "13.2000",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://servicewechat.com/wxa8da525af05281f3/585/page-frame.html",
    "Accept-Language": "zh-CN,zh;q=0.9"
}
url = "https://www.zhipin.com/wapi/zpgeek/miniapp/search/brandlist.json"
params = {
    "pageSize": "20",
    "query": "腾讯公司",
    "city": "101010100",
    "source": "1",
    "sortType": "0",
    "subwayLineId": "",
    "subwayStationId": "",
    "districtCode": "",
    "businessCode": "",
    "longitude": "",
    "latitude": "",
    "position": "",
    "expectId": "",
    "expectPosition": "",
    "encryptExpectId": "",
    "page": "1",
    "appId": "10002"
}
response = requests.get(url, headers=headers, params=params)

print(response.text)
print(response)