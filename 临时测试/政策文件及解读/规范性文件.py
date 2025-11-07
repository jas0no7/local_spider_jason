import requests


headers = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://gxt.jiangxi.gov.cn",
    "Pragma": "no-cache",
    "Referer": "https://gxt.jiangxi.gov.cn/jxsgyhxxht/gfxwj/index.html",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": "\"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
url = "https://gxt.jiangxi.gov.cn/queryList"
max_page =4
label = "规范性文件"
data = {
    "current": "1",
    "pageSize": "15",
    "webSiteCode[]": "jxsgyhxxht",
    "channelCode[]": "gfxwj",
    "sort": "sortNum",
    "order": "desc"
}
response = requests.post(url, headers=headers, data=data)
response.encoding = 'utf-8'
print(response.text)
print(response)