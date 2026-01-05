#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
e充电 - 仅采集基础表数据
直接写入本地 CSV 文件（不使用 MySQL / Kafka / config）
"""

import base64
import csv
import json
import time
from hashlib import md5
from json import loads
from os import path
from platform import system
from random import uniform
from datetime import datetime
from threading import Lock

import execjs
import requests
from loguru import logger
from urllib3 import disable_warnings

disable_warnings()

# =====================================================
# 基础配置
# =====================================================
_from = "e充电"
fail_retry = 3
max_workers = 6

search_station_url = "https://applite-evone-wx.echargenet.com/echargeassets/open/es/findStation"
detail_url = "https://applite-evone-wx.echargenet.com/echargeassets/open/es/queryStationInfo"

# =====================================================
# CSV 文件
# =====================================================
today = datetime.now().strftime("%Y%m%d")
CSV_FILE = f"sichuan_echarge_basic_{today}.csv"

CSV_FIELDS = [
    "duplicate",
    "station_id",
    "name",
    "lng",
    "lat",
    "address",
    "operator",
    "tags",
    "business_hours",
    "park_fee_desc",
    "is_open",
    "from",
    "spider_date",
    "update_date",
]

csv_lock = Lock()

def init_csv():
    if not path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()

def write_csv(row: dict):
    with csv_lock:
        with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writerow(row)

# =====================================================
# 请求头基础信息
# =====================================================
device = "ecdH5"
appid = "1233123"
version = "3070000"
api = "1.0.0"
profile = "1"
area = "12312"

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Content-Type": "application/json;charset=UTF-8",
    "Host": "applite-evone-wx.echargenet.com",
    "Origin": "https://cdn-evone-oss.echargenet.com",
    "Referer": "https://cdn-evone-oss.echargenet.com/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/116.0.0.0 Safari/537.36 "
        "MicroMessenger/7.0.20.1781 MiniProgramEnv/Windows"
    ),
    "channel": device,
    "x-evone-api": api,
    "x-evone-area": area,
    "x-evone-auth-ticket": "",
    "x-evone-device": device,
    "x-evone-meta-appid": appid,
    "x-evone-profile": profile,
    "x-evone-request-id": "",
    "x-evone-version": version,
}

# =====================================================
# JS 国密依赖
# =====================================================
gm_js_path = "./static/gm.js"
city_path = "./static/sichuan.json"

if not path.exists(gm_js_path) or not path.exists(city_path):
    raise RuntimeError("缺少 gm.js 或 sichuan.json")

with open(gm_js_path, "r", encoding="utf-8") as f:
    js_code = f.read()

cwd = None if system() == "Windows" else "/usr/local/lib/node_modules"
js_compile = execjs.compile(js_code, cwd=cwd)

with open(city_path, "r", encoding="utf-8") as f:
    cities = loads(f.read()).get("area", [])

# =====================================================
# 工具函数
# =====================================================
def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_signature(data: str) -> str:
    timestamp = int(time.time() * 1000)

    sm2_msg = f"{timestamp}evone"
    sm2_data = js_compile.call("sm2encrypt", sm2_msg)

    sm3_data = js_compile.call(
        "sm3encrypt",
        base64.b64encode(data.encode("utf-8")).decode("utf-8"),
    )

    raw = "\n".join([
        sm2_msg,
        "POST",
        sm3_data,
        headers["Content-Type"],
        str(timestamp),
        f"x-evone-api{api}"
        f"x-evone-area{area}"
        f"x-evone-auth-ticket"
        f"x-evone-device{device}"
        f"x-evone-meta-appid{appid}"
        f"x-evone-profile{profile}"
        f"x-evone-request-id"
        f"x-evone-version{version}",
    ])

    sm4_data = js_compile.call("sm4encrypt", raw)
    return f"EVOneUni:04{sm2_data}:{sm4_data}"

# =====================================================
# 采集基础信息
# =====================================================
def fetch_basic(station_id: str, duplicate: str):
    retry = 0
    while retry <= fail_retry:
        payload = {"id": station_id}
        data_json = json.dumps(payload, separators=(",", ":"))

        _headers = {
            "x-evone-signature": get_signature(data_json),
            **headers,
        }

        try:
            resp = requests.post(
                detail_url,
                data=data_json,
                headers=_headers,
                timeout=5,
                verify=False,
            )
            result = resp.json()
            if result.get("code") not in [1, "1"]:
                return

            data = js_compile.call("sm2decrypt", result.get("data"))
        except Exception as e:
            retry += 1
            logger.debug(f"{station_id} 请求失败: {e}")
            time.sleep(uniform(1, 2))
            continue

        tags = data.get("labelsAll") or []
        tags = [t.get("name") for t in tags if isinstance(t, dict)]

        row = {
            "duplicate": duplicate,
            "station_id": station_id,
            "name": data.get("stationName"),
            "lng": data.get("lng"),
            "lat": data.get("lat"),
            "address": data.get("address"),
            "operator": data.get("operatorName"),
            "tags": "|".join(tags),
            "business_hours": data.get("openTimeInfo"),
            "park_fee_desc": data.get("priceParking"),
            "is_open": data.get("open"),
            "from": _from,
            "spider_date": now_str(),
            "update_date": now_str(),
        }

        write_csv(row)
        logger.info(f"写入 CSV 成功: {station_id}")
        return

# =====================================================
# 搜索站点
# =====================================================
def search_station(lat, lng, city_name):
    logger.info(f"开始采集城市: {city_name}")

    payload = {
        "cityCode": "500100",
        "point": {"direction": 0, "lat": lat, "lng": lng},
        "radius": 50000,
        "stationType": 55,
        "searchType": 3,
        "sortBy": 1,
    }

    data_json = json.dumps(payload, separators=(",", ":"))

    retry = 0
    while retry <= fail_retry:
        _headers = {
            "x-evone-signature": get_signature(data_json),
            **headers,
        }

        try:
            resp = requests.post(
                search_station_url,
                data=data_json,
                headers=_headers,
                timeout=5,
                verify=False,
            )
            stations = resp.json().get("data") or []
        except Exception as e:
            retry += 1
            logger.debug(f"{city_name} 搜索失败: {e}")
            time.sleep(uniform(1, 2))
            continue

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            for s in stations:
                if s.get("searchType") != 1:
                    continue
                station_id = s.get("id")
                duplicate = md5(
                    f"cq_basic_{station_id}_{_from}".encode("utf-8")
                ).hexdigest()
                pool.submit(fetch_basic, station_id, duplicate)
        return

# =====================================================
# 主入口
# =====================================================
def main():
    init_csv()
    for c in cities:
        search_station(c.get("lat"), c.get("lng"), c.get("name"))
    logger.success("e充电基础表采集完成（CSV）")

if __name__ == "__main__":
    main()
