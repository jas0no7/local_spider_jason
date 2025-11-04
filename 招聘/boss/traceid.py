#!/usr/bin/env python3
"""
Boss 直聘小程序 traceid 生成与时间解析（逆向实现）

生成规则（与小程序一致）：
- 前缀：'F-'
- 时间片段：当前毫秒时间的 16 进制字符串末 6 位
- 随机片段：从 '0-9a-zA-Z' 中等概率选择 10 个字符拼接

时间解析：
- 从 traceid[2:8] 取出 6 位 16 进制的低 24bit；
- 与“参考时间（默认当前时间）去掉低 24bit”的高位相加，得到还原时间。
  注意：该方法只在 ~4.66 小时窗口内成立（2^24 ms 回绕）。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import random
import time
from typing import Optional

_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def generate_boss_traceid() -> str:
    """生成与小程序一致的 traceid。"""
    ms = int(time.time() * 1000)
    tail6 = format(ms, "x")[-6:]
    rand10 = "".join(random.choice(_ALPHABET) for _ in range(10))
    return f"F-{tail6}{rand10}"


def get_time_from_boss_traceid(traceid: str, ref_ms: Optional[int] = None) -> _dt.datetime:
    """按小程序逻辑从 traceid 还原创建时间（仅在 ~4.66 小时窗口内准确）。

    参数：
        traceid: 形如 'F-xxxxxxYYYYYYYYYY' 的字符串。
        ref_ms: 参考时间的毫秒时间戳（默认使用当前时间）。
    返回：
        Python datetime（本地时区）。
    """
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


def _main():
    parser = argparse.ArgumentParser(description="Generate or parse Boss traceid")
    parser.add_argument("traceid", nargs="?", help="when provided, parse time from traceid instead of generating")
    args = parser.parse_args()

    if args.traceid:
        dt = get_time_from_boss_traceid(args.traceid)
        print(dt.isoformat(sep=" ", timespec="milliseconds"))
    else:
        print(generate_boss_traceid())


if __name__ == "__main__":
    _main()

