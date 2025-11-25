import json
import time
import signal
from hashlib import md5
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from loguru import logger

from public import ProxyPool, UserAgent, MyRedis


# ==========================================================
# 初始化组件
# ==========================================================
proxy_pool = ProxyPool()
ua = UserAgent()
redis = MyRedis()

URL = "https://data.stats.gov.cn/easyquery.htm"


def now():
    return datetime.now(tz=ZoneInfo("PRC")).strftime("%Y-%m-%d %H:%M:%S")


base_headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://data.stats.gov.cn/easyquery.htm?cn=E0101",
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "cookie": "u=2; JSESSIONID=xxx"
}

# 全局数据
result_map = {}
exit_flag = False


# 捕捉 Ctrl+C
def exit_handler(sig, frame):
    global exit_flag
    exit_flag = True
    logger.warning("检测到中断信号，正在安全保存数据...")


signal.signal(signal.SIGINT, exit_handler)
signal.signal(signal.SIGTERM, exit_handler)


# 请求函数：带代理 + 重试
def safe_get(url, headers, params, retry=3):
    for i in range(retry):
        try:
            headers["User-Agent"] = ua.random()
            proxies = proxy_pool.get_proxy()

            resp = requests.get(url, headers=headers, params=params,
                                proxies=proxies, timeout=10)
            return resp.json()
        except Exception as e:
            logger.warning(f"请求失败({i+1}/{retry})：{e}")
            time.sleep(1)
    return None


# 增量保存
def save_now():
    with open("national_data.json", "w", encoding="utf-8") as f:
        json.dump(list(result_map.values()), f, ensure_ascii=False, indent=4)
    logger.info("增量保存完成（national_data.json）")


# ==========================================================
# 加载输入文件
# ==========================================================
with open("le3_output.json", "r", encoding="utf-8") as f:
    zhibiao = json.load(f)

with open("regions.json", "r", encoding="utf-8") as f:
    regions = json.load(f)


# ==========================================================
# 主程序
# ==========================================================
try:
    for le1_name, le2_list in zhibiao.items():

        if exit_flag:
            break

        for le2_dict in le2_list:
            for le2_name, leaf_list in le2_dict.items():

                for item in leaf_list:

                    if exit_flag:
                        break

                    # ==========================================================
                    # 自动适配：优先使用 le3，其次使用 le2（用于 table_name）
                    # ==========================================================
                    if "le3_id" in item:
                        indicator_id = item["le3_id"]
                        indicator_name = item["le3_name"]   # 最后一级标签
                    elif "le2_id" in item:
                        indicator_id = item["le2_id"]
                        indicator_name = item["le2_name"]   # 最后一级标签
                    else:
                        logger.warning(f"未知指标结构：{item}")
                        continue

                    # 地区循环
                    for city in regions:

                        if exit_flag:
                            break

                        city_code = city["city_code"]
                        city_name = city["city_name"]

                        logger.info(f"开始采集：{city_name} - {indicator_name}")

                        params = {
                            "m": "QueryData",
                            "dbcode": "fsyd",
                            "rowcode": "sj",
                            "colcode": "zb",
                            "wds": f'[{{"wdcode":"reg","valuecode":"{city_code}"}}]',
                            "dfwds": f'[{{"wdcode":"zb","valuecode":"{indicator_id}"}}]',
                            "k1": "1763086026423",
                            "h": "1"
                        }

                        resp = safe_get(URL, base_headers.copy(), params)
                        if not resp or "returndata" not in resp:
                            logger.warning(f"{city_name} 无数据/失败")
                            save_now()
                            continue

                        returndata = resp.get("returndata", {})
                        datanodes = returndata.get("datanodes", [])
                        wdnodes = returndata.get("wdnodes", [])

                        zb_map, reg_map, sj_map = {}, {}, {}

                        try:
                            for wd in wdnodes:
                                wdcode = wd.get("wdcode")
                                for node in wd.get("nodes", []):
                                    code = node.get("code")
                                    name = node.get("cname") or node.get("name")
                                    if wdcode == "zb":
                                        zb_map[code] = name
                                    elif wdcode == "reg":
                                        reg_map[code] = name
                                    elif wdcode == "sj":
                                        sj_map[code] = name
                        except Exception as e:
                            logger.error(f"解析 wdnodes 错误：{e}")
                            save_now()
                            continue

                        key = f"{indicator_id}_{city_code}"

                        # 初始化结构
                        if key not in result_map:
                            result_map[key] = {
                                "_id": md5(f"{indicator_id}{URL}{city_code}".encode()).hexdigest(),
                                "spider_date": now(),
                                "spider_from": "国家数据",
                                "location": city_name,
                                "标签1": le1_name,
                                "标签2": le2_name,
                                "table_name": indicator_name,    # ← 最底层标签
                                "code": f"zb.{indicator_id}_reg.{city_code}",
                                "content": {}     # 临时结构
                            }

                        content = result_map[key]["content"]

                        # 解析数据
                        for node in datanodes:
                            try:
                                dims = {d["wdcode"]: d["valuecode"] for d in node["wds"]}
                                zb_code = dims.get("zb")
                                sj_code = dims.get("sj")

                                zb_name = zb_map.get(zb_code, zb_code)
                                sj_name = sj_map.get(sj_code, sj_code)

                                value = None
                                if isinstance(node.get("data"), dict):
                                    value = node["data"].get("data")

                                if zb_name not in content:
                                    content[zb_name] = {}

                                content[zb_name][sj_name] = value

                            except Exception as e:
                                logger.error(f"解析 datanode 失败：{e}")
                                continue

                        # ==================================================
                        # content（三层结构） → data（拍平成行结构）
                        # ==================================================
                        all_dates = set()
                        for indicator, values in content.items():
                            all_dates.update(values.keys())

                        data_list = []
                        for sj in sorted(all_dates):
                            row = {"时间": sj}
                            for indicator, values in content.items():
                                row[indicator] = values.get(sj)
                            data_list.append(row)

                        result_map[key]["data"] = data_list
                        del result_map[key]["content"]

                        logger.info(f"完成：{city_name} - {indicator_name}")
                        logger.info(content)

                        save_now()
                        time.sleep(0.3)

except Exception as e:
    logger.error(f"程序发生未捕获异常：{e}")

finally:
    save_now()
    logger.success("脚本结束，数据已完整保存。")
