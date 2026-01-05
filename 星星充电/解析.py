#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
云快充 / 四川充电桩小程序
按【城市】采集，使用代理
边采集、边写 CSV（不中断、不丢数据）
"""

import hashlib
import json
import time
import uuid
import requests
import csv
from json import loads
from os.path import exists
from loguru import logger
from public import ProxyPool

proxypool = ProxyPool()

# ======================================================
# 1. 签名工具
# ======================================================

def _js_stringify(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple)):
        return ",".join(_js_stringify(v) for v in value)
    if isinstance(value, dict):
        return "[object Object]"
    return str(value)


def canonical_query(params: dict) -> str:
    return "&".join(
        f"{k}={_js_stringify(params[k])}"
        for k in sorted(params)
        if params[k] is not None
    )


def md5_hex(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def generate_nonce() -> str:
    return str(uuid.uuid4())


def generate_timestamp_ms() -> int:
    return int(time.time() * 1000)


def generate_x_ca_signature(params: dict) -> str:
    s = canonical_query(params)
    md5_1 = md5_hex(s)
    md5_2 = md5_hex(md5_1 + _js_stringify(params["timestamp"]))
    return md5_2.upper()


# ======================================================
# 2. 解析单个站点
# ======================================================

def parse_stub_group(item: dict) -> dict:
    return {
        "station_id": item.get("id"),
        "station_name": item.get("name"),
        "operator_id": item.get("cspId"),
        "city_code": item.get("city"),
        "address": item.get("address"),
        "lat": item.get("gisGcj02Lat"),
        "lng": item.get("gisGcj02Lng"),
        "ac_cnt": item.get("acCnt"),
        "dc_cnt": item.get("dcCnt"),
        "dc_idle_cnt": item.get("dcIdleCnt"),
        "max_power_kw": item.get("equipmentUpKw"),
    }


# ======================================================
# 3. 读取四川城市
# ======================================================

CITY_JSON = "./static/yunkuaichong_city.json"
if not exists(CITY_JSON):
    raise RuntimeError(f"缺少城市文件: {CITY_JSON}")

with open(CITY_JSON, "r", encoding="utf-8") as f:
    CITY_DATA = loads(f.read())


def read_sichuan_cities():
    for c in CITY_DATA.get("city", []):
        if c.get("pCityName") == "四川省":
            yield c


# ======================================================
# 4. 主采集逻辑（边采集边写 CSV）
# ======================================================

URL = "https://gateway.sccncdn.com/apph5/xcxApiV2/wechat/stubGroup/list/query/noUser"

HEADERS_BASE = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36 "
        "MicroMessenger/7.0.20.1781 MiniProgramEnv/Windows"
    ),
    "Content-Type": "application/x-www-form-urlencoded",
    "x-uid": "ozGb50GA8a8SEq5jomuK8s3QNI0c",
    "channel-id": "100",
    "appVersion": "8.1.0.2",
    "positCity": "510100",
    "Referer": "https://servicewechat.com/wxb8e2ba3a621b447d/298/page-frame.html",
}


def main():
    seen_ids = set()
    csv_file = "sichuan_stubgroup_all.csv"

    logger.info("开始采集四川省充电站数据（边采集边写 CSV）")

    # ========= 打开 CSV（只打开一次） =========
    with open(csv_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "station_id", "station_name", "operator_id",
                "city_code", "address",
                "lat", "lng",
                "ac_cnt", "dc_cnt", "dc_idle_cnt",
                "max_power_kw"
            ]
        )
        writer.writeheader()

        # ========= 开始采集 =========
        for city in read_sichuan_cities():
            city_name = city["cityName"]
            lng = city["lng"]
            lat = city["lat"]

            logger.info(f"开始采集城市：{city_name}")

            page = 1
            city_count = 0

            while True:
                data = {
                    "allStation": "1",
                    "equipmentType": "0",
                    "lng": lng,
                    "lat": lat,
                    "orderType": "1",
                    "page": str(page),
                    "pagecount": "10",
                    "radius": "20000",
                    "stubGroupTypes": "0,1",
                }

                data["nonce"] = generate_nonce()
                data["timestamp"] = generate_timestamp_ms()

                headers = dict(HEADERS_BASE)
                headers["X-Ca-Signature"] = generate_x_ca_signature(data)
                headers["X-Ca-Timestamp"] = str(data["timestamp"])

                proxy = proxypool.get_proxy()

                try:
                    resp = requests.post(
                        URL,
                        headers=headers,
                        data=data,
                        proxies=proxy,
                        timeout=10
                    )
                    resp_json = resp.json()
                except Exception as e:
                    logger.error(f"{city_name} 第 {page} 页失败 | 代理={proxy} | {e}")
                    continue

                if resp_json.get("code") != "200":
                    break

                rows = resp_json.get("data", [])
                if not rows:
                    break

                for item in rows:
                    sid = item.get("id")
                    if not sid or sid in seen_ids:
                        continue

                    seen_ids.add(sid)
                    city_count += 1

                    parsed = parse_stub_group(item)

                    # ====== 关键：立刻写一行 CSV ======
                    writer.writerow(parsed)

                    logger.info(f"[{city_name}] 站点 {city_count}")
                    logger.info(json.dumps(parsed, ensure_ascii=False))

                page += 1
                time.sleep(0.4)

            logger.info(f"{city_name} 采集完成，共 {city_count} 个站点")

    logger.info(f"全部采集完成，CSV 文件已生成：{csv_file}")


if __name__ == "__main__":
    main()
