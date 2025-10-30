import requests
import json


headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Origin": "https://mapi.zjzwfw.gov.cn",
    "Pragma": "no-cache",
    "Referer": "https://mapi.zjzwfw.gov.cn/web/mgop/gov-open/zj/2001941911/reserved/index.html?",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "header_optimus_auth_request_token": "c9a0b9813ee046309e6202d891545086",
    "sec-ch-ua": "\"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
cookies = {
    "$aliyungf_tc": "9d26ecfa85a2e2276e857eb4660522137183c44373b2e9bb962fd9981695588f",
    "webId": "1",
    "zjzw_siteCode": "330000000000",
    "cna": "/B+HIV6hMV4CAf////+DgJV0",
    "JSESSIONID": "71ctjGeHKTpG_nYUHO6V-C1zv8sojPX6u_XHE18BnpojXD13Wafp\\u0021344545366",
    "arialoadData": "false",
    "SERVERID": "fb4ec6a2aa4cbb746e0f0e492b2168b9|1761721416|1761716627"
}
url = "https://mapi.zjzwfw.gov.cn/h5/mgop"
params = {
    "ak": "udqmn52d+2001941911+elgttz",
    "api": "mgop.gw.sjzj.zbcxqueryInstrumentHn",
    "ts": "1761721504853",
    "sign": "f571b1f49e402ce2bcc177441ce28396",
    "data": "null"
}
#季度是 J
data = {
    "postData": "{\"data\":[{\"vtype\":\"pagination\",\"name\":\"pagerows\",\"data\":10},{\"vtype\":\"pagination\",\"name\":\"totalrows\",\"data\":0},{\"vtype\":\"pagination\",\"name\":\"page\",\"data\":1},{\"vtype\":\"pagination\",\"name\":\"sortName\",\"data\":\"\"},{\"vtype\":\"pagination\",\"name\":\"sortFlag\",\"data\":\"\"}]}",
    "bh": "",
    "ddiInstance": "urn:ddi:ZJJCKSTAT:a463a4d9-806b-4fcc-8fc9-b43a8ee4298c:1",
    "groupUrn": "",
    "studyUnitUrn": "",
    "instrumentSchemeUrn": "",
    "bgqb": "Y",
    "projectId": "zj",
    "dqCode": "33"
}
data = json.dumps(data, separators=(',', ':'))
response = requests.post(url, headers=headers, cookies=cookies, params=params, data=data)

print(response.text)
print(response)