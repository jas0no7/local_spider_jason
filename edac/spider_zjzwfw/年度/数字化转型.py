# --coding:utf-8--
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
    "header_optimus_auth_request_token": "6c9f1f08dc2644269d81e6e499b8a3cf",
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
    "SERVERID": "fb4ec6a2aa4cbb746e0f0e492b2168b9|1761720450|1761716627"
}
url = "https://mapi.zjzwfw.gov.cn/h5/mgop"
params = {
    "ak": "udqmn52d+2001941911+elgttz",
    "api": "mgop.gw.sjzj.zbcxqueryInstrumentHn",
    "ts": "1761720463982",
    "sign": "846ce46802b7178d8bf4bc84accc08ef",
    "data": "null"
}
data = {
    "postData": "{\"data\":[{\"vtype\":\"pagination\",\"name\":\"pagerows\",\"data\":10},{\"vtype\":\"pagination\",\"name\":\"totalrows\",\"data\":0},{\"vtype\":\"pagination\",\"name\":\"page\",\"data\":1},{\"vtype\":\"pagination\",\"name\":\"sortName\",\"data\":\"\"},{\"vtype\":\"pagination\",\"name\":\"sortFlag\",\"data\":\"\"}]}",
    "bh": "",
    "ddiInstance": "urn:ddi:ZJJCKSTAT:a463a4d9-806b-4fcc-8fc9-b43a8ee4298c:1",
    "groupUrn": "540617cec8d84ae7b09019d86dbc08a0",
    "studyUnitUrn": "",
    "instrumentSchemeUrn": "",
    "bgqb": "N",
    "projectId": "zj",
    "dqCode": "33"
}
data = json.dumps(data, separators=(',', ':'))
response = requests.post(url, headers=headers, cookies=cookies, params=params, data=data)

print(response.text)
print(response)