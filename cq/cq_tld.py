# _*_ coding: utf-8 _*_
"""特来电app 采集脚本 (增加本地存储与错误日志功能)"""
import csv
import threading
from hashlib import md5
from json import loads, dumps
from os import path
from random import uniform, choice, sample, randint
from time import sleep, time
from urllib.parse import urlencode, quote_plus
from uuid import uuid4
from loguru import logger
from requests import post as requests_post
import config
from public import (
    charge_kafka, date_interval, charge_filter, MyRedis, MyCrypto,
    ProxyPool, MyThreadPoolExecutor, get_now_date, scheduler, charge_filter_is_cq
)

# --- 全局配置与锁 ---
csv_lock = threading.Lock()
ERROR_LOG_PATH = "terminal_error.log"


def save_to_csv(item):
    """
    通用追加保存函数
    :param item: 包含 table_name 的数据字典
    """
    if not item or 'table_name' not in item:
        return

    # 文件名为配置中的表名.csv
    file_name = f"{item['table_name']}.csv"

    with csv_lock:
        file_exists = path.exists(file_name)
        with open(file_name, 'a', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=item.keys())
            if not file_exists:
                writer.writeheader()  # 第一次创建时写入表头
            writer.writerow(item)


def save_error_log(station_id, reason):
    """
    保存错误日志到另一份文件
    """
    with csv_lock:
        with open(ERROR_LOG_PATH, 'a', encoding='utf-8') as f:
            log_time = get_now_date()
            f.write(f"{log_time} | 站点ID: {station_id} | 原因: {reason}\n")


# --- 原有参数初始化 ---
_x_token = config.REDIS_TLD_X_TOKEN
table_basic = config.DB_BASIC
table_detail = config.DB_DETAIL
table_terminal = config.DB_TERMINAL
table_origin_price = config.DB_ORIGIN_PRICE

myredis = MyRedis()
proxypool = ProxyPool()
mycrypto = MyCrypto()
requests_timeout = config.TIMEOUT
fail_retry = config.RETRY
DES_KEY = 'UQInaE9V'
DES_IV = 'siudqUQoprVNjiA7'
AES_KEY = '7fb498553e3c462988c3b9573692bd5f'
AES_IV = '98d71fe589499967'

# URL 列表
login_url = 'https://sg.teld.cn/api/invoke?SID=UserAPI-APP-ASLogin'
token_url = 'https://sg.teld.cn/api/invoke?SID=UserAPI-APP-ASRefreshToken'
search_url = 'https://sg.teld.cn/api/invoke?SID=AAS-App0407_SearchStation'
operator_url = 'https://sg.teld.cn/api/invoke?SID=AAS-App0407_GetStationDetails'
origin_price_url = 'https://sg.teld.cn/api/invoke?SID=AAS-App0407_GetPriceInfoBySta'
terminal_url = 'https://sg.teld.cn/api/invoke?SID=BaseApi-App0304_GetTerminalOfStation'

# 读取城市信息
_path = './static/tld_city.json'
if not path.exists(_path):
    raise Exception('不存在依赖文件')
with open(_path, 'r', encoding='utf-8') as f_run:
    area_data = loads(f_run.read()).get('data')

_from = '特来电'
_headers = {
    "Cookie": "domain=.teld.cn;path=/",
    "a_c": "10000",
    "a_r": "10000",
    "TELDAppID": "",
    "AppOS": "Android",
    "AppVersion": "5.16.0",
    "ACOL": "",
    "ARS": "app",
    "TokenRelative": "NetFrameworkUpgrade",
    "Content-Type": "application/x-www-form-urlencoded",
    "Host": "sg.teld.cn",
}

acoi = [{"city_name": c.get('city_name'), "city_code": c.get('city_code', '110000')[:2 if len(p.get('city')) == 1 else 4]} for p in area_data for c in p.get('city')]
device = "network=wifi&app_version=5.16.0&client=android&os_version=9&device_nickname=2210132C&device_name=null&device_id={}&city_code={}&city_name={}&location_city_name=&lat=0.0&lng=0.0"
ascii_string = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


def str2int(num):
    try:
        return int(num)
    except:
        return 1


def get_params():
    device_nickname = ''.join(sample(ascii_string, 6))
    user_agent = f"Dalvik/2.1.0 (Linux; U; Android {randint(8, 12)}; {device_nickname} Build/PQ3B.{randint(100000, 1000000)}.0{randint(1000000, 10000000)})"
    uuid_dev = uuid4().hex
    device_id = uuid4().hex.upper()
    acoi_info = choice(acoi)
    return {**acoi_info, "user_agent": user_agent, "uuid_dev": uuid_dev, "device_id": device_id}


