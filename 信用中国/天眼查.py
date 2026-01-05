import requests
import json


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a1b)XWEB/14185",
    "Content-Type": "application/json",
    "xweb_xhr": "1",
    "Authorization": "0###oo34J0clTxy_XG83pw0lorW5irsE###1767171322002###08df1970584f77d3b29f4f4aa1c07c6d",
    "version": "TYC-XCX-WX",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://servicewechat.com/wx9f2867fc22873452/133/page-frame.html",
    "Accept-Language": "zh-CN,zh;q=0.9"
}
url = "https://capi.tianyancha.com/cloud-tempest/app/searchCompany"
data = {
    "sortType": 0,
    "pageSize": 20,
    "pageNum": 1,
    "word": "重庆群光机械工具有限公司",
    "allowModifyQuery": 1
}
data = json.dumps(data, separators=(',', ':'))
response = requests.post(url, headers=headers, data=data)

print(response.text)
print(response)