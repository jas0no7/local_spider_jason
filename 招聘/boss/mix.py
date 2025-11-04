#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Boss 直聘小程序 traceid 生成与请求示例（完整整合版）

功能：
1. 自动生成与小程序一致的 traceid；
2. 使用该 traceid 访问推荐岗位接口；
3. 可选：解析 traceid 生成时间。
"""

import time
import random
import datetime as _dt
import requests
from typing import Optional

# ---------------------------
# TraceID 生成与解析模块
# ---------------------------
_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def generate_boss_traceid() -> str:
    """生成与小程序一致的 traceid。"""
    ms = int(time.time() * 1000)
    tail6 = format(ms, "x")[-6:]
    rand10 = "".join(random.choice(_ALPHABET) for _ in range(10))
    return f"F-{tail6}{rand10}"


def get_time_from_boss_traceid(traceid: str, ref_ms: Optional[int] = None) -> _dt.datetime:
    """按小程序逻辑从 traceid 还原创建时间（仅在 ~4.66 小时窗口内准确）。"""
    if not (isinstance(traceid, str) and len(traceid) >= 8 and traceid.startswith("F-")):
        raise ValueError("invalid traceid format")

    low_hex = traceid[2:8]
    low_val = int(low_hex, 16)
    if ref_ms is None:
        ref_ms = int(time.time() * 1000)

    ref_low = int(format(ref_ms, "x")[-6:], 16)
    base = ref_ms - ref_low
    ts = base + low_val
    return _dt.datetime.fromtimestamp(ts / 1000.0)


# ---------------------------
# 请求模块101210100
#        101270100
# ---------------------------
def fetch_boss_jobs(city_code="101270100", page=2):
    """发起 Boss 直聘小程序职位请求"""
    traceid = generate_boss_traceid()
    print(f"[+] Generated traceid: {traceid}")
    print(f"[+] TraceID time: {get_time_from_boss_traceid(traceid)}\n")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 "
            "MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI "
            "MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a1b)XWEB/14185"
        ),
        "mini_ver": "13.1901",
        "ua": '{"model":"microsoft","platform":"windows"}',
        "wt2": "",
        "zp_app_id": "10002",
        "content-type": "application/x-www-form-urlencoded",
        "traceid": traceid,
        "mpt": "93b0bda2f7fe388c8465cbdc6de87bd2",
        "scene": "1260",
        "xweb_xhr": "1",
        "x-requested-with": "XMLHttpRequest",
        "zp_product_id": "10002",
        "platform": "zhipin/windows",
        "ver": "13.1901",
        "referer": "https://servicewechat.com/wxa8da525af05281f3/584/page-frame.html",
        "accept-language": "zh-CN,zh;q=0.9",
    }

    url = "https://www.zhipin.com/wapi/zpgeek/miniapp/homepage/recjoblist.json"
    params = {
        "cityCode": city_code,
        "sortType": "1",
        "page": str(page),
        "pageSize": "15",
        "encryptExpectId": "cb1494e0c1011eccynU~",
        "districtCode": "",
        "mixExpectType": "9",
        "expectId": "-1",
        "positionLv1": "p_100000",
        "positionLv2": "p_0",
        "positionLv3": "",
        "positionType": "2",
        "appId": "10002",
    }

    response = requests.get(url, headers=headers, params=params)
    print("[+] Response status:", response.status_code)
    print("[+] Response text:\n", response.text)
    return response


# ---------------------------
# 主程序入口
# ---------------------------
if __name__ == "__main__":
    fetch_boss_jobs()
