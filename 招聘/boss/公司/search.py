import json
import requests
import pandas as pd

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a1b)XWEB/14185",
    "mini_ver": "13.2000",
    "ua": "{\"model\":\"microsoft\",\"platform\":\"windows\"}",
    "zp_app_id": "10002",
    "Content-Type": "application/x-www-form-urlencoded",
    "mpt": "93fbbe218851c0664c1efd1de1acf90c",
    "Referer": "https://servicewechat.com/wxa8da525af05281f3/585/page-frame.html",
}

url = "https://www.zhipin.com/wapi/zpgeek/miniapp/search/brandlist.json"

df = pd.read_excel("科研企业名单.xlsx")
company_names = df["企业名称"].dropna().tolist()

results = []

for name in company_names:
    params = {
        "pageSize": "20",
        "query": name,
        "city": "101000000",
        "page": "1",
        "appId": "10002"
    }
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    data = resp.json()
    brand_list = data.get("zpData", {}).get("brandList", [])
    if brand_list:
        brand_id = brand_list[0].get("brandId") or brand_list[0].get("encryptBrandId")
    else:
        brand_id = None
    results.append({"company_name": name, "brand_id": brand_id})
    print(results)

with open("brand_id_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