def as_login():
    is_flag = 0
    while True:
        if is_flag > fail_retry: return {}
        params_info = get_params()
        uuid_dev = params_info.get('uuid_dev')
        device_id = params_info.get('device_id')
        dtime = str(int(time()))
        acoi_city = params_info.get('city_name')
        acoi_code = params_info.get('city_code')
        user_agent = params_info.get('user_agent')
        headers = {
            "Device": device.format(device_id, acoi_code, quote_plus(acoi_city)),
            "ASDI": device_id,
            "ACOI": quote_plus(acoi_city),
            "ATS": dtime,
            "AVER": mycrypto.des_cbc_encryt(key=DES_KEY, iv=DES_IV, text=dtime, is_log=False),
            "DeviceTime": dtime,
            "User-Agent": user_agent,
            **_headers
        }
        uts = f'{int(time())}'
        uver = mycrypto.aes_cbc_encrypt(key=AES_KEY, iv=AES_IV, text=uts, is_log=False)[:16]
        param_data = dumps({"DeviceType": "APP", "DeviceId": device_id, "ReqSource": "0"}, ensure_ascii=False, separators=(',', ':'))
        login_info = {
            "UTS": uts, "UVER": uver,
            "Data": mycrypto.aes_cbc_encrypt(key=f'{uts}000000', iv=uver, text=param_data, is_log=False),
            "UUID": uuid_dev
        }
        post_data = urlencode({"loginInfo": login_info})
        try:
            proxies = proxypool.get_proxy()
            with requests_post(login_url, headers=headers, data=post_data, proxies=proxies, timeout=requests_timeout) as res:
                enc_data = res.json().get('data')
        except Exception as e:
            logger.debug(f'请求登陆数据错误: {e}')
            is_flag += 1
            sleep(uniform(3, 5))
            continue

        if not enc_data: return {}
        decrypt_data = loads(mycrypto.aes_cbc_decrypt(key=AES_KEY, iv=AES_IV, text=enc_data, is_log=False))
        real_data = loads(mycrypto.aes_cbc_decrypt(key=decrypt_data.get('UTS') + "000000", iv=decrypt_data.get('UVER'), text=decrypt_data.get('Data'), is_log=False))
        item = {**params_info, "access_token": real_data.get('AccessToken'), "refresh_token": real_data.get('RefreshToken')}
        myredis.string_setex(name=_x_token, expire_time=30 * 24 * 3600, value=dumps(item, ensure_ascii=False), is_log=False)
        logger.success(f'登录成功！')
        break


def get_x_token():
    is_flag = 0
    while True:
        if is_flag > fail_retry: break
        x_token_info = myredis.string_get(key=_x_token, is_log=False)
        if not x_token_info:
            sleep(20);
            continue
        token_info = loads(x_token_info)
        dtime = str(int(time()))
        headers = {
            "Device": device.format(token_info.get('device_id'), token_info.get('city_code'), quote_plus(token_info.get('city_name'))),
            "ASDI": token_info.get('device_id'), "ACOI": quote_plus(token_info.get('city_name')),
            "ATS": dtime, "AVER": mycrypto.des_cbc_encryt(key=DES_KEY, iv=DES_IV, text=dtime, is_log=False),
            "DeviceTime": dtime, "User-Agent": token_info.get('user_agent'), **_headers
        }
        uts = f'{int(time())}'
        uver = mycrypto.aes_cbc_encrypt(key=AES_KEY, iv=AES_IV, text=uts, is_log=False)[:16]
        param_data = dumps({"DeviceType": "APP", "RefreshToken": token_info.get('refresh_token'), "DeviceId": token_info.get('device_id'), "ReqSource": "0"}, separators=(',', ':'))
        refreshtoken = {"UTS": uts, "UVER": uver, "Data": mycrypto.aes_cbc_encrypt(key=f'{uts}000000', iv=uver, text=param_data, is_log=False), "UUID": token_info.get('uuid_dev')}
        data = urlencode({"refreshToken": refreshtoken})
        try:
            proxies = proxypool.get_proxy()
            with requests_post(token_url, headers=headers, data=data, proxies=proxies, timeout=requests_timeout) as res:
                enc_data = res.json().get('data')
        except Exception as e:
            is_flag += 1;
            sleep(3);
            continue

        if not enc_data: break
        decrypt_data = loads(mycrypto.aes_cbc_decrypt(key=AES_KEY, iv=AES_IV, text=enc_data, is_log=False))
        real_data = loads(mycrypto.aes_cbc_decrypt(key=decrypt_data.get('UTS') + "000000", iv=decrypt_data.get('UVER'), text=decrypt_data.get('Data'), is_log=False))
        token_info.update({"access_token": real_data.get('AccessToken'), "refresh_token": real_data.get('RefreshToken')})
        myredis.string_setex(name=_x_token, expire_time=30 * 24 * 3600, value=dumps(token_info, ensure_ascii=False), is_log=False)
        logger.success(f'Token 刷新成功')
        break


