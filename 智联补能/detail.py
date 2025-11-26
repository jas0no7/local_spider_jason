import requests
import json
import config
from public import mysql, ua, now


def fetch_station_detail(station_id: str, lat: float, lng: float):
    """
    获取小程序站点详情
    """
    url = "https://gateway.enneagon.cn/charge-ex-miniapp-backend-provider/v5/station/detail"

    headers = {
        "User-Agent": ua.random(),
        "Content-Type": "application/json",
        "xweb_xhr": "1",
        "Authorization": "Basic YXBwOmFwcA==",
        "Referer": "https://servicewechat.com/wxf376e02e5f71116c/58/page-frame.html",
    }

    payload = json.dumps({
        "id": station_id,
        "lat": lat,
        "lng": lng
    }, separators=(',', ':'))

    resp = requests.post(url, headers=headers, data=payload, timeout=config.TIMEOUT)
    resp.raise_for_status()

    return resp.json().get("data", {}) or {}


def parse_station(data_obj: dict):
    """
    解析字段 → dict（可直接写库）
    """
    # 行政区划
    area_path = data_obj.get("areaNamePath") or ""
    parts = area_path.split("/") if area_path else []
    province = parts[0] if len(parts) > 0 else None
    city = parts[1] if len(parts) > 1 else None
    district = parts[2] if len(parts) > 2 else None

    # 图片
    image_urls = [
        img.get("url") for img in (data_obj.get("stationImages") or [])
        if img.get("url")
    ]

    return {
        "stationId": data_obj.get("id"),
        "stationCode": data_obj.get("code"),
        "stationName": data_obj.get("name"),
        "stationType": data_obj.get("stationType"),

        "areaNamePath": area_path,
        "province": province,
        "city": city,
        "district": district,

        "address": data_obj.get("address"),
        "lng": data_obj.get("lng"),
        "lat": data_obj.get("lat"),
        "distance_km": data_obj.get("distance"),

        "isOpenAllday": data_obj.get("isOpenAllday"),
        "businessHoursDesc": data_obj.get("businessHoursDesc"),
        "tel": data_obj.get("tel"),
        "servicePhoneNo": data_obj.get("servicePhoneNo"),

        "gunNum": data_obj.get("gunNum"),
        "fastCount": data_obj.get("fastCount"),
        "fastFree": data_obj.get("fastFree"),
        "slowCount": data_obj.get("slowCount"),
        "slowFree": data_obj.get("slowFree"),

        # json.dumps 确保可写入 MySQL
        "imageUrls": json.dumps(image_urls, ensure_ascii=False),
        "update_time": now()
    }


def save_to_db(item: dict):
    """
    写入 MySQL
    """
    mysql.insert(config.DB_DETAIL, item)
    print("写入成功:", item["stationName"])


if __name__ == "__main__":
    # 示例：采集 66378 号站
    raw_data = fetch_station_detail(
        station_id="66378",
        lat=30.57447052,
        lng=103.92376709
    )

    station_info = parse_station(raw_data)
    save_to_db(station_info)

    print(json.dumps(station_info, ensure_ascii=False, indent=2))
