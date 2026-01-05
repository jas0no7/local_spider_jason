import requests
import json
import execjs
import time
wxn_jm_path = './static/wxn_jm.js'
with open(wxn_jm_path, 'r', encoding='utf-8') as f:
    js_code = f.read()
ctx = execjs.compile(js_code)
timestamp = int(time.time()*1000)



def encry_data(post_data):
    encry_data = ctx.call('wxn_post_data', post_data)
    return encry_data


def decry_data(data):
    decry_data = ctx.call('wxn_decry_data', data)
    return decry_data


def get_detail(stationOnlyId):
    detail_url = 'https://ahzhyy.ahcce.com/api/recharge-mobile/app/station/info'
    detail_post_data = {"stationOnlyId": "{}".format(stationOnlyId), "stationLng": "117.227239", "stationLat": "31.820586", "isRecharge": 0}
    data = {
        "data": encry_data(detail_post_data)
    }
    d_url = detail_url.split('api')[1]
    signature = ctx.call('get_signature', encry_data(detail_post_data), timestamp, d_url)
    headers = {
        "Connection": "keep-alive",
        "x-recharge-systemnum": "8.0.5",
        "x-recharge-timestamp": "{}".format(timestamp),
        "x-recharge-device": "ab8157c0-8164-484a-ace9-53423a938fa4",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.3 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1 wechatdevtools/1.06.2310080 MicroMessenger/8.0.5 Language/zh_CN webview/",
        "content-type": "application/json",
        "x-recharge-signature": "{}".format(signature),
        "x-recharge-sourcetype": "1",
        "x-recharge-version": "1.0.0",
        "Accept": "*/*",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://servicewechat.com/wx75ee3cc4ffd9a1a3/devtools/page-frame.html"
    }
    response = requests.post(detail_url, headers=headers, json=data)
    print(response.status_code)
    print(response)
    data = json.loads(response.text).get('data')
    result3 = decry_data(data)
    print(result3)
    print('这是详情页的数据？包含价格？？：' + str(result3))


def get_gun(stationOnlyId):
    gun_url = 'https://ahzhyy.ahcce.com/api/recharge-mobile/app/station/getConnectorList'
    gun_data = {"stationOnlyId":"{}".format(stationOnlyId),"status":-1,"chargeType":"","current":"1","size":"9999"}
    data = {
        "data": encry_data(gun_data)
    }
    g_url = gun_url.split('api')[1]
    signature = ctx.call('get_signature', encry_data(gun_data), timestamp, g_url)
    headers = {
        "Connection": "keep-alive",
        "x-recharge-systemnum": "8.0.5",
        "x-recharge-timestamp": "{}".format(timestamp),
        "x-recharge-device": "ab8157c0-8164-484a-ace9-53423a938fa4",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.3 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1 wechatdevtools/1.06.2310080 MicroMessenger/8.0.5 Language/zh_CN webview/",
        "content-type": "application/json",
        "x-recharge-signature": "{}".format(signature),
        "x-recharge-sourcetype": "1",
        "x-recharge-version": "1.0.0",
        "Accept": "*/*",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://servicewechat.com/wx75ee3cc4ffd9a1a3/devtools/page-frame.html"
    }
    response = requests.post(gun_url, headers=headers, json=data)
    print(response.status_code)
    print(response)
    data = json.loads(response.text).get('data')
    gun = decry_data(data)
    print('这是枪的数据：' + str(gun))


def get_list():
    post_data = {
        "current": 1,
        "size": 10,
        "areaCode": "3401",
        "sortRules": 1,
        "radius": "",
        "stationLng": "117.227239",
        "stationLat": "31.820586"
    }
    index_url = "https://ahzhyy.ahcce.com/api/recharge-mobile/app/station/page"
    data = {
        "data": encry_data(post_data)
    }
    i_url = index_url.split('api')[1]
    signature = ctx.call('get_signature', encry_data(post_data), timestamp, i_url)
    headers = {
        "Connection": "keep-alive",
        "x-recharge-systemnum": "8.0.5",
        "x-recharge-timestamp": "{}".format(timestamp),
        "x-recharge-device": "ab8157c0-8164-484a-ace9-53423a938fa4",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.3 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1 wechatdevtools/1.06.2310080 MicroMessenger/8.0.5 Language/zh_CN webview/",
        "content-type": "application/json",
        "x-recharge-signature": "{}".format(signature),
        "x-recharge-sourcetype": "1",
        "x-recharge-version": "1.0.0",
        "Accept": "*/*",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://servicewechat.com/wx75ee3cc4ffd9a1a3/devtools/page-frame.html"
    }
    response = requests.post(index_url, headers=headers, json=data, verify=False)
    print(response.status_code)
    response_text = response.text
    print(response_text)
    data = json.loads(response_text).get('data')
    result2 = json.loads(decry_data(data))
    records = result2.get('data').get('records')
    for record in records:
        print('这是首页的数据:' + str(record))
        stationOnlyId = record.get('stationOnlyId')
        stationName = record.get('stationName')
        address = record.get('address')
        get_detail(stationOnlyId)
        get_gun(stationOnlyId)


if __name__ == '__main__':
    get_list()