def search_station(batch, city_code, city_name, area_code, province):
    acoi_city = quote_plus(city_name)
    page_num, page_size, page_count, is_flag = 1, 50, 1, 0
    batches = [f'{batch[:8]}000000', f'{batch[:8]}230000']

    while True:
        if is_flag >= fail_retry: break
        ats = int(time())
        x_token = myredis.string_get(key=_x_token, is_log=False)
        if not x_token: sleep(20); continue
        token_info = loads(x_token)
        headers = {
            "ATS": f'{ats}', "AVER": mycrypto.des_cbc_encryt(key=DES_KEY, iv=DES_IV, text=f'{ats}', is_log=False),
            "DeviceTime": f'{ats + 38}', "X-Token": token_info.get('access_token'), "ASDI": token_info.get('device_id'),
            "ACOI": acoi_city, "Device": device.format(token_info.get('device_id'), city_code, acoi_city),
            "User-Agent": token_info.get('user_agent'), **_headers
        }
        param = {
            "source": "app", "coordinateType": "gaode", "power": "15-360", "locationFilterType": "3",
            "locationFilterValue": area_code, "itemNumPerPage": f'{page_size}', "pageNum": f'{page_num}',
        }
        data = urlencode({'param': param})
        try:
            proxies = proxypool.get_proxy()
            with requests_post(search_url, headers=headers, data=data, proxies=proxies, timeout=requests_timeout) as response:
                content = response.json().get('data')
        except Exception as e:
            is_flag += 1;
            sleep(2);
            continue

        _count = str2int(content.get('pageCount', '1'))
        page_count = min(max(page_count, _count), 25)
        stations = content.get('stations', [])

        with MyThreadPoolExecutor(max_workers=5) as th:
            for station in stations:
                station_id = station.get('id')
                if not station_id: continue
                dup = md5(f'cq_basic_{station_id}_{_from}'.encode('utf-8')).hexdigest()
                if charge_filter_is_cq(dup): continue

                item_basic = {
                    'duplicate': dup, 'station_id': station_id, 'name': station.get('name'),
                    'lng': station.get('lng'), 'lat': station.get('lat'), 'district': station.get('businessDistrict'),
                    'address': station.get('stationAddress'), 'station_type': station.get('stationType'),
                    'business_hours': station.get('businessHours'), 'from': _from, 'spider_date': get_now_date(),
                    'table_name': table_basic,
                }
                save_to_csv(item_basic)  # 追加保存本地
                charge_kafka(item_basic)

                original_price_id = f"{dup}_{batch[:8]}"
                item_detail = {
                    'duplicate': dup, 'station_id': station_id, 'price': station.get('nowPrice'),
                    'fast_num': station.get('fastTerminalNum'), 'slow_num': station.get('slowTerminalNum'),
                    'original_price_id': original_price_id, 'batch': batch, 'spider_date': get_now_date(),
                    'table_name': table_detail
                }
                save_to_csv(item_detail)  # 追加保存本地
                charge_kafka(item_detail)

                th.submit(get_terminal, duplicate=dup, city_code=city_code, city_name=city_name, station_id=station_id, batch=batch)
                if batch in batches or not charge_filter(f'cq_original_price_{original_price_id}'):
                    th.submit(get_origin_price, duplicate=dup, original_price_id=original_price_id, city_code=city_code, city_name=city_name, station_id=station_id)
                if not charge_filter(f'cq_operator_{station_id}_{_from}_{batch[:6]}'):
                    th.submit(get_operator, duplicate=dup, city_code=city_code, city_name=city_name, station_id=station_id)

        if page_num >= page_count:
            break
        else:
            page_num += 1; is_flag = 0


def get_operator(duplicate, city_code, city_name, station_id):
    acoi_city = quote_plus(city_name)
    operator_flag = 0
    while True:
        x_token = myredis.string_get(key=_x_token, is_log=False)
        if not x_token: sleep(10); continue
        token_info = loads(x_token)
        if operator_flag > fail_retry: break
        ats = int(time())
        headers = {
            "ATS": f'{ats}', "AVER": mycrypto.des_cbc_encryt(key=DES_KEY, iv=DES_IV, text=f'{ats}', is_log=False),
            "X-Token": token_info.get('access_token'), "ASDI": token_info.get('device_id'), "ACOI": acoi_city,
            "Device": device.format(token_info.get('device_id'), city_code, acoi_city), "User-Agent": token_info.get('user_agent'), **_headers
        }
        param = {"stationId": station_id, "source": "app"}
        try:
            proxies = proxypool.get_proxy()
            with requests_post(operator_url, headers=headers, data=urlencode({'param': param}), proxies=proxies, timeout=requests_timeout) as res:
                data = res.json().get('data', {})
        except Exception:
            operator_flag += 1;
            sleep(1);
            continue

        item_operator = {'duplicate': duplicate, 'operator': data.get('operatorName'), 'table_name': table_basic}
        save_to_csv(item_operator)
        charge_kafka(item_operator)
        break


