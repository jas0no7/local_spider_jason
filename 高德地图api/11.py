import requests
import pandas as pd
import time


def company_to_location(name, key, retries=2):
    """根据公司名称获取地址与经纬度"""
    place_url = "https://restapi.amap.com/v3/place/text"
    params = {"key": key, "keywords": name, "city": "", "offset": 1}

    for attempt in range(retries + 1):
        try:
            response = requests.get(place_url, params=params, timeout=5)
            data = response.json()
        except Exception as e:
            if attempt < retries:
                print(f"⚠️ 第{attempt+1}次请求异常，重试中：{e}")
                time.sleep(1)
                continue
            return {"input_name": name, "error": f"请求异常：{e}"}

        # 状态码检查
        if data.get("status") != "1":
            return {"input_name": name, "error": f"API返回错误：{data.get('info', '未知错误')}"}

        pois = data.get("pois", [])
        if pois and isinstance(pois, list):
            poi = pois[0]
            return {
                "name": poi.get("name", ""),
                "input_name": name,
                "address": poi.get("address", ""),
                "location": poi.get("location", ""),
                "city": poi.get("cityname", ""),
                "district": poi.get("adname", "")
            }
        else:
            return {"input_name": name, "error": "未找到公司"}

    return {"input_name": name, "error": "未知错误"}


# ===============================
# 主程序
# ===============================
if __name__ == "__main__":
    key = "eba83a0da02d1375e2b3edd01aad0161"
    df = pd.read_excel("company222.xls")  # Excel中有“企业名称”列
    company_names = df["企业名称"].dropna().tolist()

    results = []
    for i, name in enumerate(company_names, 1):
        res = company_to_location(name, key)
        results.append(res)
        print(f"{i}/{len(company_names)} -> {res}")
        time.sleep(0.5)  # 降低速率防封IP

    result_df = pd.DataFrame(results)
    result_df.to_excel("company_with_address2222.xlsx", index=False)
    print("✅ 已保存到 company_with_address2222.xlsx")
