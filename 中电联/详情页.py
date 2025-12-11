import requests


headers = {
    "Accept": "application/xml, text/xml, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://gxt.jiangsu.gov.cn",
    "Pragma": "no-cache",
    "Referer": "https://gxt.jiangsu.gov.cn/col/col80181/index.html?uid=403740&pageNum=3",
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
    "JSESSIONID": "D5A1F5D49BBB67A1784450859E7DAB55",
    "__jsluid_s": "6adbbfed425abed2a58140d4b6204a37",
    "e34b3568-c02f-45db-8662-33d198d0da1b": "WyI1NjQ0Njc3NTciXQ"
}
url = "https://gxt.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp"
params = {
    "startrecord": "76",
    "endrecord": "150",
    "perpage": "25"
}
data = {
    "col": "1",
    "appid": "1",
    "webid": "23",
    "path": "/",
    "columnid": "80181",
    "sourceContentType": "1",
    "unitid": "403740",
    "webname": "江苏省工业和信息化厅",
    "permissiontype": "0"
}
response = requests.post(url, headers=headers, cookies=cookies, params=params, data=data)

print(response.text)
print(response)