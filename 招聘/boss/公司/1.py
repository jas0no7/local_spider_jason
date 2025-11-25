import requests


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a1b)XWEB/14185",
    "mini_ver": "13.2000",
    "ua": "{\"model\":\"microsoft\",\"platform\":\"windows\"}",
    "wt2": "",
    "zp_app_id": "10002",
    "content-type": "application/x-www-form-urlencoded",
    "traceid": "F-d35021wLKVWtbvg2",
    "mpt": "8aebb37e3710bdda291ba65bb3d12900",
    "scene": "1256",
    "xweb_xhr": "1",
    "x-requested-with": "XMLHttpRequest",
    "zp_product_id": "10002",
    "platform": "zhipin/windows",
    "ver": "13.2000",
    "sec-fetch-site": "cross-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": "https://servicewechat.com/wxa8da525af05281f3/585/page-frame.html",
    "accept-language": "zh-CN,zh;q=0.9",
    "priority": "u=1, i"
}
url = "https://www.zhipin.com/wapi/zpgeek/miniapp/brand/detail.json"
params = {
    "brandId": "9f36a5be4d6776e81n1y3tu_F1E~",
    "appId": "10002"
}
response = requests.get(url, headers=headers, params=params)

print(response.text)
print(response)