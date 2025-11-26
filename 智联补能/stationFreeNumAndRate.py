import json
import requests

from public import mysql, now
import config


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090c37)XWEB/14185",
    "Content-Type": "application/json",
    "xweb_xhr": "1",
    "Authorization": "Basic YXBwOmFwcA==",
    "Referer": "https://servicewechat.com/wxf376e02e5f71116c/58/page-frame.html",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

url = "https://gateway.enneagon.cn/charge-ex-miniapp-backend-provider/v5/station/stationFreeNumAndRate"


# ================================
# 写入主表：xinjiang_charge_rate
# ================================
def save_rate_main(item):
    item["update_time"] = now()
    mysql.insert("xinjiang_charge_rate", item)


# ================================
# 写入分时表：xinjiang_charge_rate_detail
# ================================
def save_rate_detail(station_code, rate_list):
    for phase in rate_list:
        phase["stationCode"] = station_code
        phase["update_time"] = now()
        mysql.insert("xinjiang_charge_rate_detail", phase)


# ================================
# 获取费率接口数据
# ================================
def fetch_rate(station_code):
    payload = json.dumps({
        "stationEquipmentType": 1,
        "stationCode": station_code
    }, separators=(',', ':'))

    resp = requests.post(url, headers=headers, data=payload, timeout=config.TIMEOUT)
    resp.raise_for_status()

    data_obj = (resp.json().get("data") or {})
    station_rate = data_obj.get("stationRateDTO") or {}

    # 顶层 rate
    main_rate = {
        "stationCode": station_code,
        "freeNum": data_obj.get("freeNum"),
        "totalNum": data_obj.get("totalNum"),
        "rate": data_obj.get("rate"),

        "currentPhaseIndex": station_rate.get("currentPhaseIndex"),
        "currentPhaseType": station_rate.get("currentPhaseType"),
        "currentStartTime": station_rate.get("currentStartTime"),
        "currentEndTime": station_rate.get("currentEndTime"),
        "currentElectricPrice": station_rate.get("currentElectricPrice"),
        "currentServicePrice": station_rate.get("currentServicePrice"),
        "currentElectricPriceSwapGun": station_rate.get("currentElectricPriceSwapGun"),
        "currentServicePriceSwapGun": station_rate.get("currentServicePriceSwapGun"),
        "currentDiscountElectricPrice": station_rate.get("currentDiscountElectricPrice"),
        "currentDiscountServicePrice": station_rate.get("currentDiscountServicePrice"),
    }

    # 分时电价列表
    rate_list = []
    for phase in station_rate.get("rateList") or []:
        rate_list.append({
            "phaseIndex": phase.get("phaseIndex"),
            "phaseType": phase.get("phaseType"),
            "startTime": phase.get("startTime"),
            "endTime": phase.get("endTime"),
            "electricPrice": phase.get("electricPrice"),
            "servicePrice": phase.get("servicePrice"),
            "electricPriceSwapGun": phase.get("electricPriceSwapGun"),
            "servicePriceSwapGun": phase.get("servicePriceSwapGun"),
            "discountElectricPrice": phase.get("discountElectricPrice"),
            "discountServicePrice": phase.get("discountServicePrice"),
        })

    return main_rate, rate_list


# ================================
# 主程序入口
# ================================
def run_rate(station_code="207573"):
    """
    统一执行费率采集 + 入库
    """
    main_rate, rate_list = fetch_rate(station_code)

    print("主费率：", json.dumps(main_rate, ensure_ascii=False, indent=2))
    print("分时费率：", json.dumps(rate_list, ensure_ascii=False, indent=2))

    save_rate_main(main_rate)
    save_rate_detail(station_code, rate_list)

    print(f"\n>>> 站点 {station_code} 费率入库完成！")