def get_origin_price(duplicate, original_price_id, city_code, city_name, station_id):
    acoi_city = quote_plus(city_name)
    price_is_flag = 0
    while True:
        x_token = myredis.string_get(key=_x_token, is_log=False)
        if not x_token: sleep(10); continue
        token_info = loads(x_token)
        if price_is_flag > fail_retry: break
        ats = int(time())
        headers = {
            "ATS": f'{ats}', "AVER": mycrypto.des_cbc_encryt(key=DES_KEY, iv=DES_IV, text=f'{ats}', is_log=False),
            "X-Token": token_info.get('access_token'), "ASDI": token_info.get('device_id'), "ACOI": acoi_city,
            "Device": device.format(token_info.get('device_id'), city_code, acoi_city), "User-Agent": token_info.get('user_agent'), **_headers
        }
        try:
            proxies = proxypool.get_proxy()
            with requests_post(origin_price_url, headers=headers, data=urlencode({'param': {"stationID": station_id}}), proxies=proxies, timeout=requests_timeout) as res:
                data = res.json().get('data', [{'rangePrice': []}])[0].get('rangePrice', [])
        except Exception:
            price_is_flag += 1;
            sleep(1);
            continue

        if data:
            _item = {'duplicate': duplicate, 'station_id': station_id, 'original_price_id': original_price_id, 'original_price': data, 'spider_date': get_now_date(), 'table_name': table_origin_price}
            save_to_csv(_item)
            charge_kafka(_item)
        break


def get_terminal(duplicate, city_code, city_name, station_id, batch):
    """获取终端数据，包含异常日志处理"""
    acoi_city = quote_plus(city_name)
    terminal_is_flag = 0
    while True:
        x_token = myredis.string_get(key=_x_token, is_log=False)
        if not x_token: sleep(10); continue
        token_info = loads(x_token)
        if terminal_is_flag > fail_retry: break
        ats = int(time())
        headers = {
            "ATS": f'{ats}', "AVER": mycrypto.des_cbc_encryt(key=DES_KEY, iv=DES_IV, text=f'{ats}', is_log=False),
            "X-Token": token_info.get('access_token'), "ASDI": token_info.get('device_id'), "ACOI": acoi_city,
            "Device": device.format(token_info.get('device_id'), city_code, acoi_city), "User-Agent": token_info.get('user_agent'), **_headers
        }
        param = {"stationId": station_id, "power": "15-360"}
        try:
            proxies = proxypool.get_proxy()
            with requests_post(terminal_url, headers=headers, data=urlencode({'param': param}), proxies=proxies, timeout=requests_timeout) as response:
                # 尝试解析 JSON，如果失败会抛出异常
                res_json = response.json()
                terminal_datas = res_json.get('data', [])
        except Exception as e:
            # --- 需求：保存为另一份日志文件 ---
            logger.warning(f'终端接口返回非 JSON，跳过该站点: {station_id}')
            save_error_log(station_id, f"非JSON返回或请求错误: {str(e)}")
            break
        else:
            if not terminal_datas:
                terminal_is_flag += 1;
                sleep(1);
                continue

            for terminal in terminal_datas:
                item = {
                    'duplicate': duplicate, 'station_id': station_id, 'batch': batch,
                    'terminal_code': terminal.get('terminalCode'), 'terminal_name': terminal.get('terminalName'),
                    'state': terminal.get('stateName'), 'power': terminal.get('power'),
                    'spider_date': get_now_date(), 'table_name': table_terminal
                }
                save_to_csv(item)  # 保存到本地
                charge_kafka(item)
            break


def run_token():
    as_login()
    get_x_token()


def main():
    batch = date_interval()
    for p in area_data:
        pro = p.get('province')
        if pro not in ['四川省']: continue
        for c in p.get('city'):
            area_code = ','.join([i.get('area_code') for i in c.get('area')])
            search_station(batch, c.get('city_code')[:4], c.get('city_name'), area_code, pro)
            sleep(uniform(3, 5))
    logger.success(f'{_from} 批次 {batch} 完成')


def run_scheduler():
    cq_cron = {**config.CRON_BASE, "minute": "04,30", "second": "35"}
    cron_token = {**config.CRON_BASE, "minute": "03,33", "second": "15"}
    scheduler([
        {'func': main, 'cron': cq_cron, 'job_id': 'spider_tld_main'},
        {'func': run_token, 'cron': cron_token, 'job_id': 'spider_tld_token'}
    ])


if __name__ == '__main__':
    logger.info("脚本启动")
    run_token()
    main()
    run_scheduler()