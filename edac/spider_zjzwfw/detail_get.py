import hashlib

import requests
import json
import requests
import json
import hashlib
import time
from bs4 import BeautifulSoup
import pandas as pd

timestamp = str(int(time.time() * 1000))

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
    "header_optimus_auth_request_token": "604cd486b7c348b4af4fde72ba2d6860",
    "sec-ch-ua": "\"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
cookies = {
    "$aliyungf_tc": "9d26ecfa85a2e2276e857eb4660522137183c44373b2e9bb962fd9981695588f",
    "webId": "1",
    "zjzw_siteCode": "330000000000",
    "arialoadData": "false",
    "cna": "/B+HIV6hMV4CAf////+DgJV0",
    "JSESSIONID": "-iQpbmUHCSUvGYIXDpS7WNpzO-bFKbMFDf96oOHZfjTvr0cCoNJi\\u0021-1473847150",
    "SERVERID": "fb4ec6a2aa4cbb746e0f0e492b2168b9|1761636554|1761631683"
}
url = "https://mapi.zjzwfw.gov.cn/h5/mgop"


def generate_sign(token, ak, api, ts, data):
    # 按照指定格式拼接字符串
    sign_str = f"token={token}&ak={ak}&api={api}&ts={ts}&data={data}"

    # 计算MD5哈希值
    md5_hash = hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    # 转换为小写
    return md5_hash.lower()


params2 = {
    "token": "",
    "ak": "udqmn52d+2001941911+elgttz",
    "api": "mgop.gw.sjzj.zbcxgetReportHtmlByCondition",
    "ts": timestamp,

    "data": "null"
}
sign = generate_sign(**params2)
params2['sign'] = sign
data3 = {
    "postData": "{\"data\":[{\"vtype\":\"attr\",\"name\":\"bsItemUrn\",\"data\":\"urn:ddi:10000681:d1ecc1bc-3556-4302-b6b7-773cec456f68:1\"},{\"vtype\":\"attr\",\"name\":\"bgq\",\"data\":\"20220000\"},{\"vtype\":\"attr\",\"name\":\"dqCode\",\"data\":\"33\"},{\"vtype\":\"attr\",\"name\":\"instrumentNumber\",\"data\":\"R-1-02-05\"}]}"
}
data3 = json.dumps(data3, separators=(',', ':'))
response2 = requests.post(url, headers=headers, cookies=cookies, params=params2, data=data3)

data_json2 = json.loads(response2.text)

print(data_json2)


