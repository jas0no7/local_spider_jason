# !/usr/bin/env python
# _*_ coding: utf-8 _*_

"""云快充app
"""

from hashlib import md5
from json import loads, dumps
from os.path import exists
from random import uniform, sample
from string import ascii_lowercase, digits
from time import time, sleep

from loguru import logger
from requests import post as requests_post
from urllib3 import disable_warnings

import config
from public import YkcSichuanTemporary, date_interval, MyCrypto, ProxyPool, MyThreadPoolExecutor, UserAgent, get_now_date, scheduler, charge_filter_is_cq

disable_warnings()

json_path = './static/yunkuaichong_city.json'
if not exists(json_path):
    raise Exception(f'不存在依赖文件, 退出: {json_path}')

with open(json_path, 'r', encoding='utf-8') as f_city:
    _city = loads(f_city.read())
search_city = _city.get("city", [])

table_basic = config.DB_BASIC
table_detail = config.DB_DETAIL
table_terminal = config.DB_TERMINAL
table_origin_price = config.DB_ORIGIN_PRICE

proxypool = ProxyPool()
mycrypto = MyCrypto()
ua = UserAgent()

requests_timeout = config.TIMEOUT
fail_retry = config.RETRY

_string = digits + ascii_lowercase
# aes key
AES_KEY = "v587wf2bqwdswhnb"
# aes iv 偏移量
AES_IV = "whnbqwdswf2bv587"
# hmac md5 的 key
HmacMd5_KEY = "75d46199475ce40b"
# requests headers
headers = {
    'Host': 'gw3.ykccn.com',
    'Content-Type': 'application/json;charset=UTF-8',
    'Origin': 'null',
    'Cipher-Type': '1',
    'Accept': 'application/json, text/plain, */*',
    'Authorization': 'MT-AUTHORIZATION',
    'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
}
# aes加密中的header的值
_aes_header = {
    "version": "0",
    "token": "",
    "isSecurity": "",
    "security": "",
    "businessID": "",
    "isSync": "0",
    "syncSignal": "",
    "expendTime": "",
    "resultCode": "",
    "resultDesc": "",
    "accessKey": "app6000000576936459",
}
# 查找站点的url
search_url = 'https://gw3.ykccn.com/api/omp/mt/os/powerStation/queryNewPowerStationList'
# 站点详情的url
station_url = 'https://gw3.ykccn.com/api/omp/mt/os/powerStation/queryStationDetail'

# 终端
terminal_url = 'https://gw3.ykccn.com/api/omp/mt/os/powerStation/queryPileListByPileType'

_from = '云快充'
status_map = {
    '0': '离线',
    '3': '充电中',
    '2': '空闲',
    '1': '故障'
}


def search_station(_info, batch):
    """
    开始的搜索 主要是获取站点的id 经纬度
    :param batch: 批次
    :param _info: 城市的信息 如经纬度
    :return:
    """
    latitude = _info.get('latitude')
    longitude = _info.get('longitude')
    city_name = _info.get('cityName')
    city_id = _info.get('cityCode')
    _body = {
        "terminalType": "1",
        'latitude': latitude,
        'longitude': longitude,
        'preferCondition': '2',
        'pileType': [],
        'label': [],
        'parkType': [],
        'parkFee': [],
        'pilePower': [],
        'pileVoltage': [],
        'cityId': city_id,
        'userId': None,
        'whichFirst': '0',
        'stationName': ''
    }
    _body = dumps(_body, separators=(',', ':'))
    page_num = 1
    is_flag = 0
    while True:
        if is_flag > fail_retry:
            break

        timestamp = int(time() * 1000)
        nonce = ''.join(sample(_string, 4))
        sign = mycrypto.hmac_md5(key=HmacMd5_KEY, text=f'{_body}{timestamp}{nonce}', is_log=False).upper()
        _header = {
            **_aes_header,
            "timestamp": timestamp,
            "nonce": nonce,
            "sign": sign,
            "isChannelUser": None
        }
        params = {
            "header": _header,
            "body": _body,
            "pageIndex": page_num,
            "pageSize": 10
        }
        enc_data = dumps(params, separators=(',', ':'))
        requests_headers = {
            'User-Agent': ua.ios()
        }
        requests_headers.update(headers)
        try:
            data = mycrypto.aes_cbc_encrypt(key=AES_KEY, iv=AES_IV, text=enc_data, is_log=False)
            proxies = proxypool.get_proxy()
            with requests_post(search_url, headers=requests_headers, proxies=proxies, data=data, timeout=requests_timeout, verify=False) as response:
                response = response.json()
        except Exception as e:
            logger.debug(f'请求{city_name}的第 {page_num} 页 出错 {e}')
            is_flag += 1
        else:
            total_page = response.get('totalPage', 0)
            total_count = response.get('totalCount', 0)
            if not total_count:
                logger.info(f'{city_name}没有数据, 退出!')
                break

            datas = response.get('body')
            with MyThreadPoolExecutor(max_workers=6) as th:
                for data in datas:
                    station_id = data.get('stationId')
                    dup = md5(f'cq_basic_{station_id}_{_from}'.encode('utf-8')).hexdigest()
                    if charge_filter_is_cq(dup):
                        logger.info(f'当前站点 {dup} 不是四川省所属站点, 跳过!')
                        continue

                    item = {
                        'station_id': station_id,
                        'lng': data.get('longitude'),
                        'lat': data.get('latitude'),
                        'city': city_name,
                        'batch': batch
                    }
                    th.submit(get_station_detail, item)
                    th.submit(get_terminal, dup, station_id, batch)

            if page_num < total_page:
                page_num += 1
                is_flag = 0
                logger.info(f'开始请求 {city_name} 的第 {page_num} 页数据！')
            else:
                logger.info(f'{city_name} 数据获取完成！')
                break


