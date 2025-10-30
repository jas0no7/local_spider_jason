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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "header_optimus_auth_request_token": "01fdaf34fd474896bab0a1aedddd835c"
}

cookies = {
    "$aliyungf_tc": "9d26ecfa85a2e2276e857eb4660522137183c44373b2e9bb962fd9981695588f",
    "webId": "1",
    "zjzw_siteCode": "330000000000",
    "arialoadData": "false",
    "JSESSIONID": "kKwotoHmZikLdzo7_2SEX2qK_WSRE_CK_Nd5jqpBd_myD6K-CISh!-1473847150",
    "cna": "/B+HIV6hMV4CAf////+DgJV0",
    "SERVERID": "fb4ec6a2aa4cbb746e0f0e492b2168b9|1761620816|1761619632"
}


def generate_sign(token, ak, api, ts, data):
    # 按照指定格式拼接字符串
    sign_str = f"token={token}&ak={ak}&api={api}&ts={ts}&data={data}"

    # 计算MD5哈希值
    md5_hash = hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    # 转换为小写
    return md5_hash.lower()


url = "https://mapi.zjzwfw.gov.cn/h5/mgop"
params = {
    "token": '',
    "ak": "udqmn52d+2001941911+elgttz",

    "api": "mgop.gw.sjzj.zbcxqueryInstrumentHn",
    "ts": timestamp,

    "data": "null"
}
signature = generate_sign(**params)
params['sign'] = signature
# for i in range(1, 710):  # 页码从1到710
post_data = {
    "data": [
        {"vtype": "pagination", "name": "pagerows", "data": 10},
        {"vtype": "pagination", "name": "totalrows", "data": 0},
        {"vtype": "pagination", "name": "page", "data": 1},
        {"vtype": "pagination", "name": "sortName", "data": ""},
        {"vtype": "pagination", "name": "sortFlag", "data": ""}
    ]
}

data = {
    "postData": json.dumps(post_data, separators=(',', ':')),
    "bh": "",
    "ddiInstance": "urn:ddi:ZJJCKSTAT:a463a4d9-806b-4fcc-8fc9-b43a8ee4298c:1",
    "groupUrn": "",
    "studyUnitUrn": "",
    "instrumentSchemeUrn": "",
    "bgqb": "N",
    "projectId": "zj",
    "dqCode": "33"
}

# 转换为 JSON 字符串
data = json.dumps(data, separators=(',', ':'))

# 发送请求
response = requests.post(url, headers=headers, cookies=cookies, params=params, data=data)

response.encoding = 'utf-8'

# 解析返回的 JSON
data_json = json.loads(response.text)
print(data_json)
# 提取发布日期
# rows = data_json["data"]["data"][0]["data"]["rows"]
#
# for i, item in enumerate(rows):
#     bsItemUrn = data_json["data"]["data"][0]["data"]["rows"][i]["bsItemUrn"]
#     bgq = data_json["data"]["data"][0]["data"]["rows"][i]["bgq"]
#     taskId = data_json["data"]["data"][0]["data"]["rows"][i]["taskId"]
#     instrumentNumber = data_json["data"]["data"][0]["data"]["rows"][i]["instrumentNumber"]
#     url = headers["Referer"] + f"#/wholeTableData/queryDetail?taskId={taskId}&bgq={bgq}&instrumentNumber={instrumentNumber}"
#     id = data_json["data"]["data"][0]["data"]["rows"][i]["Id"]
#
#     post_data = {
#         "data": [
#             {"vtype": "attr", "name": "bsItemUrn", "data": bsItemUrn},
#             {"vtype": "attr", "name": "bgq", "data": bgq},
#             {"vtype": "attr", "name": "dqCode", "data": "33"},
#             {"vtype": "attr", "name": "instrumentNumber", "data": instrumentNumber}
#         ]
#     }
#     data3 = json.dumps({"postData": json.dumps(post_data, separators=(',', ':'))}, separators=(',', ':'))
#
#     # 注意：mgop 要求 postData 是一个“JSON字符串”，所以要用 json.dumps 再包一层
#     params2 = {
#         "token": "",
#         "ak": "udqmn52d+2001941911+elgttz",
#         "api": "mgop.gw.sjzj.zbcxgetReportHtmlByCondition",
#         "ts": timestamp,
#
#         "data": "null"
#     }
#     sign = generate_sign(**params2)
#     params2['sign'] = sign
#
#     # data3 = json.dumps(data3, separators=(',', ':'))
#     response2 = requests.post(url, headers=headers, cookies=cookies, params=params2, data=data3)
#
#     print(response2.text)
#     # 解析返回的 JSON
#     # data_json2 = json.loads(response2.text)
#     # html_raw = data_json2["data"]["data"][4]["data"]  # 这里取出完整的 HTML 字符串
#     # soup = BeautifulSoup(body_html, "html.parser")
#     #
#     # # 2. 提取表格（只取第一个表格）
#     # table_html = str(soup.find("table"))
#     # #
#     # # 3. 使用 pandas 解析为 DataFrame（无需保存 Excel）
#     # content = pd.read_html(table_html)[0]
#     #
#     #
#     # url = headers['Referer'] + '#/wholeTableData/queryDetail?' + 'taskId=' + taskId + '&' + 'bgq=' + bgq + '&' + 'instrumentNumber=' + instrumentNumber
#     # publish_time = data_json2["data"]["data"][0]["data"]
#     # title = data_json2["data"]["data"][1]["data"]
#     # body_html = html_raw
#     # content = content
#     # images = [],
#     # print(url,publish_time,title,body_html,content,)
#
