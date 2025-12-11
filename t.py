import requests


headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://drc.jiangxi.gov.cn",
    "Pragma": "no-cache",
    "Referer": "https://drc.jiangxi.gov.cn/jxsfzhggwyh/col/col14590/index.html",
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
    "arialoadData": "false",
    "zh_choose_undefined": "s",
    "ariauseGraymode": "false"
}
url = "https://drc.jiangxi.gov.cn/queryList"
data = {
    "current": "1",
    "unitid": "522756",
    "webSiteCode%5B%5D": "jxsfzhggwyh",
    "channelCode%5B%5D": "col14590",
    "dataBefore": "",
    "dataAfter": "",
    "perPage": "15",
    "showMode": "full",
    "groupSize": "1",
    "barPosition": "bottom",
    "titleMax": "39",
    "templateContainerId": "div522756",
    "themeName": "default",
    "pageSize": "15"
}
response = requests.post(url, headers=headers, cookies=cookies, data=data)

print(response.text)
print(response)