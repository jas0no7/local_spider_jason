#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
云快充 / 四川充电桩小程序
stubGroup list 查询（自动生成 X-Ca-Signature）
"""

import hashlib
import json
import time
import uuid
import requests


# ======================================================
# 1. 签名相关工具函数（从你原脚本中“抽精华”）
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
    pairs = []
    for key in sorted(params.keys()):
        val = params[key]
        if val is None:
            continue
        pairs.append(f"{key}={_js_stringify(val)}")
    return "&".join(pairs)


def md5_hex(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def generate_nonce() -> str:
    return str(uuid.uuid4())


def generate_timestamp_ms() -> int:
    return int(time.time() * 1000)


def generate_x_ca_signature(params: dict) -> str:
    canonical = canonical_query(params)
    md5_1 = md5_hex(canonical)
    md5_2 = md5_hex(md5_1 + _js_stringify(params["timestamp"]))
    return md5_2.upper()


# ======================================================
# 2. 构造请求并发送
# ======================================================

def main():
    url = "https://gateway.sccncdn.com/apph5/xcxApiV2/wechat/stubGroup/list/query/noUser"

    # --------- 基础业务参数（你后面只改这里）---------
    data = {
        "allStation": "1",
        "equipmentType": "0",
        "lat": "30.570199966430664",
        "lng": "104.06475830078125",
        "orderType": "1",
        "page": "1",
        "pagecount": "10",
        "radius": "10000",
        "stubGroupTypes": "0,1",
    }

    # --------- 动态参数 ---------
    nonce = generate_nonce()
    timestamp = generate_timestamp_ms()

    data["nonce"] = nonce
    data["timestamp"] = timestamp

    # --------- 生成签名 ---------
    x_ca_signature = generate_x_ca_signature(data)

    # --------- headers ---------
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36 "
            "MicroMessenger/7.0.20.1781 MiniProgramEnv/Windows"
        ),
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Ca-Signature": x_ca_signature,
        "X-Ca-Timestamp": str(timestamp),
        "x-uid": "ozGb50GA8a8SEq5jomuK8s3QNI0c",
        "channel-id": "100",
        "appVersion": "8.1.0.2",
        "positCity": "510100",
        "Referer": "https://servicewechat.com/wxb8e2ba3a621b447d/298/page-frame.html",
    }

    print(">>> 请求参数 data：")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("\n>>> X-Ca-Signature:", x_ca_signature)

    # --------- 发起请求 ---------
    resp = requests.post(url, headers=headers, data=data, timeout=10)

    print("\n>>> HTTP 状态码:", resp.status_code)
    print(">>> 返回内容:")
    print(resp.text)


if __name__ == "__main__":
    main()
