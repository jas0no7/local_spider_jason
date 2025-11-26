import json
import requests

from public import mysql, now
import config

# =======================
# 请求头（直接使用你抓包的）
# =======================
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090c37)XWEB/14185",
    "Content-Type": "application/json",
    "xweb_xhr": "1",
    "Authorization": "Basic YXBwOmFwcA==",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://servicewechat.com/wxf376e02e5f71116c/58/page-frame.html",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

# 请求地址
url = "https://gateway.enneagon.cn/charge-ex-miniapp-backend-provider/v5/station/getGunListByStationCodeV2"


# =======================
# 保存到 MySQL
# =======================
def save_gun_list(station_code, gun_list):
    """
    将枪列表写入 MySQL 表：xinjiang_charge_gun
    """
    for gun in gun_list:
        gun["stationCode"] = station_code
        gun["update_time"] = now()
        mysql.insert("xinjiang_charge_gun", gun)
    print(f"成功写入 {len(gun_list)} 条充电枪数据")


# =======================
# 主爬虫逻辑
# =======================
def fetch_gun_list(station_code):
    """
    获取某一个站点的枪列表（多页）
    """
    all_result = []

    for page in range(1, 5):   # 最多跑 4 页，正常只 1 页有数据
        payload = {
            "page": page,
            "stationCode": station_code,
            "size": 10,
            "equipmentType": 1
        }

        response = requests.post(url, headers=headers, json=payload, timeout=config.TIMEOUT)
        response.raise_for_status()

        resp_json = response.json()
        records = resp_json.get("data", {}).get("records", [])

        if not records:
            break

        for item in records:
            bms = item.get("bmsInfo") or {}
            tele = item.get("telecModel") or {}

            gun_info = {
                "gun_index": item.get("gun"),
                "chargingGunCode": item.get("chargingGunCode"),
                "chargingGunName": item.get("chargingGunName"),
                "chargingPileCode": item.get("chargingPileCode"),
                "chargingPileName": item.get("chargingPileName"),
                "chargingGunType": item.get("chargingGunType"),
                "chargingGunPower": item.get("chargingGunPower"),

                # BMS 信息
                "bms_soc": bms.get("soc"),
                "bms_remainTime": bms.get("remainTime"),
                "bms_batteryCapacity": bms.get("brmBatteryCapacity"),
                "bms_ratedVoltage": bms.get("brmRatedVoltage"),
                "bms_batteryManufacturer": bms.get("brmBatteryManufacturer"),
                "bms_vin": bms.get("brmVin"),
                "bms_startDate": bms.get("startDate"),
                "bms_startElect": bms.get("startElect"),
                "bms_batteryVoltage": bms.get("bcpBatteryVoltage"),
                "bms_batteryCurrent": bms.get("bcsCurrent"),
                "plateNumber": bms.get("plateNumber"),

                # 枪状态
                "gunState": tele.get("gunState"),
                "runningState": tele.get("runningState"),
                "connectState": tele.get("connectState"),
                "powerState": tele.get("powerState"),
                "workType": tele.get("workType"),
            }

            all_result.append(gun_info)

    return all_result


# =======================
# 主程序运行入口
# =======================
def run_gun(station_code="207573"):
    """
    获取指定站点的充电枪列表并写入数据库
    """
    gun_list = fetch_gun_list(station_code)

    print(json.dumps(gun_list, ensure_ascii=False, indent=2))

    # 写入数据库
    save_gun_list(station_code, gun_list)

    print(f"\n>>> 站点 {station_code} 枪列表入库完成！")
