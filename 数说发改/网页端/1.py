import requests

headers = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://jyt.zj.gov.cn",
    "Pragma": "no-cache",
    "Referer": "https://jyt.zj.gov.cn/col/col1229106823/index.html",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
cookies = {
    "sensorsdata2015jssdkcross": "%7B%22distinct_id%22%3A%2219ac4ead2fa5e0-0f74a8475b5f97-26061b51-1440000-19ac4ead2fb44d%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTlhYzRlYWQyZmE1ZTAtMGY3NGE4NDc1YjVmOTctMjYwNjFiNTEtMTQ0MDAwMC0xOWFjNGVhZDJmYjQ0ZCJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219ac4ead2fa5e0-0f74a8475b5f97-26061b51-1440000-19ac4ead2fb44d%22%7D",
    "sensorsdata2015jssdksession": "%7B%22session_id%22%3A%2219ac9906e465610b8f1e214a60826061b51144000019ac9906e471966%22%2C%22first_session_time%22%3A1764318277190%2C%22latest_session_time%22%3A1764318277590%7D",
    "SERVERID": "bc6beea6e995cecb42c7a1341ba3517f|1765870949|1765870946"
}
url = "https://jyt.zj.gov.cn/module/xxgk/search.jsp"
params = {
    "standardXxgk": "0",
    "isAllList": "1",
    "texttype": "",
    "fbtime": "",
    "vc_all": "",
    "vc_filenumber": "",
    "vc_title": "",
    "vc_number": "",
    "currpage": "2",
    "sortfield": ",compaltedate:0"
}
data = {
    "infotypeId": "A02003",
    "jdid": "3099",
    "area": "",
    "divid": "div1532973",
    "vc_title": [
        "",
        ""
    ],
    "vc_number": [
        "",
        ""
    ],
    "sortfield": [
        ",compaltedate:0",
        ",compaltedate:0"
    ],
    "currpage": [
        "2",
        "2"
    ],
    "vc_filenumber": [
        "",
        ""
    ],
    "vc_all": [
        "",
        ""
    ],
    "texttype": [
        "",
        ""
    ],
    "fbtime": [
        "",
        ""
    ],
    "standardXxgk": "0",
    "isAllList": "1"
}
response = requests.post(url, headers=headers, cookies=cookies, params=params, data=data)

print(response.text)
print(response)
