import requests
import json


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a1b)XWEB/14185",
    "Content-Type": "application/json",
    "xweb_xhr": "1",
    "Authorization": "Basic YXBwOmFwcA==",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://servicewechat.com/wxf376e02e5f71116c/58/page-frame.html",
    "Accept-Language": "zh-CN,zh;q=0.9"
}
url = "https://gateway.enneagon.cn/charge-ex-miniapp-backend-provider/v5/station/getGunListByStationCodeV2"
data = {
    "page": 1,
    "stationCode": "207573",
    "size": 10,
    "equipmentType": 1
}
data = json.dumps(data, separators=(',', ':'))
response = requests.post(url, headers=headers, data=data)

print(response.text)
print(response)