def get_station_detail(_item):
    """
    站点详情
    :param _item: 站点的经纬度 和id等
    :return:
    """
    station_id = _item.get('station_id')
    station_body = {
        'userId': '',
        'stationId': station_id,
        'longitude': _item.get('lng'),
        'latitude': _item.get('lat'),
        "terminalType": "1",
        "cityId": "2585",
        "appTag": "V1.0"
    }
    station_body = dumps(station_body, separators=(',', ':'))
    batch = _item.get('batch')
    is_flag = 0
    while True:
        if is_flag > fail_retry:
            logger.debug(f'请求出错次数太多, 退出: {_item}')
            break
        timestamp = int(time() * 1000)
        nonce = ''.join(sample(_string, 4))
        sign = mycrypto.hmac_md5(key=HmacMd5_KEY, text=f'{station_body}{timestamp}{nonce}', is_log=False).upper()
        _header = {
            "timestamp": timestamp,
            "nonce": nonce,
            "sign": sign,
            "isChannelUser": None
        }
        _header.update(_aes_header)
        station_params = {
            "header": _header,
            "body": station_body,
        }
        station_enc_data = dumps(station_params, separators=(',', ':'))
        requests_headers = {
            'User-Agent': ua.ios(),
        }
        requests_headers.update(headers)
        data = mycrypto.aes_cbc_encrypt(key=AES_KEY, iv=AES_IV, text=station_enc_data, is_log=False)
        proxies = proxypool.get_proxy()
        try:
            with requests_post(station_url, headers=requests_headers, proxies=proxies, data=data, timeout=requests_timeout, verify=False) as response:
                response = response.json()
        except Exception as e:
            logger.debug(f'请求 {_item} 出错 {e}')
            is_flag += 1
            sleep(uniform(0.5, 1.2))
        else:
            data = response.get('body')
            if not data:
                break

            label_list = data.get('labelList', [])
            if not label_list:
                tags = ''
            else:
                tags = [i.get('labelName', '') for i in label_list if i.get('labelName', '')]

            duplicate = md5(f'cq_basic_{station_id}_{_from}'.encode('utf-8')).hexdigest()
            item_basic = {
                'duplicate': duplicate,
                'station_id': station_id,
                'lng': _item.get('lng'),
                'lat': _item.get('lat'),
                'name': data.get('stationName'),
                'address': data.get('stationPosition'),
                'operator': data.get('siteOperator'),
                'tags': tags,
                'business_hours': data.get('businessTime'),
                'park_fee_desc': data.get('parkingFee'),
                'from': _from,
                'spider_date': get_now_date(),
                'update_date': get_now_date(),
                'table_name': table_basic,
            }
            YkcSichuanTemporary(item_basic)

            original_price_id = f"{duplicate}_{batch}"
            item_detail = {
                'duplicate': duplicate,
                'station_id': station_id,
                'batch': batch,
                'price': data.get('total'),
                'fast_num': data.get('quickChargeTotalNum'),
                'slow_num': data.get('slowChargeTotalNum'),
                'fast_idle_num': data.get('quickChargeFreeNum'),
                'slow_idle_num': data.get('slowChargeTotalNum'),
                'spider_date': get_now_date(),
                'table_name': table_detail,
                'original_price_id': original_price_id,
            }
            YkcSichuanTemporary(item_detail)

            original_price = [{
                'electricPrice': data.get('electFee'),
                'servicePrice': data.get('serviceFee'),
                'timeRange': data.get('currentBilling')
            }]
            origin_price_item = {
                'duplicate': duplicate,
                'station_id': station_id,
                'original_price_id': original_price_id,
                'original_price': original_price,
                'spider_date': get_now_date(),
                'table_name': table_origin_price
            }
            YkcSichuanTemporary(origin_price_item)

            break


def get_terminal(duplicate, station_id, batch):
    """
    终端
    :param duplicate:
    :param station_id:
    :param batch:
    :return:
    """

    for _ty in ['直流', '交流']:
        is_flag = 0
        while True:
            if is_flag > fail_retry:
                logger.info('请求次数太多, 退出!')
                break

            timestamp = int(time() * 1000)
            nonce = ''.join(sample(_string, 4))
            body = {"stationId": station_id, "userId": "", "pileType": _ty}
            body = dumps(body, ensure_ascii=False, separators=(',', ':'))
            sign = mycrypto.hmac_md5(key=HmacMd5_KEY, text=f'{body}{timestamp}{nonce}', is_log=False).upper()
            _headers_body = {
                "version": "0",
                "token": "",
                "isSecurity": "",
                "security": "",
                "businessID": "",
                "isSync": "0",
                "syncSignal": "",
                "expendTime": "",
                "resultCode": "",
                "resultDesc": "",
                "accessKey": "app6000000576936459",
                "timestamp": timestamp,
                "nonce": nonce,
                "sign": sign,
                "isChannelUser": None
            }

            data = {
                "header": _headers_body,
                "body": body,
                "pageIndex": 1,
                "pageSize": 100
            }
            station_enc_data = dumps(data, separators=(',', ':'))

            requests_headers = {
                'User-Agent': ua.ios(),
            }
            requests_headers.update(headers)
            data = mycrypto.aes_cbc_encrypt(key=AES_KEY, iv=AES_IV, text=station_enc_data, is_log=False)
            try:
                proxies = proxypool.get_proxy()
                with requests_post(terminal_url, headers=requests_headers, data=data, proxies=proxies, verify=False, timeout=requests_timeout) as response:
                    data = response.json().get('body').get('dataList')
            except Exception as e:
                logger.debug(f'请求 {station_id} 出错：{e}')
                is_flag += 1
            else:
                for i in data:
                    terminal_code = i.get('gunNo')
                    state = i.get('gunStatus')
                    gun_connect_status = i.get('gunConnectStatus')
                    state = '已插枪' if gun_connect_status == '1' and state == '2' else status_map.get(state, state)

                    item = {
                        'duplicate': duplicate,
                        'station_id': station_id,
                        'batch': batch,
                        'terminal_code': terminal_code,
                        'state': state,
                        'terminal_name': i.get('gunName'),
                        'terminal_type': i.get('pileType'),
                        'power': i.get('power'),
                        'voltage': i.get('workVoltage'),
                        'spider_date': get_now_date(),
                        'table_name': table_terminal
                    }
                    YkcSichuanTemporary(item)

            break


def main():
    batch = date_interval()
    for info in search_city:
        province = info.get('pCityName')
        if province not in ['四川省']:
            continue
        search_station(info, batch)
    logger.success(f'云快充 {batch} 批次数据获取完成')


def run_scheduler():
    cron = {
        **config.CRON_BASE,
        "minute": "01,31",
        "second": "19",
    }
    scheduler([
        {
            'func': main,
            'cron': cron,
            'message': f"充电桩-{_from}",
            'file_path': __file__,
            'job_id': 'spider_charge_cq_ykc'
        },
    ])


if __name__ == '__main__':
    main()
    run_scheduler()
